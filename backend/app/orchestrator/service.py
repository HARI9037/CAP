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

SPEC_PATH = Path(__file__).resolve().parents[3] / "docs" / "ORCHESTRATION_SPEC.md"
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
        logger.error(f"Failed to load system prompt from orchestration specification: {e}")
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
    raise ConfigurationError("GROQ_API_KEY environment variable is not configured.")


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
        response = client.post(settings.groq_api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Groq response structural payload missing assistant content.") from exc


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
        logger.error(f"Memory store update failed during fallback orchestration handling: {e}")
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
        raise RuntimeError("System configuration settings are required for orchestration layer execution.")

    # Core state initialization
    try:
        active_session_id = memory_store.ensure_session(session_id=session_id)
        memory_store.append_message(active_session_id, "user", message)
        current_phase = memory_store.get_session_phase(active_session_id) or "initialization"
        session_history = memory_store.get_session_history(active_session_id) or []
    except Exception as e:
        logger.error(f"Failed to process session memory bounds: {e}")
        return ChatResult(
            session_id=session_id or "unknown_session",
            reply="The system memory cache pipeline is recovering. Please resend your request.",
            pending_actions=[],
            memory_summary={},
            state="error",
            error="memory_store_disconnected"
        )

    # Core LLM processing engine
    try:
        raw_llm_response = _call_groq_api(
            session_history=session_history,
            current_phase=current_phase,
            settings=settings,
        )
    except ConfigurationError as exc:
        logger.exception("Groq provider runtime properties missing.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_configuration_missing",
            reply="Infrastructure Config Error: GROQ_API_KEY environment variable is not populated on your Render environment dashboard.",
        )
    except (httpx.TimeoutException, httpx.ConnectTimeout):
        logger.exception("Groq gateway timed out.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_timeout",
            reply=TIMEOUT_FALLBACK_REPLY,
        )
    except httpx.HTTPStatusError as exc:
        logger.exception(f"Groq upstream interface error returned status code {exc.response.status_code}")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_api_failure",
            reply=f"Upstream API Gateway Error: Received status code {exc.response.status_code} from Groq cloud. Check account balances or service status.",
        )
    except Exception as exc:
        logger.exception("Unhandled runtime error intercepted during pipeline orchestration execution.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="pipeline_execution_crash",
            reply=f"Internal Engine Error: {str(exc)}",
        )

    # Structural verification and conversion
    try:
        llm_response = _parse_llm_response(raw_llm_response)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.exception("Groq structural payload output failed Pydantic contract definition validation checks.")
        # Production recovery: if it's text but not strict JSON, try to wrap it cleanly
        if raw_llm_response and isinstance(raw_llm_response, str) and not raw_llm_response.strip().startswith("{"):
            memory_store.append_message(active_session_id, "assistant", raw_llm_response)
            return ChatResult(
                session_id=active_session_id,
                reply=raw_llm_response,
                pending_actions=[],
                memory_summary=memory_store.get_session_summary(active_session_id),
                state="ready",
            )
        return _build_fallback_result(
            session_id=active_session_id,
            error="llm_parse_failure",
            reply=PARSE_FALLBACK_REPLY,
        )

    pending_actions = [action.model_dump() for action in llm_response.pending_actions]
    memory_store.append_message(active_session_id, "assistant", llm_response.reply)

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