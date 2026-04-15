import os
import google.generativeai as genai
from .base import BaseProvider

class GeminiProvider(BaseProvider):
    default_model = "gemini-1.5-pro"
    known_models = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro"
    ]
    models_url = "https://ai.google.dev/models/gemini"

    def __init__(self, model=None):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = model or self.default_model
        self.model = genai.GenerativeModel(self.model_name)

    def complete(self, system: str, user: str) -> str:
        try:
            # Gemini combines system and user prompts
            prompt = f"{system}\n\nUser: {user}"
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")
