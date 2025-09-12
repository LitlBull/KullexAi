import os, json, requests
from .base import Provider
from ..stream import iter_sse_lines


class Anthropic(Provider):
    name = "anthropic"
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base = base_url or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.version = os.getenv("ANTHROPIC_VERSION", "2023-06-01")

    def _headers(self, stream=False):
        h = {"x-api-key": self.key, "anthropic-version": self.version, "content-type": "application/json"}
        if stream: h["accept"] = "text/event-stream"
        return h

    def stream(self, prompt, text, model, max_tokens, timeout):
        url = f"{self.base}/v1/messages"
        body = {"model": model, "max_tokens": max_tokens, "system": prompt,
                "messages": [{"role": "user", "content": text}], "stream": True, "temperature": 0.2}
        with requests.post(url, headers=self._headers(stream=True), json=body, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            for ev in iter_sse_lines(r):
                data = ev.get("data")
                if not data:
                    continue
                try:
                    j = json.loads(data)
                except Exception:
                    continue
                if j.get("type") == "message_stop":
                    break
                if j.get("type") == "content_block_delta":
                    delta = j.get("delta", {}).get("text")
                    if delta:
                        yield delta

    def complete(self, prompt, text, model, max_tokens, timeout) -> str:
        url = f"{self.base}/v1/messages"
        body = {"model": model, "max_tokens": max_tokens, "system": prompt,
                "messages": [{"role": "user", "content": text}], "temperature": 0.2}
        r = requests.post(url, headers=self._headers(), json=body, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        out = []
        for block in j.get("content", []):
            if block.get("type") == "text":
                out.append(block.get("text", ""))
        return "".join(out).strip()