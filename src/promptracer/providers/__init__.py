"""Provider registry — parse model strings and return the right adapter."""

from __future__ import annotations

from promptracer.providers.base import Provider

_PROVIDER_MAP: dict[str, type[Provider]] = {}


def _register_defaults() -> None:
    from promptracer.providers.openai import OpenAIProvider
    from promptracer.providers.anthropic import AnthropicProvider
    from promptracer.providers.gemini import GeminiProvider
    from promptracer.providers.ollama import OllamaProvider

    _PROVIDER_MAP.update(
        {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "google": GeminiProvider,
            "ollama": OllamaProvider,
        }
    )


def parse_model(model_string: str) -> tuple[str, str]:
    """Parse 'provider/model' into (provider, model). Defaults to openai."""
    if "/" in model_string:
        provider, model = model_string.split("/", 1)
        return provider.lower(), model
    return "openai", model_string


def get_provider(model_string: str) -> Provider:
    """Get a configured provider instance for the given model string."""
    if not _PROVIDER_MAP:
        _register_defaults()

    provider_name, model = parse_model(model_string)
    if provider_name not in _PROVIDER_MAP:
        available = ", ".join(sorted(_PROVIDER_MAP.keys()))
        raise ValueError(f"Unknown provider '{provider_name}'. Available: {available}")

    return _PROVIDER_MAP[provider_name](model)


def register_provider(name: str, provider_class: type[Provider]) -> None:
    """Register a custom provider.

    Usage:
        from promptracer.providers import register_provider, Provider
        from promptracer.prompt import RunResult

        class MyProvider(Provider):
            def complete(self, prompt, *, system=None, **kwargs):
                # Your implementation
                return RunResult(...)

            async def acomplete(self, prompt, *, system=None, **kwargs):
                return self.complete(prompt, system=system, **kwargs)

        register_provider("myapi", MyProvider)
        # Now use: Prompt("hello").run("myapi/my-model")
    """
    if not _PROVIDER_MAP:
        _register_defaults()
    _PROVIDER_MAP[name.lower()] = provider_class


__all__ = ["Provider", "get_provider", "parse_model", "register_provider"]
