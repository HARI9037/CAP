from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError
from ..context_builder import build_context
from ..memory.store import memory_store
from ..tools.executor import execute_tool
from ..utils.env import Settings

SPEC_PATH = Path(__file__).resolve(
).parents[3] / "docs" / "ORCHESTRATION_SPEC.md"
TIMEOUT_FALLBACK_REPLY = (
    "I'm experiencing a slight network delay on the backend. Could you try sending that again?"
)
ACTION_TYPE_ALIASES = {
    "create": "write",
    "create_file": "write",
    "create-note": "write",
    "create_note": "write",
    "edit": "update",
    "modify": "update",
    "save-note": "save",
    "save_note": "save",
    "write_file": "write",
    "write-file": "write",
}
MUTATING_ACTION_TYPES = {"write", "update", "organize", "save", "delete"}
PARSE_FALLBACK_REPLY = (
    "I received an empty response from the model. Could you try sending that again?"
)
logger = logging.getLogger(__name__)
TEXT_RESPONSE_KEYS = ("reply", "message", "content", "response", "text")


class ConfigurationError(RuntimeError):
    pass


class PendingAction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action_id: StrictStr
    action_type: StrictStr
    description: StrictStr
    payload: dict


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

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
        "response_format": {"type": "json_object"},
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
    if not cleaned:
        raise ValueError("LLM response was empty.")
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
    try:
        parsed_response = json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        extracted_reply = _extract_text_from_jsonish_response(cleaned)
        if extracted_reply:
            return LLMResponse(reply=_clean_reply_text(extracted_reply), pending_actions=[])
        return LLMResponse(reply=_clean_reply_text(raw_response.strip()), pending_actions=[])

    if isinstance(parsed_response, str):
        return LLMResponse(reply=_clean_reply_text(parsed_response), pending_actions=[])

    if isinstance(parsed_response, dict):
        if "reply" not in parsed_response:
            content = next(
                (
                    parsed_response.get(key)
                    for key in TEXT_RESPONSE_KEYS
                    if isinstance(parsed_response.get(key), str)
                ),
                None,
            )
            if isinstance(content, str):
                parsed_response = {
                    "reply": _clean_reply_text(content),
                    "pending_actions": parsed_response.get("pending_actions", []),
                }
        elif isinstance(parsed_response["reply"], str):
            parsed_response["reply"] = _clean_reply_text(
                parsed_response["reply"])
        if not isinstance(parsed_response.get("pending_actions", []), list):
            parsed_response["pending_actions"] = []
        else:
            valid_actions = []
            for action in parsed_response.get("pending_actions", []):
                if (
                    isinstance(action, dict)
                    and isinstance(action.get("action_id"), str)
                    and isinstance(action.get("action_type"), str)
                    and isinstance(action.get("description"), str)
                    and isinstance(action.get("payload"), dict)
                ):
                    valid_actions.append(action)
            parsed_response["pending_actions"] = valid_actions
        return LLMResponse.model_validate(parsed_response)

    return LLMResponse(reply=_clean_reply_text(raw_response.strip()), pending_actions=[])


def _extract_text_from_jsonish_response(raw_response: str) -> str | None:
    if not raw_response.lstrip().startswith("{"):
        return None

    for key in TEXT_RESPONSE_KEYS:
        match = re.search(
            rf'"{re.escape(key)}"\s*:\s*"(?P<value>.*?)(?<!\\)"\s*(?:,|\}})',
            raw_response,
            flags=re.DOTALL,
        )
        if not match:
            continue
        value = match.group("value")
        try:
            return json.loads(f'"{value}"', strict=False)
        except json.JSONDecodeError:
            return value.replace("\\n", "\n").replace('\\"', '"').strip()

    return None


def _clean_reply_text(reply: str) -> str:
    cleaned = reply.strip()
    cleaned = re.sub(
        r"\n*\s*\*{0,2}Pending Actions:?[\s\S]*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


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
    context = build_context(active_session_id)
    current_phase = context["workflow_context"].get("phase", "general_chat")
    session_history = context["llm_messages"]

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
    except (ValueError, ValidationError):
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


def normalize_action_type(action_type: str) -> str:
    normalized = action_type.strip().lower().replace(" ", "_")
    return ACTION_TYPE_ALIASES.get(normalized, normalized)


def requires_confirmation(action_type: str) -> bool:
    return normalize_action_type(action_type) in MUTATING_ACTION_TYPES


def handle_confirmation(
    action_id: str,
    action_type: str,
    approved: bool,
    session_id: str,
) -> dict:
    matching_action, updated_pending_actions = memory_store.resolve_pending_action(
        session_id,
        action_id,
    )

    if matching_action is None and not requires_confirmation(action_type):
        return {
            "ok": True,
            "action_id": action_id,
            "status": "not_required",
            "message": "Confirmation is not required for read-only actions.",
            "execution_result": None,
            "remaining_actions": memory_store.get_pending_actions(session_id),
            "memory_summary": memory_store.get_session_summary(session_id),
        }

    if matching_action is None:
        return {
            "ok": True,
            "action_id": action_id,
            "status": "not_found",
            "message": "Action is no longer pending.",
            "execution_result": None,
            "remaining_actions": updated_pending_actions,
            "memory_summary": memory_store.get_session_summary(session_id),
        }

    execution_result = None
    if approved:
        action_payload = matching_action.get("payload", {})
        resolved_action_type = normalize_action_type(
            matching_action.get("action_type") or action_type
        )
        try:
            tool_result = execute_tool(
                resolved_action_type, action_id, action_payload)
            if tool_result.get("success"):
                execution_result = (
                    f"\u2713 Action executed: {tool_result['message']}"
                )
                if tool_result.get("data", {}).get("note"):
                    memory_store.update_session_summary(
                        session_id,
                        tool_result["data"]["note"],
                    )
                    execution_result += f"\n\n{tool_result['data']['note']}"
            else:
                execution_result = "\u26a0 Action could not be completed at this time."
        except Exception:
            logger.exception(
                "Tool execution failed for action_id=%s", action_id)
            execution_result = "\u26a0 Action failed. Session context is preserved."

    return {
        "ok": True,
        "action_id": action_id,
        "status": "approved" if approved else "rejected",
        "execution_result": execution_result,
        "remaining_actions": updated_pending_actions,
        "memory_summary": memory_store.get_session_summary(session_id),
    }
