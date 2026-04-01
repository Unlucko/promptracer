"""PromptRacer CLI — test, compare, and evaluate prompts from the terminal."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="promptracer",
    help="The open-source prompt engineering toolkit.",
    no_args_is_help=True,
)
console = Console()


def _parse_vars(var_strings: list[str]) -> dict[str, str]:
    """Parse ['key=value', ...] into a dict."""
    result = {}
    for v in var_strings:
        if "=" not in v:
            raise typer.BadParameter(f"Invalid variable format: {v!r}. Use key=value")
        key, value = v.split("=", 1)
        result[key.strip()] = value.strip()
    return result


@app.command()
def run(
    prompt: str = typer.Argument(help="Prompt text or path to a .yaml prompt file"),
    model: str = typer.Option("openai/gpt-4o", "--model", "-m", help="Model to use"),
    var: list[str] = typer.Option([], "--var", "-v", help="Variables as key=value"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    stream: bool = typer.Option(False, "--stream", help="Stream response in real-time"),
) -> None:
    """Run a prompt against a single model."""
    from promptracer.prompt import Prompt
    from promptracer.providers import get_provider

    if Path(prompt).exists() and prompt.endswith((".yaml", ".yml")):
        p = Prompt.load(prompt)
    else:
        p = Prompt(prompt)

    if var:
        p.set_vars(**_parse_vars(var))
    if system:
        p.system = system

    if stream:
        rendered = p.render()
        provider = get_provider(model)
        console.print(f"[cyan bold]{model}[/]\n")
        for token in provider.stream(rendered, system=p.system):
            console.print(token, end="")
        console.print()
    else:
        with console.status(f"Running on {model}..."):
            result = p.run(model)

        console.print(f"\n[cyan bold]{result.model}[/] [dim]({result.latency:.2f}s, ${result.cost:.4f})[/]\n")
        console.print(result.response)


@app.command()
def compare(
    prompt: str = typer.Argument(help="Prompt text or path to a .yaml prompt file"),
    models: str = typer.Option(
        "openai/gpt-4o,anthropic/claude-sonnet-4-6",
        "--models",
        "-m",
        help="Comma-separated list of models",
    ),
    var: list[str] = typer.Option([], "--var", "-v", help="Variables as key=value"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
) -> None:
    """Compare a prompt across multiple models side-by-side."""
    from promptracer.compare import compare as do_compare
    from promptracer.prompt import Prompt

    if Path(prompt).exists() and prompt.endswith((".yaml", ".yml")):
        p = Prompt.load(prompt)
    else:
        p = Prompt(prompt)

    if var:
        p.set_vars(**_parse_vars(var))
    if system:
        p.system = system

    model_list = [m.strip() for m in models.split(",")]

    with console.status(f"Comparing across {len(model_list)} models..."):
        result = do_compare(p, model_list)

    result.print_table()


@app.command()
def eval(
    prompt: str = typer.Argument(help="Prompt text or path to a .yaml prompt file"),
    model: str = typer.Option("openai/gpt-4o", "--model", "-m", help="Model to evaluate"),
    judge: str = typer.Option("openai/gpt-4o-mini", "--judge", "-j", help="Judge model"),
    criteria: str = typer.Option(
        "accuracy, relevance, and completeness",
        "--criteria",
        "-c",
        help="Evaluation criteria",
    ),
    var: list[str] = typer.Option([], "--var", "-v", help="Variables as key=value"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
) -> None:
    """Evaluate a model's response using LLM-as-judge."""
    from promptracer.eval import evaluate
    from promptracer.prompt import Prompt

    if Path(prompt).exists() and prompt.endswith((".yaml", ".yml")):
        p = Prompt.load(prompt)
    else:
        p = Prompt(prompt)

    if var:
        p.set_vars(**_parse_vars(var))
    if system:
        p.system = system

    with console.status(f"Running on {model}..."):
        result = p.run(model)

    console.print(f"\n[cyan bold]Response from {model}:[/]\n{result.response}\n")

    with console.status(f"Evaluating with {judge}..."):
        eval_result = evaluate(result, criteria=criteria, judge=judge)

    eval_result.print()


@app.command()
def batch(
    suite: str = typer.Argument(help="Path to a test suite YAML file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Export results to JSON file"),
) -> None:
    """Run a batch test suite from a YAML file."""
    from promptracer.batch import run_suite

    with console.status("Running test suite..."):
        results = run_suite(suite)

    for batch_result in results:
        batch_result.print_table()
        console.print()

    if output:
        import json

        export = []
        for br in results:
            export.append({
                "model": br.model,
                "avg_score": br.avg_score,
                "avg_latency": round(br.avg_latency, 3),
                "total_cost": round(br.total_cost, 6),
                "cases": [
                    {
                        "name": tc.name,
                        "response": run.response,
                        "latency": round(run.latency, 3),
                        "cost": round(run.cost, 6),
                        "score": ev.score if ev else None,
                        "reasoning": ev.reasoning if ev else None,
                    }
                    for tc, run, ev in br.results
                ],
            })
        Path(output).write_text(json.dumps(export, indent=2, ensure_ascii=False))
        console.print(f"[green]Results exported to:[/] {output}")


@app.command()
def init(
    name: str = typer.Argument("my-prompt", help="Prompt name"),
    path: str = typer.Option("prompts", "--path", "-p", help="Directory for prompt files"),
) -> None:
    """Create a new prompt YAML file from a template."""
    from promptracer.prompt import Prompt

    p = Prompt(
        "You are a helpful assistant. {{task}}",
        name=name,
        metadata={"author": "", "tags": ["example"]},
    )
    p.set_vars(task="Describe what you can do")

    file_path = Path(path) / f"{name}.yaml"
    p.save(file_path)
    console.print(f"[green]Created prompt file:[/] {file_path}")


if __name__ == "__main__":
    app()
