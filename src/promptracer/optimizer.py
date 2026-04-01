"""Prompt optimizer: use LLM feedback to iteratively improve prompts."""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from promptracer.prompt import Prompt
from promptracer.eval import evaluate
from promptracer.providers import get_provider

_OPTIMIZE_PROMPT = """You are a prompt engineering expert. Analyze this prompt and its evaluation, then suggest an improved version.

ORIGINAL PROMPT:
{prompt}

MODEL RESPONSE:
{response}

EVALUATION:
Score: {score}/10
Reasoning: {reasoning}

Write an improved version of the prompt that would score higher. Only output the improved prompt text, nothing else. Keep the same {{variable}} placeholders if any."""


@dataclass
class OptimizeIteration:
    """A single optimization iteration."""

    version: int
    prompt_text: str
    response: str
    score: float
    reasoning: str


@dataclass
class OptimizeResult:
    """Results from prompt optimization."""

    original: str
    iterations: list[OptimizeIteration] = field(default_factory=list)

    @property
    def best(self) -> OptimizeIteration:
        return max(self.iterations, key=lambda i: i.score)

    @property
    def improvement(self) -> float:
        if len(self.iterations) < 2:
            return 0.0
        return self.iterations[-1].score - self.iterations[0].score

    def print(self) -> None:
        console = Console()

        table = Table(title="Prompt Optimization", show_lines=True)
        table.add_column("Version", justify="center")
        table.add_column("Score", justify="center")
        table.add_column("Prompt Preview", max_width=60)

        for it in self.iterations:
            color = "green" if it.score >= 7 else "yellow" if it.score >= 4 else "red"
            preview = it.prompt_text[:60] + "..." if len(it.prompt_text) > 60 else it.prompt_text
            table.add_row(
                f"v{it.version}",
                f"[{color}]{it.score}/10[/{color}]",
                preview,
            )

        console.print(table)

        best = self.best
        console.print(
            Panel(
                best.prompt_text,
                title=f"Best Prompt (v{best.version}, score: {best.score}/10)",
                border_style="green",
            )
        )

        imp = self.improvement
        if imp > 0:
            console.print(f"\n[green]Improvement: +{imp:.1f} points[/green]")
        elif imp < 0:
            console.print(f"\n[red]Regression: {imp:.1f} points[/red]")
        else:
            console.print("\n[yellow]No change in score[/yellow]")


def optimize(
    prompt: Prompt,
    *,
    model: str = "openai/gpt-4o",
    optimizer: str = "openai/gpt-4o",
    criteria: str = "accuracy, relevance, and completeness",
    judge: str = "openai/gpt-4o-mini",
    iterations: int = 3,
) -> OptimizeResult:
    """Iteratively optimize a prompt using LLM feedback.

    Args:
        prompt: The prompt to optimize.
        model: Model to test the prompt against.
        optimizer: Model to suggest improvements.
        criteria: Evaluation criteria.
        judge: Model to judge quality.
        iterations: Number of optimization rounds.
    """
    result = OptimizeResult(original=prompt.template)
    current_template = prompt.template

    for i in range(iterations):
        # Run the current prompt
        p = Prompt(current_template, system=prompt.system)
        p._vars = dict(prompt._vars)
        run_result = p.run(model)

        # Evaluate
        eval_result = evaluate(run_result, criteria=criteria, judge=judge)

        result.iterations.append(
            OptimizeIteration(
                version=i + 1,
                prompt_text=current_template,
                response=run_result.response,
                score=eval_result.score,
                reasoning=eval_result.reasoning,
            )
        )

        # If perfect score, stop
        if eval_result.score >= 9.5:
            break

        # Ask optimizer for improvement
        if i < iterations - 1:
            opt_prompt = _OPTIMIZE_PROMPT.format(
                prompt=current_template,
                response=run_result.response,
                score=eval_result.score,
                reasoning=eval_result.reasoning,
            )
            opt_provider = get_provider(optimizer)
            opt_result = opt_provider.complete(opt_prompt)
            current_template = opt_result.response.strip()

    return result
