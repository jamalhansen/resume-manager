import os
import anthropic
from .base import BaseProvider

class AnthropicProvider(BaseProvider):
    default_model = "claude-3-5-sonnet-20240620"
    known_models = [
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307"
    ]
    models_url = "https://docs.anthropic.com/claude/docs/models-overview"

    def __init__(self, model=None):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model or self.default_model

    def complete(self, system: str, user: str) -> str:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                messages=[
                    {"role": "user", "content": user}
                ]
            )
            # Handle list of content blocks
            if isinstance(message.content, list):
                return "".join([block.text for block in message.content if hasattr(block, 'text')])
            return str(message.content)
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")
