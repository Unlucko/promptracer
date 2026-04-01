"""Tests for eval module parsing."""

from promptpilot.eval import _parse_eval_response


def test_parse_score_and_reasoning():
    response = "SCORE: 8\nREASONING: Great response with good detail."
    score, reasoning = _parse_eval_response(response)
    assert score == 8.0
    assert "Great response" in reasoning


def test_parse_score_with_slash():
    response = "SCORE: 7/10\nREASONING: Pretty good."
    score, reasoning = _parse_eval_response(response)
    assert score == 7.0


def test_parse_clamps_score():
    response = "SCORE: 15\nREASONING: Off the charts."
    score, _ = _parse_eval_response(response)
    assert score == 10.0

    response2 = "SCORE: -3\nREASONING: Terrible."
    score2, _ = _parse_eval_response(response2)
    assert score2 == 0.0


def test_parse_fallback():
    response = "This is just free text without a score."
    score, reasoning = _parse_eval_response(response)
    assert score == 5.0  # default
    assert reasoning == response
