"""Batch evaluation: run test suites defined in YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from promptracer.prompt import Prompt, RunResult
from promptracer.eval import evaluate, EvalResult


@dataclass
class Case:
    """A single test case with input variables and optional expected output."""

    name: str
    vars: dict[str, str]
    expected: str | None = None
    criteria: str | None = None


@dataclass
class BatchResult:
    """Results from running a batch of test cases."""

    model: str
    results: list[tuple[Case, RunResult, EvalResult | None]] = field(default_factory=list)

    @property
    def avg_score(self) -> float | None:
        scores = [e.score for _, _, e in self.results if e is not None]
        return sum(scores) / len(scores) if scores else None

    @property
    def avg_latency(self) -> float:
        return sum(r.latency for _, r, _ in self.results) / len(self.results)

    @property
    def total_cost(self) -> float:
        return sum(r.cost for _, r, _ in self.results)

    def print_table(self, max_response_len: int = 60) -> None:
        console = Console()
        table = Table(title=f"Batch Results — {self.model}", show_lines=True)

        table.add_column("Test Case", style="cyan")
        table.add_column("Response", max_width=max_response_len)
        table.add_column("Score", justify="center")
        table.add_column("Latency", justify="right", style="yellow")
        table.add_column("Cost", justify="right", style="green")

        for tc, run, ev in self.results:
            response_preview = run.response[:max_response_len]
            if len(run.response) > max_response_len:
                response_preview += "..."

            score_str = ""
            if ev is not None:
                color = "green" if ev.score >= 7 else "yellow" if ev.score >= 4 else "red"
                score_str = f"[{color}]{ev.score}/10[/{color}]"

            cost_str = "FREE" if run.cost == 0 else f"${run.cost:.4f}"

            table.add_row(tc.name, response_preview, score_str, f"{run.latency:.2f}s", cost_str)

        # Summary row
        avg = self.avg_score
        avg_str = f"{avg:.1f}/10" if avg is not None else "—"
        table.add_row(
            "[bold]TOTAL[/bold]",
            "",
            f"[bold]{avg_str}[/bold]",
            f"[bold]{self.avg_latency:.2f}s[/bold]",
            f"[bold]${self.total_cost:.4f}[/bold]",
        )

        console.print(table)


@dataclass
class SuiteConfig:
    """Configuration for a test suite loaded from YAML."""

    template: str
    system: str | None
    models: list[str]
    judge: str | None
    criteria: str
    cases: list[Case]

    @classmethod
    def load(cls, path: str | Path) -> SuiteConfig:
        """Load a test suite from a YAML file.

        Expected format:
            template: "Translate to {{lang}}: {{text}}"
            system: "You are a translator"    # optional
            models:
              - openai/gpt-4o
              - anthropic/claude-sonnet-4-6
            judge: openai/gpt-4o-mini          # optional
            criteria: "accuracy and fluency"   # optional
            cases:
              - name: "Spanish to English"
                vars:
                  lang: English
                  text: "Hola mundo"
                expected: "Hello world"        # optional
              - name: "French to English"
                vars:
                  lang: English
                  text: "Bonjour le monde"
        """
        data = yaml.safe_load(Path(path).read_text())

        cases = []
        for c in data.get("cases", []):
            cases.append(
                Case(
                    name=c.get("name", f"case-{len(cases) + 1}"),
                    vars=c.get("vars", {}),
                    expected=c.get("expected"),
                    criteria=c.get("criteria"),
                )
            )

        return cls(
            template=data["template"],
            system=data.get("system"),
            models=data.get("models", ["openai/gpt-4o"]),
            judge=data.get("judge"),
            criteria=data.get("criteria", "accuracy, relevance, and completeness"),
            cases=cases,
        )


def run_batch(
    prompt: Prompt | str,
    cases: list[Case],
    *,
    model: str = "openai/gpt-4o",
    judge: str | None = None,
    criteria: str = "accuracy, relevance, and completeness",
    system: str | None = None,
) -> BatchResult:
    """Run a batch of test cases against a model.

    Args:
        prompt: Prompt template or Prompt instance.
        cases: List of test cases with variables.
        model: Model to test.
        judge: Judge model for evaluation (None to skip).
        criteria: Evaluation criteria.
        system: System prompt override.
    """
    if isinstance(prompt, str):
        prompt = Prompt(prompt, system=system)
    elif system:
        prompt.system = system

    batch = BatchResult(model=model)

    for tc in cases:
        p = Prompt(prompt.template, system=prompt.system)
        p.set_vars(**tc.vars)

        run_result = p.run(model)

        eval_result = None
        if judge:
            case_criteria = tc.criteria or criteria
            if tc.expected:
                case_criteria += f". Expected output: {tc.expected}"
            eval_result = evaluate(run_result, criteria=case_criteria, judge=judge)

        batch.results.append((tc, run_result, eval_result))

    return batch


def run_suite(path: str | Path) -> list[BatchResult]:
    """Load and run a complete test suite from YAML."""
    config = SuiteConfig.load(path)
    results = []

    for model in config.models:
        batch = run_batch(
            config.template,
            config.cases,
            model=model,
            judge=config.judge,
            criteria=config.criteria,
            system=config.system,
        )
        results.append(batch)

    return results
