"""Tests for custom provider registration."""

from promptracer.providers import register_provider, get_provider, Provider
from promptracer.prompt import RunResult


class MockProvider(Provider):
    def complete(self, prompt, *, system=None, **kwargs):
        return RunResult(
            model=f"mock/{self.model}",
            response="mock response",
            latency=0.01,
            input_tokens=5,
            output_tokens=3,
            cost=0.0,
            prompt_text=prompt,
        )

    async def acomplete(self, prompt, *, system=None, **kwargs):
        return self.complete(prompt, system=system, **kwargs)


def test_register_and_use_custom_provider():
    register_provider("mock", MockProvider)
    provider = get_provider("mock/test-model")
    assert isinstance(provider, MockProvider)

    result = provider.complete("hello")
    assert result.model == "mock/test-model"
    assert result.response == "mock response"


def test_custom_provider_via_prompt():
    register_provider("mock", MockProvider)
    from promptracer.prompt import Prompt
    p = Prompt("Hello {{name}}")
    p.set_vars(name="World")
    result = p.run("mock/any-model")
    assert result.response == "mock response"
