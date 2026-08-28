"""Production hardening utilities for the Universal Multi-Agent Builder.

This module adds:
- Retry with backoff for transient failures
- Rate limiting for delegate_task calls
- Token budget tracking
- Windows/Termux environment validation
"""

from __future__ import annotations

import os
import platform
import time
from typing import Any, Callable, Dict, Optional, Tuple


class RateLimiter:
    """Simple token-bucket style rate limiter for delegate_task calls."""

    def __init__(self, rate: float = 1.0, burst: int = 1) -> None:
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()

    def acquire(self, cost: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


class TokenBudget:
    """Tracks token usage across pipeline stages."""

    def __init__(self, limit: int = 100_000) -> None:
        self.limit = limit
        self.used = 0

    def consume(self, tokens: int) -> bool:
        if self.used + tokens > self.limit:
            return False
        self.used += tokens
        return True

    def remaining(self) -> int:
        return max(0, self.limit - self.used)


def with_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory for retry with exponential backoff."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[BaseException] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    sleep_time = backoff_factor ** (attempt - 1)
                    time.sleep(sleep_time)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


def validate_windows_termux() -> Dict[str, Any]:
    """Validate platform-specific requirements for Windows and Termux."""
    system = platform.system()
    result: Dict[str, Any] = {
        "platform": system,
        "supported": system in {"Windows", "Linux", "Darwin"},
        "warnings": [],
        "errors": [],
    }

    if system == "Windows":
        result["warnings"].append("Native Windows detected; use PowerShell or Git Bash.")
    elif system == "Linux":
        if os.path.exists("/data/data/com.termux"):
            result["platform"] = "Termux"
            result["supported"] = True
            result["warnings"].append("Termux detected; ensure termux-api and python installed.")

    return result
