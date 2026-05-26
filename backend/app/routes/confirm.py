from fastapi import APIRouter
from pydantic import BaseModel

from app.orchestrator.service import handle_confirmation

router = APIRouter(tags=["confirm"])


class ConfirmRequest(BaseModel):
    action_id: str
    action_type: str
    approved: bool


@router.post("/confirm")
def confirm_action(payload: ConfirmRequest) -> dict:
    result = handle_confirmation(
        action_id=payload.action_id,
        action_type=payload.action_type,
        approved=payload.approved,
    )
    return result
