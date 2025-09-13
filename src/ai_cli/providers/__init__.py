from .openai import OpenAI
from .anthropic import Anthropic
from .openrouter import OpenRouter
from .ollama import Ollama
from .vllm import VLLM

PROVIDERS = {
    "openai": OpenAI,
    "anthropic": Anthropic,
    "openrouter": OpenRouter,
    "ollama": Ollama,
    "vllm": VLLM,
}