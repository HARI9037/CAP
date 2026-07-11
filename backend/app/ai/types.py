from typing import Literal, List, Optional, Any, Protocol
from pydantic import BaseModel, Field

TaskType = Literal['chat', 'document', 'image', 'audio', 'video', 'code']

class AIRequest(BaseModel):
    task_type: TaskType
    prompt: str
    input_media: Optional[Any] = Field(default=None)  # image, audio, video, etc.
    options: Optional[dict] = Field(default=None)     # e.g., temperature, max_tokens, etc.

class AIResponse(BaseModel):
    content: str                             # normalized output (main text/response)
    raw_response: Optional[Any] = None       # full provider response (for debugging/logging)
    media: Optional[Any] = None              # output media if present (image, etc.)

class ModelProvider(Protocol):
    name: str
    supported_task_types: List[TaskType]
    cost_tier: str
    latency_tier: str
    def complete(self, request: AIRequest) -> AIResponse:
        ...

from datetime import datetime, timedelta
import threading

class QuotaTracker:
    def __init__(self, daily_limit: int, rpm_limit: int):
        self.daily_limit = daily_limit
        self.rpm_limit = rpm_limit
        self.history: List[datetime] = []
        self.lock = threading.Lock()
    def record(self):
        with self.lock:
            self.history.append(datetime.utcnow())
    def available(self) -> bool:
        with self.lock:
            now = datetime.utcnow()
            one_minute_ago = now - timedelta(minutes=1)
            today = now.date()
            # Remove old events (only track today)
            self.history = [t for t in self.history if t.date() == today]
            recent_minute = [t for t in self.history if t >= one_minute_ago]
            return len(self.history) < self.daily_limit and len(recent_minute) < self.rpm_limit
