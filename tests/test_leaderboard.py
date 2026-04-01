"""Tests for leaderboard module."""

from promptracer.batch import BatchResult, Case
from promptracer.eval import EvalResult
from promptracer.leaderboard import build_leaderboard
from promptracer.prompt import RunResult


def _make_batch(model: str, scores: list[float]) -> BatchResult:
    br = BatchResult(model=model)
    for i, score in enumerate(scores):
        tc = Case(name=f"case-{i}", vars={"x": str(i)})
        run = RunResult(
            model=model, response="r", latency=1.0,
            input_tokens=10, output_tokens=5, cost=0.01, prompt_text="t"
        )
        ev = EvalResult(
            score=score, reasoning="ok", criteria="accuracy",
            judge_model="j", evaluated_model=model
        )
        br.results.append((tc, run, ev))
    return br


def test_leaderboard_ranking():
    batches = [
        _make_batch("model-a", [6.0, 7.0, 5.0]),  # avg 6.0
        _make_batch("model-b", [9.0, 8.0, 10.0]),  # avg 9.0
        _make_batch("model-c", [7.0, 7.0, 7.0]),  # avg 7.0
    ]
    lb = build_leaderboard(batches)
    assert lb.models[0].model == "model-b"
    assert lb.models[1].model == "model-c"
    assert lb.models[2].model == "model-a"


def test_leaderboard_pass_rate():
    batches = [_make_batch("m", [9.0, 3.0, 7.0, 5.0])]  # 2/4 >= 7
    lb = build_leaderboard(batches)
    assert lb.models[0].pass_rate == 50.0


def test_leaderboard_print(capsys):
    """Just ensure print doesn't crash."""
    batches = [_make_batch("m", [8.0, 9.0])]
    lb = build_leaderboard(batches)
    lb.print_table()
