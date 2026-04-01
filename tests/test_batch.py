"""Tests for batch module."""

import tempfile

from promptracer.batch import Case, BatchResult, SuiteConfig
from promptracer.prompt import RunResult


def _make_result(model: str, latency: float, cost: float) -> RunResult:
    return RunResult(
        model=model,
        response="test response",
        latency=latency,
        input_tokens=100,
        output_tokens=50,
        cost=cost,
        prompt_text="test",
    )


def test_batch_result_avg_score():
    from promptracer.eval import EvalResult

    br = BatchResult(model="test")
    tc = Case(name="t1", vars={"x": "1"})
    ev = EvalResult(score=8.0, reasoning="good", criteria="accuracy", judge_model="j", evaluated_model="m")
    br.results.append((tc, _make_result("m", 1.0, 0.01), ev))

    tc2 = Case(name="t2", vars={"x": "2"})
    ev2 = EvalResult(score=6.0, reasoning="ok", criteria="accuracy", judge_model="j", evaluated_model="m")
    br.results.append((tc2, _make_result("m", 2.0, 0.02), ev2))

    assert br.avg_score == 7.0
    assert br.avg_latency == 1.5
    assert br.total_cost == 0.03


def test_batch_result_no_eval():
    br = BatchResult(model="test")
    tc = Case(name="t1", vars={"x": "1"})
    br.results.append((tc, _make_result("m", 1.0, 0.01), None))
    assert br.avg_score is None


def test_suite_config_load():
    suite_yaml = """\
template: "Translate to {{lang}}: {{text}}"
system: "You are a translator"
models:
  - openai/gpt-4o
  - ollama/llama3
judge: openai/gpt-4o-mini
criteria: "accuracy"
cases:
  - name: "Spanish"
    vars:
      lang: English
      text: "Hola"
    expected: "Hello"
  - name: "French"
    vars:
      lang: English
      text: "Bonjour"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(suite_yaml)
        f.flush()

        config = SuiteConfig.load(f.name)

    assert config.template == "Translate to {{lang}}: {{text}}"
    assert config.system == "You are a translator"
    assert len(config.models) == 2
    assert config.judge == "openai/gpt-4o-mini"
    assert len(config.cases) == 2
    assert config.cases[0].name == "Spanish"
    assert config.cases[0].expected == "Hello"
    assert config.cases[1].vars["text"] == "Bonjour"


def test_batch_result_print_table(capsys):
    """Just ensure print_table doesn't crash."""
    br = BatchResult(model="test/model")
    tc = Case(name="t1", vars={"x": "1"})
    br.results.append((tc, _make_result("test/model", 1.0, 0.0), None))
    br.print_table()
