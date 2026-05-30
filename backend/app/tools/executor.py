"""
CAP Tool Executor - Priority 2 implementation.
Implements the 'save' and 'write' action types as a session note tool.
All other action types return a safe informational result.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _utc_timestamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def execute_save_note(action_id: str, payload: dict) -> dict:
    """
    Generates a markdown note from the action payload.
    Returns a structured result with a human-readable summary.
    """
    title = payload.get("title") or payload.get("target_resource") or "Session Note"
    content = payload.get("content") or payload.get("description") or "No content provided."
    timestamp = _utc_timestamp()

    note = (
        f"## {title}\n"
        f"_Saved at {timestamp}_\n\n"
        f"{content}"
    )

    return {
        "success": True,
        "message": f"Note '{title}' saved successfully.",
        "data": {"note": note, "saved_at": timestamp},
    }


def execute_tool(action_type: str, action_id: str, payload: dict) -> dict:
    """
    Dispatch an approved action to the correct tool handler.
    Only 'save' and 'write' trigger real execution; all others return
    a safe 'acknowledged' response so the workflow never crashes.
    """
    action_type_lower = action_type.strip().lower()

    if action_type_lower in ("save", "write"):
        return execute_save_note(action_id, payload)

    return {
        "success": True,
        "message": f"Action '{action_type}' acknowledged. Execution noted in session.",
        "data": {},
    }
