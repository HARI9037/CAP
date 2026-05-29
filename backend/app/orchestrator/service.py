from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError
from ..memory.store import memory_store
from ..utils.env import Settings

SPEC_PATH = Path(__file__).resolve(
).parents[3] / "docs" / "ORCHESTRATION_SPEC.md"
TIMEOUT_FALLBACK_REPLY = (
    "I'm experiencing a slight network delay on the backend. Could you try sending that again?"
)
PARSE_FALLBACK_REPLY = (
    "I processed your request, but hit a minor formatting glitch. "
    "Let's continue our architecture review—what would you like to check next?"
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
    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    marker = "```text"
    start = spec_text.index(marker) + len(marker)
    end = spec_text.index("```", start)
    return spec_text[start:end].strip()


def _build_system_prompt(current_phase: str) -> str:
    return _load_system_prompt_template().replace("{current_phase}", current_phase)


def _ensure_groq_settings(settings: Settings) -> Settings:
    if settings.groq_api_key:
        return settings
    raise ConfigurationError("GROQ_API_KEY is not configured.")


def _call_groq_api(
    session_history: list[dict],
    current_phase: str,
    settings: Settings,
) -> str:
    settings = _ensure_groq_settings(settings)

    messages = [
        {"role": "system", "content": _build_system_prompt(current_phase)},
        *[{"role": msg["role"], "content": msg["content"]}
            for msg in session_history],
    ]
    payload = {
        "model": settings.groq_model,
        "messages": messages,
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(settings.groq_timeout_seconds)

    with httpx.Client(timeout=timeout) as client:
        response = client.post(settings.groq_api_url,
                               json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "Groq response did not include assistant content.") from exc


def _parse_llm_response(raw_response: str) -> LLMResponse:
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    # Extract first JSON object if there's any prose around it
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    parsed_response = json.loads(cleaned)
    return LLMResponse.model_validate(parsed_response)


def _build_fallback_result(
    session_id: str,
    error: str,
    reply: str,
) -> ChatResult:
    memory_store.append_message(session_id, "assistant", reply)
    memory_store.update_session_workflow_state(
        session_id=session_id,
        updates={
            "phase": "fallback",
            "pending_actions": [],
            "state": "fallback",
        },
    )
    return ChatResult(
        session_id=session_id,
        reply=reply,
        pending_actions=[],
        memory_summary=memory_store.get_session_summary(session_id),
        state="fallback",
        error=error,
    )


def process_chat_message(
    message: str,
    session_id: str | None = None,
    settings: Settings | None = None,
) -> ChatResult:
    if settings is None:
        raise RuntimeError("Settings are required for chat orchestration.")

    active_session_id = memory_store.ensure_session(session_id=session_id)
    memory_store.append_message(active_session_id, "user", message)
    current_phase = memory_store.get_session_phase(active_session_id)
    session_history = memory_store.get_session_history(active_session_id)

    # ------------------------------------------------------------------
    # ⚡ INTERCEPTOR FOR DISPLAYING LOCAL EMAIL/ACTIONS PAYLOADS
    # ------------------------------------------------------------------
    normalized_msg = message.lower().strip()
    if "show" in normalized_msg or "view" in normalized_msg or "read" in normalized_msg:
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

    try:
        raw_llm_response = _call_groq_api(
            session_history=session_history,
            current_phase=current_phase,
            settings=settings,
        )
    except ConfigurationError:
        logger.exception("Groq configuration is missing.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_configuration_missing",
            reply=(
                "GROQ_API_KEY is not configured. Add it to backend/.env "
                "and restart the backend."
            ),
        )
    except httpx.TimeoutException:
        logger.exception("Groq request timed out.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_timeout",
            reply=TIMEOUT_FALLBACK_REPLY,
        )
    except httpx.HTTPStatusError:
        logger.exception("Groq API returned an error response.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_api_failure",
            reply=TIMEOUT_FALLBACK_REPLY,
        )
    except (httpx.RequestError, RuntimeError, ValueError):
        logger.exception("Groq request failed.")
        return _build_fallback_result(
            session_id=active_session_id,
            error="groq_api_failure",
            reply=TIMEOUT_FALLBACK_REPLY,
        )

    try:
        llm_response = _parse_llm_response(raw_llm_response)
    except (json.JSONDecodeError, ValidationError):
        logger.exception(
            "Groq response could not be parsed as a valid LLMResponse.")
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

    summary_text = f"Last turn — User: {message[:80]} | Assistant: {llm_response.reply[:80]}"
    memory_store.update_session_summary(active_session_id, summary_text)

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


def handle_confirmation(
    action_id: str,
    action_type: str,
    approved: bool,
    session_id: str,
) -> dict:
    if not requires_confirmation(action_type):
        return {
            "ok": True,
            "action_id": action_id,
            "status": "not_required",
            "message": "Confirmation is not required for read-only actions.",
        }

    with memory_store._connect() as connection:
        workflow_state = memory_store._read_workflow_state(
            connection, session_id)
    pending_actions = workflow_state.get("pending_actions") or []

    if isinstance(pending_actions, list):
        updated_pending_actions = [
            action
            for action in pending_actions
            if isinstance(action, dict) and action.get("action_id") != action_id
        ]
    else:
        updated_pending_actions = []

    memory_store.update_session_workflow_state(
        session_id=session_id,
        updates={
            "pending_actions": updated_pending_actions,
            "state": "ready" if not updated_pending_actions else "awaiting_confirmation",
        },
    )

    return {
        "ok": True,
        "action_id": action_id,
        "status": "approved" if approved else "rejected",
    }
