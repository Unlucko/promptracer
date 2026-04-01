"""Tests for optimizer module."""

from promptracer.optimizer import OptimizeResult, OptimizeIteration


def test_optimize_result_best():
    result = OptimizeResult(
        original="test",
        iterations=[
            OptimizeIteration(version=1, prompt_text="v1", response="r", score=5.0, reasoning="ok"),
            OptimizeIteration(version=2, prompt_text="v2", response="r", score=8.0, reasoning="good"),
            OptimizeIteration(version=3, prompt_text="v3", response="r", score=7.0, reasoning="ok"),
        ],
    )
    assert result.best.version == 2
    assert result.best.score == 8.0


def test_optimize_result_improvement():
    result = OptimizeResult(
        original="test",
        iterations=[
            OptimizeIteration(version=1, prompt_text="v1", response="r", score=4.0, reasoning="bad"),
            OptimizeIteration(version=2, prompt_text="v2", response="r", score=8.0, reasoning="good"),
        ],
    )
    assert result.improvement == 4.0


def test_optimize_result_no_improvement():
    result = OptimizeResult(
        original="test",
        iterations=[
            OptimizeIteration(version=1, prompt_text="v1", response="r", score=7.0, reasoning="ok"),
        ],
    )
    assert result.improvement == 0.0


def test_optimize_result_print(capsys):
    """Just ensure print doesn't crash."""
    result = OptimizeResult(
        original="test",
        iterations=[
            OptimizeIteration(version=1, prompt_text="v1", response="r", score=6.0, reasoning="ok"),
            OptimizeIteration(version=2, prompt_text="v2", response="r", score=8.5, reasoning="great"),
        ],
    )
    result.print()
