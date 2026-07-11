import time
import random
import requests
from ..utils.env import get_settings
from .types import AIRequest, AIResponse, TaskType, QuotaTracker

class OpenRouterQuotaExceeded(Exception):
    pass

class OpenRouterGemmaProvider:
    name = "openrouter-gemma"
    supported_task_types = ['document', 'image', 'audio', 'video']
    cost_tier = 'free'
    latency_tier = 'modest'
    def __init__(self, settings=None, quota_tracker=None):
        self.settings = settings or get_settings()
        self.model = self.settings.openrouter_model
        self.api_url = self.settings.openrouter_api_url
        self.api_key = self.settings.openrouter_api_key
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured. Set it in the backend .env.")
        self.quota = quota_tracker or QuotaTracker(50, 20)
    def complete(self, request: AIRequest) -> AIResponse:
        if not self.quota.available():
            raise OpenRouterQuotaExceeded("OpenRouter quota exceeded for this API key")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.input_media:
            payload["media"] = request.input_media
        tries = 0
        while tries < 2:
            self.quota.record()
            resp = requests.post(self.api_url, json=payload, headers=headers)
            if resp.status_code == 429:
                tries += 1
                retry_after = resp.headers.get("Retry-After")
                delay = int(retry_after) if retry_after else 2 ** tries + random.uniform(0, 1.5)
                time.sleep(delay)
            else:
                break
        if resp.status_code == 429:
            raise OpenRouterQuotaExceeded("OpenRouter quota exceeded (HTTP 429 after retries)")
        resp.raise_for_status()
        data = resp.json()
        try:
            out_text = data["choices"][0]["message"]["content"]
        except Exception:
            out_text = ""
        return AIResponse(
            content=out_text,
            raw_response=data,
        )
