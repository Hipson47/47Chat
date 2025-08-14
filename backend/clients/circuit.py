"""Circuit breaker implementation for fault tolerance.

Implements the circuit breaker pattern to prevent cascading failures
and provide fast failure when downstream services are unhealthy.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Protocol


class ClockProtocol(Protocol):
    """Protocol for time providers to enable testing with fake clocks."""
    
    def time(self) -> float:
        """Return current time in seconds since epoch."""
        ...


class SystemClock:
    """Real system clock implementation."""
    
    def time(self) -> float:
        return time.time()


class CircuitState(Enum):
    """Circuit breaker states."""
    
    CLOSED = 0      # Normal operation
    HALF_OPEN = 1   # Testing if service recovered
    OPEN = 2        # Failing fast


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures.
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Fast-fail mode after threshold failures, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    Transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After recovery_time_s cooldown period
    - HALF_OPEN -> CLOSED: After half_open_max_success consecutive successes
    - HALF_OPEN -> OPEN: On any failure during testing
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_time_s: int = 30,
        half_open_max_success: int = 2,
        clock: ClockProtocol | None = None,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_time_s = recovery_time_s
        self.half_open_max_success = half_open_max_success
        self.clock = clock or SystemClock()
        
        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state, updating if needed."""
        self._update_state()
        return self._state
    
    def allow_request(self) -> bool:
        """Check if request should be allowed through the circuit."""
        current_state = self.state  # This triggers state update
        
        if current_state == CircuitState.CLOSED:
            return True
        elif current_state == CircuitState.OPEN:
            return False
        else:  # HALF_OPEN
            return True
    
    def on_success(self) -> None:
        """Record successful operation."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_success:
                self._reset_to_closed()
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0
    
    def on_failure(self) -> None:
        """Record failed operation."""
        self._last_failure_time = self.clock.time()
        
        if self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
        elif self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately goes back to open
            self._state = CircuitState.OPEN
    
    def _update_state(self) -> None:
        """Update state based on current time and conditions."""
        if self._state == CircuitState.OPEN:
            time_since_failure = self.clock.time() - self._last_failure_time
            if time_since_failure >= self.recovery_time_s:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
    
    def _reset_to_closed(self) -> None:
        """Reset circuit to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
