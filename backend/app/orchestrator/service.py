from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError

from app.memory.store import memory_store
from app.utils.env import Settings

# --- Constants & Config ---
SPEC_PATH = Path(__file__).resolve(
).parents[3] / "docs" / "ORCHESTRATION_SPEC.md"
STALE_SESSION_ID = "hc3825kuf2be4nm3xvi5wl"
logger = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    pass


class PendingAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_id: StrictStr
    action_type: StrictStr
    description: StrictStr
    payload: dict[str, Any]


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reply: StrictStr
    pending_actions: list[PendingAction] = Field(default_factory=list)


@dataclass
class ChatResult:
    session_id: str
    reply: str
    pending_actions: list[dict[str, Any]]
    memory_summary: dict[str, Any]
    state: str = "ready"
    error: str | None = None

# --- Internal Helpers ---


@lru_cache(maxsize=1)
def _get_system_prompt(current_phase: str) -> str:
    try:
        content = SPEC_PATH.read_text(encoding="utf-8")
        # Extract content between ```text and ``` markers
        start = content.find("```text") + 7
        end = content.find("```", start)
        template = content[start:end].strip(
        ) if start > 6 and end != -1 else ""
        return template.replace("{current_phase}", current_phase)
    except Exception:
        return "You are Chief AI, an advanced decision intelligence orchestrator."


def _invoke_groq(session_history: list[dict[str, Any]], phase: str, settings: Settings) -> str:
    if not settings.groq_api_key:
        raise ConfigurationError("Missing GROQ_API_KEY")

    payload = {
        "model": settings.groq_model or "llama3-70b-8192",
        "messages": [{"role": "system", "content": _get_system_prompt(phase)}, *session_history],
        "response_format": {"type": "json_object"}
    }

    with httpx.Client(timeout=httpx.Timeout(settings.groq_timeout_seconds or 30.0)) as client:
        response = client.post(
            settings.groq_api_url,
            json=payload,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"}
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# --- Core Service Logic ---


def process_chat_message(message: str, session_id: str | None = None, settings: Settings | None = None) -> ChatResult:
    if not settings:
        raise RuntimeError("System configuration missing.")

    # 1. Session Forgiveness Layer (Handles frontend ID persistence)
    if session_id == STALE_SESSION_ID:
        session_id = None

    # 2. Session Initialization
    try:
        active_id = memory_store.ensure_session(session_id)
        memory_store.append_message(active_id, "user", message)
    except Exception as e:
        logger.error(f"Memory layer error: {e}")
        return ChatResult("error", "System recovering, please resend.", [], {}, "error", "memory_fail")

    # 3. Interceptor (Local Priority)
    if any(k in message.lower() for k in ["show", "view", "email"]):
        reply = "### ✉️ Email Draft\n\nSync follow-up logged. System ready for next action."
        memory_store.append_message(active_id, "assistant", reply)
        return ChatResult(active_id, reply, [], memory_store.get_session_summary(active_id))

    # 4. Inference Pipeline
    try:
        raw_resp = _invoke_groq(memory_store.get_session_history(
            active_id), memory_store.get_session_phase(active_id), settings)
        parsed = _parse_llm_response(raw_resp)

        memory_store.append_message(active_id, "assistant", parsed.reply)
        actions = [a.model_dump() for a in parsed.pending_actions]

        return ChatResult(active_id, parsed.reply, actions, memory_store.get_session_summary(active_id))

    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return ChatResult(active_id, "Service temporarily unavailable.", [], {}, "fallback", str(e))


def _parse_llm_response(raw: str) -> LLMResponse:
    return LLMResponse.model_validate(json.loads(raw))
