"""Tests for provider parsing and registry."""

import pytest

from promptpilot.providers import parse_model, get_provider
from promptpilot.providers.openai import OpenAIProvider
from promptpilot.providers.anthropic import AnthropicProvider
from promptpilot.providers.gemini import GeminiProvider
from promptpilot.providers.ollama import OllamaProvider


def test_parse_model_with_provider():
    provider, model = parse_model("openai/gpt-4o")
    assert provider == "openai"
    assert model == "gpt-4o"


def test_parse_model_default_openai():
    provider, model = parse_model("gpt-4o")
    assert provider == "openai"
    assert model == "gpt-4o"


def test_parse_model_anthropic():
    provider, model = parse_model("anthropic/claude-sonnet-4-6")
    assert provider == "anthropic"
    assert model == "claude-sonnet-4-6"


def test_parse_model_ollama():
    provider, model = parse_model("ollama/llama3")
    assert provider == "ollama"
    assert model == "llama3"


def test_get_provider_returns_correct_type():
    assert isinstance(get_provider("openai/gpt-4o"), OpenAIProvider)
    assert isinstance(get_provider("anthropic/claude-sonnet-4-6"), AnthropicProvider)
    assert isinstance(get_provider("gemini/gemini-2.0-flash"), GeminiProvider)
    assert isinstance(get_provider("google/gemini-2.0-flash"), GeminiProvider)
    assert isinstance(get_provider("ollama/llama3"), OllamaProvider)


def test_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("unknown/model")
