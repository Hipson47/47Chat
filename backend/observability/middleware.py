"""
FastAPI middleware for request tracking and observability.

This module provides:
- Request ID generation and injection
- Request context management
- Response time tracking
- Error tracking and logging
- Integration with structured logging and tracing
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware

from .logging import (
    generate_request_id,
    generate_trace_id,
    set_request_context,
    clear_request_context,
    get_logger,
)
from .tracing import create_span, add_span_attributes, record_exception

logger = get_logger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracking, logging, and tracing."""

    def __init__(self, app: Callable, exclude_paths: list[str] = None):
        """Initialize the middleware.

        Args:
            app: The FastAPI application
            exclude_paths: List of paths to exclude from tracking
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add tracking information.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            The response from the route handler
        """
        # Skip tracking for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate request and trace IDs
        request_id = generate_request_id()
        trace_id = generate_trace_id()

        # Set request context for logging
        set_request_context(request_id, trace_id)

        # Add headers to request for downstream use
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        # Start timing
        start_time = time.time()

        # Create a span for this request
        with create_span(
            f"http.{request.method.lower()}",
            kind=trace.SpanKind.SERVER,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.headers.get("host", ""),
                "http.user_agent": request.headers.get("user-agent", ""),
                "net.peer.ip": request.client.host if request.client else "",
                "request.id": request_id,
                "trace.id": trace_id,
            }
        ) as span:
            try:
                # Add request ID header to response
                response = await call_next(request)

                # Calculate response time
                response_time = time.time() - start_time

                # Add response headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Trace-ID"] = trace_id
                response.headers["X-Response-Time"] = ".3f"

                # Add response attributes to span
                add_span_attributes(span, {
                    "http.status_code": response.status_code,
                    "http.response_time": response_time,
                    "response.content_length": len(response.body) if hasattr(response, 'body') else 0,
                })

                # Log successful request
                logger.info(
                    "Request completed",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    response_time=response_time,
                    user_agent=request.headers.get("user-agent", ""),
                    client_ip=request.client.host if request.client else "",
                )

                return response

            except Exception as exc:
                # Calculate response time for failed requests
                response_time = time.time() - start_time

                # Record exception in span
                record_exception(span, exc)

                # Add error attributes to span
                add_span_attributes(span, {
                    "error": True,
                    "error.type": type(exc).__name__,
                    "error.message": str(exc),
                    "http.response_time": response_time,
                })

                # Log error
                logger.error(
                    "Request failed",
                    method=request.method,
                    path=request.url.path,
                    error=str(exc),
                    error_type=type(exc).__name__,
                    response_time=response_time,
                    user_agent=request.headers.get("user-agent", ""),
                    client_ip=request.client.host if request.client else "",
                    exc_info=True,
                )

                # Re-raise the exception
                raise
            finally:
                # Clear request context
                clear_request_context()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Simple middleware for request ID generation only."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request and response.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            The response from the route handler
        """
        # Generate request ID
        request_id = generate_request_id()

        # Add to request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id_from_request(request: Request) -> str:
    """Get the request ID from a FastAPI request.

    Args:
        request: The FastAPI request object

    Returns:
        The request ID string
    """
    return getattr(request.state, "request_id", "unknown")


def get_trace_id_from_request(request: Request) -> str:
    """Get the trace ID from a FastAPI request.

    Args:
        request: The FastAPI request object

    Returns:
        The trace ID string
    """
    return getattr(request.state, "trace_id", generate_trace_id())
