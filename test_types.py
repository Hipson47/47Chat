#!/usr/bin/env python3
"""
Simple test script to verify type annotations and Pydantic models work correctly.
"""

def test_basic_imports():
    """Test that all modules can be imported without issues."""
    try:
        import backend.main
        import backend.config
        import backend.rag_utils
        from backend.orchestrator.utils.loader import load_meta_prompt
        from backend.orchestrator.utils.team_assigner import auto_assign_teams
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_pydantic_model():
    """Test that Pydantic models work correctly."""
    try:
        from backend.main import OrchestrationRequest

        # Test valid data
        request = OrchestrationRequest(question="Test question", use_rag=True)
        assert request.question == "Test question"
        assert request.use_rag is True

        print("✅ Pydantic model validation works")
        return True
    except Exception as e:
        print(f"❌ Pydantic model test failed: {e}")
        return False

def test_type_annotations():
    """Test that type annotations are present."""
    try:
        import inspect
        import backend.main

        # Check function signatures
        sig = inspect.signature(backend.main.get_orchestrator)
        assert sig.return_annotation != inspect.Signature.empty

        sig = inspect.signature(backend.main.read_root)
        assert sig.return_annotation != inspect.Signature.empty

        sig = inspect.signature(backend.main.health_check)
        assert sig.return_annotation != inspect.Signature.empty

        print("✅ Type annotations are present")
        return True
    except Exception as e:
        print(f"❌ Type annotation test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing type safety improvements...")

    tests = [
        test_basic_imports,
        test_pydantic_model,
        test_type_annotations,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All type safety tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed")
        exit(1)
