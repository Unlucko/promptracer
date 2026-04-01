"""Ollama provider adapter (local models, free)."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from promptlab.prompt import RunResult
from promptlab.providers.base import Provider


class OllamaProvider(Provider):
    def _base_url(self) -> str:
        return os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> RunResult:
        url = f"{self._base_url()}/api/chat"
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }

        start = time.perf_counter()
        resp = httpx.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        latency = time.perf_counter() - start

        data = resp.json()
        text = data.get("message", {}).get("content", "")
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return RunResult(
            model=f"ollama/{self.model}",
            response=text,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=0.0,
            prompt_text=prompt,
        )

    async def acomplete(
        self, prompt: str, *, system: str | None = None, **kwargs: Any
    ) -> RunResult:
        url = f"{self._base_url()}/api/chat"
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }

        start = time.perf_counter()
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=120)
            resp.raise_for_status()
        latency = time.perf_counter() - start

        data = resp.json()
        text = data.get("message", {}).get("content", "")
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return RunResult(
            model=f"ollama/{self.model}",
            response=text,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=0.0,
            prompt_text=prompt,
        )
