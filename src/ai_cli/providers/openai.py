import os, json, requests
from .base import Provider
from ..stream import iter_sse_lines


class OpenAI(Provider):
    name = "openai"
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise RuntimeError("OPENAI_API_KEY is not set")

    def _headers(self, stream=False):
        h = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if stream: h["Accept"] = "text/event-stream"
        return h

    def stream(self, prompt, text, model, max_tokens, timeout):
        url = f"{self.base}/chat/completions"
        body = {"model": model,
                "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}],
                "stream": True, "temperature": 0.2, "max_tokens": max_tokens}
        with requests.post(url, headers=self._headers(stream=True), json=body, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            for ev in iter_sse_lines(r):
                data = ev.get("data")
                if not data:
                    continue
                if data.strip() == "[DONE]":
                    break
                try:
                    j = json.loads(data)
                except Exception:
                    continue
                for ch in j.get("choices", []):
                    delta = ch.get("delta", {}).get("content")
                    if delta:
                        yield delta
    def complete(self, prompt, text, model, max_tokens, timeout) -> str:
        url = f"{self.base}/chat/completions"
        body = {"model": model,
                "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}],
                "stream": False, "temperature": 0.2, "max_tokens": max_tokens}
        r = requests.post(url, headers=self._headers(), json=body, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        return j["choices"][0]["message"]["content"].strip()