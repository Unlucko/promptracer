"""Tests for resilience module."""

import time

from promptracer.resilience import retry, RateLimiter


def test_retry_succeeds_first_try():
    call_count = 0

    @retry(max_retries=3)
    def succeed():
        nonlocal call_count
        call_count += 1
        return "ok"

    assert succeed() == "ok"
    assert call_count == 1


def test_retry_succeeds_after_failures():
    call_count = 0

    @retry(max_retries=3, backoff_base=0.01)
    def fail_twice():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("not yet")
        return "ok"

    assert fail_twice() == "ok"
    assert call_count == 3


def test_retry_exhausts_retries():
    @retry(max_retries=2, backoff_base=0.01)
    def always_fail():
        raise ValueError("nope")

    try:
        always_fail()
        assert False, "Should have raised"
    except ValueError:
        pass


def test_rate_limiter():
    limiter = RateLimiter(requests_per_minute=6000)  # 100/sec = 10ms interval
    limiter.wait()
    start = time.monotonic()
    limiter.wait()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.005  # at least some delay


def test_export_json(tmp_path):
    from promptracer.compare import CompareResult
    from promptracer.prompt import RunResult

    cr = CompareResult(results=[
        RunResult(model="a", response="hi", latency=1.0, input_tokens=10, output_tokens=5, cost=0.001, prompt_text="x"),
    ])
    path = str(tmp_path / "out.json")
    cr.to_json(path)
    import json
    data = json.loads(open(path).read())
    assert len(data) == 1
    assert data[0]["model"] == "a"


def test_export_csv(tmp_path):
    from promptracer.compare import CompareResult
    from promptracer.prompt import RunResult

    cr = CompareResult(results=[
        RunResult(model="a", response="hi", latency=1.0, input_tokens=10, output_tokens=5, cost=0.001, prompt_text="x"),
    ])
    path = str(tmp_path / "out.csv")
    cr.to_csv(path)
    content = open(path).read()
    assert "model" in content
    assert "a" in content
