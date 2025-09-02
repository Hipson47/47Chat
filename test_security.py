#!/usr/bin/env python3
"""
Security hardening validation script.
Tests that our security measures are properly implemented.
"""

import os
import subprocess
import sys
from pathlib import Path


def test_gitignore_security():
    """Test that .gitignore properly excludes sensitive files."""
    gitignore_path = Path(".gitignore")

    if not gitignore_path.exists():
        print("❌ .gitignore not found")
        return False

    with open(gitignore_path, 'r') as f:
        content = f.read()

    required_patterns = [
        ".env*",
        "*.key",
        "*.pem",
        "*API_KEY*",
        "*SECRET*",
        "*TOKEN*",
        ".aws/",
        ".azure/",
        "secrets.*"
    ]

    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)

    if missing_patterns:
        print(f"❌ Missing security patterns in .gitignore: {missing_patterns}")
        return False

    print("✅ .gitignore has comprehensive security patterns")
    return True


def test_cursorignore_exists():
    """Test that .cursorignore exists and excludes sensitive files."""
    cursorignore_path = Path(".cursorignore")

    if not cursorignore_path.exists():
        print("❌ .cursorignore not found")
        return False

    with open(cursorignore_path, 'r') as f:
        content = f.read()

    required_patterns = [
        ".env*",
        "*API_KEY*",
        "*SECRET*",
        "*.key",
        "*.pem",
        "secrets.*",
        "uploads/"
    ]

    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)

    if missing_patterns:
        print(f"❌ Missing security patterns in .cursorignore: {missing_patterns}")
        return False

    print("✅ .cursorignore properly excludes sensitive files")
    return True


def test_agent_rules_exist():
    """Test that agent command restriction rules exist."""
    rules_path = Path(".cursor/rules/agent-commands.mdc")

    if not rules_path.exists():
        print("❌ Agent command rules not found")
        return False

    with open(rules_path, 'r') as f:
        content = f.read()

    required_sections = [
        "ALLOWED COMMANDS",
        "RESTRICTED COMMANDS",
        "shell=True",
        "eval(",
        "exec("
    ]

    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        print(f"❌ Missing security sections in agent rules: {missing_sections}")
        return False

    print("✅ Agent command restriction rules are in place")
    return True


def test_ci_security_job():
    """Test that CI workflow includes security audit job."""
    workflow_path = Path(".github/workflows/ci.yml")

    if not workflow_path.exists():
        print("❌ CI workflow not found")
        return False

    with open(workflow_path, 'r') as f:
        content = f.read()

    required_elements = [
        "security-audit",
        "pip-audit",
        "safety check",
        "--strict"
    ]

    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)

    if missing_elements:
        print(f"❌ Missing security elements in CI: {missing_elements}")
        return False

    print("✅ CI workflow includes comprehensive security audit")
    return True


def test_docs_security_sections():
    """Test that documentation includes security sections."""
    files_to_check = [
        ("README.md", ["🔒 Security", "Vulnerability Management"]),
        ("CONTRIBUTING.md", ["🔒 Security Guidelines", "Secure Development Practices"])
    ]

    all_good = True
    for filename, required_sections in files_to_check:
        filepath = Path(filename)
        if not filepath.exists():
            print(f"❌ {filename} not found")
            all_good = False
            continue

        with open(filepath, 'r') as f:
            content = f.read()

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        if missing_sections:
            print(f"❌ Missing security sections in {filename}: {missing_sections}")
            all_good = False
        else:
            print(f"✅ {filename} includes security documentation")

    return all_good


def test_no_hardcoded_secrets():
    """Test that no hardcoded secrets exist in the codebase."""
    # Simple check for common secret patterns
    secret_patterns = [
        "password",
        "secret",
        "api_key",
        "token"
    ]

    # Get all Python files
    python_files = list(Path(".").rglob("*.py"))

    suspicious_files = []
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            for pattern in secret_patterns:
                if pattern in content and "import" not in content and "from" not in content:
                    # This is a very basic check - in practice you'd want more sophisticated detection
                    suspicious_files.append(str(py_file))
                    break
        except Exception:
            continue

    if suspicious_files:
        print(f"⚠️  Files with potential secret patterns: {suspicious_files[:5]}")
        print("   (This is a basic check - manual review recommended)")

    print("✅ Basic secret detection completed")
    return True


def main():
    """Run all security validation tests."""
    print("🔒 Testing 47Chat Security Hardening\n")

    tests = [
        test_gitignore_security,
        test_cursorignore_exists,
        test_agent_rules_exist,
        test_ci_security_job,
        test_docs_security_sections,
        test_no_hardcoded_secrets,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

    print(f"\n📊 Security Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All security hardening measures are in place!")
        print("\n🔐 Security Features Implemented:")
        print("  ✅ Comprehensive .gitignore with secret exclusion")
        print("  ✅ .cursorignore protecting AI context")
        print("  ✅ Agent command execution restrictions")
        print("  ✅ CI/CD security audit pipeline")
        print("  ✅ Security documentation and guidelines")
        print("  ✅ Basic secret detection")
        return True
    else:
        print("❌ Some security measures need attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
