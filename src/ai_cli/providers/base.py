class Provider:
    name: str = "provider"
    def stream(self,prompt: str, text: str, model: str, max_tokens: int, timeout: int):
        raise NotImplementedError
    def complete(self, prompt: str, text: str, model: str, max_tokens: int, timeout: int):
        raise NotImplementedError