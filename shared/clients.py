"""
API Clients for AML Three-Layer Tribunal

Provides singleton clients for OpenAI and Anthropic APIs.
"""

from typing import Optional, List
import anthropic
from openai import OpenAI

from shared.config import OPENAI_API_KEY, ANTHROPIC_API_KEY, EMBEDDING_MODEL


class APIClients:
    """
    Singleton API client manager.

    Usage:
        clients = APIClients()
        embedding = clients.get_embedding("some text")
        response = clients.chat("user message", "system prompt")
    """

    _instance: Optional["APIClients"] = None
    _openai: Optional[OpenAI] = None
    _anthropic: Optional[anthropic.Anthropic] = None

    def __new__(cls) -> "APIClients":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._openai is None:
            self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize API clients."""
        if OPENAI_API_KEY:
            self._openai = OpenAI(api_key=OPENAI_API_KEY)

        if ANTHROPIC_API_KEY:
            self._anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    @property
    def openai(self) -> OpenAI:
        """Get the OpenAI client."""
        if self._openai is None:
            raise ValueError("OpenAI API key not configured")
        return self._openai

    @property
    def anthropic(self) -> anthropic.Anthropic:
        """Get the Anthropic client."""
        if self._anthropic is None:
            raise ValueError("Anthropic API key not configured")
        return self._anthropic

    # ==========================================================================
    # EMBEDDING METHODS
    # ==========================================================================

    def get_embedding(self, text: str, model: str = EMBEDDING_MODEL) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: OpenAI embedding model to use

        Returns:
            List of floats representing the embedding vector
        """
        response = self.openai.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding

    def get_embeddings(self, texts: List[str], model: str = EMBEDDING_MODEL) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            model: OpenAI embedding model to use

        Returns:
            List of embedding vectors
        """
        response = self.openai.embeddings.create(
            model=model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    # ==========================================================================
    # CHAT METHODS
    # ==========================================================================

    def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """
        Send a chat message to Claude.

        Args:
            user_message: The user's message
            system_prompt: Optional system prompt
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Claude's response text
        """
        response = self.anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else None,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_clients() -> APIClients:
    """Get the singleton API clients."""
    return APIClients()


def get_embedding(text: str) -> List[float]:
    """Generate embedding for text."""
    return get_clients().get_embedding(text)


def chat(user_message: str, system_prompt: str = "") -> str:
    """Send a chat message to Claude."""
    return get_clients().chat(user_message, system_prompt)
