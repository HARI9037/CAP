from .types import AIRequest, AIResponse, TaskType, ModelProvider

class GeminiProviderStub:
    name = "gemini-stub"
    supported_task_types = ["chat", "image", "document"]
    cost_tier = "not_configured"
    latency_tier = "n/a"
    def complete(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError("Gemini provider not yet configured. Configure credentials and implementation.")
