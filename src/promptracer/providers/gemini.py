"""Google Gemini provider adapter."""

from __future__ import annotations

import time
from typing import Any

from promptracer.prompt import RunResult
from promptracer.providers.base import Provider

_PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.15, 0.60),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = _PRICING.get(model, (0.15, 0.60))
    return (input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000


class GeminiProvider(Provider):
    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> RunResult:
        try:
            from google import genai
        except ImportError:
            raise ImportError("Install google-genai: pip install promptracer[google]")

        client = genai.Client(api_key=self._get_env("GEMINI_API_KEY"))

        config: dict[str, Any] = {}
        if system:
            config["system_instruction"] = system

        start = time.perf_counter()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config if config else None,
            **kwargs,
        )
        latency = time.perf_counter() - start

        text = response.text or ""
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0

        return RunResult(
            model=f"gemini/{self.model}",
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
            from google import genai
        except ImportError:
            raise ImportError("Install google-genai: pip install promptracer[google]")

        client = genai.Client(api_key=self._get_env("GEMINI_API_KEY"))

        config: dict[str, Any] = {}
        if system:
            config["system_instruction"] = system

        start = time.perf_counter()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config if config else None,
            **kwargs,
        )
        latency = time.perf_counter() - start

        text = response.text or ""
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0

        return RunResult(
            model=f"gemini/{self.model}",
            response=text,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=_estimate_cost(self.model, input_tokens, output_tokens),
            prompt_text=prompt,
        )
