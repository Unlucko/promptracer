"""Tests for cost tracker."""

from unittest.mock import patch

from promptracer.prompt import RunResult
from promptracer import tracker


def test_log_and_load(tmp_path):
    log_file = tmp_path / "usage.jsonl"
    with patch.object(tracker, "_LOG_FILE", log_file), patch.object(tracker, "_DEFAULT_DIR", tmp_path):
        result = RunResult(
            model="openai/gpt-4o",
            response="hi",
            latency=0.5,
            input_tokens=100,
            output_tokens=50,
            cost=0.003,
            prompt_text="test",
        )
        tracker.log_run(result)
        tracker.log_run(result)

        entries = tracker._load_entries()
        assert len(entries) == 2
        assert entries[0]["model"] == "openai/gpt-4o"
        assert entries[0]["cost"] == 0.003


def test_aggregate(tmp_path):
    log_file = tmp_path / "usage.jsonl"
    with patch.object(tracker, "_LOG_FILE", log_file), patch.object(tracker, "_DEFAULT_DIR", tmp_path):
        for model, cost in [("a", 0.01), ("a", 0.02), ("b", 0.05)]:
            result = RunResult(
                model=model, response="r", latency=1.0,
                input_tokens=10, output_tokens=5, cost=cost, prompt_text="t"
            )
            tracker.log_run(result)

        entries = tracker._load_entries()
        agg = tracker._aggregate(entries)
        assert agg["a"]["requests"] == 2
        assert abs(agg["a"]["cost"] - 0.03) < 0.001
        assert agg["b"]["requests"] == 1


def test_clear_log(tmp_path):
    log_file = tmp_path / "usage.jsonl"
    log_file.write_text('{"test": 1}\n')
    with patch.object(tracker, "_LOG_FILE", log_file):
        tracker.clear_log()
        assert not log_file.exists()
