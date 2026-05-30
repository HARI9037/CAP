"""
CAP Tool Executor.
Implements safe, deployment-friendly handlers for approved CAP actions.
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


def execute_acknowledgement(action_type: str, payload: dict) -> dict:
    target = payload.get("title") or payload.get("target_resource") or "session"
    messages = {
        "update": f"Update for '{target}' recorded in session.",
        "organize": f"Organization request for '{target}' recorded in session.",
        "delete": f"Delete request for '{target}' recorded without destructive side effects.",
    }
    return {
        "success": True,
        "message": messages.get(
            action_type,
            f"Action '{action_type}' acknowledged. Execution noted in session.",
        ),
        "data": {},
    }


def execute_tool(action_type: str, action_id: str, payload: dict) -> dict:
    """
    Dispatch an approved action to the correct tool handler.
    Only 'save' and 'write' create session notes; all others return
    a safe acknowledgement so the workflow never crashes or mutates external state.
    """
    action_type_lower = action_type.strip().lower()

    if action_type_lower in ("save", "write"):
        return execute_save_note(action_id, payload)

    return execute_acknowledgement(action_type_lower, payload)
