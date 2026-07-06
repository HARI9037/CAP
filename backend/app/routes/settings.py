from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from ..memory.store import memory_store
from ..utils.auth import get_current_user_id

router = APIRouter(tags=["settings"])

ALLOWED_GROQ_MODELS = {
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
}


class SettingsPayload(BaseModel):
    theme: str | None = Field(default=None, pattern="^(dark|light|system)$")
    model: str | None = Field(default=None, max_length=80)
    memory_enabled: bool | None = None
    confirmation_required: bool | None = None
    verbose_replies: bool | None = None

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_GROQ_MODELS:
            raise ValueError("Unsupported model selection.")
        return value


@router.get("/settings")
def get_settings(user_id: str = Depends(get_current_user_id)) -> dict:
    return {"ok": True, "settings": memory_store.get_settings(user_id=user_id)}


@router.put("/settings")
def update_settings(payload: SettingsPayload, user_id: str = Depends(get_current_user_id)) -> dict:
    updates = payload.model_dump(exclude_none=True)
    return {"ok": True, "settings": memory_store.update_settings(updates, user_id=user_id)}
