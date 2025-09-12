from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "kullexai"
CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home()/".config")) / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "provider": os.getenv("KULL_PROVIDER", "openai"),
    "model": os.getenv("KULL_MODEL", "gpt-4o-mini"),
    "endpoint": os.getenv("KULL_ENDPOINT", ""),
    "window_bytes": int(os.getenv("KULL_WINDOW_BYTES", 128*1024)),
    "max_tokens": int(os.getenv("KULL_MAX_TOKENS", 400)),
    "redact": os.getenv("KULL_REDACT", "basic"), # "basic" | "off"
}

ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

def parse_toml_minimal(text: str) -> dict:
    data: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().lower()
        v = v.strip().strip('"')
        data[k] = v
    return data

def load_config() -> dict:
    cfg = DEFAULTS.copy()
    if CONFIG_PATH.exists():
        parsed = parse_toml_minimal(CONFIG_PATH.read_text(encoding="utf-8", errors="ignore"))
        cfg.update({k: parsed[k] for k in parsed if k in cfg})
        # derive key env from file if present, else from map
        key_env = parsed.get("key_env") or ENV_KEYS.get(cfg["provider"], "")
    cfg["key_env"] = key_env
    return cfg