"""Retry, timeout, and rate limiting utilities."""

from __future__ import annotations

import time
import functools
from typing import Any, Callable, TypeVar

from rich.console import Console

T = TypeVar("T")

console = Console(stderr=True)


def retry(
    max_retries: int = 3,
    backoff_base: float = 1.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator that retries a function with exponential backoff.

    Usage:
        @retry(max_retries=3)
        def my_function():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait = backoff_base * (2**attempt)
                        console.print(
                            f"[yellow]Retry {attempt + 1}/{max_retries} "
                            f"after {wait:.1f}s: {e}[/yellow]"
                        )
                        time.sleep(wait)
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


class RateLimiter:
    """Simple token-bucket rate limiter.

    Usage:
        limiter = RateLimiter(requests_per_minute=60)
        limiter.wait()  # blocks if needed
        # ... make request
    """

    def __init__(self, requests_per_minute: int = 60):
        self.min_interval = 60.0 / requests_per_minute
        self._last_request: float = 0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()
