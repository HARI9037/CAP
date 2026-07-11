from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from uuid import uuid4
import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError
from ..context_builder import build_context, _is_memory_recall_request
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
GROQ_FREE_TIER_SAFE_MAX_TOKENS = {
    "openai/gpt-oss-20b": 4096,
    "openai/gpt-oss-120b": 4096,
}
GROQ_413_RETRY_MAX_TOKENS = 2048
PARSE_FALLBACK_REPLY = (
    "I received an empty response from the model. Could you try sending that again?"
)
logger = logging.getLogger(__name__)
TEXT_RESPONSE_KEYS = ("reply", "message", "content", "response", "text")
CONTENT_REQUEST_KEYWORDS = (
    "architecture",
    "checklist",
    "compare",
    "comparison",
    "dashboard",
    "detail",
    "detailed",
    "explain",
    "feature",
    "features",
    "guide",
    "recommend",
    "recommendation",
    "recap",
    "plan",
    "road map",
    "roadmap",
    "session summary",
    "steps",
    "summarize",
    "summary",
    "tech-stack",
    "tech stack",
    "techstack",
    "web app",
    "webapp",
    "workflow",
)
STATE_CHANGING_PATTERNS = (
    r"\bsave\s*this\b",
    r"\bsave\s*it\b",
    r"\bsavethis\b",
    r"\b(save|remember|store)\b",
    r"\bin\s+your\s+memory\b",
    r"\b(to|in)\s+memory\b",
    r"\b(delete|remove)\b",
    r"\borganize\b",
    r"\b(update|modify|edit|change)\b.*\b(existing|saved|stored|memory|session|note|file|document|resource|diagram)\b",
    r"\b(add|append)\b.*\b(to|into)\b.*\b(memory|session|note|file|document|resource)\b",
    r"\b(pivot|switch|replace)\b.*\b(instead of|rather than|from|to)\b",
)
PENDING_QUEUE_PATTERNS = (
    r"\bpending\b",
    r"\bqueue\b",
    r"\bapproval\b",
    r"\bapprove\b",
    r"\breject\b",
    r"\bdo\s+not\s+execute\b",
    r"\bdon't\s+execute\b",
    r"\buntil\s+i\s+(explicitly\s+)?approve\b",
    r"\bfor\s+my\s+approval\b",
)
ACTION_CONTENT_KEYS = (
    "content",
    "markdown",
    "roadmap",
    "checklist",
    "plan",
    "workflow",
    "answer",
    "body",
    "text",
    "description",
)


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


def _groq_max_tokens_for_model(settings: Settings) -> int:
    configured_max_tokens = settings.groq_max_tokens
    model_cap = GROQ_FREE_TIER_SAFE_MAX_TOKENS.get(settings.groq_model)
    if model_cap is None:
        return configured_max_tokens
    return min(configured_max_tokens, model_cap)


def _post_groq_completion(
    *,
    payload: dict,
    headers: dict,
    settings: Settings,
) -> httpx.Response:
    timeout = httpx.Timeout(settings.groq_timeout_seconds)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(settings.groq_api_url,
                               json=payload, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if response.status_code != 413 or payload.get("max_tokens") <= GROQ_413_RETRY_MAX_TOKENS:
                raise

            retry_payload = {
                **payload,
                "max_tokens": min(payload["max_tokens"] // 2, GROQ_413_RETRY_MAX_TOKENS),
            }
            logger.warning(
                "Groq returned 413 for model=%s max_tokens=%s; retrying once with max_tokens=%s.",
                payload.get("model"),
                payload.get("max_tokens"),
                retry_payload["max_tokens"],
            )
            retry_response = client.post(
                settings.groq_api_url,
                json=retry_payload,
                headers=headers,
            )
            try:
                retry_response.raise_for_status()
            except httpx.HTTPStatusError:
                raise exc
            return retry_response
        return response


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
        "max_tokens": _groq_max_tokens_for_model(settings),
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    logger.info(
        "Sending Groq completion request model=%s max_tokens=%s messages=%s.",
        payload["model"],
        payload["max_tokens"],
        len(messages),
    )
    response = _post_groq_completion(
        payload=payload,
        headers=headers,
        settings=settings,
    )
    data = response.json()

    try:
        choice = data["choices"][0]
        logger.info(
            "Groq completion finished with finish_reason=%s model=%s",
            choice.get("finish_reason"),
            payload["model"],
        )
        return choice["message"]["content"]
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


def _looks_like_content_request(message: str) -> bool:
    if _is_memory_recall_request(message):
        return True
    lowered = message.lower()
    return any(keyword in lowered for keyword in CONTENT_REQUEST_KEYWORDS)


def _looks_state_changing(message: str) -> bool:
    if _is_memory_recall_request(message):
        return False
    lowered = message.lower()
    return any(re.search(pattern, lowered) for pattern in STATE_CHANGING_PATTERNS)


def _explicitly_requests_pending_queue(message: str) -> bool:
    lowered = message.lower()
    return any(re.search(pattern, lowered) for pattern in PENDING_QUEUE_PATTERNS)


def _should_keep_pending_actions(message: str) -> bool:
    return _explicitly_requests_pending_queue(message) or _looks_state_changing(message)


def _reply_is_too_thin_for_content(reply: str) -> bool:
    normalized = reply.strip()
    if len(normalized) < 90:
        return True
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    return len(lines) <= 2 and not re.search(r"(^|\n)\s*([-*]|\d+\.)\s+", normalized)


def _reply_looks_truncated(reply: str) -> bool:
    normalized = reply.strip()
    if not normalized:
        return True
    if normalized[-1] in ".!?)]}":
        return False

    trailing_fragment = normalized.lower()
    if re.search(r"\b(the|and|to|of|with|for|a|an|in|on|at|by|from)\s*$", trailing_fragment):
        return True
    if re.search(r"[,:;]\s*$", normalized):
        return True
    return False


def _extract_action_content(value: object) -> str | None:
    if isinstance(value, str):
        cleaned = _clean_reply_text(value)
        return cleaned if cleaned else None
    if isinstance(value, dict):
        for key in ACTION_CONTENT_KEYS:
            extracted = _extract_action_content(value.get(key))
            if extracted:
                return extracted
        for nested_value in value.values():
            if not isinstance(nested_value, (dict, list)):
                continue
            extracted = _extract_action_content(nested_value)
            if extracted:
                return extracted
    if isinstance(value, list):
        items = [
            extracted
            for item in value
            if (extracted := _extract_action_content(item))
        ]
        if items:
            return "\n".join(items)
    return None


def _action_memory_title(action: dict) -> str:
    payload = action.get("payload", {})
    title = payload.get("title") if isinstance(payload, dict) else None
    if isinstance(title, str) and title.strip():
        return title.strip()[:120]

    description = action.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()[:120]

    return "Approved action"


def _repair_content_generation_response(
    message: str,
    llm_response: LLMResponse,
) -> LLMResponse:
    """
    Some models over-apply the approval protocol and turn ordinary chat advice
    into update actions. Unless the user clearly requested a state change,
    keep the interaction as visible chat content.
    """
    if _should_keep_pending_actions(message) or not llm_response.pending_actions:
        return llm_response

    for action in llm_response.pending_actions:
        extracted = _extract_action_content(action.payload)
        if extracted and (len(extracted) > len(llm_response.reply) or _reply_is_too_thin_for_content(llm_response.reply)):
            return LLMResponse(reply=extracted, pending_actions=[])

    return LLMResponse(reply=llm_response.reply, pending_actions=[])


def _needs_content_retry(message: str, llm_response: LLMResponse) -> bool:
    if _should_keep_pending_actions(message):
        return False
    if (
        _is_memory_recall_request(message)
        and len(llm_response.reply.strip()) >= 140
        and not _reply_looks_truncated(llm_response.reply)
    ):
        return False
    return (
        _looks_like_content_request(message)
        and _reply_is_too_thin_for_content(llm_response.reply)
    )


def _needs_reply_completion_retry(message: str, llm_response: LLMResponse) -> bool:
    return (
        (_looks_like_content_request(message) or _explicitly_requests_pending_queue(message))
        and _reply_looks_truncated(llm_response.reply)
    )


def _build_content_retry_history(
    session_history: list[dict],
    message: str,
    short_reply: str,
) -> list[dict]:
    retry_prompt = (
        "Your previous answer was incomplete for a normal chat request. "
        "Answer the original request completely in the JSON reply field, "
        "with concrete details and no pending_actions. Do not create update, "
        "save, or organize actions unless the user explicitly asked to change "
        "stored state.\n\n"
        f"Original user request: {message}"
    )
    return [
        *session_history,
        {"role": "assistant", "content": short_reply},
        {"role": "user", "content": retry_prompt},
    ]


def _build_reply_completion_history(
    session_history: list[dict],
    message: str,
    reply: str,
    pending_actions: list[PendingAction],
) -> list[dict]:
    if pending_actions:
        pending_description = "\n".join(
            f"- {action.description}" for action in pending_actions
        )
        retry_prompt = (
            "Your previous reply was cut off. Return the same JSON object with "
            "a complete, polished reply in the reply field. Keep the pending "
            "actions you already proposed. Do not shorten the explanation.\n\n"
            f"Original user request: {message}\n\n"
            f"Current reply draft:\n{reply}\n\n"
            f"Current pending actions:\n{pending_description}"
        )
    else:
        retry_prompt = (
            "Your previous reply was cut off. Return the same JSON object with "
            "a complete, polished reply in the reply field. Do not shorten the "
            "explanation.\n\n"
            f"Original user request: {message}\n\n"
            f"Current reply draft:\n{reply}"
        )
    return [
        *session_history,
        {"role": "assistant", "content": reply},
        {"role": "user", "content": retry_prompt},
    ]


def _reply_has_more_content(candidate: str, current: str) -> bool:
    candidate_text = candidate.strip()
    current_text = current.strip()
    if len(candidate_text) >= max(140, len(current_text) + 80):
        return True
    candidate_items = len(re.findall(r"(^|\n)\s*([-*]|\d+\.)\s+", candidate_text))
    current_items = len(re.findall(r"(^|\n)\s*([-*]|\d+\.)\s+", current_text))
    return candidate_items >= 3 and candidate_items > current_items


def _needs_action_retry(message: str, llm_response: LLMResponse) -> bool:
    return _should_keep_pending_actions(message) and not llm_response.pending_actions


def _build_action_retry_history(
    session_history: list[dict],
    message: str,
    reply: str,
) -> list[dict]:
    retry_prompt = (
        "Your previous answer did not include pending_actions, but the user "
        "explicitly requested an approval queue or a state-changing operation. "
        "Return a JSON object with a helpful reply and 1 to 5 concrete "
        "pending_actions. Each pending action must have action_id, action_type, "
        "description, and payload. Do not execute the actions.\n\n"
        f"Original user request: {message}"
    )
    return [
        *session_history,
        {"role": "assistant", "content": reply},
        {"role": "user", "content": retry_prompt},
    ]


def _strip_list_marker(line: str) -> str:
    return re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", line).strip()


def _extract_action_candidates(reply: str) -> list[str]:
    candidates = []
    for raw_line in reply.splitlines():
        line = _strip_list_marker(raw_line)
        if not line or len(line) < 8:
            continue
        if line.endswith(":"):
            continue
        if line.lower().startswith(("to start", "here", "structure", "then,")):
            continue
        candidates.append(line)
    return candidates[:5]


def _synthesize_pending_actions(message: str, reply: str) -> list[PendingAction]:
    if not _should_keep_pending_actions(message):
        return []

    action_type = "save" if re.search(
        r"\b(save|remember|store|savethis|memory)\b",
        message.lower(),
    ) else "update"
    candidates = _extract_action_candidates(reply)
    if not candidates and reply.strip():
        candidates = [reply.strip()]

    actions = []
    for index, candidate in enumerate(candidates[:5], start=1):
        actions.append(
            PendingAction(
                action_id=f"queued-{uuid4()}",
                action_type=action_type,
                description=candidate[:240],
                payload={
                    "target_resource": "session",
                    "content": candidate,
                    "source": "synthesized_from_reply",
                    "position": index,
                },
            )
        )
    return actions


def _build_fallback_result(
    session_id: str,
    user_id: str,
    error: str,
    reply: str,
) -> ChatResult:
    memory_store.append_message(session_id, "assistant", reply, user_id)
    memory_store.update_session_workflow_state(
        session_id=session_id,
        user_id=user_id,
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
        memory_summary=memory_store.get_session_summary(user_id, session_id),
        state="fallback",
        error=error,
    )


def _http_error_detail(exc: httpx.HTTPStatusError) -> str:
    response = exc.response
    body = response.text[:500] if response is not None else ""
    return f"status={response.status_code if response is not None else 'unknown'} body={body}"


def process_chat_message(
    message: str,
    user_id: str,
    session_id: str | None = None,
    settings: Settings | None = None,
    model: str | None = None,
) -> ChatResult:
    if settings is None:
        raise RuntimeError("Settings are required for chat orchestration.")
    if model:
        settings = replace(settings, groq_model=model)

    active_session_id = memory_store.ensure_session(user_id=user_id, session_id=session_id)
    memory_store.append_message(active_session_id, "user", message, user_id)
    context = build_context(active_session_id, user_id)
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
            user_id=user_id,
            error="groq_configuration_missing",
            reply=(
                "GROQ_API_KEY is not configured. Add it to backend/.env "
                "and restart the backend."
            ),
        )
    except httpx.TimeoutException:
        logger.exception(
            "Fallback triggered: Groq request timed out model=%s max_tokens=%s.",
            settings.groq_model,
            _groq_max_tokens_for_model(settings),
        )
        return _build_fallback_result(
            session_id=active_session_id,
            user_id=user_id,
            error="groq_timeout",
            reply=TIMEOUT_FALLBACK_REPLY,
        )
    except httpx.HTTPStatusError as exc:
        logger.exception(
            "Fallback triggered: Groq API returned an error response model=%s max_tokens=%s %s.",
            settings.groq_model,
            _groq_max_tokens_for_model(settings),
            _http_error_detail(exc),
        )
        return _build_fallback_result(
            session_id=active_session_id,
            user_id=user_id,
            error="groq_api_failure",
            reply=TIMEOUT_FALLBACK_REPLY,
        )
    except (httpx.RequestError, RuntimeError, ValueError):
        logger.exception(
            "Fallback triggered: Groq request failed model=%s max_tokens=%s.",
            settings.groq_model,
            _groq_max_tokens_for_model(settings),
        )
        return _build_fallback_result(
            session_id=active_session_id,
            user_id=user_id,
            error="groq_api_failure",
            reply=TIMEOUT_FALLBACK_REPLY,
        )

    try:
        llm_response = _parse_llm_response(raw_llm_response)
    except (ValueError, ValidationError):
        logger.exception(
            "Fallback triggered: Groq response could not be parsed as a valid LLMResponse. raw_response_prefix=%r",
            raw_llm_response[:500],
        )
        return _build_fallback_result(
            session_id=active_session_id,
            user_id=user_id,
            error="llm_parse_failure",
            reply=PARSE_FALLBACK_REPLY,
        )

    llm_response = _repair_content_generation_response(message, llm_response)
    if _needs_action_retry(message, llm_response):
        try:
            retry_raw_response = _call_groq_api(
                session_history=_build_action_retry_history(
                    session_history,
                    message,
                    llm_response.reply,
                ),
                current_phase=current_phase,
                settings=settings,
            )
            retry_response = _parse_llm_response(retry_raw_response)
            if retry_response.pending_actions:
                reply = (
                    retry_response.reply
                    if _reply_has_more_content(retry_response.reply, llm_response.reply)
                    else llm_response.reply
                )
                llm_response = LLMResponse(
                    reply=reply,
                    pending_actions=retry_response.pending_actions,
                )
        except Exception:
            logger.exception("Action retry failed; synthesizing pending actions.")

        if not llm_response.pending_actions:
            synthesized_actions = _synthesize_pending_actions(
                message,
                llm_response.reply,
            )
            if synthesized_actions:
                llm_response = LLMResponse(
                    reply=llm_response.reply,
                    pending_actions=synthesized_actions,
                )

    if _needs_reply_completion_retry(message, llm_response):
        try:
            completion_raw_response = _call_groq_api(
                session_history=_build_reply_completion_history(
                    session_history,
                    message,
                    llm_response.reply,
                    llm_response.pending_actions,
                ),
                current_phase=current_phase,
                settings=settings,
            )
            completion_response = _parse_llm_response(completion_raw_response)
            completion_response = _repair_content_generation_response(
                message,
                completion_response,
            )
            if _reply_has_more_content(completion_response.reply, llm_response.reply):
                llm_response = LLMResponse(
                    reply=completion_response.reply,
                    pending_actions=(
                        completion_response.pending_actions
                        or llm_response.pending_actions
                    ),
                )
        except Exception:
            logger.exception("Reply completion retry failed; using initial response.")

    if _needs_content_retry(message, llm_response):
        try:
            retry_raw_response = _call_groq_api(
                session_history=_build_content_retry_history(
                    session_history,
                    message,
                    llm_response.reply,
                ),
                current_phase=current_phase,
                settings=settings,
            )
            retry_response = _parse_llm_response(retry_raw_response)
            retry_response = _repair_content_generation_response(
                message,
                retry_response,
            )
            if _reply_has_more_content(retry_response.reply, llm_response.reply):
                llm_response = LLMResponse(
                    reply=retry_response.reply,
                    pending_actions=[],
                )
        except Exception:
            logger.exception("Content retry failed; using initial response.")

    pending_actions = [action.model_dump()
                       for action in llm_response.pending_actions]
    memory_store.append_message(
        active_session_id, "assistant", llm_response.reply, user_id)

    if pending_actions:
        memory_store.store_pending_actions(active_session_id, user_id, pending_actions)
        state = "awaiting_confirmation"
    else:
        memory_store.update_session_workflow_state(
            session_id=active_session_id,
            user_id=user_id,
            updates={
                "pending_actions": [],
                "state": "ready",
            },
        )
        state = "ready"

    summary_text = f"Last turn — User: {message[:80]} | Assistant: {llm_response.reply[:80]}"
    memory_store.update_session_summary(active_session_id, user_id, summary_text)

    return ChatResult(
        session_id=active_session_id,
        reply=llm_response.reply,
        pending_actions=pending_actions,
        memory_summary=memory_store.get_session_summary(user_id, active_session_id),
        state=state,
    )


def read_memory_summary(user_id: str, session_id: str | None = None) -> dict:
    return memory_store.get_session_summary(user_id=user_id, session_id=session_id)


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
    user_id: str,
) -> dict:
    matching_action, updated_pending_actions = memory_store.resolve_pending_action(
        session_id,
        user_id,
        action_id,
    )

    if matching_action is None and not requires_confirmation(action_type):
        return {
            "ok": True,
            "action_id": action_id,
            "status": "not_required",
            "message": "Confirmation is not required for read-only actions.",
            "execution_result": None,
            "remaining_actions": memory_store.get_pending_actions(session_id, user_id),
            "memory_summary": memory_store.get_session_summary(user_id, session_id),
        }

    if matching_action is None:
        return {
            "ok": True,
            "action_id": action_id,
            "status": "not_found",
            "message": "Action is no longer pending.",
            "execution_result": None,
            "remaining_actions": updated_pending_actions,
            "memory_summary": memory_store.get_session_summary(user_id, session_id),
        }

    action_description = matching_action.get("description")
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
                        user_id,
                        tool_result["data"]["note"],
                    )
                    execution_result += f"\n\n{tool_result['data']['note']}"
                else:
                    visible_payload_content = _extract_action_content(
                        action_payload)
                    if visible_payload_content:
                        execution_result += f"\n\n{visible_payload_content}"
                    elif action_description:
                        execution_result += f"\n\n{action_description}"
                memory_content = (
                    _extract_action_content(action_payload)
                    or action_description
                    or tool_result["message"]
                )
                memory_store.upsert_memory(
                    title=_action_memory_title(matching_action),
                    content=memory_content,
                    memory_type="approved_action",
                    user_id=user_id,
                    source_session_id=session_id,
                )
            else:
                execution_result = "\u26a0 Action could not be completed at this time."
        except Exception:
            logger.exception(
                "Tool execution failed for action_id=%s", action_id)
            execution_result = "\u26a0 Action failed. Session context is preserved."
    else:
        execution_result = (
            f"Action rejected: {action_description}"
            if action_description
            else "Action rejected. No changes were applied."
        )

    return {
        "ok": True,
        "action_id": action_id,
        "status": "approved" if approved else "rejected",
        "execution_result": execution_result,
        "remaining_actions": updated_pending_actions,
        "memory_summary": memory_store.get_session_summary(user_id, session_id),
    }
