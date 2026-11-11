"""Global LLM Rate Limiter protecting shared API limits (RPM & concurrency)."""

import asyncio
import collections
import threading
import time
from typing import Deque, Optional

from zoe.utils.logging import get_logger

logger = get_logger("zoe.llm.rate_limiter")


class GlobalLLMRateLimiter:
    """Sliding-window rate limiter and concurrency guard for LLM providers."""

    def __init__(
        self,
        max_requests_per_minute: int = 30,
        max_concurrent_requests: int = 3,
    ) -> None:
        self.max_rpm = max_requests_per_minute
        self.max_concurrent = max_concurrent_requests
        self._timestamps: Deque[float] = collections.deque()
        self._active_requests = 0
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._async_semaphore: Optional[asyncio.Semaphore] = None

    def acquire(self, timeout: float = 60.0) -> None:
        """Synchronously acquire capacity under RPM and concurrency constraints."""
        start_time = time.time()
        with self._condition:
            while True:
                now = time.time()
                # Purge timestamps older than 60 seconds
                while self._timestamps and now - self._timestamps[0] >= 60.0:
                    self._timestamps.popleft()

                # Check RPM and concurrency constraints
                if len(self._timestamps) < self.max_rpm and self._active_requests < self.max_concurrent:
                    self._timestamps.append(now)
                    self._active_requests += 1
                    return

                # Wait for capacity
                if time.time() - start_time >= timeout:
                    raise TimeoutError(f"Timed out waiting for LLM rate limit capacity after {timeout}s")

                wait_delay = 0.2
                if len(self._timestamps) >= self.max_rpm and self._timestamps:
                    oldest = self._timestamps[0]
                    wait_delay = max(0.05, min(wait_delay, (oldest + 60.0) - now))

                logger.info(
                    "LLM Rate limit reached (%d/%d RPM, %d active). Throttling for %.2fs...",
                    len(self._timestamps),
                    self.max_rpm,
                    self._active_requests,
                    wait_delay,
                )
                self._condition.wait(timeout=wait_delay)

    def release(self) -> None:
        """Release active request slot."""
        with self._condition:
            if self._active_requests > 0:
                self._active_requests -= 1
            self._condition.notify_all()

    async def acquire_async(self, timeout: float = 60.0) -> None:
        """Asynchronously acquire rate limit capacity."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.acquire, timeout)

    async def release_async(self) -> None:
        """Asynchronously release rate limit slot."""
        self.release()

    def __enter__(self) -> "GlobalLLMRateLimiter":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    async def __aenter__(self) -> "GlobalLLMRateLimiter":
        await self.acquire_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.release_async()


_GLOBAL_LIMITER: Optional[GlobalLLMRateLimiter] = None
_LIMITER_LOCK = threading.Lock()


def get_global_rate_limiter(max_rpm: int = 30, max_concurrent: int = 3) -> GlobalLLMRateLimiter:
    """Return the shared process-wide LLM rate limiter."""
    global _GLOBAL_LIMITER
    if _GLOBAL_LIMITER is None:
        with _LIMITER_LOCK:
            if _GLOBAL_LIMITER is None:
                _GLOBAL_LIMITER = GlobalLLMRateLimiter(
                    max_requests_per_minute=max_rpm,
                    max_concurrent_requests=max_concurrent,
                )
    return _GLOBAL_LIMITER

