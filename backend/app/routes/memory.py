from fastapi import APIRouter, Query

from ..memory.store import memory_store
from ..orchestrator.service import read_memory_summary
router = APIRouter(tags=["memory"])


@router.get("/memory")
def get_memory(session_id: str | None = Query(default=None)) -> dict:
    history = memory_store.get_session_history(session_id) if session_id else []
    return {
        "ok": True,
        "status": "success",
        "memory": read_memory_summary(session_id=session_id),
        "history": history,
    }


@router.delete("/memory")
def delete_memory(session_id: str = Query(...)) -> dict:
    memory_store.delete_session(session_id)
    return {"ok": True, "status": "success"}
