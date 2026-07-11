from ..utils.env import Settings, get_settings
from ..orchestrator.service import _post_groq_completion
from .types import AIRequest, AIResponse, TaskType, ModelProvider

class GroqProvider:
    name = "groq"
    supported_task_types = ['chat', 'code']
    cost_tier = 'free'
    latency_tier = 'fast'

    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()

    def complete(self, request: AIRequest) -> AIResponse:
        """
        Translates AIRequest to Groq API call and normalizes the response.
        """
        payload = {
            "model": self.settings.groq_model,
            "messages": [{"role": "user", "content": request.prompt}],
            "response_format": {"type": "json_object"},
            "max_tokens": self.settings.groq_max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        response = _post_groq_completion(
            payload=payload,
            headers=headers,
            settings=self.settings,
        )
        result = response.json()
        try:
            out_text = result["choices"][0]["message"]["content"]
        except Exception:
            out_text = ""
        return AIResponse(
            content=out_text,
            raw_response=result,
        )
