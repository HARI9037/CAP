from .types import AIRequest, AIResponse, TaskType
from .router import ModelRouter, MultimodalProviderUnavailable

__all__ = [
    "AIRequest",
    "AIResponse",
    "TaskType",
    "ModelRouter",
    "MultimodalProviderUnavailable",
]

def get_model_router(settings=None, quota_tracker=None):
    return ModelRouter(settings, quota_tracker)
