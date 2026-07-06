from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, model_validator

from ..memory.store import memory_store
from ..orchestrator.service import process_chat_message
from ..utils.auth import get_current_user_id

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
def chat(payload: ChatRequest, request: Request, user_id: str = Depends(get_current_user_id)) -> dict:
    try:
        user_settings = memory_store.get_settings(user_id=user_id)
        result = process_chat_message(
            message=payload.user_message,
            user_id=user_id,
            session_id=payload.session_id,
            settings=request.app.state.settings,
            model=user_settings["model"],
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
