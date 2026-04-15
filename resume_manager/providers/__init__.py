from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .local_provider import LocalProvider

PROVIDERS = {
    "anthropic": AnthropicProvider,
    "gemini":    GeminiProvider,
    "local":     LocalProvider,
}
