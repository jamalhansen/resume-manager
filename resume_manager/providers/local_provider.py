import requests
from .base import BaseProvider

class LocalProvider(BaseProvider):
    default_model = "llama3"
    known_models = [] # Fetched from /api/tags
    models_url = "https://ollama.com/library"

    def __init__(self, model=None, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = model or self.default_model
        try:
            resp = requests.get(f"{self.base_url}/api/tags")
            if resp.status_code == 200:
                self.known_models = [m['name'] for m in resp.json().get('models', [])]
        except Exception:
            pass

    def complete(self, system: str, user: str) -> str:
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system}\n\nUser: {user}",
                    "stream": False
                }
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            raise RuntimeError(f"Local (Ollama) API error: {e}")
