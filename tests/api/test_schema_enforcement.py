"""
Comprehensive API schema enforcement tests.
Tests strict JSON contracts with additionalProperties: false enforcement.
Validates that rogue fields are rejected with 400 status codes.
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestOrchestrationRequestSchema:
    """Test orchestration request schema enforcement."""

    def test_valid_orchestration_request(self, client):
        """Test that valid orchestration requests are accepted."""
        valid_payload = {
            "question": "How can I improve my application architecture?",
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=valid_payload)

        # Should be accepted (even if orchestration fails, schema should be valid)
        assert response.status_code in [200, 500]  # 200 for success, 500 for orchestration failure

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "transcript" in data
            assert data["status"] == "success"

    def test_missing_required_field(self, client):
        """Test that requests missing required fields are rejected."""
        # Missing 'question' field
        invalid_payload = {
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=invalid_payload)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data
        # Should mention the missing required field
        error_detail = str(data["detail"]).lower()
        assert "question" in error_detail or "required" in error_detail

    def test_empty_question(self, client):
        """Test that empty questions are rejected."""
        invalid_payload = {
            "question": "",
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=invalid_payload)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data

    def test_question_too_long(self, client):
        """Test that questions exceeding max length are rejected."""
        long_question = "a" * 2001  # Exceeds 2000 character limit
        invalid_payload = {
            "question": long_question,
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=invalid_payload)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data

    def test_extra_property_rejection(self, client):
        """Test that extra properties are rejected (additionalProperties: false)."""
        # Try to inject a rogue admin field
        malicious_payload = {
            "question": "How can I improve my application architecture?",
            "use_rag": True,
            "isAdmin": True,  # This should be rejected
            "secretField": "malicious_value"
        }

        response = client.post("/orchestrate/", json=malicious_payload)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data
        # Should mention extra fields
        error_detail = str(data["detail"]).lower()
        assert "extra" in error_detail or "additional" in error_detail or "forbidden" in error_detail

    def test_wrong_data_types(self, client):
        """Test that wrong data types are rejected."""
        # Wrong types for fields
        invalid_payload = {
            "question": 12345,  # Should be string
            "use_rag": "true"   # Should be boolean
        }

        response = client.post("/orchestrate/", json=invalid_payload)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data

    def test_null_values(self, client):
        """Test that null values are handled appropriately."""
        invalid_payload = {
            "question": None,  # Should be string
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=invalid_payload)
        assert response.status_code == 422  # Validation error


class TestHealthEndpointSchema:
    """Test health endpoint schema enforcement."""

    def test_health_endpoint_response_schema(self, client):
        """Test that health endpoint returns valid schema."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # Validate required fields
        assert "status" in data
        assert "ollama_available" in data
        assert "rag_store_exists" in data

        # Validate field types
        assert isinstance(data["status"], str)
        assert isinstance(data["ollama_available"], bool)
        assert isinstance(data["rag_store_exists"], bool)

        # Validate status enum
        assert data["status"] in ["healthy", "unhealthy", "degraded"]

    def test_health_endpoint_no_extra_fields(self, client):
        """Test that health endpoint doesn't return extra fields."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should only contain the expected fields
        expected_fields = {"status", "ollama_available", "rag_store_exists"}
        actual_fields = set(data.keys())

        # No extra fields should be present
        assert actual_fields == expected_fields


class TestRootEndpointSchema:
    """Test root endpoint schema enforcement."""

    def test_root_endpoint_response_schema(self, client):
        """Test that root endpoint returns valid schema."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # Validate required fields
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "config" in data

        # Validate field types
        assert isinstance(data["message"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["endpoints"], dict)
        assert isinstance(data["config"], dict)

        # Validate patterns
        assert data["message"].startswith("47Chat")
        assert "." in data["version"]  # Basic version format check

    def test_root_endpoint_expected_endpoints(self, client):
        """Test that root endpoint contains expected endpoints."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        endpoints = data["endpoints"]
        assert "/upload/" in endpoints
        assert "/orchestrate/" in endpoints

        # Validate endpoint descriptions are strings
        assert isinstance(endpoints["/upload/"], str)
        assert isinstance(endpoints["/orchestrate/"], str)


class TestSchemaValidationEdgeCases:
    """Test edge cases and boundary conditions for schema validation."""

    def test_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/orchestrate/",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # JSON parsing error

    def test_wrong_content_type(self, client):
        """Test requests with wrong content type."""
        payload = {
            "question": "Test question",
            "use_rag": True
        }

        response = client.post(
            "/orchestrate/",
            data=json.dumps(payload),
            headers={"Content-Type": "text/plain"}
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_very_large_question(self, client):
        """Test with question at the boundary of max length."""
        # Exactly at the limit
        max_question = "a" * 2000
        valid_payload = {
            "question": max_question,
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=valid_payload)
        assert response.status_code in [200, 500]  # Should be accepted

    def test_minimum_question_length(self, client):
        """Test with minimum valid question length."""
        min_question = "a"  # 1 character
        valid_payload = {
            "question": min_question,
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=valid_payload)
        assert response.status_code in [200, 500]  # Should be accepted

    def test_whitespace_only_question(self, client):
        """Test that whitespace-only questions are rejected."""
        invalid_payload = {
            "question": "   \n\t  ",  # Only whitespace
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=invalid_payload)
        assert response.status_code == 422  # Should be rejected


class TestSecuritySchemaValidation:
    """Test security-related schema validations."""

    def test_sql_injection_attempt(self, client):
        """Test that SQL injection attempts in questions are handled safely."""
        malicious_payload = {
            "question": "'; DROP TABLE users; --",
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=malicious_payload)
        # Should be accepted by schema (string is valid), but handled safely by the app
        assert response.status_code in [200, 500]

    def test_xss_attempt(self, client):
        """Test that XSS attempts are handled as regular strings."""
        malicious_payload = {
            "question": "<script>alert('xss')</script>",
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=malicious_payload)
        # Should be accepted by schema (string is valid)
        assert response.status_code in [200, 500]

    def test_path_traversal_attempt(self, client):
        """Test that path traversal attempts are handled as regular strings."""
        malicious_payload = {
            "question": "../../../etc/passwd",
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=malicious_payload)
        # Should be accepted by schema (string is valid)
        assert response.status_code in [200, 500]

    def test_command_injection_attempt(self, client):
        """Test that command injection attempts are handled as regular strings."""
        malicious_payload = {
            "question": "; rm -rf /",
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=malicious_payload)
        # Should be accepted by schema (string is valid)
        assert response.status_code in [200, 500]


class TestSchemaConsistency:
    """Test schema consistency across the API."""

    def test_error_response_format(self, client):
        """Test that error responses follow consistent schema."""
        # Trigger an error by sending invalid data
        invalid_payload = {
            "question": "",  # Empty question should trigger error
            "use_rag": True
        }

        response = client.post("/orchestrate/", json=invalid_payload)

        if response.status_code >= 400:
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
            assert len(data["detail"]) > 0

    def test_response_headers_consistency(self, client):
        """Test that all responses have consistent headers."""
        endpoints = ["/", "/health"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_schema_adherence(self, client):
        """Test that all endpoints adhere to their defined schemas."""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"message", "version", "endpoints", "config"}

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"status", "ollama_available", "rag_store_exists"}
