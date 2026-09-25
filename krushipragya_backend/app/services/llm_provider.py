"""LLM Provider abstraction layer for KrushiPragya.

Provides a clean interface for Large Language Model text generation,
allowing decoupling between domain advisory logic and underlying LLM engines
(supporting both Groq OpenAI-compatible Chat Completions API and local Ollama).
"""
from abc import ABC, abstractmethod
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class LLMProviderError(Exception):
    """Base exception for LLM provider operations."""
    pass


class LLMConnectionError(LLMProviderError):
    """Raised when the LLM service cannot be reached."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM inference request times out."""
    pass


class LLMResponseError(LLMProviderError):
    """Raised when the LLM service returns an unexpected error status code."""
    pass


# ==============================================================================
# Provider Interface
# ==============================================================================

class LLMProvider(ABC):
    """Abstract base class defining the LLM provider contract."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text completion from a prompt and optional system instructions.

        Args:
            prompt: User/task prompt text
            system_prompt: Optional system persona or constraints

        Returns:
            str: Generated completion text

        Raises:
            LLMProviderError: On generation, network, or service failures
        """
        pass

    def close(self) -> None:
        """Close any open client resources."""
        pass


# ==============================================================================
# Groq Provider Implementation (OpenAI-compatible Chat Completions)
# ==============================================================================

_DEFAULT_KEY = object()


class GroqProvider(LLMProvider):
    """External LLM provider communicating with Groq's OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: object = _DEFAULT_KEY,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        client: Optional[httpx.Client] = None,
    ):
        """Initialize GroqProvider.

        Args:
            base_url: Base URL for Groq API (defaults to settings.LLM_BASE_URL)
            api_key: Groq API key (defaults to settings.LLM_API_KEY)
            model: Model identifier (defaults to settings.LLM_MODEL or 'openai/gpt-oss-120b')
            temperature: Sampling temperature (defaults to settings.LLM_TEMPERATURE or 0.0)
            timeout: Request timeout in seconds (defaults to settings.LLM_TIMEOUT or 300.0)
            client: Optional pre-configured httpx.Client instance for dependency injection
        """
        self.base_url = (base_url or settings.LLM_BASE_URL or "https://api.groq.com/openai/v1").rstrip("/")
        self.api_key = settings.LLM_API_KEY if api_key is _DEFAULT_KEY else api_key
        self.model = model or settings.LLM_MODEL or "openai/gpt-oss-120b"
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.timeout = timeout if timeout is not None else settings.LLM_TIMEOUT
        self._client = client

    @property
    def client(self) -> httpx.Client:
        """Return lazily-initialized HTTP client instance."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate completion using Groq /chat/completions endpoint.

        Args:
            prompt: User prompt text
            system_prompt: Optional system persona instructions

        Returns:
            str: Generated completion text

        Raises:
            LLMProviderError: If prompt is empty, API key is missing, or response parsing fails
            LLMConnectionError: If connection to Groq fails
            LLMTimeoutError: If Groq request times out
            LLMResponseError: If Groq returns non-200 HTTP status (401, 403, 429, 5xx)
        """
        if not prompt or not prompt.strip():
            raise LLMProviderError("Prompt cannot be empty.")

        if not self.api_key or not self.api_key.strip():
            raise LLMProviderError("Groq API key is not configured.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        try:
            logger.info("Calling Groq API at %s for model '%s'", self.base_url, self.model)
            response = self.client.post(url, json=payload, headers=headers, timeout=self.timeout)
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("Failed to connect to Groq at %s: %s", self.base_url, exc)
            raise LLMConnectionError("Unable to connect to Groq LLM service.") from exc
        except httpx.TimeoutException as exc:
            logger.error("Timeout communicating with Groq (%ss): %s", self.timeout, exc)
            raise LLMTimeoutError("Groq LLM service request timed out.") from exc
        except httpx.HTTPError as exc:
            logger.error("HTTP error communicating with Groq: %s", exc)
            raise LLMProviderError("Groq LLM service communication failed.") from exc

        if response.status_code != 200:
            if response.status_code in (401, 403):
                logger.error("Groq API authentication failed with status %d", response.status_code)
                raise LLMResponseError("Groq API authentication failed.")
            elif response.status_code == 429:
                logger.error("Groq API rate limit exceeded")
                raise LLMResponseError("Groq API rate limit exceeded.")
            else:
                logger.error("Groq API returned error status %d", response.status_code)
                raise LLMResponseError(
                    f"Groq API returned error status {response.status_code}."
                )

        try:
            data = response.json()
        except Exception as exc:
            logger.error("Failed to parse JSON response from Groq: %s", exc)
            raise LLMProviderError("Invalid JSON response from Groq service.") from exc

        choices = data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            logger.error("No choices returned in Groq response: %s", data)
            raise LLMProviderError("No response choices returned by Groq service.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMProviderError("Invalid choice item in Groq service response.")

        message = first_choice.get("message")
        if not message or not isinstance(message, dict):
            logger.error("Invalid message format in Groq response: %s", first_choice)
            raise LLMProviderError("Invalid message format in Groq service response.")

        content = message.get("content")
        if content is None:
            logger.error("Missing content in Groq message: %s", message)
            raise LLMProviderError("Missing content in Groq service response.")

        return content.strip()

    def close(self) -> None:
        """Close the underlying HTTP client if initialized."""
        if self._client is not None:
            self._client.close()


# ==============================================================================
# Ollama Provider Implementation (Local Development)
# ==============================================================================

class OllamaProvider(LLMProvider):
    """Local LLM provider communicating with Ollama REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
        client: Optional[httpx.Client] = None,
    ):
        """Initialize OllamaProvider.

        Args:
            base_url: Ollama API base URL (defaults to settings.OLLAMA_BASE_URL)
            model: Ollama model name (defaults to settings.OLLAMA_MODEL)
            timeout: Request timeout in seconds (default: 60.0s)
            client: Optional pre-configured httpx.Client instance for dependency injection
        """
        self.base_url = (base_url or settings.LLM_BASE_URL or settings.OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
        self.model = model or settings.OLLAMA_MODEL or settings.LLM_MODEL or "qwen3:8b"
        self.timeout = timeout
        self._client = client

    @property
    def client(self) -> httpx.Client:
        """Return lazily-initialized HTTP client instance."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate completion using local Ollama /api/generate endpoint.

        Args:
            prompt: User prompt text
            system_prompt: Optional system persona instructions

        Returns:
            str: Generated completion text

        Raises:
            LLMProviderError: If prompt is empty or response parsing fails
            LLMConnectionError: If connection to Ollama fails
            LLMTimeoutError: If Ollama request times out
            LLMResponseError: If Ollama returns non-200 HTTP status
        """
        if not prompt or not prompt.strip():
            raise LLMProviderError("Prompt cannot be empty.")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            logger.info("Calling Ollama API at %s for model '%s'", self.base_url, self.model)
            response = self.client.post(url, json=payload, timeout=self.timeout)
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("Failed to connect to Ollama at %s: %s", self.base_url, exc)
            raise LLMConnectionError("Unable to connect to local LLM service.") from exc
        except httpx.TimeoutException as exc:
            logger.error("Timeout communicating with Ollama (%ss): %s", self.timeout, exc)
            raise LLMTimeoutError("LLM service request timed out.") from exc
        except httpx.HTTPError as exc:
            logger.error("HTTP error communicating with Ollama: %s", exc)
            raise LLMProviderError("LLM service communication failed.") from exc

        if response.status_code != 200:
            logger.error(
                "Ollama returned HTTP %d for model '%s': %s",
                response.status_code,
                self.model,
                response.text,
            )
            raise LLMResponseError(
                f"LLM service returned error status {response.status_code}."
            )

        try:
            data = response.json()
            generated = data.get("response", "")
            return generated.strip()
        except Exception as exc:
            logger.error("Failed to parse JSON response from Ollama: %s", exc)
            raise LLMProviderError("Invalid response format from LLM service.") from exc

    def close(self) -> None:
        """Close the underlying HTTP client if initialized."""
        if self._client is not None:
            self._client.close()


def get_llm_provider() -> LLMProvider:
    """Dependency provider / singleton factory for active LLMProvider based on LLM_PROVIDER setting."""
    provider_name = (settings.LLM_PROVIDER or "ollama").strip().lower()
    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.LLM_BASE_URL or settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL or settings.OLLAMA_MODEL,
            timeout=settings.LLM_TIMEOUT,
        )
    elif provider_name == "groq":
        return GroqProvider(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            timeout=settings.LLM_TIMEOUT,
        )
    else:
        raise LLMProviderError(
            f"Unsupported LLM provider: '{settings.LLM_PROVIDER}'. Supported: 'ollama', 'groq'."
        )
