"""Tests for compare module (unit tests with mocked providers)."""

from promptlab.compare import CompareResult
from promptlab.prompt import RunResult


def _make_result(model: str, latency: float, cost: float) -> RunResult:
    return RunResult(
        model=model,
        response=f"Response from {model}",
        latency=latency,
        input_tokens=100,
        output_tokens=50,
        cost=cost,
        prompt_text="test prompt",
    )


def test_compare_result_fastest():
    cr = CompareResult(
        results=[
            _make_result("a", 2.0, 0.01),
            _make_result("b", 0.5, 0.02),
            _make_result("c", 1.0, 0.015),
        ]
    )
    assert cr.fastest.model == "b"


def test_compare_result_cheapest():
    cr = CompareResult(
        results=[
            _make_result("a", 2.0, 0.01),
            _make_result("b", 0.5, 0.02),
            _make_result("c", 1.0, 0.0),
        ]
    )
    assert cr.cheapest.model == "c"


def test_compare_result_to_dict():
    cr = CompareResult(results=[_make_result("a", 1.0, 0.01)])
    d = cr.to_dict()
    assert len(d) == 1
    assert d[0]["model"] == "a"
    assert d[0]["latency"] == 1.0


def test_compare_result_print_table(capsys):
    """Just ensure print_table doesn't crash."""
    cr = CompareResult(
        results=[
            _make_result("openai/gpt-4o", 1.0, 0.01),
            _make_result("ollama/llama3", 2.0, 0.0),
        ]
    )
    cr.print_table()
