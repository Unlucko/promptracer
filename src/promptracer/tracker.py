"""Cost tracker: persist and report spending across sessions."""

from __future__ import annotations

import json
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from promptracer.prompt import RunResult

_DEFAULT_DIR = Path.home() / ".promptracer"
_LOG_FILE = _DEFAULT_DIR / "usage.jsonl"


def _ensure_dir() -> None:
    _DEFAULT_DIR.mkdir(parents=True, exist_ok=True)


def log_run(result: RunResult) -> None:
    """Append a run result to the usage log."""
    _ensure_dir()
    entry = {
        "timestamp": result.timestamp,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "cost": result.cost,
        "latency": round(result.latency, 3),
    }
    with _LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def _load_entries(since: float | None = None) -> list[dict]:
    if not _LOG_FILE.exists():
        return []
    entries = []
    for line in _LOG_FILE.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if since and entry["timestamp"] < since:
            continue
        entries.append(entry)
    return entries


def _aggregate(entries: list[dict]) -> dict[str, dict]:
    """Aggregate entries by model."""
    models: dict[str, dict] = {}
    for e in entries:
        model = e["model"]
        if model not in models:
            models[model] = {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "total_latency": 0.0,
            }
        m = models[model]
        m["requests"] += 1
        m["input_tokens"] += e["input_tokens"]
        m["output_tokens"] += e["output_tokens"]
        m["cost"] += e["cost"]
        m["total_latency"] += e["latency"]
    return models


def report(period: str = "all") -> None:
    """Print a cost report.

    Args:
        period: "today", "week", "month", or "all"
    """
    now = time.time()
    since = None
    if period == "today":
        since = now - 86400
    elif period == "week":
        since = now - 86400 * 7
    elif period == "month":
        since = now - 86400 * 30

    entries = _load_entries(since)
    if not entries:
        Console().print("[dim]No usage data found.[/dim]")
        return

    models = _aggregate(entries)
    console = Console()
    title = f"Cost Report — {period}" if period != "all" else "Cost Report — All Time"
    table = Table(title=title, show_lines=True)

    table.add_column("Model", style="cyan")
    table.add_column("Requests", justify="right")
    table.add_column("Tokens (in/out)", justify="right")
    table.add_column("Avg Latency", justify="right", style="yellow")
    table.add_column("Total Cost", justify="right", style="green")

    total_cost = 0.0
    total_requests = 0

    for model, data in sorted(models.items(), key=lambda x: x[1]["cost"], reverse=True):
        avg_latency = data["total_latency"] / data["requests"]
        cost_str = "FREE" if data["cost"] == 0 else f"${data['cost']:.4f}"
        total_cost += data["cost"]
        total_requests += data["requests"]

        table.add_row(
            model,
            str(data["requests"]),
            f"{data['input_tokens']}/{data['output_tokens']}",
            f"{avg_latency:.2f}s",
            cost_str,
        )

    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_requests}[/bold]",
        "",
        "",
        f"[bold]${total_cost:.4f}[/bold]",
    )

    console.print(table)


def clear_log() -> None:
    """Clear usage history."""
    if _LOG_FILE.exists():
        _LOG_FILE.unlink()
