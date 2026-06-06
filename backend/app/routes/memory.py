from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ..memory.store import memory_store
from ..orchestrator.service import read_memory_summary
from ..utils.auth import get_current_user_id

router = APIRouter(tags=["memory"])


class MemoryPayload(BaseModel):
    memory_type: str = Field(pattern="^(preference|context|goal|project)$")
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=4000)
    source_session_id: str | None = None


@router.get("/memory")
def get_memory(session_id: str | None = Query(default=None), user_id: str = Depends(get_current_user_id)) -> dict:
    history = memory_store.get_session_history(session_id, user_id) if session_id else []
    return {
        "ok": True,
        "status": "success",
        "memory": read_memory_summary(user_id=user_id, session_id=session_id),
        "history": history,
    }


@router.get("/memory/items")
def list_memories(memory_type: str | None = Query(default=None), user_id: str = Depends(get_current_user_id)) -> dict:
    return {"ok": True, "memories": memory_store.list_memories(user_id=user_id, memory_type=memory_type)}


@router.post("/memory/items")
def create_memory(payload: MemoryPayload, user_id: str = Depends(get_current_user_id)) -> dict:
    memory = memory_store.upsert_memory(user_id=user_id, **payload.model_dump())
    return {"ok": True, "memory": memory}


@router.put("/memory/items/{memory_id}")
def update_memory(memory_id: str, payload: MemoryPayload, user_id: str = Depends(get_current_user_id)) -> dict:
    memory = memory_store.upsert_memory(memory_id=memory_id, user_id=user_id, **payload.model_dump())
    return {"ok": True, "memory": memory}


@router.delete("/memory/items/{memory_id}")
def remove_memory(memory_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    deleted = memory_store.delete_memory(memory_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"ok": True, "status": "deleted"}


@router.delete("/memory")
def delete_memory(session_id: str = Query(...), user_id: str = Depends(get_current_user_id)) -> dict:
    memory_store.delete_session(session_id, user_id)
    return {"ok": True, "status": "success"}
