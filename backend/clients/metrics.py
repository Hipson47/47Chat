"""Prometheus metrics for model client resilience.

Provides metrics for tracking model client performance, errors, timeouts,
and circuit breaker states.
"""

from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:  # pragma: no cover
    # Fallback when prometheus_client not available
    Counter = None  # type: ignore
    Histogram = None  # type: ignore
    Gauge = None  # type: ignore

from .circuit import CircuitState


# Model client request metrics
MODEL_REQUESTS_TOTAL = (
    Counter(
        "model_requests_total",
        "Total number of model requests made",
        ["client"]
    ) if Counter else None
)

MODEL_ERRORS_TOTAL = (
    Counter(
        "model_errors_total", 
        "Total number of model request errors",
        ["client", "kind"]
    ) if Counter else None
)

MODEL_TIMEOUTS_TOTAL = (
    Counter(
        "model_timeouts_total",
        "Total number of model request timeouts", 
        ["client"]
    ) if Counter else None
)

MODEL_REQUEST_DURATION = (
    Histogram(
        "model_request_duration_seconds",
        "Model request duration in seconds",
        ["client"],
        buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
    ) if Histogram else None
)

CIRCUIT_STATE = (
    Gauge(
        "circuit_state",
        "Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)",
        ["client"]
    ) if Gauge else None
)


def record_request_start(client: str) -> None:
    """Record the start of a model request."""
    if MODEL_REQUESTS_TOTAL:
        MODEL_REQUESTS_TOTAL.labels(client=client).inc()


def record_request_success(client: str, duration: float) -> None:
    """Record a successful model request."""
    if MODEL_REQUEST_DURATION:
        MODEL_REQUEST_DURATION.labels(client=client).observe(duration)


def record_request_error(client: str, error_kind: str, duration: float) -> None:
    """Record a failed model request."""
    if MODEL_ERRORS_TOTAL:
        MODEL_ERRORS_TOTAL.labels(client=client, kind=error_kind).inc()
    if MODEL_REQUEST_DURATION:
        MODEL_REQUEST_DURATION.labels(client=client).observe(duration)


def record_timeout(client: str) -> None:
    """Record a model request timeout."""
    if MODEL_TIMEOUTS_TOTAL:
        MODEL_TIMEOUTS_TOTAL.labels(client=client).inc()


def update_circuit_state(client: str, state: CircuitState) -> None:
    """Update circuit breaker state metric."""
    if CIRCUIT_STATE:
        CIRCUIT_STATE.labels(client=client).set(state.value)


def classify_exception(exc: Exception) -> str:
    """Classify an exception into a metrics category."""
    exc_name = type(exc).__name__.lower()
    
    if "timeout" in exc_name:
        return "timeout"
    elif "ratelimit" in exc_name or "429" in str(exc):
        return "rate_limit"  
    elif any(net in exc_name for net in ["connection", "network", "dns"]):
        return "network"
    elif any(srv in exc_name for srv in ["server", "500", "502", "503", "504"]):
        return "server"
    else:
        return "other"
