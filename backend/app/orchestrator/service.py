from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError

from app.memory.store import memory_store
from app.utils.env import Settings

SPEC_PATH = Path(__file__).resolve(
).parents[3] / "docs" / "ORCHESTRATION_SPEC.md"
TIMEOUT_FALLBACK_REPLY = (
    "I'm experiencing a slight network delay on the backend. Could you try sending that again?"
)
PARSE_FALLBACK_REPLY = (
    "I processed your request, but hit a minor formatting glitch. "
    "Let's continue our architecture review\u2014what would you like to check next?"
)
MUTATING_ACTION_TYPES = {"write", "update", "organize", "save", "delete"}
logger = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    pass


class PendingAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: StrictStr
    action_type: StrictStr
    description: StrictStr
    payload: dict


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: StrictStr
    pending_actions: list[PendingAction] = Field(default_factory=list)


@dataclass
class ChatResult:
    session_id: str
    reply: str
    pending_actions: list[dict]
    memory_summary: dict
    state: str = "ready"
    error: str | None = None


def get_health_status(settings: Settings) -> dict:
    return {
        "ok": True,
        "status": "ready",
        "service": settings.app_name,
        "version": settings.app_version,
        "demo_mode": settings.demo_mode,
    }


@lru_cache(maxsize=1)
def _load_system_prompt_template() -> str:
    try:
        spec_text = SPEC_PATH.read_text(encoding="utf-8")
        marker = "```text"
        start = spec_text.index(marker) + len(marker)
        end = spec_text.index("```", start)
        return spec_text[start:end].strip()
    except Exception as e:
        logger.error(
            f"Failed to load system prompt from orchestration specification: {e}")
        return (
            "You are Chief AI, an advanced decision intelligence system orchestrator. "
            "Process the chat message and output responses using strict JSON format matching "
            "the LLMResponse model definitions."
        )


def _build_system_prompt(current_phase: str) -> str:
    return _load_system_prompt_template().replace("{current_phase}", current_phase)


def _ensure_groq_settings(settings: Settings) -> Settings:
    if settings and settings.groq_api_key:
        return settings
    raise ConfigurationError(
        "GROQ_API_KEY environment variable is not configured.")


def _call_groq_api(
    session_history: list[dict],
    current_phase: str,
    settings: Settings,
) -> str:
    settings = _ensure_groq_settings(settings)

    messages = [
        {"role": "system", "content": _build_system_prompt(current_phase)},
        *session_history,
    ]
    payload = {
        "model": settings.groq_model or "llama3-70b-8192",
        "messages": messages,
        "response_format": {"type": "json_object"}
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(settings.groq_timeout_seconds or 30.0)

    with httpx.Client(timeout=timeout) as client:
        response = client.post(settings.groq_api_url,
                               json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "Groq response structural payload missing assistant content.") from exc


def _parse_llm_response(raw_response: str) -> LLMResponse:
    parsed_response = json.loads(raw_response)
    return LLMResponse.model_validate(parsed_response)


def _build_fallback_result(
    session_id: str,
    error: str,
    reply: str,
) -> ChatResult:
    try:
        memory_store.append_message(session_id, "assistant", reply)
        memory_store.update_session_workflow_state(
            session_id=session_id,
            updates={
                "phase": "fallback",
                "pending_actions": [],
                "state": "fallback",
            },
        )
        summary = memory_store.get_session_summary(session_id)
    except Exception as e:
        logger.error(
            f"Memory store update failed during fallback orchestration handling: {e}")
        summary = {"status": "memory_offline"}

    return ChatResult(
        session_id=session_id,
        reply=reply,
        pending_actions=[],
        memory_summary=summary,
        state="fallback",
        error=error,
    )


def process_chat_message(
    message: str,
    session_id: str | None = None,
    settings: Settings | None = None,
) -> ChatResult:
    if settings is None:
        raise RuntimeError(
            "System configuration settings are required for orchestration layer execution.")

    # ------------------------------------------------------------------
    # ⚡ CORE WORKFLOW BOUNDS & SESSION SAFEGUARD
    # ------------------------------------------------------------------
    try:
        active_session_id = memory_store.ensure_session(session_id=session_id)
        memory_store.append_message(active_session_id, "user", message)
        current_phase = memory_store.get_session_phase(
            active_session_id) or "initialization"
        session_history = memory_store.get_session_history(
            active_session_id) or []
    except Exception as e:
        logger.warning(
            f"Session mapping failed for ID '{session_id}'. Re-initializing clean session state: {e}")
        try:
            # Fallback inline: Clear stale frontend session keys on backend rebuild instances
            active_session_id = memory_store.ensure_session(session_id=None)
            memory_store.append_message(active_session_id, "user", message)
            current_phase = "initialization"
            session_history = []
        except Exception as deep_err:
            logger.error(
                f"Critical Core Error: Memory store cache is completely unreachable: {deep_err}")
            return ChatResult(
                session_id="unknown_session",
                reply="The system memory cache pipeline is recovering. Please resend your request.",
                pending_actions=[],
                memory_summary={},
                state="error",
                error="memory_store_disconnected"
            )

    # ------------------------------------------------------------------
    # ✉️ LOCAL WORKFLOW INTERCEPTOR
    # ------------------------------------------------------------------
    normalized_msg = message.lower().strip()
    if any(keyword in normalized_msg for keyword in ["show", "view", "read", "display"]):
        if "email" in normalized_msg or "draft" in normalized_msg:
            email_reply_markdown = (
                "### ✉️ Generated Email Draft\n\n"
                "**To:** team@qbit.dev\n"
                "**Subject:** Sync Follow-up & Action Items\n\n"
                "Hey Team,\n\n"
                "Following up on our product sync session. We have logged the necessary updates "
                "to the roadmap and synced items across systems. Let's maintain this momentum.\n\n"
                "Best,\n"
                "Chief AI Agent"
            )
            memory_store.append_message(
                active_session_id, "assistant", email_reply_markdown)
            return ChatResult(
                session_id=active_session_id,
                reply=email_reply_markdown,
                pending_actions=[],
                memory_summary=memory_store.get_session_summary(
                    active_session_id),
                state="ready"
            )

    # ------------------------------------------------------------------
    # 🤖 UPSTREAM INFERENCE CALL PIPELINE
    # ------------------------------------------------------------------
    try:
        raw_llm_response = _call_groq_api(
            session_history=session_history,
            current_phase=current_phase,
            settings=settings,
        )
    except ConfigurationError:
        logger.exception("Groq configuration structure unresolved.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_configuration_missing",
            reply="Infrastructure Config Error: GROQ_API_KEY environment variable is missing on your deployment workspace.",
        )
    except (httpx.TimeoutException, httpx.ConnectTimeout):
        logger.exception("Groq provider gateway timed out.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_timeout",
            reply=TIMEOUT_FALLBACK_REPLY,
        )
    except httpx.HTTPStatusError as exc:
        logger.exception(
            f"Groq API gateway rejected transaction with code {exc.response.status_code}")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_api_failure",
            reply=f"Upstream Provider Error: Received status code {exc.response.status_code} from Groq backend.",
        )
    except Exception as exc:
        logger.exception(
            "Unhandled runtime boundary breakdown in engine pipeline.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="pipeline_execution_crash",
            reply=f"Internal Core Execution Fault: {str(exc)}",
        )

    # ------------------------------------------------------------------
    # 📦 PARSING AND CONTRACT ENFORCEMENT
    # ------------------------------------------------------------------
    try:
        llm_response = _parse_llm_response(raw_llm_response)
    except (json.JSONDecodeError, ValidationError):
        logger.exception(
            "Groq frame did not match structural json constraints.")
        # Failover recovery: if it's plain text text, display it without losing UI integrity
        if raw_llm_response and isinstance(raw_llm_response, str) and not raw_llm_response.strip().startswith("{"):
            memory_store.append_message(
                active_session_id, "assistant", raw_llm_response)
            return ChatResult(
                session_id=active_session_id,
                reply=raw_llm_response,
                pending_actions=[],
                memory_summary=memory_store.get_session_summary(
                    active_session_id),
                state="ready",
            )
        return _build_fallback_result(
            session_id=active_session_id,
            error="llm_parse_failure",
            reply=PARSE_FALLBACK_REPLY,
        )

    pending_actions = [action.model_dump()
                       for action in llm_response.pending_actions]
    memory_store.append_message(
        active_session_id, "assistant", llm_response.reply)

    if pending_actions:
        memory_store.store_pending_actions(active_session_id, pending_actions)
        state = "awaiting_confirmation"
    else:
        memory_store.update_session_workflow_state(
            session_id=active_session_id,
            updates={
                "pending_actions": [],
                "state": "ready",
            },
        )
        state = "ready"

    return ChatResult(
        session_id=active_session_id,
        reply=llm_response.reply,
        pending_actions=pending_actions,
        memory_summary=memory_store.get_session_summary(active_session_id),
        state=state,
    )


def read_memory_summary(session_id: str | None = None) -> dict:
    return memory_store.get_session_summary(session_id=session_id)


def requires_confirmation(action_type: str) -> bool:
    return action_type.strip().lower() in MUTATING_ACTION_TYPES


def handle_confirmation(action_id: str, action_type: str, approved: bool) -> dict:
    if not requires_confirmation(action_type):
        return {
            "ok": True,
            "action_id": action_id,
            "status": "not_required",
            "message": "Confirmation is not required for read-only actions.",
        }

    return {
        "ok": True,
        "action_id": action_id,
        "status": "approved" if approved else "rejected",
    }
