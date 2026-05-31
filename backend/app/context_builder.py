import textwrap
from typing import Any, Dict, List

from .memory.store import memory_store

DEFAULT_RECENT_MESSAGE_LIMIT = 10
DEFAULT_COMPRESSED_MEMORY_WIDTH = 500
RECALL_RECENT_MESSAGE_LIMIT = 40
RECALL_COMPRESSED_MEMORY_WIDTH = 3000

MEMORY_RECALL_PHRASES = (
    "what do you remember",
    "what you remember",
    "summarize this session",
    "summarize the session",
    "session summary",
    "what happened in this session",
    "recap this session",
    "recap the session",
)


def _is_memory_recall_request(message: str) -> bool:
    lowered = message.lower()
    return any(phrase in lowered for phrase in MEMORY_RECALL_PHRASES)


def _summarize_messages(
    messages: List[Dict[str, Any]],
    width: int = DEFAULT_COMPRESSED_MEMORY_WIDTH,
) -> str:
    """Create a compact summary of older messages."""
    if not messages:
        return ""
    combined = " ".join(m.get("content", "") for m in messages)
    return textwrap.shorten(combined, width=width, placeholder="...")


def _phase_hint(phase: str) -> str:
    """Map a session phase to a short system hint."""
    hints = {
        "architecture_review": "Focus on system design, constraints, and trade-offs.",
        "code_review": "Provide detailed code suggestions and refactoring guidance.",
        "demo_prep": "Help prepare a concise demo narrative and UI walkthrough.",
        "ready": "The system is ready to handle normal user queries.",
    }
    return hints.get(phase, "Proceed with the current user request.")


def build_context(session_id: str) -> Dict[str, Any]:
    """Build structured context for the LLM."""
    full_history: List[Dict[str, Any]] = memory_store.get_session_history(session_id) or []

    latest_user_message = next(
        (
            message.get("content", "")
            for message in reversed(full_history)
            if message.get("role") == "user"
        ),
        "",
    )
    is_memory_recall = _is_memory_recall_request(latest_user_message)
    recent_limit = (
        RECALL_RECENT_MESSAGE_LIMIT
        if is_memory_recall
        else DEFAULT_RECENT_MESSAGE_LIMIT
    )
    compressed_width = (
        RECALL_COMPRESSED_MEMORY_WIDTH
        if is_memory_recall
        else DEFAULT_COMPRESSED_MEMORY_WIDTH
    )

    recent_messages = (
        full_history[-recent_limit:]
        if len(full_history) > recent_limit
        else full_history
    )
    older_messages = (
        full_history[:-recent_limit] if len(full_history) > recent_limit else []
    )
    compressed_memory = _summarize_messages(older_messages, width=compressed_width)

    phase: str = memory_store.get_session_phase(session_id) or ""
    summary_dict: Dict[str, Any] = memory_store.get_session_summary(session_id) or {}
    workflow_state = summary_dict.get("workflow_state") or {}
    workflow_state_str = (
        workflow_state.get("state", "") if isinstance(workflow_state, dict) else ""
    )
    workflow_context = {"phase": phase, "state": workflow_state_str}

    intent_hint = summary_dict.get("summary") or ""
    if isinstance(intent_hint, dict):
        intent_hint = intent_hint.get("summary", "")

    phase_advice = _phase_hint(phase)
    system_context_parts = [
        f"Current phase: {phase}" if phase else "",
        phase_advice,
        f"User intent: {intent_hint}" if intent_hint else "",
    ]
    system_context = " ".join(part for part in system_context_parts if part)

    llm_messages: List[Dict[str, str]] = []
    if compressed_memory:
        llm_messages.append(
            {
                "role": "assistant",
                "content": f"Earlier session summary: {compressed_memory}",
            }
        )
    llm_messages.extend(recent_messages)

    return {
        "system_context": system_context,
        "compressed_memory": compressed_memory,
        "recent_messages": recent_messages,
        "workflow_context": workflow_context,
        "llm_messages": llm_messages,
    }
