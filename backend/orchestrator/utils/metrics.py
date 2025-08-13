# orchestrator/utils/metrics.py
"""
Utility for logging and exporting orchestrator metrics.

This module acts as the single place where we bridge internal metrics to
Prometheus exposition, while preserving the lightweight existing file log.
"""

from __future__ import annotations

import json
import time
from typing import Dict, Any, List

try:  # Prometheus is optional in some dev environments
    from prometheus_client import Counter, Histogram
except Exception:  # pragma: no cover - fall back when dependency is missing
    Counter = None  # type: ignore
    Histogram = None  # type: ignore


# Prometheus metrics (created lazily when dependency is available)
ORCHESTRATOR_ROUNDS = (
    Counter("orchestrator_rounds_total", "Total orchestrator rounds executed")
    if Counter
    else None
)
ORCHESTRATOR_PASSES = (
    Counter(
        "orchestrator_passes_total",
        "Total number of passes/phases executed across rounds",
    )
    if Counter
    else None
)
ORCHESTRATOR_TOKENS = (
    Counter("orchestrator_tokens_total", "Total tokens used across all LLM calls")
    if Counter
    else None
)
ORCHESTRATOR_ROUND_LATENCY = (
    Histogram(
        "orchestrator_round_latency_seconds",
        "Orchestrator round latency in seconds",
        buckets=(
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
            30.0,
            60.0,
            120.0,
        ),
    )
    if Histogram
    else None
)


def log_metrics(data: Dict[str, Any]) -> None:
    """Log orchestrator metrics and export to Prometheus if available.

    Args:
        data: Arbitrary metrics payload from the orchestrator. Recognized keys:
            - num_phases: int, number of phases executed in a round
            - tokens_used: int, total tokens used (if available)
    """
    log_entry = {"timestamp": time.time(), "data": data}
    with open("metrics.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"Logged metrics: {data}")

    # Best-effort Prometheus updates
    if ORCHESTRATOR_ROUNDS is not None:
        ORCHESTRATOR_ROUNDS.inc()
    if ORCHESTRATOR_PASSES is not None and isinstance(data.get("num_phases"), int):
        ORCHESTRATOR_PASSES.inc(int(data["num_phases"]))
    if ORCHESTRATOR_TOKENS is not None and isinstance(data.get("tokens_used"), int):
        ORCHESTRATOR_TOKENS.inc(int(data["tokens_used"]))


def record_round_latency(duration_seconds: float) -> None:
    """Record the latency of a completed round.

    Args:
        duration_seconds: Elapsed seconds for the orchestrator round.
    """
    if ORCHESTRATOR_ROUND_LATENCY is not None and duration_seconds >= 0:
        ORCHESTRATOR_ROUND_LATENCY.observe(duration_seconds)


def check_adaptive_scheduling(metrics: Dict[str, Any]) -> List[str]:
    """Check if adaptive scheduling rules should be applied.

    This is a stub and can be expanded to read thresholds from configuration.

    Args:
        metrics: The current metrics snapshot.

    Returns:
        List of actions to take.
    """
    actions: List[str] = []
    if metrics.get("slow_response_ms", 0) > 1500:
        actions.append("extend_phase: Brainstorm")
    return actions
