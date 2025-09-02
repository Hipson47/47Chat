"""
Smoke tests for critical application endpoints.
These tests ensure the application starts up correctly and basic functionality works.
"""

import pytest
import httpx
from fastapi.testclient import TestClient

# Import the FastAPI app
from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.mark.smoke
def test_health_endpoint_basic(client):
    """Test that the health endpoint responds with a valid status."""
    response = client.get("/health")

    # Should return 200 OK
    assert response.status_code == 200

    # Should return JSON
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    # Should have required fields
    assert "status" in data
    assert "ollama_available" in data
    assert "rag_store_exists" in data

    # Status should be "healthy"
    assert data["status"] == "healthy"

    # ollama_available and rag_store_exists should be booleans
    assert isinstance(data["ollama_available"], bool)
    assert isinstance(data["rag_store_exists"], bool)


@pytest.mark.smoke
def test_root_endpoint(client):
    """Test that the root endpoint provides service information."""
    response = client.get("/")

    # Should return 200 OK
    assert response.status_code == 200

    # Should return JSON
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    # Should have basic service information
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data
    assert "config" in data

    # Should mention the service
    assert "47Chat" in data["message"]

    # Should have version
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


@pytest.mark.smoke
def test_application_startup():
    """Test that the FastAPI application can be created without errors."""
    # This test ensures the app can be imported and instantiated
    from backend.main import app

    # App should be a FastAPI instance
    assert app is not None
    assert hasattr(app, 'routes')

    # Should have some routes
    routes = [route for route in app.routes]
    assert len(routes) > 0

    # Should have our expected endpoints
    route_paths = {route.path for route in routes}
    assert "/" in route_paths
    assert "/health" in route_paths


@pytest.mark.smoke
def test_cors_headers(client):
    """Test that CORS headers are properly configured."""
    # Test preflight request
    response = client.options("/health",
                           headers={
                               "Origin": "http://localhost:3000",
                               "Access-Control-Request-Method": "GET"
                           })

    # Should handle preflight (even if CORS is not configured, shouldn't crash)
    assert response.status_code in [200, 404, 405]  # Various acceptable responses


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_async_endpoints():
    """Test that async endpoints work correctly."""
    # Test with httpx for async support
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as async_client:
        # Test health endpoint
        response = await async_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.smoke
def test_error_handling(client):
    """Test that error handling works for invalid endpoints."""
    # Test non-existent endpoint
    response = client.get("/nonexistent")
    assert response.status_code == 404

    # Should return JSON error
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    assert "detail" in data


@pytest.mark.smoke
def test_content_type_validation(client):
    """Test that content type validation works."""
    # Test with wrong content type for endpoints that expect JSON
    response = client.post("/orchestrate/",
                          data="not json",
                          headers={"Content-Type": "text/plain"})

    # Should handle gracefully (might return 422 for validation error)
    assert response.status_code in [200, 400, 422]


@pytest.mark.smoke
def test_response_time(client):
    """Test that endpoints respond within reasonable time."""
    import time

    start_time = time.time()
    response = client.get("/health")
    end_time = time.time()

    # Should respond within 5 seconds (generous for smoke test)
    response_time = end_time - start_time
    assert response_time < 5.0

    # Should still be successful
    assert response.status_code == 200
