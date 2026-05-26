from __future__ import annotations

from dataclasses import dataclass

from app.memory.store import memory_store
from app.utils.env import Settings

MUTATING_ACTION_TYPES = {"write", "update", "organize", "save", "delete"}


@dataclass
class ChatResult:
    session_id: str
    reply: str
    pending_actions: list[dict]
    memory_summary: dict


def get_health_status(settings: Settings) -> dict:
    return {
        "ok": True,
        "status": "ready",
        "service": settings.app_name,
        "version": settings.app_version,
        "demo_mode": settings.demo_mode,
    }


def process_chat_message(prompt: str, session_id: str | None = None) -> ChatResult:
    active_session_id = memory_store.ensure_session(session_id=session_id)
    memory_store.append_message(active_session_id, "user", prompt)

    # Groq orchestration and tool dispatch are intentionally deferred for this first slice.
    assistant_reply = (
        "CAP backend is online. I received your message and the vertical slice is active."
    )
    memory_store.append_message(active_session_id, "assistant", assistant_reply)

    return ChatResult(
        session_id=active_session_id,
        reply=assistant_reply,
        pending_actions=[],
        memory_summary=memory_store.get_session_summary(active_session_id),
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
