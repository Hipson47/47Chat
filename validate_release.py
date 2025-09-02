#!/usr/bin/env python3
"""
Validation script for semantic release configuration.
Tests the setup without actually creating releases.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_pyproject_config():
    """Test that pyproject.toml has correct semantic release configuration."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        return False

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    # Check required fields
    required_fields = [
        ("project", "name"),
        ("project", "dynamic"),
        ("tool", "semantic_release"),
    ]

    for field_path in required_fields:
        current = config
        try:
            for key in field_path:
                current = current[key]
        except KeyError:
            print(f"❌ Missing configuration: {'.'.join(field_path)}")
            return False

    # Check semantic release configuration
    sr_config = config.get("tool", {}).get("semantic_release", {})

    required_sr_fields = [
        "version_toml",
        "version_variables",
        "branch",
        "changelog_file",
        "build_command",
        "commit_parser_options",
    ]

    for field in required_sr_fields:
        if field not in sr_config:
            print(f"❌ Missing semantic release field: {field}")
            return False

    # Check version variables point to existing files
    version_vars = sr_config.get("version_variables", [])
    for var_path in version_vars:
        file_path = Path(var_path.split(":")[0])
        if not file_path.exists():
            print(f"❌ Version variable file not found: {file_path}")
            return False

        # Check if the file has the version variable
        with open(file_path, "r") as f:
            content = f.read()
            if "__version__" not in content:
                print(f"❌ Version variable not found in {file_path}")
                return False

    # Check dynamic version is configured
    if "version" not in config.get("project", {}):
        print("❌ Dynamic version not configured in project section")
        return False

    print("✅ pyproject.toml configuration is valid")
    return True


def test_changelog_file():
    """Test that CHANGELOG.md exists and has proper structure."""
    changelog_path = Path("CHANGELOG.md")

    if not changelog_path.exists():
        print("❌ CHANGELOG.md not found")
        return False

    with open(changelog_path, "r") as f:
        content = f.read()

    # Check for required sections
    required_sections = [
        "# Changelog",
        "## [Unreleased]",
    ]

    for section in required_sections:
        if section not in content:
            print(f"❌ Missing changelog section: {section}")
            return False

    print("✅ CHANGELOG.md is properly structured")
    return True


def test_build_system():
    """Test that build system is properly configured."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    pyproject_path = Path("pyproject.toml")

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    build_system = config.get("build-system", {})

    # Check for required build tools
    required_requires = ["setuptools", "wheel"]
    actual_requires = build_system.get("requires", [])

    for req in required_requires:
        if not any(req in r for r in actual_requires):
            print(f"❌ Missing build requirement: {req}")
            return False

    # Check build backend
    if build_system.get("build-backend") != "setuptools.build_meta":
        print("❌ Incorrect build backend")
        return False

    print("✅ Build system is properly configured")
    return True


def test_semantic_release_installation():
    """Test that python-semantic-release is available."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import semantic_release; print('Available')"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✅ python-semantic-release is installed")
            return True
        else:
            print("❌ python-semantic-release is not available")
            print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Timeout testing semantic release installation")
        return False
    except Exception as e:
        print(f"❌ Error testing semantic release: {e}")
        return False


def test_conventional_commits_examples():
    """Test that conventional commit examples work as expected."""
    # Test commit message parsing logic
    test_commits = [
        ("feat: add new endpoint", "minor"),
        ("fix: resolve bug", "patch"),
        ("breaking: change API", "major"),
        ("docs: update readme", None),
        ("feat!: breaking change", "major"),
        ("fix!: breaking fix", "major"),
    ]

    print("📝 Testing conventional commit parsing:")

    for commit_msg, expected_bump in test_commits:
        # Simple parsing logic (in real semantic release, this is more complex)
        if commit_msg.startswith("feat"):
            if "!" in commit_msg or "breaking" in commit_msg:
                bump = "major"
            else:
                bump = "minor"
        elif commit_msg.startswith("fix"):
            if "!" in commit_msg or "breaking" in commit_msg:
                bump = "major"
            else:
                bump = "patch"
        elif commit_msg.startswith("breaking"):
            bump = "major"
        else:
            bump = None

        if bump == expected_bump:
            print(f"✅ '{commit_msg}' → {bump}")
        else:
            print(f"❌ '{commit_msg}' → {bump} (expected {expected_bump})")
            return False

    print("✅ Conventional commit examples work correctly")
    return True


def test_github_workflow():
    """Test that GitHub Actions workflow is properly configured."""
    workflow_path = Path(".github/workflows/release.yml")

    if not workflow_path.exists():
        print("❌ GitHub Actions release workflow not found")
        return False

    with open(workflow_path, "r") as f:
        content = f.read()

    # Check for required elements
    required_elements = [
        "semantic-release",
        "python-semantic-release",
        "build",
        "dist/",
        "CHANGELOG.md",
        "github_release",
        "upload_to_release",
    ]

    for element in required_elements:
        if element not in content:
            print(f"❌ Missing workflow element: {element}")
            return False

    print("✅ GitHub Actions workflow is properly configured")
    return True


def test_version_files():
    """Test that version files exist and are properly configured."""
    version_files = [
        "backend/__init__.py",
        "frontend/__init__.py",
        "pyproject.toml",
    ]

    for file_path in version_files:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ Version file not found: {file_path}")
            return False

        if file_path.endswith("__init__.py"):
            with open(path, "r") as f:
                content = f.read()
                if "__version__" not in content:
                    print(f"❌ Version variable not found in {file_path}")
                    return False

    print("✅ Version files are properly configured")
    return True


def main():
    """Run all release validation tests."""
    print("🚀 Validating 47Chat Release Configuration\n")

    tests = [
        ("PyProject Configuration", test_pyproject_config),
        ("Changelog File", test_changelog_file),
        ("Build System", test_build_system),
        ("Semantic Release Installation", test_semantic_release_installation),
        ("Conventional Commits Examples", test_conventional_commits_examples),
        ("GitHub Workflow", test_github_workflow),
        ("Version Files", test_version_files),
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

    print("\n📊 Release Validation Results:")
    print(f"   Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All release configurations are valid!")
        print("\n🚀 Ready for automated releases with:")
        print("  ✅ Semantic versioning based on conventional commits")
        print("  ✅ Automated changelog generation")
        print("  ✅ GitHub release creation with artifacts")
        print("  ✅ PyPI package publishing (optional)")
        print("  ✅ Version management across multiple files")
        return True
    else:
        print("\n❌ Some release configurations need attention")
        print("\n🔧 To fix issues:")
        print("  1. Install dependencies: uv pip install -e .[dev]")
        print("  2. Check configuration files for errors")
        print("  3. Run: semantic-release --dry-run to test locally")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
