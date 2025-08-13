# orchestrator/utils/metrics.py
"""
Utility for logging metrics and exposing Prometheus-compatible gauges/counters.

This module serves two purposes:
1) Persist human-readable metrics to a simple newline-delimited JSON log file
2) Maintain Prometheus metrics that can be scraped via the /metrics endpoint

It is intentionally import-light so it can be used by both API and orchestrator layers.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List

try:
    # Prometheus is optional until the /metrics endpoint is requested
    from prometheus_client import Counter, Gauge, Histogram
except Exception:  # pragma: no cover - allow running even if not installed in some contexts
    Counter = Gauge = Histogram = None  # type: ignore[assignment]

# -------------------------
# Prometheus metric objects
# -------------------------

ROUND_LATENCY_SECONDS = (
    Histogram(
        "orchestrator_round_latency_seconds",
        "Latency of orchestration rounds in seconds",
        buckets=(
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.0,
            5.0,
            10.0,
            30.0,
            60.0,
        ),
    )
    if Histogram is not None
    else None
)

TOKENS_USED_TOTAL = (
    Counter(
        "orchestrator_tokens_used_total",
        "Total tokens used across orchestration rounds",
    )
    if Counter is not None
    else None
)

PASSES_COUNT_GAUGE = (
    Gauge(
        "orchestrator_passes_count",
        "Number of passes (phases) in the most recently completed round",
    )
    if Gauge is not None
    else None
)

ROUNDS_TOTAL = (
    Counter("orchestrator_rounds_total", "Total number of completed orchestration rounds")
    if Counter is not None
    else None
)


def record_round_latency_seconds(latency_seconds: float) -> None:
    """Record a single round latency observation in seconds.

    Args:
        latency_seconds: Duration of the orchestration round in seconds.
    """
    if ROUND_LATENCY_SECONDS is not None:
        ROUND_LATENCY_SECONDS.observe(latency_seconds)


def set_passes_count(passes_count: int) -> None:
    """Set the gauge for number of passes (phases) in the last round."""
    if PASSES_COUNT_GAUGE is not None:
        PASSES_COUNT_GAUGE.set(float(passes_count))


def add_tokens_used(tokens_used: int) -> None:
    """Increment the cumulative tokens-used counter if available."""
    if TOKENS_USED_TOTAL is not None and tokens_used >= 0:
        TOKENS_USED_TOTAL.inc(tokens_used)


def _maybe_update_prom_metrics(data: Dict[str, Any]) -> None:
    """Update Prometheus metrics based on keys present in the provided data.

    Supported keys:
      - latency_ms: Round duration in milliseconds
      - tokens_used: Integer tokens used in the round
      - num_phases | passes_count: Number of phases executed in the round
    """
    try:
        if "latency_ms" in data and isinstance(data["latency_ms"], (int, float)):
            record_round_latency_seconds(float(data["latency_ms"]) / 1000.0)
        if "tokens_used" in data and isinstance(data["tokens_used"], int):
            add_tokens_used(int(data["tokens_used"]))
        passes = None
        if "num_phases" in data and isinstance(data["num_phases"], int):
            passes = int(data["num_phases"])
        elif "passes_count" in data and isinstance(data["passes_count"], int):
            passes = int(data["passes_count"])
        if passes is not None:
            set_passes_count(passes)
        if ROUNDS_TOTAL is not None:
            # Count the fact that a round completed if data hints at a round-level log
            if "num_phases" in data or "passes_count" in data or "latency_ms" in data:
                ROUNDS_TOTAL.inc()
    except Exception:
        # Metrics must never break the app
        pass


def log_metrics(data: Dict[str, Any]) -> None:
    """
    Logs metrics to a file and updates Prometheus metrics.

    Args:
        data: The data to log.
    """
    log_entry = {"timestamp": time.time(), "data": data}
    try:
        with open("metrics.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        # File logging should not break the application flow
        pass

    _maybe_update_prom_metrics(data)


def check_adaptive_scheduling(metrics: Dict[str, Any]) -> List[str]:
    """
    Checks if adaptive scheduling rules should be applied.

    Args:
        metrics: The current metrics.

    Returns:
        A list of actions to take.
    """
    # This is a stub implementation.
    # In a real implementation, you would check the metrics against
    # the rules in the meta_prompt.
    actions: List[str] = []
    if metrics.get("slow_response_ms", 0) > 1500:
        actions.append("extend_phase: Brainstorm")
    return actions
