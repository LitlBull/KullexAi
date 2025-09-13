import os
from .openai import OpenAI

class VLLM(OpenAI):
    """vLLM uses OpenAI-compatible API"""
    name = "vllm"
    
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        base = base_url or os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        # vLLM doesn't require an API key by default
        key = api_key or os.getenv("VLLM_API_KEY", "dummy-key")
        super().__init__(base_url=base, api_key=key)