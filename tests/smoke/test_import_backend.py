"""
Smoke test for backend package imports.
Ensures that the backend.main module can be imported without errors.
"""

import pytest


def test_import_backend_main():
    """Test that backend.main can be imported successfully."""
    try:
        import backend.main
        # Verify that the app object exists
        assert hasattr(backend.main, 'app')
        assert backend.main.app is not None
    except ImportError as e:
        pytest.fail(f"Failed to import backend.main: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing backend.main: {e}")


def test_import_backend_config():
    """Test that backend.config can be imported successfully."""
    try:
        import backend.config
        # Verify that settings object exists
        assert hasattr(backend.config, 'settings')
        assert backend.config.settings is not None
    except ImportError as e:
        pytest.fail(f"Failed to import backend.config: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing backend.config: {e}")


def test_import_backend_orchestrator():
    """Test that backend.orchestrator modules can be imported successfully."""
    try:
        import backend.orchestrator.agent
        # Verify that the main class exists
        assert hasattr(backend.orchestrator.agent, 'OrchestratorAgent')
    except ImportError as e:
        pytest.fail(f"Failed to import backend.orchestrator.agent: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing backend.orchestrator.agent: {e}")


def test_import_backend_rag_utils():
    """Test that backend.rag_utils can be imported successfully."""
    try:
        import backend.rag_utils
        # Verify that the main class exists
        assert hasattr(backend.rag_utils, 'RAGUtils')
    except ImportError as e:
        pytest.fail(f"Failed to import backend.rag_utils: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing backend.rag_utils: {e}")


def test_import_backend_observability():
    """Test that backend.observability modules can be imported successfully."""
    try:
        import backend.observability.logging
        import backend.observability.tracing
        import backend.observability.metrics
        import backend.observability.middleware

        # Verify that key functions/classes exist
        assert hasattr(backend.observability.logging, 'setup_logging')
        assert hasattr(backend.observability.tracing, 'setup_tracing')
        assert hasattr(backend.observability.metrics, 'get_metrics_collector')
        assert hasattr(backend.observability.middleware, 'RequestTrackingMiddleware')
    except ImportError as e:
        # Observability modules are optional, so skip test if dependencies not installed
        pytest.skip(f"Observability modules not available (dependencies not installed): {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing backend.observability modules: {e}")


def test_backend_package_structure():
    """Test that the backend package has proper structure."""
    try:
        import backend
        # Verify package version
        assert hasattr(backend, '__version__')
        assert isinstance(backend.__version__, str)
        assert len(backend.__version__) > 0
    except ImportError as e:
        pytest.fail(f"Failed to import backend package: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error with backend package: {e}")


def test_backend_main_app_creation():
    """Test that the FastAPI app can be created without errors."""
    try:
        import backend.main
        # The app should be created during import
        app = backend.main.app

        # Verify it's a FastAPI app
        assert app is not None
        assert hasattr(app, 'routes')
        assert hasattr(app, 'add_middleware')
        assert hasattr(app, 'add_route')

        # Check that some routes exist
        routes = list(app.routes)
        assert len(routes) > 0

        # Check for expected routes
        route_paths = {route.path for route in routes}
        expected_paths = {"/", "/health", "/orchestrate/", "/upload/", "/metrics"}
        assert expected_paths.issubset(route_paths), f"Missing routes: {expected_paths - route_paths}"

    except ImportError as e:
        pytest.fail(f"Failed to create FastAPI app: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error creating FastAPI app: {e}")
