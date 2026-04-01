"""Interactive REPL playground for testing prompts."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt as RichPrompt

from promptracer.prompt import Prompt
from promptracer.providers import get_provider

console = Console()

HELP_TEXT = """
[bold cyan]PromptRacer Playground[/bold cyan]

Commands:
  [green]/model <provider/model>[/green]  — Switch model (e.g. /model ollama/llama3)
  [green]/system <text>[/green]           — Set system prompt
  [green]/vars <key=val ...>[/green]      — Set template variables
  [green]/stream[/green]                  — Toggle streaming on/off
  [green]/compare <models>[/green]        — Compare last prompt across models (comma-separated)
  [green]/history[/green]                 — Show prompt history
  [green]/cost[/green]                    — Show cost for this session
  [green]/help[/green]                    — Show this help
  [green]/quit[/green]                    — Exit

Type any text to send it as a prompt.
"""


def playground(model: str = "openai/gpt-4o", system: str | None = None) -> None:
    """Start an interactive REPL session."""
    current_model = model
    current_system = system
    streaming = False
    session_cost = 0.0
    session_tokens = 0
    history: list[tuple[str, str, str]] = []  # (prompt, model, response)
    template_vars: dict[str, str] = {}

    console.print(HELP_TEXT)
    console.print(f"[dim]Model: {current_model} | Streaming: {'on' if streaming else 'off'}[/dim]\n")

    while True:
        try:
            user_input = RichPrompt.ask("[bold green]>>>[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        # Handle commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/quit" or cmd == "/exit" or cmd == "/q":
                console.print("[dim]Goodbye![/dim]")
                break
            elif cmd == "/help":
                console.print(HELP_TEXT)
            elif cmd == "/model":
                if arg:
                    current_model = arg.strip()
                    console.print(f"[cyan]Model set to: {current_model}[/cyan]")
                else:
                    console.print(f"[cyan]Current model: {current_model}[/cyan]")
            elif cmd == "/system":
                current_system = arg.strip() if arg else None
                if current_system:
                    console.print(f"[cyan]System prompt set: {current_system[:60]}...[/cyan]")
                else:
                    console.print("[cyan]System prompt cleared[/cyan]")
            elif cmd == "/stream":
                streaming = not streaming
                console.print(f"[cyan]Streaming: {'on' if streaming else 'off'}[/cyan]")
            elif cmd == "/vars":
                if arg:
                    for pair in arg.split():
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            template_vars[k.strip()] = v.strip()
                    console.print(f"[cyan]Variables: {template_vars}[/cyan]")
                else:
                    console.print(f"[cyan]Variables: {template_vars}[/cyan]")
            elif cmd == "/compare":
                if not history:
                    console.print("[yellow]No prompt history yet. Send a prompt first.[/yellow]")
                    continue
                models = [m.strip() for m in arg.split(",")] if arg else [current_model]
                last_prompt = history[-1][0]
                from promptracer.compare import compare
                p = Prompt(last_prompt, system=current_system)
                if template_vars:
                    p.set_vars(**template_vars)
                with console.status("Comparing..."):
                    result = compare(p, models)
                result.print_table()
            elif cmd == "/history":
                if not history:
                    console.print("[dim]No history yet.[/dim]")
                else:
                    for i, (prompt_text, m, resp) in enumerate(history[-10:], 1):
                        preview = resp[:60] + "..." if len(resp) > 60 else resp
                        console.print(f"[dim]{i}.[/dim] [{m}] {prompt_text[:40]}... → {preview}")
            elif cmd == "/cost":
                console.print(f"[cyan]Session: {session_tokens} tokens, ${session_cost:.4f}[/cyan]")
            else:
                console.print(f"[yellow]Unknown command: {cmd}. Type /help[/yellow]")
            continue

        # Run prompt
        try:
            p = Prompt(user_input, system=current_system)
            if template_vars:
                p.set_vars(**template_vars)

            if streaming:
                rendered = p.render()
                provider = get_provider(current_model)
                console.print(f"\n[cyan]{current_model}[/cyan]")
                full_response = ""
                for token in provider.stream(rendered, system=current_system):
                    console.print(token, end="")
                    full_response += token
                console.print("\n")
                history.append((user_input, current_model, full_response))
            else:
                with console.status(f"Running on {current_model}..."):
                    result = p.run(current_model)

                console.print(
                    f"\n[cyan]{result.model}[/cyan] "
                    f"[dim]({result.latency:.2f}s, "
                    f"{result.input_tokens}+{result.output_tokens} tokens, "
                    f"${result.cost:.4f})[/dim]\n"
                )
                console.print(result.response)
                console.print()
                session_cost += result.cost
                session_tokens += result.input_tokens + result.output_tokens
                history.append((user_input, current_model, result.response))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
