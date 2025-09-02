# orchestrator/utils/metrics.py
"""
Utility for logging metrics and handling adaptive scheduling.
"""

import json
import time
from typing import Any


def log_metrics(data: dict[str, Any]) -> None:
    """
    Logs metrics to a file.

    Args:
        data (dict): The data to log.
    """
    log_entry = {"timestamp": time.time(), "data": data}
    with open("metrics.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"Logged metrics: {data}")


def check_adaptive_scheduling(metrics: dict[str, Any]) -> list[str]:
    """
    Checks if adaptive scheduling rules should be applied.

    Args:
        metrics (dict): The current metrics.

    Returns:
        list: A list of actions to take.
    """
    # This is a stub implementation.
    # In a real implementation, you would check the metrics against
    # the rules in the meta_prompt.
    actions = []
    if metrics.get("slow_response_ms", 0) > 1500:
        actions.append("extend_phase: Brainstorm")
    return actions
