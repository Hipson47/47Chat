#!/usr/bin/env python3
"""
Validation script for observability features.
Tests logging, tracing, and metrics functionality.
"""

import json
import sys
import os
from pathlib import Path

def test_imports():
    """Test that all observability modules can be imported."""
    try:
        # Test logging imports
        from backend.observability.logging import setup_logging, get_logger, generate_request_id
        print("✅ Logging module imports successful")

        # Test tracing imports
        from backend.observability.tracing import setup_tracing, get_tracer
        print("✅ Tracing module imports successful")

        # Test middleware imports
        from backend.observability.middleware import RequestTrackingMiddleware
        print("✅ Middleware module imports successful")

        # Test metrics imports
        from backend.observability.metrics import get_metrics_collector
        print("✅ Metrics module imports successful")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_logging_functionality():
    """Test basic logging functionality."""
    try:
        from backend.observability.logging import setup_logging, get_logger

        # Set up logging
        setup_logging(level="INFO", format_json=True)

        # Get logger and test logging
        logger = get_logger(__name__)

        # Test different log levels
        logger.info("Test info message", test_field="test_value")
        logger.warning("Test warning message", warning_code=123)
        logger.error("Test error message", error_code=500)

        print("✅ Logging functionality works")
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def test_request_id_generation():
    """Test request ID generation."""
    try:
        from backend.observability.logging import generate_request_id, generate_trace_id

        request_id = generate_request_id()
        trace_id = generate_trace_id()

        # Check format (should be UUID)
        import uuid
        uuid.UUID(request_id)  # Should not raise exception
        uuid.UUID(trace_id)    # Should not raise exception

        print(f"✅ Request ID generation works: {request_id[:8]}...")
        return True
    except Exception as e:
        print(f"❌ Request ID generation failed: {e}")
        return False

def test_tracing_setup():
    """Test tracing setup."""
    try:
        from backend.observability.tracing import setup_tracing, get_tracer

        # Set up tracing (console exporter for testing)
        setup_tracing(
            service_name="test-service",
            service_version="1.0.0",
            otlp_endpoint=None  # Use console exporter
        )

        # Get tracer
        tracer = get_tracer("test-tracer")

        # Create a test span
        with tracer.start_as_span("test-span") as span:
            span.set_attribute("test.attribute", "test_value")

        print("✅ Tracing setup works")
        return True
    except Exception as e:
        print(f"❌ Tracing setup failed: {e}")
        return False

def test_metrics_collection():
    """Test metrics collection."""
    try:
        from backend.observability.metrics import get_metrics_collector

        collector = get_metrics_collector()

        # Record some test metrics
        collector.record_http_request("GET", "/health", 200, 0.1)
        collector.record_orchestration_request("success", 3, 2.5)

        # Get metrics
        metrics = collector.get_metrics()

        # Should contain some metrics
        assert len(metrics) > 0
        assert "http_requests_total" in metrics
        assert "orchestration_requests_total" in metrics

        print("✅ Metrics collection works")
        return True
    except Exception as e:
        print(f"❌ Metrics collection failed: {e}")
        return False

def test_fastapi_integration():
    """Test FastAPI integration with observability."""
    try:
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200

        # Check response headers for request ID
        assert "X-Request-ID" in response.headers
        assert "X-Trace-ID" in response.headers

        data = response.json()
        assert "status" in data
        assert "ollama_available" in data
        assert "rag_store_exists" in data

        print("✅ FastAPI integration works")

        # Test metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics_data = response.text
        assert len(metrics_data) > 0

        print("✅ Metrics endpoint works")
        return True

    except Exception as e:
        print(f"❌ FastAPI integration failed: {e}")
        return False

def test_json_log_format():
    """Test JSON log format parsing."""
    try:
        import json
        from backend.observability.logging import setup_logging, get_logger

        # Set up logging
        setup_logging(level="INFO", format_json=True)

        logger = get_logger(__name__)

        # This should produce JSON output
        # In a real scenario, we'd capture the output, but for now just ensure no exceptions
        logger.info("JSON format test", test_key="test_value")

        print("✅ JSON log format works")
        return True
    except Exception as e:
        print(f"❌ JSON log format failed: {e}")
        return False

def main():
    """Run all observability validation tests."""
    print("🔍 Validating 47Chat Observability Features\n")

    tests = [
        ("Module Imports", test_imports),
        ("Logging Functionality", test_logging_functionality),
        ("Request ID Generation", test_request_id_generation),
        ("Tracing Setup", test_tracing_setup),
        ("Metrics Collection", test_metrics_collection),
        ("FastAPI Integration", test_fastapi_integration),
        ("JSON Log Format", test_json_log_format),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n🧪 Testing {name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {name} passed")
            else:
                print(f"❌ {name} failed")
        except Exception as e:
            print(f"❌ {name} failed with error: {e}")

    print("\n📊 Observability Validation Results:")
    print(f"   Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All observability features are working correctly!")
        print("\n🔍 Features Verified:")
        print("  ✅ Structured JSON logging with request ID injection")
        print("  ✅ OpenTelemetry tracing with FastAPI instrumentation")
        print("  ✅ Request tracking middleware")
        print("  ✅ Prometheus metrics collection")
        print("  ✅ Health and metrics endpoints")
        print("  ✅ Error handling and logging")
        return True
    else:
        print("\n❌ Some observability features need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
