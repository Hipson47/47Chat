import os
import sys
import time
import subprocess
import requests


def start_server() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8002"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_health_and_metrics_endpoints():
    proc = start_server()
    try:
        time.sleep(3)
        base = "http://127.0.0.1:8002"
        # Health
        r = requests.get(f"{base}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert isinstance(data.get("version"), str)

        # Metrics
        r2 = requests.get(f"{base}/metrics", timeout=10)
        assert r2.status_code == 200
        text = r2.text
        assert "#" in text or "Prometheus client not installed" in text
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


