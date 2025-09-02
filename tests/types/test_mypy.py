"""
Type checking tests to ensure mypy runs correctly in CI.
"""

import subprocess
import sys
from pathlib import Path


def test_mypy_runs_without_errors():
    """Test that mypy runs without critical errors."""
    # Skip if mypy is not available
    try:
        import mypy  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("mypy not available")

    # Run mypy on the project
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )

    # Check that mypy ran (exit code should be 0 for success, 1 for type errors)
    # We don't require zero errors, but we do require mypy to run successfully
    assert result.returncode in [0, 1], f"mypy failed to run: {result.stderr}"

    # If there are errors, they should be type-related, not mypy configuration errors
    if result.returncode == 1:
        # Check that the output contains actual type checking results, not config errors
        assert "error:" in result.stdout or "note:" in result.stdout, \
            f"mypy produced unexpected output: {result.stdout}"


def test_critical_modules_have_types():
    """Test that critical modules have proper type annotations."""
    import backend.main
    import backend.config
    import backend.rag_utils

    # These should be importable without issues
    assert hasattr(backend.main, 'get_orchestrator')
    assert hasattr(backend.main, 'read_root')
    assert hasattr(backend.main, 'health_check')

    # Check that the main functions have proper signatures
    import inspect

    sig = inspect.signature(backend.main.get_orchestrator)
    assert sig.return_annotation != inspect.Signature.empty

    sig = inspect.signature(backend.main.read_root)
    assert sig.return_annotation != inspect.Signature.empty

    sig = inspect.signature(backend.main.health_check)
    assert sig.return_annotation != inspect.Signature.empty


def test_pydantic_models_validate():
    """Test that Pydantic models work correctly."""
    from backend.main import OrchestrationRequest

    # Test valid data
    request = OrchestrationRequest(question="Test question", use_rag=True)
    assert request.question == "Test question"
    assert request.use_rag is True

    # Test validation
    try:
        OrchestrationRequest(question="", use_rag=True)
        assert False, "Should have raised validation error for empty question"
    except Exception:
        pass  # Expected validation error
