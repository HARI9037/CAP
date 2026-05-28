from fastapi import APIRouter, Query

from backend.app.orchestrator.service import read_memory_summary
router = APIRouter(tags=["memory"])


@router.get("/memory")
def get_memory(session_id: str | None = Query(default=None)) -> dict:
    return {
        "ok": True,
        "memory": read_memory_summary(session_id=session_id),
    }
