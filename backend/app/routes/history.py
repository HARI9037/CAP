from fastapi import APIRouter, Query, Depends

from ..memory.store import memory_store
from ..utils.auth import get_current_user_id

router = APIRouter(tags=["history"])


@router.get("/history")
def list_history(query: str | None = Query(default=None), user_id: str = Depends(get_current_user_id)) -> dict:
    return {"ok": True, "conversations": memory_store.list_sessions(user_id=user_id, query=query)}


@router.get("/history/{session_id}")
def get_conversation(session_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    return {
        "ok": True,
        "session_id": session_id,
        "messages": memory_store.get_session_messages(session_id, user_id),
        "memory": memory_store.get_session_summary(user_id, session_id),
    }


@router.delete("/history/{session_id}")
def delete_conversation(session_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    memory_store.delete_session(session_id, user_id)
    return {"ok": True, "status": "deleted"}
