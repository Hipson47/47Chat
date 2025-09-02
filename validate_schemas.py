#!/usr/bin/env python3
"""
Simple validation script for API schema enforcement.
Tests that strict contracts are working correctly.
"""

import sys
import json
from pathlib import Path

def test_json_schemas():
    """Test that JSON schemas are valid JSON and have required structure."""
    schema_dir = Path("schemas/v1")

    if not schema_dir.exists():
        print("❌ Schemas directory not found")
        return False

    schemas = [
        "orchestration_request.json",
        "orchestration_response.json",
        "health_response.json",
        "root_response.json",
        "upload_response.json",
        "error_response.json"
    ]

    for schema_file in schemas:
        schema_path = schema_dir / schema_file
        if not schema_path.exists():
            print(f"❌ Schema file missing: {schema_file}")
            return False

        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)

            # Check required fields
            if "$schema" not in schema:
                print(f"❌ Missing $schema in {schema_file}")
                return False

            if "type" not in schema:
                print(f"❌ Missing type in {schema_file}")
                return False

            if "additionalProperties" not in schema:
                print(f"❌ Missing additionalProperties in {schema_file}")
                return False

            if schema.get("additionalProperties") is not False:
                print(f"❌ additionalProperties not set to false in {schema_file}")
                return False

            print(f"✅ {schema_file} is valid")

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {schema_file}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading {schema_file}: {e}")
            return False

    return True

def test_pydantic_models():
    """Test that Pydantic models have strict validation."""
    try:
        from backend.main import OrchestrationRequest, HealthResponse

        # Test 1: Valid model
        valid = OrchestrationRequest(question="Test question", use_rag=True)
        print("✅ Valid OrchestrationRequest created")

        # Test 2: Extra field should fail
        try:
            invalid = OrchestrationRequest(question="Test", use_rag=True, extra="field")
            print("❌ Extra field was accepted (should fail)")
            return False
        except Exception:
            print("✅ Extra field correctly rejected")

        # Test 3: Missing required field should fail
        try:
            missing = OrchestrationRequest(use_rag=True)
            print("❌ Missing required field was accepted (should fail)")
            return False
        except Exception:
            print("✅ Missing required field correctly rejected")

        # Test 4: Empty question should fail
        try:
            empty = OrchestrationRequest(question="", use_rag=True)
            print("❌ Empty question was accepted (should fail)")
            return False
        except Exception:
            print("✅ Empty question correctly rejected")

        return True

    except ImportError as e:
        print(f"❌ Could not import models: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

def test_fastapi_integration():
    """Test that FastAPI endpoints use the correct response models."""
    try:
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)

        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            required_fields = {"status", "ollama_available", "rag_store_exists"}
            if set(data.keys()) == required_fields:
                print("✅ Health endpoint returns correct schema")
            else:
                print(f"❌ Health endpoint missing/extra fields: {set(data.keys()) ^ required_fields}")
                return False
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False

        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            data = response.json()
            required_fields = {"message", "version", "endpoints", "config"}
            if set(data.keys()) == required_fields:
                print("✅ Root endpoint returns correct schema")
            else:
                print(f"❌ Root endpoint missing/extra fields: {set(data.keys()) ^ required_fields}")
                return False
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False

        # Test extra field rejection
        malicious_payload = {
            "question": "Test question",
            "use_rag": True,
            "isAdmin": True
        }
        response = client.post("/orchestrate/", json=malicious_payload)
        if response.status_code == 422:
            print("✅ Orchestration endpoint rejects extra fields")
        else:
            print(f"❌ Orchestration endpoint accepted extra fields: {response.status_code}")
            return False

        return True

    except Exception as e:
        print(f"❌ Error testing FastAPI integration: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🔒 Validating API Schema Enforcement\n")

    tests = [
        ("JSON Schemas", test_json_schemas),
        ("Pydantic Models", test_pydantic_models),
        ("FastAPI Integration", test_fastapi_integration),
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

    print("
📊 Validation Results:"    print(f"   Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All schema enforcement validations passed!")
        print("\n🛡️ Security Features Confirmed:")
        print("  ✅ JSON Schema contracts with additionalProperties: false")
        print("  ✅ Pydantic models with strict validation")
        print("  ✅ FastAPI response models enforcing contracts")
        print("  ✅ Extra field rejection working correctly")
        print("  ✅ Required field validation enforced")
        return True
    else:
        print("\n❌ Some validations failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
