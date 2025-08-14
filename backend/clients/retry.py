"""Async retry policy implementation with exponential backoff and jitter.

Provides a reusable retry mechanism for handling transient failures in
distributed systems with configurable backoff and timeout strategies.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Configuration for retry behavior with exponential backoff and jitter."""
    
    max_retries: int = 3
    base_backoff_ms: int = 200
    max_backoff_ms: int = 5000
    jitter_ms: int = 100
    timeout_s: float = 30.0
    retry_on: tuple[type[Exception], ...] = (
        asyncio.TimeoutError,
        ConnectionError,
        OSError,
    )


async def with_retries(
    coro_factory: Callable[[], Awaitable[T]], 
    policy: RetryPolicy
) -> T:
    """Execute coroutine with retry policy and per-attempt timeout.
    
    Args:
        coro_factory: Factory function that creates a fresh coroutine for each attempt
        policy: Retry configuration
        
    Returns:
        Result from successful coroutine execution
        
    Raises:
        The last exception encountered after all retries are exhausted
    """
    last_exception: Exception | None = None
    
    for attempt in range(policy.max_retries + 1):  # +1 for initial attempt
        try:
            # Create fresh coroutine for this attempt
            coro = coro_factory()
            # Apply per-attempt timeout
            result = await asyncio.wait_for(coro, timeout=policy.timeout_s)
            return result
            
        except Exception as e:
            last_exception = e
            
            # Don't retry on non-retryable exceptions
            if not isinstance(e, policy.retry_on):
                raise
                
            # Don't sleep after the last attempt
            if attempt == policy.max_retries:
                break
                
            # Calculate exponential backoff with jitter
            backoff_ms = min(
                policy.base_backoff_ms * (2 ** attempt),
                policy.max_backoff_ms
            )
            jitter = random.randint(-policy.jitter_ms, policy.jitter_ms)
            sleep_ms = max(0, backoff_ms + jitter)
            
            await asyncio.sleep(sleep_ms / 1000.0)
    
    # All retries exhausted, raise the last exception
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError("Retry loop completed without result or exception")
