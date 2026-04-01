"""Model leaderboard: aggregate and rank models across batch results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table

from promptracer.batch import BatchResult


@dataclass
class ModelStats:
    """Aggregated stats for a single model."""

    model: str
    avg_score: float | None
    avg_latency: float
    total_cost: float
    total_requests: int
    pass_rate: float  # % of scores >= 7


@dataclass
class Leaderboard:
    """Ranked list of models by performance."""

    models: list[ModelStats] = field(default_factory=list)

    def print_table(self) -> None:
        console = Console()
        table = Table(title="Model Leaderboard", show_lines=True)

        table.add_column("Rank", justify="center", style="bold")
        table.add_column("Model", style="cyan")
        table.add_column("Avg Score", justify="center")
        table.add_column("Pass Rate", justify="center")
        table.add_column("Avg Latency", justify="right", style="yellow")
        table.add_column("Total Cost", justify="right", style="green")

        medals = {1: "[gold1]1st[/gold1]", 2: "[grey70]2nd[/grey70]", 3: "[orange3]3rd[/orange3]"}

        for i, m in enumerate(self.models, 1):
            rank = medals.get(i, str(i))
            score_str = f"{m.avg_score:.1f}/10" if m.avg_score is not None else "—"
            color = "green" if m.avg_score and m.avg_score >= 7 else "yellow" if m.avg_score and m.avg_score >= 4 else "red"
            score_str = f"[{color}]{score_str}[/{color}]"
            cost_str = "FREE" if m.total_cost == 0 else f"${m.total_cost:.4f}"
            pass_str = f"{m.pass_rate:.0f}%"

            table.add_row(
                rank, m.model, score_str, pass_str, f"{m.avg_latency:.2f}s", cost_str
            )

        console.print(table)

    def to_json(self, path: str) -> None:
        data = [
            {
                "rank": i,
                "model": m.model,
                "avg_score": m.avg_score,
                "pass_rate": round(m.pass_rate, 1),
                "avg_latency": round(m.avg_latency, 3),
                "total_cost": round(m.total_cost, 6),
                "total_requests": m.total_requests,
            }
            for i, m in enumerate(self.models, 1)
        ]
        Path(path).write_text(json.dumps(data, indent=2))


def build_leaderboard(batch_results: list[BatchResult]) -> Leaderboard:
    """Build a leaderboard from batch results, ranked by avg score (desc)."""
    stats = []
    for br in batch_results:
        scores = [ev.score for _, _, ev in br.results if ev is not None]
        avg_score = sum(scores) / len(scores) if scores else None
        pass_count = sum(1 for s in scores if s >= 7)
        pass_rate = (pass_count / len(scores) * 100) if scores else 0.0

        stats.append(
            ModelStats(
                model=br.model,
                avg_score=avg_score,
                avg_latency=br.avg_latency,
                total_cost=br.total_cost,
                total_requests=len(br.results),
                pass_rate=pass_rate,
            )
        )

    # Sort: by score desc (None last), then by latency asc
    stats.sort(key=lambda s: (-(s.avg_score or -1), s.avg_latency))
    return Leaderboard(models=stats)
