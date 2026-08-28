"""Production hardening tests for the Universal Multi-Agent Builder."""

from __future__ import annotations

import platform
import time

import pytest

from multi_agent_builder.hardening import (
    RateLimiter,
    TokenBudget,
    validate_windows_termux,
    with_retry,
)


class FakeRateLimitedTask:
    def __init__(self, rate: float = 1.0, burst: int = 1) -> None:
        self.limiter = RateLimiter(rate=rate, burst=burst)
        self.calls = 0

    def __call__(self, goal: str, context: str | None = None, role: str | None = None) -> str:
        if not self.limiter.acquire():
            raise RuntimeError("rate limited")
        self.calls += 1
        return '{"ok": true}'


class FakeFailingTask:
    def __init__(self, fail_times: int = 2) -> None:
        self.fail_times = fail_times
        self.calls = 0

    @with_retry(max_attempts=3, backoff_factor=0.01, exceptions=(RuntimeError,))
    def __call__(self, goal: str, context: str | None = None, role: str | None = None) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient failure")
        return '{"ok": true}'


def test_rate_limiter_allows_within_burst() -> None:
    limiter = RateLimiter(rate=1.0, burst=2)
    assert limiter.acquire() is True
    assert limiter.acquire() is True
    assert limiter.acquire() is False


def test_rate_limiter_refills_over_time() -> None:
    limiter = RateLimiter(rate=10.0, burst=1)
    assert limiter.acquire() is True
    assert limiter.acquire() is False
    time.sleep(0.2)
    assert limiter.acquire() is True


def test_token_budget_blocks_when_exhausted() -> None:
    budget = TokenBudget(limit=10)
    assert budget.consume(5) is True
    assert budget.remaining() == 5
    assert budget.consume(6) is False
    assert budget.remaining() == 5


def test_with_retry_retries_then_succeeds() -> None:
    task = FakeFailingTask(fail_times=2)
    result = task("test")
    assert result == '{"ok": true}'
    assert task.calls == 3


def test_validate_windows_termux_reports_platform() -> None:
    result = validate_windows_termux()
    assert "platform" in result
    assert "supported" in result
    assert result["supported"] is True


def test_validate_windows_termux_detects_termux() -> None:
    result = validate_windows_termux()
    if platform.system() == "Linux" and __import__("os").path.exists("/data/data/com.termux"):
        assert result["platform"] == "Termux"
