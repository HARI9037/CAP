from .types import AIRequest, AIResponse, TaskType, ModelProvider

class ClaudeProviderStub:
    name = "claude-stub"
    supported_task_types = ["chat"]
    cost_tier = "not_configured"
    latency_tier = "n/a"
    def complete(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError("Claude provider not yet configured. Configure credentials and implementation.")
