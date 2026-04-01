"""Prompt chains: pipe output from one prompt into the next."""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console
from rich.panel import Panel

from promptracer.prompt import Prompt, RunResult


@dataclass
class ChainStep:
    """A single step in a prompt chain."""

    template: str
    model: str = "openai/gpt-4o"
    system: str | None = None
    output_var: str = "output"


@dataclass
class ChainResult:
    """Results from running a prompt chain."""

    steps: list[tuple[ChainStep, RunResult]] = field(default_factory=list)

    @property
    def final_response(self) -> str:
        return self.steps[-1][1].response if self.steps else ""

    @property
    def total_cost(self) -> float:
        return sum(r.cost for _, r in self.steps)

    @property
    def total_latency(self) -> float:
        return sum(r.latency for _, r in self.steps)

    def print(self) -> None:
        console = Console()
        for i, (step, result) in enumerate(self.steps, 1):
            console.print(
                Panel(
                    f"[dim]{step.template[:80]}...[/dim]\n\n{result.response}",
                    title=f"Step {i} — {result.model} ({result.latency:.2f}s, ${result.cost:.4f})",
                    border_style="cyan",
                )
            )
        console.print(
            f"\n[bold]Total:[/bold] {self.total_latency:.2f}s, ${self.total_cost:.4f}"
        )


class Chain:
    """Build and run a sequence of prompts where each output feeds the next.

    Usage:
        result = (
            Chain()
            .step("Summarize this: {{input}}", model="openai/gpt-4o")
            .step("Translate to Spanish: {{output}}")
            .step("Make it sound poetic: {{output}}", model="anthropic/claude-sonnet-4-6")
            .run(input="Long article text here...")
        )
        print(result.final_response)
    """

    def __init__(self) -> None:
        self._steps: list[ChainStep] = []

    def step(
        self,
        template: str,
        *,
        model: str = "openai/gpt-4o",
        system: str | None = None,
        output_var: str = "output",
    ) -> Chain:
        """Add a step to the chain. Returns self for chaining."""
        self._steps.append(
            ChainStep(template=template, model=model, system=system, output_var=output_var)
        )
        return self

    def run(self, **initial_vars: str) -> ChainResult:
        """Execute the chain, piping outputs between steps."""
        if not self._steps:
            raise ValueError("Chain has no steps. Add steps with .step()")

        chain_result = ChainResult()
        current_vars = dict(initial_vars)

        for chain_step in self._steps:
            p = Prompt(chain_step.template, system=chain_step.system)
            p.set_vars(**current_vars)
            result = p.run(chain_step.model)
            chain_result.steps.append((chain_step, result))
            current_vars[chain_step.output_var] = result.response

        return chain_result

    async def arun(self, **initial_vars: str) -> ChainResult:
        """Async version of run()."""
        if not self._steps:
            raise ValueError("Chain has no steps. Add steps with .step()")

        chain_result = ChainResult()
        current_vars = dict(initial_vars)

        for chain_step in self._steps:
            p = Prompt(chain_step.template, system=chain_step.system)
            p.set_vars(**current_vars)
            result = await p.arun(chain_step.model)
            chain_result.steps.append((chain_step, result))
            current_vars[chain_step.output_var] = result.response

        return chain_result
