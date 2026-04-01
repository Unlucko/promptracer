"""LLM-as-judge evaluation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from promptracer.prompt import RunResult


@dataclass
class EvalResult:
    """Result from evaluating a model response."""

    score: float  # 0-10
    reasoning: str
    criteria: str
    judge_model: str
    evaluated_model: str

    def print(self) -> None:
        console = Console()
        color = "green" if self.score >= 7 else "yellow" if self.score >= 4 else "red"
        score_text = Text(f"{self.score}/10", style=f"bold {color}")

        content = Text()
        content.append("Score: ")
        content.append(score_text)
        content.append(f"\nCriteria: {self.criteria}")
        content.append(f"\nJudge: {self.judge_model}")
        content.append(f"\nEvaluated: {self.evaluated_model}")
        content.append(f"\n\n{self.reasoning}")

        console.print(Panel(content, title="PromptLab Eval", border_style=color))


_EVAL_PROMPT = """You are an expert evaluator. Score the following AI response on a scale of 0-10 based on the given criteria.

CRITERIA: {criteria}

ORIGINAL PROMPT: {prompt}

RESPONSE TO EVALUATE:
{response}

Respond in this exact format:
SCORE: <number 0-10>
REASONING: <brief explanation>"""


def evaluate(
    result: RunResult,
    *,
    criteria: str = "accuracy, relevance, and completeness",
    judge: str = "openai/gpt-4o-mini",
    **kwargs: Any,
) -> EvalResult:
    """Evaluate a model response using LLM-as-judge.

    Args:
        result: The RunResult to evaluate.
        criteria: What to evaluate on (e.g., "accuracy", "creativity").
        judge: Model to use as judge.
        **kwargs: Additional arguments passed to the judge provider.
    """
    from promptracer.providers import get_provider

    provider = get_provider(judge)
    eval_prompt = _EVAL_PROMPT.format(
        criteria=criteria,
        prompt=result.prompt_text,
        response=result.response,
    )

    judge_result = provider.complete(eval_prompt, **kwargs)
    score, reasoning = _parse_eval_response(judge_result.response)

    return EvalResult(
        score=score,
        reasoning=reasoning,
        criteria=criteria,
        judge_model=judge,
        evaluated_model=result.model,
    )


def evaluate_compare(
    results: list[RunResult],
    *,
    criteria: str = "accuracy, relevance, and completeness",
    judge: str = "openai/gpt-4o-mini",
    **kwargs: Any,
) -> list[EvalResult]:
    """Evaluate multiple results and return sorted by score (best first)."""
    evals = [evaluate(r, criteria=criteria, judge=judge, **kwargs) for r in results]
    evals.sort(key=lambda e: e.score, reverse=True)
    return evals


def _parse_eval_response(response: str) -> tuple[float, str]:
    """Parse SCORE and REASONING from judge response."""
    score = 5.0
    reasoning = response

    for line in response.splitlines():
        line = line.strip()
        if line.upper().startswith("SCORE:"):
            try:
                raw = line.split(":", 1)[1].strip()
                # Handle "8/10" or just "8"
                score = float(raw.split("/")[0].strip())
                score = max(0, min(10, score))
            except (ValueError, IndexError):
                pass
        elif line.upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    return score, reasoning
