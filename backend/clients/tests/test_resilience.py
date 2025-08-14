"""Tests for resilience layer: retries, circuit breaker, and metrics.

Tests use fake clocks and mock clients to ensure fast execution
and deterministic behavior.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch
from typing import Awaitable, Callable

from ..retry import RetryPolicy, with_retries
from ..circuit import CircuitBreaker, CircuitState
from .. import metrics


class FakeClock:
    """Fake clock for testing time-dependent behavior."""
    
    def __init__(self, start_time: float = 0.0):
        self._time = start_time
    
    def time(self) -> float:
        return self._time
    
    def advance(self, seconds: float) -> None:
        self._time += seconds


class FailingClient:
    """Mock client that fails N times then succeeds."""
    
    def __init__(self, fail_count: int, exception: Exception = ConnectionError("Mock failure")):
        self.fail_count = fail_count
        self.exception = exception
        self.call_count = 0
    
    async def call(self) -> str:
        self.call_count += 1
        if self.call_count <= self.fail_count:
            raise self.exception
        return f"Success after {self.call_count} calls"


class TestRetryPolicy:
    """Test retry mechanism with exponential backoff and jitter."""
    
    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test that successful calls don't retry."""
        async def success_coro() -> str:
            return "success"
        
        policy = RetryPolicy(max_retries=3)
        result = await with_retries(success_coro, policy)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that failures are retried up to max_retries."""
        client = FailingClient(fail_count=2)
        policy = RetryPolicy(max_retries=3, base_backoff_ms=1, jitter_ms=0)  # Fast test
        
        result = await with_retries(client.call, policy)
        
        assert result == "Success after 3 calls"
        assert client.call_count == 3
    
    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        """Test that exception is raised when retries are exhausted."""
        client = FailingClient(fail_count=5)
        policy = RetryPolicy(max_retries=3, base_backoff_ms=1, jitter_ms=0)
        
        with pytest.raises(ConnectionError, match="Mock failure"):
            await with_retries(client.call, policy)
        
        assert client.call_count == 4  # Initial + 3 retries
    
    @pytest.mark.asyncio
    async def test_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried."""
        async def fail_fast() -> str:
            raise ValueError("Not retryable")
        
        policy = RetryPolicy(max_retries=3, retry_on=(ConnectionError,))
        
        with pytest.raises(ValueError, match="Not retryable"):
            await with_retries(fail_fast, policy)
    
    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test that per-attempt timeout works."""
        async def slow_coro() -> str:
            await asyncio.sleep(0.1)  # Longer than timeout
            return "too slow"
        
        policy = RetryPolicy(max_retries=1, timeout_s=0.01)
        
        with pytest.raises(asyncio.TimeoutError):
            await with_retries(slow_coro, policy)


class TestCircuitBreaker:
    """Test circuit breaker state transitions and behavior."""
    
    def test_initial_state(self):
        """Test that circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True
    
    def test_open_on_threshold(self):
        """Test transition to OPEN state after failure threshold."""
        cb = CircuitBreaker("test", failure_threshold=3)
        
        # Should remain closed until threshold
        for _ in range(2):
            cb.on_failure()
            assert cb.state == CircuitState.CLOSED
            assert cb.allow_request() is True
        
        # Third failure should open circuit
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False
    
    def test_half_open_after_cooldown(self):
        """Test transition to HALF_OPEN after recovery time."""
        fake_clock = FakeClock()
        cb = CircuitBreaker("test", failure_threshold=1, recovery_time_s=30, clock=fake_clock)
        
        # Trigger open state
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        
        # Should remain open before cooldown
        fake_clock.advance(29)
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False
        
        # Should go to half-open after cooldown
        fake_clock.advance(2)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True
    
    def test_half_open_to_closed_on_success(self):
        """Test transition from HALF_OPEN to CLOSED on success."""
        fake_clock = FakeClock()
        cb = CircuitBreaker("test", failure_threshold=1, recovery_time_s=30, 
                           half_open_max_success=2, clock=fake_clock)
        
        # Open the circuit and advance to half-open
        cb.on_failure()
        fake_clock.advance(31)
        assert cb.state == CircuitState.HALF_OPEN
        
        # First success should keep it half-open
        cb.on_success()
        assert cb.state == CircuitState.HALF_OPEN
        
        # Second success should close it
        cb.on_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True
    
    def test_half_open_to_open_on_failure(self):
        """Test transition from HALF_OPEN back to OPEN on failure."""
        fake_clock = FakeClock()
        cb = CircuitBreaker("test", failure_threshold=1, recovery_time_s=30, clock=fake_clock)
        
        # Open the circuit and advance to half-open
        cb.on_failure()
        fake_clock.advance(31)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Any failure in half-open should go back to open
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False


class TestMetrics:
    """Test metrics recording and classification."""
    
    def test_classify_exception(self):
        """Test exception classification for metrics."""
        assert metrics.classify_exception(asyncio.TimeoutError()) == "timeout"
        assert metrics.classify_exception(ConnectionError()) == "network"
        
        # Create a mock server error
        class ServerError(Exception):
            pass
        
        assert metrics.classify_exception(ServerError("500 Internal Server Error")) == "server"
        assert metrics.classify_exception(ValueError("random error")) == "other"
    
    @patch('backend.clients.metrics.MODEL_REQUESTS_TOTAL')
    def test_record_request_start(self, mock_counter):
        """Test request start recording."""
        if mock_counter:
            metrics.record_request_start("test_client")
            mock_counter.labels.assert_called_with(client="test_client")
            mock_counter.labels.return_value.inc.assert_called_once()
    
    @patch('backend.clients.metrics.MODEL_REQUEST_DURATION')
    def test_record_request_success(self, mock_histogram):
        """Test successful request recording."""
        if mock_histogram:
            metrics.record_request_success("test_client", 1.5)
            mock_histogram.labels.assert_called_with(client="test_client")
            mock_histogram.labels.return_value.observe.assert_called_with(1.5)
    
    @patch('backend.clients.metrics.CIRCUIT_STATE')
    def test_update_circuit_state(self, mock_gauge):
        """Test circuit state metric updates."""
        if mock_gauge:
            metrics.update_circuit_state("test_client", CircuitState.OPEN)
            mock_gauge.labels.assert_called_with(client="test_client")
            mock_gauge.labels.return_value.set.assert_called_with(CircuitState.OPEN.value)


class TestIntegration:
    """Integration tests combining retry, circuit breaker, and metrics."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retries(self):
        """Test circuit breaker behavior with retry policy."""
        fake_clock = FakeClock()
        cb = CircuitBreaker("test", failure_threshold=2, recovery_time_s=10, clock=fake_clock)
        
        # Simulate multiple failed requests that should open the circuit
        client = FailingClient(fail_count=10)  # Always fails
        policy = RetryPolicy(max_retries=1, base_backoff_ms=1, jitter_ms=0)
        
        # First request fails but doesn't open circuit yet
        with pytest.raises(ConnectionError):
            await with_retries(client.call, policy)
        cb.on_failure()
        assert cb.state == CircuitState.CLOSED
        
        # Second request fails and opens circuit
        client.call_count = 0  # Reset for clean test
        with pytest.raises(ConnectionError):
            await with_retries(client.call, policy)
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        
        # Third request should be blocked by circuit breaker
        assert cb.allow_request() is False
        
        # After cooldown, circuit should allow testing
        fake_clock.advance(11)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True
    
    @pytest.mark.asyncio
    async def test_successful_recovery(self):
        """Test full recovery cycle: failure -> open -> half-open -> closed."""
        fake_clock = FakeClock()
        cb = CircuitBreaker("test", failure_threshold=1, recovery_time_s=5,
                           half_open_max_success=1, clock=fake_clock)
        
        # Open circuit
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery
        fake_clock.advance(6)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Successful request should close circuit
        cb.on_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True
