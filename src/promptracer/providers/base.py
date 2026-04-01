"""Base provider interface."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

from promptracer.prompt import RunResult


class Provider(ABC):
    """Abstract base for LLM providers."""

    def __init__(self, model: str):
        self.model = model

    def _get_env(self, key: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise EnvironmentError(
                f"Missing environment variable '{key}'. "
                f"Set it with: export {key}=your-key-here"
            )
        return value

    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> RunResult:
        ...

    @abstractmethod
    async def acomplete(
        self, prompt: str, *, system: str | None = None, **kwargs: Any
    ) -> RunResult:
        ...
