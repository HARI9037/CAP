from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..memory.store import memory_store
from ..utils.auth import get_current_user_id

router = APIRouter(tags=["feedback"])


class FeedbackPayload(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=4000)


@router.post("/feedback")
def create_feedback(payload: FeedbackPayload, user_id: str = Depends(get_current_user_id)) -> dict:
    feedback = memory_store.add_feedback(
        rating=payload.rating,
        comment=payload.comment,
        user_id=user_id,
    )
    return {"ok": True, "feedback": feedback}
