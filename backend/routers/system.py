from __future__ import annotations

from fastapi import APIRouter, Response
from typing import Dict, Any

try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"  # type: ignore[assignment]
    def generate_latest() -> bytes:  # type: ignore[no-redef]
        return b""  # Provide empty metrics when prometheus_client is not installed

from ..version import __version__

router = APIRouter()


@router.get("/health")
def health() -> Dict[str, Any]:
    """Simple health endpoint returning only status and version."""
    return {"status": "ok", "version": __version__}


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics in the standard text exposition format."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


