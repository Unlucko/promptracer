"""OpenAI provider adapter."""

from __future__ import annotations

import time
from typing import Any

from promptpilot.prompt import RunResult
from promptpilot.providers.base import Provider

# Pricing per 1M tokens (input, output) — approximate
_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "o3-mini": (1.10, 4.40),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = _PRICING.get(model, (2.50, 10.00))
    return (input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000


class OpenAIProvider(Provider):
    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> RunResult:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install promptpilot[openai]")

        client = OpenAI(api_key=self._get_env("OPENAI_API_KEY"))
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.perf_counter()
        response = client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        latency = time.perf_counter() - start

        choice = response.choices[0]
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return RunResult(
            model=f"openai/{self.model}",
            response=choice.message.content or "",
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
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Install openai: pip install promptpilot[openai]")

        client = AsyncOpenAI(api_key=self._get_env("OPENAI_API_KEY"))
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.perf_counter()
        response = await client.chat.completions.create(
            model=self.model, messages=messages, **kwargs
        )
        latency = time.perf_counter() - start

        choice = response.choices[0]
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return RunResult(
            model=f"openai/{self.model}",
            response=choice.message.content or "",
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=_estimate_cost(self.model, input_tokens, output_tokens),
            prompt_text=prompt,
        )
