"""
Structured logging configuration with JSON formatting and request ID injection.

This module provides:
- JSON-formatted logging with consistent structure
- Request ID injection into log context
- Structured logging for different log levels
- Configurable log levels and formatters
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars

# Context variables for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Get the current request and trace IDs
        request_id = request_id_context.get()
        trace_id = trace_id_context.get()

        # Create structured log entry
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if request_id:
            log_entry["request_id"] = request_id
        if trace_id:
            log_entry["trace_id"] = trace_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add any extra fields from the record
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in {
                    "name", "msg", "args", "levelname", "levelno", "pathname",
                    "filename", "module", "exc_info", "exc_text", "stack_info",
                    "lineno", "funcName", "created", "msecs", "relativeCreated",
                    "thread", "threadName", "processName", "process", "message"
                }:
                    log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_structlog() -> None:
    """Configure structlog for structured logging."""
    # Configure structlog processors
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.processors.TimeStamper(fmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            # Add log level
            structlog.processors.add_log_level,
            # Merge context variables
            merge_contextvars,
            # Render as JSON
            structlog.processors.JSONRenderer(),
        ],
        # Set up context class
        context_class=dict,
        # Set up logger factory
        logger_factory=structlog.WriteLoggerFactory(),
        # Set up wrapper class
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        # Cache logger on first use
        cache_logger_on_first_use=True,
    )


def setup_logging(
    level: str = "INFO",
    format_json: bool = True,
    enable_request_context: bool = True
) -> None:
    """Set up Python logging with structured JSON formatting.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_json: Whether to use JSON formatting
        enable_request_context: Whether to enable request ID context
    """
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if format_json:
        # Use JSON formatter
        formatter = JSONFormatter()
    else:
        # Use standard formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure structlog if requested
    if format_json:
        setup_structlog()

    # Set up loggers for common libraries to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)

    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        level=level,
        format="json" if format_json else "text",
        request_context=enable_request_context
    )


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return str(uuid.uuid4())


def set_request_context(request_id: str, trace_id: Optional[str] = None) -> None:
    """Set request context for logging."""
    request_id_context.set(request_id)
    if trace_id:
        trace_id_context.set(trace_id)
    else:
        trace_id_context.set(request_id)  # Use request_id as trace_id if not provided


def clear_request_context() -> None:
    """Clear request context."""
    request_id_context.set(None)
    trace_id_context.set(None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_context.get()


def get_trace_id() -> Optional[str]:
    """Get current trace ID from context."""
    return trace_id_context.get()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


# Create a default logger for this module
logger = get_logger(__name__)
