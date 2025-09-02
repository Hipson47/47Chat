"""
OpenTelemetry tracing configuration for distributed tracing.

This module provides:
- OpenTelemetry SDK initialization
- Service name and resource attributes configuration
- FastAPI instrumentation for automatic tracing
- OTLP exporter configuration for trace collection
- Custom span creation for key functions
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from .logging import get_logger

logger = get_logger(__name__)


def setup_tracing(
    service_name: str = "47chat",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    enable_fastapi_instrumentation: bool = True,
) -> None:
    """Set up OpenTelemetry tracing.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP endpoint URL (e.g., "http://localhost:4317")
        enable_fastapi_instrumentation: Whether to enable FastAPI auto-instrumentation
    """
    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "service.instance.id": "47chat-instance-1",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.language": "python",
        "telemetry.sdk.version": "1.20.0",
    })

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter if endpoint is provided
    if otlp_endpoint:
        logger.info("Setting up OTLP exporter", endpoint=otlp_endpoint)

        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True,  # Use insecure for local development
        )

        # Create batch span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        logger.info("OTLP exporter configured", endpoint=otlp_endpoint)
    else:
        # Use console exporter for local development
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        console_exporter = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(console_exporter)
        tracer_provider.add_span_processor(span_processor)

        logger.info("Console exporter configured for local development")

    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Get a tracer for this module
    tracer = trace.get_tracer(__name__)

    # Enable FastAPI instrumentation
    if enable_fastapi_instrumentation:
        logger.info("Enabling FastAPI instrumentation")
        FastAPIInstrumentor.instrument()
        logger.info("FastAPI instrumentation enabled")

    logger.info(
        "Tracing setup complete",
        service_name=service_name,
        service_version=service_version,
        otlp_endpoint=otlp_endpoint,
        fastapi_instrumentation=enable_fastapi_instrumentation
    )


def get_tracer(name: str, version: Optional[str] = None) -> trace.Tracer:
    """Get a tracer instance.

    Args:
        name: Name of the tracer
        version: Optional version

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name, version)


def create_span(
    name: str,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: Optional[dict] = None,
) -> trace.Span:
    """Create a new span.

    Args:
        name: Name of the span
        kind: Kind of span (INTERNAL, SERVER, CLIENT, etc.)
        attributes: Additional attributes to set on the span

    Returns:
        Created span
    """
    tracer = get_tracer(__name__)
    span = tracer.start_span(name, kind=kind)

    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span


def add_span_attributes(span: trace.Span, attributes: dict) -> None:
    """Add attributes to an existing span.

    Args:
        span: The span to add attributes to
        attributes: Dictionary of attributes to add
    """
    for key, value in attributes.items():
        span.set_attribute(key, value)


def record_exception(span: trace.Span, exception: Exception) -> None:
    """Record an exception on a span.

    Args:
        span: The span to record the exception on
        exception: The exception to record
    """
    span.record_exception(exception)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


# Create a default tracer for this module
tracer = get_tracer(__name__)


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """Decorator to trace function execution.

    Args:
        name: Optional name for the span (defaults to function name)
        attributes: Optional attributes to add to the span
        kind: Kind of span
    """
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        def wrapper(*args, **kwargs):
            with tracer.start_as_span(span_name, kind=kind) as span:
                if attributes:
                    add_span_attributes(span, attributes)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as exc:
                    record_exception(span, exc)
                    raise

        return wrapper
    return decorator


def trace_async_function(
    name: Optional[str] = None,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """Decorator to trace async function execution.

    Args:
        name: Optional name for the span (defaults to function name)
        attributes: Optional attributes to add to the span
        kind: Kind of span
    """
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        async def wrapper(*args, **kwargs):
            with tracer.start_as_span(span_name, kind=kind) as span:
                if attributes:
                    add_span_attributes(span, attributes)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as exc:
                    record_exception(span, exc)
                    raise

        return wrapper
    return decorator


# Utility functions for common tracing patterns
def trace_database_operation(operation: str, table: str):
    """Create a span for database operations.

    Args:
        operation: The database operation (SELECT, INSERT, UPDATE, DELETE)
        table: The table being operated on

    Returns:
        Span context manager
    """
    return tracer.start_as_span(
        f"db.{operation.lower()}",
        kind=trace.SpanKind.CLIENT,
        attributes={
            "db.operation": operation,
            "db.table": table,
        }
    )


def trace_external_api_call(method: str, url: str, service: Optional[str] = None):
    """Create a span for external API calls.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: The URL being called
        service: Optional service name

    Returns:
        Span context manager
    """
    attributes = {
        "http.method": method,
        "http.url": url,
    }

    if service:
        attributes["service.name"] = service

    return tracer.start_as_span(
        f"http.{method.lower()}",
        kind=trace.SpanKind.CLIENT,
        attributes=attributes
    )


def trace_ai_model_inference(model_name: str, input_tokens: Optional[int] = None):
    """Create a span for AI model inference.

    Args:
        model_name: Name of the AI model
        input_tokens: Number of input tokens (optional)

    Returns:
        Span context manager
    """
    attributes = {
        "ai.model.name": model_name,
    }

    if input_tokens is not None:
        attributes["ai.input.tokens"] = input_tokens

    return tracer.start_as_span(
        f"ai.inference.{model_name}",
        kind=trace.SpanKind.INTERNAL,
        attributes=attributes
    )
