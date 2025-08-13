from fastapi.testclient import TestClient

from backend.main import app


def test_health_and_metrics_endpoints():
    client = TestClient(app)

    # /health
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert "version" in body

    # /metrics
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.headers.get("content-type", "").startswith("text/plain")
    assert isinstance(metrics.content, (bytes, bytearray))


