from abc import ABC, abstractmethod

class BaseProvider(ABC):
    default_model: str
    known_models: list[str]
    models_url: str

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """
        Send a completion request to the provider.
        """
        pass
