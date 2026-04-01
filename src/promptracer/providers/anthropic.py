"""Anthropic (Claude) provider adapter."""

from __future__ import annotations

import time
from typing import Any

from promptracer.prompt import RunResult
from promptracer.providers.base import Provider

_PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-6": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.80, 4.00),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = _PRICING.get(model, (3.00, 15.00))
    return (input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000


class AnthropicProvider(Provider):
    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> RunResult:
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install promptracer[anthropic]")

        client = anthropic.Anthropic(api_key=self._get_env("ANTHROPIC_API_KEY"))

        api_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.pop("max_tokens", 4096),
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }
        if system:
            api_kwargs["system"] = system

        start = time.perf_counter()
        response = client.messages.create(**api_kwargs)
        latency = time.perf_counter() - start

        text = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return RunResult(
            model=f"anthropic/{self.model}",
            response=text,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=_estimate_cost(self.model, input_tokens, output_tokens),
            prompt_text=prompt,
        )

    async def acomplete(
        self, prompt: str, *, system: str | None = None, **kwargs: Any
    ) -> RunResult:
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install promptracer[anthropic]")

        client = anthropic.AsyncAnthropic(api_key=self._get_env("ANTHROPIC_API_KEY"))

        api_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.pop("max_tokens", 4096),
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }
        if system:
            api_kwargs["system"] = system

        start = time.perf_counter()
        response = await client.messages.create(**api_kwargs)
        latency = time.perf_counter() - start

        text = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return RunResult(
            model=f"anthropic/{self.model}",
            response=text,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=_estimate_cost(self.model, input_tokens, output_tokens),
            prompt_text=prompt,
        )
