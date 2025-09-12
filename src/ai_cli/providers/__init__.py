from .openai import OpenAI
from .anthropic import Anthropic
from .openrouter import OpenRouter


PROVIDERS = {p.name: p for p in (OpenAI, Anthropic, OpenRouter)}