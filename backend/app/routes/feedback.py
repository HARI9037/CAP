import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import requests

from ..memory.store import memory_store
from ..utils.auth import get_current_user_id

router = APIRouter(tags=["feedback"])
logger = logging.getLogger(__name__)


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
    try:
        webhook_url = os.environ["SLACK_FEEDBACK_WEBHOOK_URL"]
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        response = requests.post(
            webhook_url,
            json={
                "text": (
                    "*CAP feedback received*\n"
                    f"*User:* {user_id}\n"
                    f"*Rating:* {payload.rating}/5\n"
                    f"*Comment:* {payload.comment or '(empty)'}\n"
                    f"*Timestamp:* {timestamp}"
                )
            },
            timeout=5,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Slack feedback delivery failed: %s", exc)
    return {"ok": True, "feedback": feedback}
