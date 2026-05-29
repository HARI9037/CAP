from fastapi import APIRouter, Request

from ..orchestrator.service import get_health_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(request: Request) -> dict:
    return get_health_status(request.app.state.settings)
