"""Side-by-side comparison of prompts across multiple models."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text

from promptracer.prompt import Prompt, RunResult


@dataclass
class CompareResult:
    """Results from comparing a prompt across multiple models."""

    results: list[RunResult] = field(default_factory=list)

    @property
    def fastest(self) -> RunResult:
        return min(self.results, key=lambda r: r.latency)

    @property
    def cheapest(self) -> RunResult:
        return min(self.results, key=lambda r: r.cost)

    def print_table(self, max_response_len: int = 80) -> None:
        console = Console()
        table = Table(title="PromptLab Comparison", show_lines=True)

        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Response", style="white", max_width=max_response_len)
        table.add_column("Latency", style="yellow", justify="right")
        table.add_column("Tokens (in/out)", justify="right")
        table.add_column("Cost", style="green", justify="right")

        fastest_model = self.fastest.model
        cheapest_model = self.cheapest.model

        for r in self.results:
            model_text = Text(r.model)
            badges = []
            if r.model == fastest_model:
                badges.append("fastest")
            if r.model == cheapest_model:
                badges.append("cheapest")
            if badges:
                model_text.append(f" [{', '.join(badges)}]", style="bold green")

            response_preview = r.response[:max_response_len]
            if len(r.response) > max_response_len:
                response_preview += "..."

            cost_str = "FREE" if r.cost == 0 else f"${r.cost:.4f}"

            table.add_row(
                model_text,
                response_preview,
                f"{r.latency:.2f}s",
                f"{r.input_tokens}/{r.output_tokens}",
                cost_str,
            )

        console.print(table)

    def to_dict(self) -> list[dict[str, Any]]:
        return [
            {
                "model": r.model,
                "response": r.response,
                "latency": round(r.latency, 3),
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cost": round(r.cost, 6),
            }
            for r in self.results
        ]


def compare(
    prompt: Prompt | str,
    models: list[str],
    *,
    vars: dict[str, str] | None = None,
    system: str | None = None,
    **kwargs: Any,
) -> CompareResult:
    """Compare a prompt across multiple models.

    Args:
        prompt: A Prompt instance or template string.
        models: List of model strings like ["openai/gpt-4o", "anthropic/claude-sonnet-4-6"].
        vars: Template variables (if prompt is a string).
        system: System prompt override.
        **kwargs: Additional arguments passed to providers.
    """
    if isinstance(prompt, str):
        prompt = Prompt(prompt, system=system)
        if vars:
            prompt.set_vars(**vars)
    elif system:
        prompt.system = system

    if vars and not isinstance(prompt, str):
        prompt.set_vars(**vars)

    result = CompareResult()
    for model in models:
        try:
            run_result = prompt.run(model, **kwargs)
            result.results.append(run_result)
        except Exception as e:
            result.results.append(
                RunResult(
                    model=model,
                    response=f"[ERROR] {e}",
                    latency=0,
                    input_tokens=0,
                    output_tokens=0,
                    cost=0,
                    prompt_text=prompt.render(),
                )
            )

    return result


async def acompare(
    prompt: Prompt | str,
    models: list[str],
    *,
    vars: dict[str, str] | None = None,
    system: str | None = None,
    **kwargs: Any,
) -> CompareResult:
    """Async version — runs all models concurrently."""
    if isinstance(prompt, str):
        prompt = Prompt(prompt, system=system)
        if vars:
            prompt.set_vars(**vars)
    elif system:
        prompt.system = system

    if vars and not isinstance(prompt, str):
        prompt.set_vars(**vars)

    async def _run(model: str) -> RunResult:
        try:
            return await prompt.arun(model, **kwargs)
        except Exception as e:
            return RunResult(
                model=model,
                response=f"[ERROR] {e}",
                latency=0,
                input_tokens=0,
                output_tokens=0,
                cost=0,
                prompt_text=prompt.render(),
            )

    results = await asyncio.gather(*[_run(m) for m in models])
    return CompareResult(results=list(results))
