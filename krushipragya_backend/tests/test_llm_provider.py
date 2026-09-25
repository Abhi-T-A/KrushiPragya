"""Unit tests for LLMProvider, GroqProvider, and OllamaProvider.

All HTTP interactions are mocked using MagicMock / unittest.mock to ensure
deterministic tests that do NOT call external APIs or require running servers.
Never logs or exposes actual API keys.
"""
from unittest.mock import MagicMock
import httpx
import pytest

from app.core.config import settings
from app.services.llm_provider import (
    GroqProvider,
    LLMConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMResponseError,
    LLMTimeoutError,
    OllamaProvider,
    get_llm_provider,
)


# ==============================================================================
# Abstract Interface Tests
# ==============================================================================

def test_llm_provider_is_abstract():
    """Verify that LLMProvider cannot be instantiated directly."""
    with pytest.raises(TypeError) as exc_info:
        LLMProvider()
    assert "Can't instantiate abstract class" in str(exc_info.value)


# ==============================================================================
# GroqProvider Tests
# ==============================================================================

def test_groq_provider_initialization():
    """Verify GroqProvider initializes with custom parameters and strips trailing slashes."""
    mock_client = MagicMock(spec=httpx.Client)
    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1/",
        api_key="mock_secret_key_123",
        model="openai/gpt-oss-120b",
        temperature=0.0,
        timeout=180.0,
        client=mock_client,
    )

    assert provider.base_url == "https://api.groq.com/openai/v1"
    assert provider.api_key == "mock_secret_key_123"
    assert provider.model == "openai/gpt-oss-120b"
    assert provider.temperature == 0.0
    assert provider.timeout == 180.0
    assert provider.client is mock_client


def test_groq_provider_endpoint_and_authorization_header():
    """Verify GroqProvider calls /chat/completions with Authorization Bearer header."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Apply 1% Bordeaux mixture for fruit rot prevention.",
                }
            }
        ]
    }
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        model="openai/gpt-oss-120b",
        temperature=0.0,
        client=mock_client,
    )

    result = provider.generate("What should I apply for arecanut rot?")

    assert result == "Apply 1% Bordeaux mixture for fruit rot prevention."
    mock_client.post.assert_called_once()
    called_url, called_kwargs = mock_client.post.call_args
    assert called_url[0] == "https://api.groq.com/openai/v1/chat/completions"
    assert called_kwargs["headers"]["Authorization"] == "Bearer test_dummy_key_abc"
    assert called_kwargs["headers"]["Content-Type"] == "application/json"


def test_groq_provider_payload_model_and_temperature():
    """Verify GroqProvider sends the exact model and temperature in payload."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Advisory text"}}]
    }
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        model="openai/gpt-oss-120b",
        temperature=0.2,
        client=mock_client,
    )

    provider.generate("Test prompt")

    called_kwargs = mock_client.post.call_args[1]
    assert called_kwargs["json"]["model"] == "openai/gpt-oss-120b"
    assert called_kwargs["json"]["temperature"] == 0.2


def test_groq_provider_system_and_user_messages():
    """Verify system message is placed before user message when system_prompt is provided."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Advisory output"}}]
    }
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    provider.generate(
        prompt="Explain weather risks.",
        system_prompt="You are a KrushiPragya assistant.",
    )

    called_kwargs = mock_client.post.call_args[1]
    messages = called_kwargs["json"]["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a KrushiPragya assistant."
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Explain weather risks."


def test_groq_provider_user_message_only_when_no_system_prompt():
    """Verify only user message is sent when system_prompt is None or whitespace."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Advisory output"}}]
    }
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    provider.generate(prompt="Explain weather risks.", system_prompt="   ")

    called_kwargs = mock_client.post.call_args[1]
    messages = called_kwargs["json"]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Explain weather risks."


@pytest.mark.parametrize("empty_prompt", ["", "   ", "\n\t"])
def test_groq_provider_empty_prompt_raises_error(empty_prompt):
    """Verify empty or whitespace prompt raises LLMProviderError without network call."""
    mock_client = MagicMock(spec=httpx.Client)
    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate(empty_prompt)

    assert "Prompt cannot be empty" in str(exc_info.value)
    mock_client.post.assert_not_called()


@pytest.mark.parametrize("invalid_key", [None, "", "   "])
def test_groq_provider_missing_api_key_raises_error(invalid_key):
    """Verify missing API key raises LLMProviderError without network call."""
    mock_client = MagicMock(spec=httpx.Client)
    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key=invalid_key,
        client=mock_client,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate("Valid prompt")

    assert "Groq API key is not configured" in str(exc_info.value)
    mock_client.post.assert_not_called()


@pytest.mark.parametrize("auth_status", [401, 403])
def test_groq_provider_auth_error_handling(auth_status):
    """Verify HTTP 401 and 403 raise LLMResponseError for authentication failure."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = auth_status
    mock_response.text = '{"error": {"message": "Invalid API Key"}}'
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMResponseError) as exc_info:
        provider.generate("Test prompt")

    assert "Groq API authentication failed" in str(exc_info.value)
    # Ensure sensitive credentials are never in the exception string
    assert "test_dummy_key_abc" not in str(exc_info.value)


def test_groq_provider_rate_limit_429_handling():
    """Verify HTTP 429 raises LLMResponseError with rate limit description."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = '{"error": {"message": "Rate limit reached"}}'
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMResponseError) as exc_info:
        provider.generate("Test prompt")

    assert "Groq API rate limit exceeded" in str(exc_info.value)


@pytest.mark.parametrize("server_status", [500, 502, 503, 504])
def test_groq_provider_server_error_handling(server_status):
    """Verify HTTP 5xx errors raise LLMResponseError with status code."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = server_status
    mock_response.text = "Internal Server Error"
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMResponseError) as exc_info:
        provider.generate("Test prompt")

    assert f"Groq API returned error status {server_status}" in str(exc_info.value)


def test_groq_provider_timeout_handling():
    """Verify timeout raises LLMTimeoutError."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ReadTimeout("Request timed out after 300s")

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMTimeoutError) as exc_info:
        provider.generate("Test prompt")

    assert "Groq LLM service request timed out" in str(exc_info.value)


def test_groq_provider_connection_failure():
    """Verify network connection failure raises LLMConnectionError."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ConnectError("Failed to resolve host api.groq.com")

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMConnectionError) as exc_info:
        provider.generate("Test prompt")

    assert "Unable to connect to Groq LLM service" in str(exc_info.value)


def test_groq_provider_generic_http_error():
    """Verify generic HTTP protocol errors raise LLMProviderError."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ProtocolError("Connection reset by peer")

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate("Test prompt")

    assert "Groq LLM service communication failed" in str(exc_info.value)


def test_groq_provider_malformed_json_response():
    """Verify malformed JSON response raises LLMProviderError."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON string")
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate("Test prompt")

    assert "Invalid JSON response from Groq service" in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"role": "assistant", "content": None}}]},
        {"choices": ["invalid_choice"]},
    ],
)
def test_groq_provider_malformed_structure_raises_error(invalid_payload):
    """Verify incomplete or empty choices structure raises LLMProviderError."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = invalid_payload
    mock_client.post.return_value = mock_response

    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )

    with pytest.raises(LLMProviderError):
        provider.generate("Test prompt")


def test_groq_provider_close_client():
    """Verify provider.close() properly closes the underlying httpx client."""
    mock_client = MagicMock(spec=httpx.Client)
    provider = GroqProvider(
        base_url="https://api.groq.com/openai/v1",
        api_key="test_dummy_key_abc",
        client=mock_client,
    )
    provider.close()
    mock_client.close.assert_called_once()


# ==============================================================================
# OllamaProvider Tests (Preserved for Local Development)
# ==============================================================================

def test_ollama_provider_defaults():
    """Verify OllamaProvider initializes with configuration defaults."""
    provider = OllamaProvider()
    assert provider.base_url == (settings.LLM_BASE_URL or settings.OLLAMA_BASE_URL).rstrip("/")
    assert provider.timeout == 60.0
    assert provider._client is None


def test_ollama_provider_custom_initialization():
    """Verify OllamaProvider accepts custom parameters and strips trailing slashes."""
    mock_client = MagicMock(spec=httpx.Client)
    provider = OllamaProvider(
        base_url="http://custom-ollama:11434/",
        model="custom-model:latest",
        timeout=120.0,
        client=mock_client,
    )
    assert provider.base_url == "http://custom-ollama:11434"
    assert provider.model == "custom-model:latest"
    assert provider.timeout == 120.0
    assert provider.client is mock_client


def test_ollama_provider_generate_success():
    """Verify successful completion returns clean generated text."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "qwen3:8b",
        "response": "  Apply 2g/L copper oxychloride spray.  \n",
        "done": True,
    }
    mock_client.post.return_value = mock_response

    provider = OllamaProvider(client=mock_client)
    result = provider.generate("What is the treatment for yellow leaf disease?")

    assert result == "Apply 2g/L copper oxychloride spray."
    mock_client.post.assert_called_once()
    called_url, called_kwargs = mock_client.post.call_args
    assert called_url[0].endswith("/api/generate")
    assert called_kwargs["json"]["prompt"] == "What is the treatment for yellow leaf disease?"
    assert called_kwargs["json"]["stream"] is False


def test_ollama_provider_generate_with_system_prompt():
    """Verify that system_prompt is included in the Ollama request payload."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "qwen3:8b",
        "response": "Advisory text generated with persona.",
        "done": True,
    }
    mock_client.post.return_value = mock_response

    provider = OllamaProvider(client=mock_client)
    result = provider.generate(
        prompt="Tell me about paddy blast.",
        system_prompt="You are an expert Kannada agricultural extension officer.",
    )

    assert result == "Advisory text generated with persona."
    called_kwargs = mock_client.post.call_args[1]
    assert called_kwargs["json"]["system"] == "You are an expert Kannada agricultural extension officer."
    assert called_kwargs["json"]["prompt"] == "Tell me about paddy blast."


@pytest.mark.parametrize("empty_prompt", ["", "   ", "\n\t"])
def test_ollama_provider_empty_prompt_raises_error(empty_prompt):
    """Verify that empty or whitespace prompts raise LLMProviderError without network calls."""
    mock_client = MagicMock(spec=httpx.Client)
    provider = OllamaProvider(client=mock_client)

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate(empty_prompt)

    assert "Prompt cannot be empty" in str(exc_info.value)
    mock_client.post.assert_not_called()


def test_ollama_provider_connection_error():
    """Verify connection failure raises clean LLMConnectionError without leaking internals."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")

    provider = OllamaProvider(client=mock_client)

    with pytest.raises(LLMConnectionError) as exc_info:
        provider.generate("Test prompt")

    assert "Unable to connect to local LLM service" in str(exc_info.value)


def test_ollama_provider_timeout_error():
    """Verify request timeout raises LLMTimeoutError."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ReadTimeout("The read operation timed out")

    provider = OllamaProvider(client=mock_client)

    with pytest.raises(LLMTimeoutError) as exc_info:
        provider.generate("Test prompt")

    assert "LLM service request timed out" in str(exc_info.value)


def test_ollama_provider_non_200_status():
    """Verify non-200 HTTP response raises LLMResponseError with status code."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = '{"error": "model not found"}'
    mock_client.post.return_value = mock_response

    provider = OllamaProvider(client=mock_client)

    with pytest.raises(LLMResponseError) as exc_info:
        provider.generate("Test prompt")

    assert "LLM service returned error status 404" in str(exc_info.value)


def test_ollama_provider_invalid_json_response():
    """Verify non-JSON response from server raises LLMProviderError."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_client.post.return_value = mock_response

    provider = OllamaProvider(client=mock_client)

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate("Test prompt")

    assert "Invalid response format from LLM service" in str(exc_info.value)


def test_ollama_provider_close_client():
    """Verify provider.close() properly closes the client."""
    mock_client = MagicMock(spec=httpx.Client)
    provider = OllamaProvider(client=mock_client)
    provider.close()
    mock_client.close.assert_called_once()


# ==============================================================================
# Factory Selector Tests
# ==============================================================================

def test_get_llm_provider_factory_groq(monkeypatch):
    """Verify get_llm_provider returns GroqProvider when LLM_PROVIDER='groq'."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setattr(settings, "LLM_API_KEY", "dummy_key_for_test")
    monkeypatch.setattr(settings, "LLM_MODEL", "openai/gpt-oss-120b")

    provider = get_llm_provider()
    assert isinstance(provider, GroqProvider)
    assert isinstance(provider, LLMProvider)
    assert provider.base_url == "https://api.groq.com/openai/v1"
    assert provider.model == "openai/gpt-oss-120b"


def test_get_llm_provider_factory_ollama(monkeypatch):
    """Verify get_llm_provider returns OllamaProvider when LLM_PROVIDER='ollama'."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "http://localhost:11434")
    monkeypatch.setattr(settings, "LLM_MODEL", "qwen3:8b")

    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)
    assert isinstance(provider, LLMProvider)
    assert provider.base_url == "http://localhost:11434"
    assert provider.model == "qwen3:8b"


def test_get_llm_provider_factory_unsupported(monkeypatch):
    """Verify get_llm_provider raises LLMProviderError for unsupported providers."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "unsupported_provider")

    with pytest.raises(LLMProviderError) as exc_info:
        get_llm_provider()

    assert "Unsupported LLM provider" in str(exc_info.value)
