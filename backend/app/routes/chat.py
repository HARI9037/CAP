from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from backend.app.orchestrator.service import process_chat_message

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str | None = Field(default=None, min_length=1, max_length=6000)
    prompt: str | None = Field(default=None, min_length=1, max_length=6000)
    session_id: str | None = None

    @model_validator(mode="after")
    def require_message_or_prompt(self):
        if not self.message and not self.prompt:
            raise ValueError("message is required.")
        return self

    @property
    def user_message(self) -> str:
        return self.message or self.prompt or ""


@router.post("/chat")
def chat(payload: ChatRequest, request: Request) -> dict:
    try:
        result = process_chat_message(
            message=payload.user_message,
            session_id=payload.session_id,
            settings=request.app.state.settings,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "ok": result.error is None,
        "session_id": result.session_id,
        "reply": result.reply,
        "pending_actions": result.pending_actions,
        "state": result.state,
        "memory_summary": result.memory_summary,
        "error": result.error,
    }
