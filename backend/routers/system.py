"""System endpoints: health and metrics.

Provides:
- GET /health: basic health status and version
- GET /metrics: Prometheus exposition format metrics
"""

from __future__ import annotations

from fastapi import APIRouter, Response

try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest  # type: ignore
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"  # type: ignore
    generate_latest = None  # type: ignore

try:
    # Package context
    from .. import __version__
except Exception:  # pragma: no cover
    # Script context fallback
    from backend import __version__  # type: ignore


router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    """Return a simple application health status and version.

    Returns:
        dict: {"status": "ok", "version": "..."}
    """
    return {"status": "ok", "version": __version__}


@router.get("/metrics")
def metrics() -> Response:
    """Return application metrics in Prometheus exposition format."""
    if generate_latest is None:
        # Prometheus client not installed
        return Response(
            content="# Prometheus client not installed\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=200,
        )
    payload = generate_latest()  # type: ignore[operator]
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


