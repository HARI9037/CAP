import textwrap
from typing import List, Dict, Any
from app.memory.store import memory_store


def _summarize_messages(messages: List[Dict[str, Any]]) -> str:
    """Create a brief summary of older messages.
    For simplicity we concatenate content and truncate to a reasonable length.
    """
    if not messages:
        return ""
    # Join contents with spaces
    combined = " ".join(m.get("content", "") for m in messages)
    # Truncate to 500 characters, preserving whole words
    return textwrap.shorten(combined, width=500, placeholder="...")


def _phase_hint(phase: str) -> str:
    """Map a session phase to a short system hint."""
    hints = {
        "architecture_review": "Focus on system design, constraints, and trade‑offs.",
        "code_review": "Provide detailed code suggestions and refactoring guidance.",
        "demo_prep": "Help prepare a concise demo narrative and UI walkthrough.",
        "ready": "The system is ready to handle normal user queries.",
    }
    return hints.get(phase, "Proceed with the current user request.")


def build_context(session_id: str) -> Dict[str, Any]:
    """Build a structured context for the LLM.

    Returns a dict with keys:
        system_context, compressed_memory, recent_messages,
        workflow_context, llm_messages
    """
    # --- retrieve raw history ------------------------------------------------
    full_history: List[Dict[str, Any]
                       ] = memory_store.get_session_history(session_id) or []

    # recent 10 messages (preserve order)
    recent_messages = full_history[-10:] if len(
        full_history) > 10 else full_history

    # older messages summary
    older_messages = full_history[:-10] if len(full_history) > 10 else []
    compressed_memory = _summarize_messages(older_messages)

    # --- workflow information ----------------------------------------------
    phase: str = memory_store.get_session_phase(session_id) or ""
    summary_dict: Dict[str, Any] = memory_store.get_session_summary(session_id) or {
    }
    # workflow_state may be stored under "state" or "workflow_state"
    workflow_state = summary_dict.get(
        "state") or summary_dict.get("workflow_state") or ""
    workflow_context = {"phase": phase, "state": workflow_state}

    # --- system context generation ------------------------------------------
    # User intent hint – try to extract a short intent from the memory summary if present
    intent_hint = summary_dict.get("summary") or ""
    if isinstance(intent_hint, dict):
        # Some implementations may store a "summary" string under a key
        intent_hint = intent_hint.get("summary", "")
    phase_advice = _phase_hint(phase)
    system_context_parts = [
        f"Current phase: {phase}" if phase else "",
        phase_advice,
        f"User intent: {intent_hint}" if intent_hint else "",
    ]
    # Filter empty parts and join
    system_context = " ".join(part for part in system_context_parts if part)

    # --- assemble final LLM messages ---------------------------------------
    llm_messages: List[Dict[str, str]] = []
    if system_context:
        llm_messages.append({"role": "system", "content": system_context})
    if compressed_memory:
        llm_messages.append({"role": "system", "content": compressed_memory})
    # Add recent messages preserving their original role/content
    llm_messages.extend(recent_messages)

    return {
        "system_context": system_context,
        "compressed_memory": compressed_memory,
        "recent_messages": recent_messages,
        "workflow_context": workflow_context,
        "llm_messages": llm_messages,
    }
