# PromptPilot

**The open-source prompt engineering toolkit.** Test, compare, and evaluate your prompts across any LLM — from your terminal or Python code.

> Free & open-source alternative to LangSmith, PromptLayer, and Humanloop.

[![PyPI](https://img.shields.io/pypi/v/promptpilot)](https://pypi.org/project/promptpilot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Why PromptPilot?

- **One `pip install`** — no web app, no database, no account needed
- **Multi-provider** — OpenAI, Anthropic, Google Gemini, Ollama (local models)
- **Compare models side-by-side** — latency, cost, and quality in one table
- **LLM-as-judge evaluation** — automated scoring with customizable criteria
- **Version your prompts** — save as YAML, track changes with git
- **Template variables** — reusable prompts with `{{placeholders}}`
- **CLI + Python API** — use it however you want

## Install

```bash
pip install promptpilot

# With specific providers:
pip install promptpilot[openai]          # OpenAI
pip install promptpilot[anthropic]       # Anthropic (Claude)
pip install promptpilot[google]          # Google Gemini
pip install promptpilot[all]             # All providers
```

Ollama works out of the box — no extra install needed (just have Ollama running locally).

## Quick Start

### Python API

```python
from promptpilot import Prompt, compare, evaluate

# Create a prompt with template variables
p = Prompt("Translate to {{lang}}: {{text}}")
p.set_vars(lang="English", text="Hola mundo")

# Run against a single model
result = p.run("openai/gpt-4o")
print(result.response)   # "Hello world"
print(result.latency)    # 0.82
print(result.cost)       # 0.0003

# Compare across models
results = compare(p, models=[
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4-6",
    "gemini/gemini-2.5-flash",
    "ollama/llama3",
])
results.print_table()
# ┌──────────────────────────────┬──────────────┬─────────┬─────────────────┬─────────┐
# │ Model                        │ Response     │ Latency │ Tokens (in/out) │ Cost    │
# ├──────────────────────────────┼──────────────┼─────────┼─────────────────┼─────────┤
# │ openai/gpt-4o [fastest]      │ Hello world  │ 0.52s   │ 24/3            │ $0.0001 │
# │ anthropic/claude-sonnet-4-6  │ Hello world  │ 0.61s   │ 22/3            │ $0.0001 │
# │ gemini/gemini-2.5-flash      │ Hello world  │ 0.48s   │ 20/3            │ $0.0000 │
# │ ollama/llama3 [cheapest]     │ Hello world! │ 1.20s   │ 18/4            │ FREE    │
# └──────────────────────────────┴──────────────┴─────────┴─────────────────┴─────────┘

# Evaluate quality with LLM-as-judge
eval_result = evaluate(result, criteria="accuracy", judge="openai/gpt-4o-mini")
eval_result.print()
# ╭──────────── PromptPilot Eval ────────────╮
# │ Score: 9/10                            │
# │ Criteria: accuracy                     │
# │ Reasoning: Accurate translation...     │
# ╰────────────────────────────────────────╯
```

### Save & Load Prompts as YAML

```python
# Save — version control with git!
p.save("prompts/translate.yaml")

# Load
p2 = Prompt.load("prompts/translate.yaml")
```

```yaml
# prompts/translate.yaml
template: "Translate to {{lang}}: {{text}}"
name: translate
system: You are a professional translator
vars:
  lang: English
  text: Hola mundo
```

### Prompt Versioning

```python
p = Prompt("Translate: {{text}}")
p.update("Translate accurately: {{text}}")
p.update("Translate accurately and naturally: {{text}}")

# View history
p.history()  # [{'version': 1, ...}, {'version': 2, ...}, {'version': 3, ...}]

# Compare versions
old, new = p.diff(1, 3)
```

### CLI

```bash
# Set your API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=AI...

# Run a prompt
promptpilot run "What is Python?" -m openai/gpt-4o

# Compare models
promptpilot compare "Explain quantum computing" \
  -m "openai/gpt-4o,anthropic/claude-sonnet-4-6,ollama/llama3"

# With template variables
promptpilot compare "Translate to {{lang}}: {{text}}" \
  -v lang=French -v text="Good morning" \
  -m "openai/gpt-4o,gemini/gemini-2.5-flash"

# Evaluate a response
promptpilot eval "Write a haiku about coding" \
  -m openai/gpt-4o \
  -j openai/gpt-4o-mini \
  -c "creativity and adherence to haiku format"

# Create a prompt template
promptpilot init my-prompt
```

### Async Support

```python
import asyncio
from promptpilot import Prompt
from promptpilot.compare import acompare

async def main():
    p = Prompt("Explain {{topic}} simply")
    p.set_vars(topic="quantum computing")

    # All models run concurrently
    results = await acompare(p, models=[
        "openai/gpt-4o",
        "anthropic/claude-sonnet-4-6",
        "ollama/llama3",
    ])
    results.print_table()

asyncio.run(main())
```

## Supported Models

| Provider | Prefix | Example | API Key |
|----------|--------|---------|---------|
| OpenAI | `openai/` | `openai/gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/` | `anthropic/claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini/` or `google/` | `gemini/gemini-2.5-flash` | `GEMINI_API_KEY` |
| Ollama | `ollama/` | `ollama/llama3` | None (local) |

## Contributing

Contributions are welcome! Please open an issue or submit a PR.

```bash
# Dev setup
git clone https://github.com/Unlucko/promptpilot.git
cd promptpilot
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

## License

MIT License — use it however you want.
