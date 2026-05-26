from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.orchestrator.service import process_chat_message

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=6000)
    session_id: str | None = None


@router.post("/chat")
def chat(payload: ChatRequest) -> dict:
    result = process_chat_message(prompt=payload.prompt, session_id=payload.session_id)
    return {
        "ok": True,
        "session_id": result.session_id,
        "reply": result.reply,
        "pending_actions": result.pending_actions,
        "memory_summary": result.memory_summary,
    }
