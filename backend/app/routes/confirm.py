from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..orchestrator.service import handle_confirmation
from ..utils.auth import get_current_user_id

router = APIRouter(tags=["confirm"])

class ConfirmRequest(BaseModel):
    action_id: str
    action_type: str
    approved: bool
    session_id: str

@router.post("/confirm")
def confirm_action(payload: ConfirmRequest, user_id: str = Depends(get_current_user_id)) -> dict:
    result = handle_confirmation(
        action_id=payload.action_id,
        action_type=payload.action_type,
        approved=payload.approved,
        session_id=payload.session_id,
        user_id=user_id,
    )
    return result
