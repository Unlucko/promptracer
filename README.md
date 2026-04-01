# PromptRacer

**The open-source prompt engineering toolkit.** Test, compare, and evaluate your prompts across any LLM — from your terminal or Python code.

> Free & open-source alternative to LangSmith, PromptLayer, and Humanloop.

[![PyPI](https://img.shields.io/pypi/v/promptracer)](https://pypi.org/project/promptracer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Why PromptRacer?

- **One `pip install`** — no web app, no database, no account needed
- **Multi-provider** — OpenAI, Anthropic, Google Gemini, Ollama (local models)
- **Compare models side-by-side** — latency, cost, and quality in one table
- **LLM-as-judge evaluation** — automated scoring with customizable criteria
- **Version your prompts** — save as YAML, track changes with git
- **Template variables** — reusable prompts with `{{placeholders}}`
- **Batch test suites** — define test cases in YAML, run them all at once
- **Streaming** — real-time token streaming in the CLI
- **Export** — save results to JSON or CSV
- **Prompt chains** — pipe output between models: summarize → translate → polish
- **Auto-optimizer** — LLM iteratively improves your prompts
- **Interactive playground** — REPL for live testing
- **Model leaderboard** — rank models by score across test suites
- **Cost tracking** — automatic spend logging with daily/weekly/monthly reports
- **Dataset loading** — scale testing with CSV/JSON inputs
- **Custom providers** — register any LLM API (Groq, Together, Azure, etc.)
- **Retry & rate limiting** — built-in resilience for production use
- **CLI + Python API** — use it however you want

## Install

```bash
pip install promptracer

# With specific providers:
pip install promptracer[openai]          # OpenAI
pip install promptracer[anthropic]       # Anthropic (Claude)
pip install promptracer[google]          # Google Gemini
pip install promptracer[all]             # All providers
```

Ollama works out of the box — no extra install needed (just have Ollama running locally).

## Quick Start

### Python API

```python
from promptracer import Prompt, compare, evaluate

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
# ╭──────────── PromptRacer Eval ────────────╮
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
promptracer run "What is Python?" -m openai/gpt-4o

# Compare models
promptracer compare "Explain quantum computing" \
  -m "openai/gpt-4o,anthropic/claude-sonnet-4-6,ollama/llama3"

# With template variables
promptracer compare "Translate to {{lang}}: {{text}}" \
  -v lang=French -v text="Good morning" \
  -m "openai/gpt-4o,gemini/gemini-2.5-flash"

# Evaluate a response
promptracer eval "Write a haiku about coding" \
  -m openai/gpt-4o \
  -j openai/gpt-4o-mini \
  -c "creativity and adherence to haiku format"

# Create a prompt template
promptracer init my-prompt
```

### Batch Test Suites

Define test cases in YAML and race models against each other:

```yaml
# suites/translation.yaml
template: "Translate to {{lang}}: {{text}}"
system: "You are a professional translator"
models:
  - openai/gpt-4o
  - anthropic/claude-sonnet-4-6
  - ollama/llama3
judge: openai/gpt-4o-mini
criteria: "accuracy and natural fluency"
cases:
  - name: "Spanish → English"
    vars: { lang: English, text: "Hola, ¿cómo estás?" }
    expected: "Hello, how are you?"
  - name: "Technical jargon"
    vars: { lang: English, text: "El algoritmo converge rápidamente" }
```

```python
from promptracer import run_suite

results = run_suite("suites/translation.yaml")
for batch in results:
    batch.print_table()
```

```bash
# From CLI
promptracer batch suites/translation.yaml
promptracer batch suites/translation.yaml -o results.json
```

### Streaming

```bash
promptracer run "Write a poem about AI" -m openai/gpt-4o --stream
```

### Export Results

```python
results = compare(p, models=["openai/gpt-4o", "ollama/llama3"])
results.to_json("results.json")
results.to_csv("results.csv")
```

### Prompt Chains

Pipe the output of one prompt into the next — across different models:

```python
from promptracer import Chain

result = (
    Chain()
    .step("Summarize this article: {{input}}", model="openai/gpt-4o")
    .step("Translate to Spanish: {{output}}", model="anthropic/claude-sonnet-4-6")
    .step("Make it sound poetic: {{output}}", model="ollama/llama3")
    .run(input="Long article text here...")
)

result.print()           # Shows each step with latency/cost
print(result.final_response)
print(result.total_cost)  # Total across all steps
```

### Model Leaderboard

Race models and rank them by score:

```bash
promptracer leaderboard suites/translation.yaml
# ┌──────┬──────────────────────────────┬───────────┬───────────┬─────────────┬────────────┐
# │ Rank │ Model                        │ Avg Score │ Pass Rate │ Avg Latency │ Total Cost │
# ├──────┼──────────────────────────────┼───────────┼───────────┼─────────────┼────────────┤
# │ 1st  │ openai/gpt-4o               │ 9.2/10    │ 100%      │ 0.85s       │ $0.0032    │
# │ 2nd  │ anthropic/claude-sonnet-4-6  │ 8.8/10    │ 100%      │ 0.92s       │ $0.0028    │
# │ 3rd  │ ollama/llama3               │ 7.1/10    │ 75%       │ 2.10s       │ FREE       │
# └──────┴──────────────────────────────┴───────────┴───────────┴─────────────┴────────────┘
```

### Cost Tracking

Every run is automatically logged. Check your spending anytime:

```bash
promptracer cost           # All time
promptracer cost today     # Last 24h
promptracer cost week      # Last 7 days
promptracer cost month     # Last 30 days
promptracer cost --clear   # Reset history
```

### Project Config

Create a `.promptracer.yaml` in your project root:

```yaml
default_model: openai/gpt-4o
default_judge: openai/gpt-4o-mini
models:
  - openai/gpt-4o
  - anthropic/claude-sonnet-4-6
  - ollama/llama3
criteria: "accuracy, relevance, and completeness"
track_costs: true
```

### Async Support

```python
import asyncio
from promptracer import Prompt
from promptracer.compare import acompare

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

### Interactive Playground

Launch an interactive REPL to test prompts live:

```bash
promptracer play
promptracer play -m ollama/llama3 -s "You are a pirate"
```

Inside the playground:
```
>>> What is the meaning of life?
>>> /model anthropic/claude-sonnet-4-6
>>> /stream
>>> /compare openai/gpt-4o,ollama/llama3
>>> /cost
>>> /quit
```

### Prompt Optimization

Let an LLM iteratively improve your prompts:

```bash
promptracer optimize "Translate: {{text}}" -v text="Hola mundo" -n 3
# ┌─────────┬───────┬──────────────────────────────────────────────────────┐
# │ Version │ Score │ Prompt Preview                                       │
# ├─────────┼───────┼──────────────────────────────────────────────────────┤
# │ v1      │ 6/10  │ Translate: {{text}}                                  │
# │ v2      │ 8/10  │ Translate the following text accurately: {{text}}    │
# │ v3      │ 9/10  │ Provide a natural, accurate English translation...   │
# └─────────┴───────┴──────────────────────────────────────────────────────┘
```

```python
from promptracer.optimizer import optimize
from promptracer import Prompt

p = Prompt("Summarize: {{text}}")
p.set_vars(text="Long article...")
result = optimize(p, model="openai/gpt-4o", iterations=3)
print(result.best.prompt_text)  # Optimized prompt
```

### Load Test Cases from CSV/JSON

Scale your testing with dataset files:

```python
from promptracer import Prompt, load_cases
from promptracer.batch import run_batch

cases = load_cases("test-cases.csv")  # or .json
result = run_batch("Translate to {{lang}}: {{text}}", cases, model="openai/gpt-4o")
result.print_table()
```

```csv
name,lang,text,expected
Spanish,English,Hola mundo,Hello world
French,English,Bonjour,Hello
```

### Custom Providers

Register your own LLM provider (Azure, Groq, Together, etc.):

```python
from promptracer.providers import register_provider, Provider
from promptracer.prompt import RunResult

class GroqProvider(Provider):
    def complete(self, prompt, *, system=None, **kwargs):
        # Your implementation here
        return RunResult(model=f"groq/{self.model}", ...)

    async def acomplete(self, prompt, *, system=None, **kwargs):
        return self.complete(prompt, system=system, **kwargs)

register_provider("groq", GroqProvider)

# Now use it everywhere
from promptracer import Prompt
result = Prompt("Hello").run("groq/llama-3-70b")
```

## Supported Models

| Provider | Prefix | Example | API Key |
|----------|--------|---------|---------|
| OpenAI | `openai/` | `openai/gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/` | `anthropic/claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini/` or `google/` | `gemini/gemini-2.5-flash` | `GEMINI_API_KEY` |
| Ollama | `ollama/` | `ollama/llama3` | None (local) |
| Custom | any | `groq/llama-3-70b` | You define |

## Contributing

Contributions are welcome! Please open an issue or submit a PR.

```bash
# Dev setup
git clone https://github.com/Unlucko/promptracer.git
cd promptracer
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

## License

MIT License — use it however you want.
