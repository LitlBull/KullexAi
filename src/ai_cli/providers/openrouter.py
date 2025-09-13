import os
from .openai import OpenAI

class OpenRouter(OpenAI):
    name = "openrouter"
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        base = base_url or "https://openrouter.ai/api/v1"
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        super().__init__(base_url=base, api_key=key)
