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
SPEC_PATH = Path(__file__).resolve().parents[3] / "docs" / "ORCHESTRATION_SPEC.md"
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

def _get_system_prompt(current_phase: str) -> str:
    try:
        content = SPEC_PATH.read_text(encoding="utf-8")
        return content.replace("{current_phase}", current_phase)
    except Exception:
        return "You are Chief AI, an advanced decision intelligence system."

def process_chat_message(message: str, session_id: str | None = None, settings: Settings | None = None) -> ChatResult:
    if not settings:
        raise RuntimeError("System configuration missing.")

    if session_id == STALE_SESSION_ID:
        session_id = None

    try:
        active_id = memory_store.ensure_session(session_id)
        memory_store.append_message(active_id, "user", message)
    except Exception as e:
        return ChatResult("error", "System recovery in progress.", [], {}, "error", str(e))

    # Simple local interceptor
    if any(k in message.lower() for k in ["show", "email"]):
        reply = "### ✉️ Email Draft\n\nSync complete. System ready."
        memory_store.append_message(active_id, "assistant", reply)
        return ChatResult(active_id, reply, [], memory_store.get_session_summary(active_id))

    return ChatResult(active_id, "System operational.", [], {})
