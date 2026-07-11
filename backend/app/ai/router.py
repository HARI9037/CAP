from .types import ModelProvider, AIRequest, AIResponse, TaskType
from .providers.groq import GroqProvider
from .providers.openrouter_gemma import OpenRouterGemmaProvider, OpenRouterQuotaExceeded
from .providers.claude_stub import ClaudeProviderStub
from .providers.gemini_stub import GeminiProviderStub

class MultimodalProviderUnavailable(Exception):
    pass

class ModelRouter:
    def __init__(self, settings=None, quota_tracker=None):
        self.groq = GroqProvider(settings)
        self.openrouter_gemma = OpenRouterGemmaProvider(settings, quota_tracker)
        self.lookup = {
            'chat': self.groq,
            'code': self.groq,
            'document': self.openrouter_gemma,
            'image': self.openrouter_gemma,
            'audio': self.openrouter_gemma,
            'video': self.openrouter_gemma,
        }
    def route(self, ai_request: AIRequest) -> AIResponse:
        task_type = ai_request.task_type
        provider = self.lookup.get(task_type, None)
        if not provider:
            raise ValueError(f"No provider configured for task_type: {task_type}")
        try:
            return provider.complete(ai_request)
        except OpenRouterQuotaExceeded as e:
            raise MultimodalProviderUnavailable(str(e))
