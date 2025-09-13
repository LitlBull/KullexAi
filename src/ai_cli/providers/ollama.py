import os, json, requests
from .base import Provider

class Ollama(Provider):
    name = "ollama"
    
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Ollama doesn't require an API key
    
    def stream(self, prompt, text, model, max_tokens, timeout):
        url = f"{self.base}/api/generate"
        body = {
            "model": model,
            "prompt": f"{prompt}\n\n{text}",
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.2
            }
        }
        
        with requests.post(url, json=body, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    try:
                        j = json.loads(line)
                        if j.get("response"):
                            yield j["response"]
                        if j.get("done"):
                            break
                    except Exception:
                        continue
    
    def complete(self, prompt, text, model, max_tokens, timeout) -> str:
        url = f"{self.base}/api/generate"
        body = {
            "model": model,
            "prompt": f"{prompt}\n\n{text}",
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.2
            }
        }
        
        r = requests.post(url, json=body, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        return j.get("response", "").strip()