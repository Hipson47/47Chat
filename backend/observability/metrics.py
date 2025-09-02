"""
Metrics collection and Prometheus endpoint for 47Chat.

This module provides:
- Prometheus metrics collection
- HTTP request metrics (duration, count, status codes)
- Business metrics (orchestration count, model inference time)
- Health status metrics
- Metrics endpoint for Prometheus scraping
"""

import time
from typing import Optional

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from .logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Prometheus metrics collector for 47Chat."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize the metrics collector.

        Args:
            registry: Optional custom registry (uses default if None)
        """
        self.registry = registry or CollectorRegistry()

        # HTTP request metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry,
        )

        # Business metrics
        self.orchestration_requests_total = Counter(
            "orchestration_requests_total",
            "Total number of orchestration requests",
            ["status", "teams_count"],
            registry=self.registry,
        )

        self.orchestration_duration_seconds = Histogram(
            "orchestration_duration_seconds",
            "Orchestration duration in seconds",
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=self.registry,
        )

        # AI model metrics
        self.ai_model_inference_total = Counter(
            "ai_model_inference_total",
            "Total number of AI model inferences",
            ["model_name", "provider"],
            registry=self.registry,
        )

        self.ai_model_inference_duration_seconds = Histogram(
            "ai_model_inference_duration_seconds",
            "AI model inference duration in seconds",
            ["model_name", "provider"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry,
        )

        # System health metrics
        self.health_status = Gauge(
            "health_status",
            "Current health status (1=healthy, 0=unhealthy)",
            registry=self.registry,
        )

        self.ollama_available = Gauge(
            "ollama_available",
            "Ollama service availability (1=available, 0=unavailable)",
            registry=self.registry,
        )

        self.rag_store_exists = Gauge(
            "rag_store_exists",
            "RAG store existence (1=exists, 0=missing)",
            registry=self.registry,
        )

        # Resource metrics
        self.active_requests = Gauge(
            "active_requests",
            "Number of currently active requests",
            registry=self.registry,
        )

        # Error metrics
        self.errors_total = Counter(
            "errors_total",
            "Total number of errors",
            ["type", "endpoint"],
            registry=self.registry,
        )

        logger.info("Metrics collector initialized")

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ) -> None:
        """Record an HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_orchestration_request(
        self,
        status: str,
        teams_count: int,
        duration: float
    ) -> None:
        """Record an orchestration request.

        Args:
            status: Request status ("success" or "error")
            teams_count: Number of teams involved
            duration: Orchestration duration in seconds
        """
        self.orchestration_requests_total.labels(
            status=status,
            teams_count=teams_count
        ).inc()

        self.orchestration_duration_seconds.observe(duration)

    def record_ai_inference(
        self,
        model_name: str,
        provider: str,
        duration: float
    ) -> None:
        """Record AI model inference.

        Args:
            model_name: Name of the AI model
            provider: AI provider ("ollama" or "openai")
            duration: Inference duration in seconds
        """
        self.ai_model_inference_total.labels(
            model_name=model_name,
            provider=provider
        ).inc()

        self.ai_model_inference_duration_seconds.labels(
            model_name=model_name,
            provider=provider
        ).observe(duration)

    def update_health_status(
        self,
        is_healthy: bool,
        ollama_available: bool,
        rag_store_exists: bool
    ) -> None:
        """Update health status metrics.

        Args:
            is_healthy: Overall health status
            ollama_available: Ollama service availability
            rag_store_exists: RAG store existence
        """
        self.health_status.set(1 if is_healthy else 0)
        self.ollama_available.set(1 if ollama_available else 0)
        self.rag_store_exists.set(1 if rag_store_exists else 0)

    def increment_active_requests(self) -> None:
        """Increment the active requests counter."""
        self.active_requests.inc()

    def decrement_active_requests(self) -> None:
        """Decrement the active requests counter."""
        self.active_requests.dec()

    def record_error(self, error_type: str, endpoint: str) -> None:
        """Record an error.

        Args:
            error_type: Type of error
            endpoint: Endpoint where error occurred
        """
        self.errors_total.labels(
            type=error_type,
            endpoint=endpoint
        ).inc()

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format.

        Returns:
            Metrics in Prometheus exposition format
        """
        return generate_latest(self.registry).decode("utf-8")


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance.

    Returns:
        The global metrics collector
    """
    return metrics_collector


def record_http_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float
) -> None:
    """Record an HTTP request (convenience function).

    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    metrics_collector.record_http_request(method, endpoint, status_code, duration)


def record_orchestration_request(
    status: str,
    teams_count: int,
    duration: float
) -> None:
    """Record an orchestration request (convenience function).

    Args:
        status: Request status
        teams_count: Number of teams involved
        duration: Orchestration duration in seconds
    """
    metrics_collector.record_orchestration_request(status, teams_count, duration)


def record_ai_inference(
    model_name: str,
    provider: str,
    duration: float
) -> None:
    """Record AI model inference (convenience function).

    Args:
        model_name: Name of the AI model
        provider: AI provider
        duration: Inference duration in seconds
    """
    metrics_collector.record_ai_inference(model_name, provider, duration)


def update_health_status(
    is_healthy: bool,
    ollama_available: bool,
    rag_store_exists: bool
) -> None:
    """Update health status metrics (convenience function).

    Args:
        is_healthy: Overall health status
        ollama_available: Ollama service availability
        rag_store_exists: RAG store existence
    """
    metrics_collector.update_health_status(is_healthy, ollama_available, rag_store_exists)
