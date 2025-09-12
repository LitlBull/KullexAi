import re


def basic(text: str) -> str:
    text = re.sub(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*([A-Za-z0-9_\-]{12,})", r"\1=[REDACTED]", text)
    text = re.sub(r"(?i)password\s*[:=]\s*\S+", "password=[REDACTED]", text)
    text = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA****************", text)
    return text