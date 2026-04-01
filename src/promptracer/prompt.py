"""Core Prompt class with template variables, versioning, and YAML persistence."""

from __future__ import annotations

import copy
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RunResult:
    """Result from running a prompt against a model."""

    model: str
    response: str
    latency: float
    input_tokens: int
    output_tokens: int
    cost: float
    prompt_text: str
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return f"RunResult(model={self.model!r}, latency={self.latency:.2f}s, cost=${self.cost:.4f})"


class Prompt:
    """A versionable, templated prompt that can run against any LLM provider.

    Usage:
        p = Prompt("Translate to {{lang}}: {{text}}")
        p.set_vars(lang="English", text="Hola mundo")
        result = p.run("openai/gpt-4o")
    """

    VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")

    def __init__(
        self,
        template: str,
        *,
        name: str | None = None,
        system: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.template = template
        self.name = name
        self.system = system
        self.metadata = metadata or {}
        self._vars: dict[str, str] = {}
        self._history: list[dict[str, Any]] = [
            {"version": 1, "template": template, "timestamp": time.time()}
        ]

    @property
    def variables(self) -> list[str]:
        """Extract variable names from the template."""
        return self.VAR_PATTERN.findall(self.template)

    @property
    def version(self) -> int:
        return len(self._history)

    def set_vars(self, **kwargs: str) -> Prompt:
        """Set template variables. Returns self for chaining."""
        self._vars.update(kwargs)
        return self

    def render(self) -> str:
        """Render the template with current variables."""
        missing = [v for v in self.variables if v not in self._vars]
        if missing:
            raise ValueError(f"Missing variables: {', '.join(missing)}")

        text = self.template
        for key, value in self._vars.items():
            text = text.replace(f"{{{{{key}}}}}", str(value))
        return text

    def update(self, new_template: str) -> Prompt:
        """Update the template and record a new version."""
        self._history.append(
            {"version": self.version + 1, "template": new_template, "timestamp": time.time()}
        )
        self.template = new_template
        return self

    def history(self) -> list[dict[str, Any]]:
        """Return version history."""
        return copy.deepcopy(self._history)

    def diff(self, v1: int = -1, v2: int | None = None) -> tuple[str, str]:
        """Return two template versions for comparison. Defaults to previous vs current."""
        if v2 is None:
            v2_idx = len(self._history) - 1
            v1_idx = max(0, v2_idx + v1) if v1 < 0 else v1 - 1
        else:
            v1_idx = v1 - 1
            v2_idx = v2 - 1
        return self._history[v1_idx]["template"], self._history[v2_idx]["template"]

    def run(self, model: str, **kwargs: Any) -> RunResult:
        """Run this prompt against a model.

        Args:
            model: Provider/model string like "openai/gpt-4o" or "ollama/llama3"
            **kwargs: Additional arguments passed to the provider.
        """
        from promptracer.providers import get_provider

        rendered = self.render()
        provider = get_provider(model)
        return provider.complete(rendered, system=self.system, **kwargs)

    async def arun(self, model: str, **kwargs: Any) -> RunResult:
        """Async version of run()."""
        from promptracer.providers import get_provider

        rendered = self.render()
        provider = get_provider(model)
        return await provider.acomplete(rendered, system=self.system, **kwargs)

    def save(self, path: str | Path) -> None:
        """Save prompt to a YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {"template": self.template}
        if self.name:
            data["name"] = self.name
        if self.system:
            data["system"] = self.system
        if self.metadata:
            data["metadata"] = self.metadata
        if self._vars:
            data["vars"] = self._vars
        if len(self._history) > 1:
            data["history"] = self._history

        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))

    @classmethod
    def load(cls, path: str | Path) -> Prompt:
        """Load a prompt from a YAML file."""
        path = Path(path)
        data = yaml.safe_load(path.read_text())
        p = cls(
            data["template"],
            name=data.get("name"),
            system=data.get("system"),
            metadata=data.get("metadata", {}),
        )
        if "vars" in data:
            p._vars = data["vars"]
        if "history" in data:
            p._history = data["history"]
        return p

    def __repr__(self) -> str:
        preview = self.template[:50] + "..." if len(self.template) > 50 else self.template
        return f"Prompt({preview!r}, v{self.version})"
