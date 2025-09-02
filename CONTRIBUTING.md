# Contributing to 47Chat

Welcome! This document provides guidelines for contributing to the 47Chat project.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or later
- Git

### Development Setup

We use [`uv`](https://github.com/astral-sh/uv) for fast, reliable Python package management.

#### 1. Install uv

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. Clone and Setup

```bash
git clone https://github.com/Hipson47/47Chat.git
cd 47Chat

# Create virtual environment (optional, uv can manage this)
uv venv

# Sync dependencies
uv pip sync requirements.txt requirements-dev.txt
```

#### 3. Verify Installation

```bash
# Check that everything is working
python -c "import fastapi, streamlit; print('✅ Dependencies installed successfully')"

# Run linting
python -m ruff check .

# Or use uv tool run for one-off usage
python -m uv tool run ruff check .

# Run type checking
python -m mypy .
```

## 🛠️ Development Workflow

### Code Quality

This project uses several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checker
- **Pytest**: Test runner
- **Safety**: Dependency vulnerability scanner

### Running Quality Checks

```bash
# Format code
python -m ruff format .

# Lint code
python -m ruff check .

# Fix auto-fixable issues
python -m ruff check --fix .

# Type check
python -m mypy .

# Run tests
python -m pytest

# Security scan
python -m safety check
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

## 📦 Dependency Management

### Adding Dependencies

1. **Runtime dependencies**: Add to `pyproject.toml` under `[project.dependencies]`
2. **Development dependencies**: Add to `pyproject.toml` under `[project.optional-dependencies.dev]`
3. **Regenerate requirements files**:
   ```bash
   # After updating pyproject.toml, regenerate requirements files
   # (This step will be automated in CI)
   uv pip compile pyproject.toml -o requirements.txt
   uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
   ```

### Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
uv lock --upgrade

# Update specific package
uv lock --upgrade-package <package-name>

# Sync with updated lockfile
uv pip sync requirements.txt requirements-dev.txt
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest backend/orchestrator/tests/test_rag.py

# Run with coverage
python -m pytest --cov=backend --cov=frontend

# Run tests in verbose mode
python -m pytest -v
```

### Writing Tests

- Tests should be placed in `backend/tests/` or `frontend/tests/`
- Test files should follow the pattern `test_*.py`
- Use descriptive test names and docstrings
- Mock external dependencies when possible

## 🚀 Local Development

### Running the Application

```bash
# Start both backend and frontend
./start_local.bat

# Or manually:
# Terminal 1 - Backend
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
python -m streamlit run frontend/app.py --server.port 8501
```

### API Documentation

Once the backend is running, visit:
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:8501

## 📝 Code Style

### Python Style
- Follow PEP 8 with some modifications
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (enforced by Ruff)
- Use double quotes for strings

### Commit Messages

47Chat uses [Conventional Commits](https://conventionalcommits.org/) to enable automated versioning and changelog generation. All commit messages must follow this format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types

| Type | Description | Version Impact |
|------|-------------|----------------|
| `feat` | New feature | **Minor** (0.1.0 → 0.2.0) |
| `fix` | Bug fix | **Patch** (0.1.0 → 0.1.1) |
| `breaking` | Breaking change | **Major** (0.1.0 → 1.0.0) |
| `docs` | Documentation only | No version change |
| `style` | Code style/formatting | No version change |
| `refactor` | Code refactoring | No version change |
| `perf` | Performance improvement | **Patch** (0.1.0 → 0.1.1) |
| `test` | Testing related | No version change |
| `build` | Build system/CI | No version change |
| `ci` | CI/CD changes | No version change |
| `chore` | Maintenance tasks | No version change |

#### Examples

```bash
# Feature commits
feat: add OpenTelemetry tracing support
feat(auth): implement JWT token validation
feat(api): add health check endpoint

# Fix commits
fix: resolve memory leak in RAG processing
fix(api): handle empty request bodies gracefully
fix(frontend): correct button alignment in mobile view

# Breaking changes
breaking: remove deprecated API endpoints
breaking(auth): change password hashing algorithm

# Other types
docs: update API documentation for health endpoints
style: format code with ruff
refactor: extract common utilities to shared module
perf: optimize vector search with FAISS indexing
test: add comprehensive API schema validation tests
build: update Python version requirement
ci: add semantic release configuration
chore: update dependency versions
```

#### Breaking Changes

For breaking changes, use either:

```bash
breaking: remove deprecated API endpoints
feat!: add new authentication system (replaces old one)
fix!: change response format (breaks existing clients)
```

#### Scope (Optional)

Scopes help categorize commits:

```bash
feat(api): add new endpoint
fix(frontend): resolve UI bug
docs(readme): update installation instructions
```

Common scopes:
- `api` - API/backend changes
- `frontend` - Frontend/UI changes
- `auth` - Authentication/authorization
- `db` - Database changes
- `docs` - Documentation
- `ci` - CI/CD pipeline
- `deps` - Dependencies

#### Body and Footer

For complex changes, add a body:

```bash
feat: add multi-agent orchestration

This implements the core orchestration logic that coordinates
multiple AI agents through brainstorming, review, and voting phases.

The implementation includes:
- Agent role assignment
- Phase transition management
- Consensus building algorithms

BREAKING CHANGE: The API response format has changed
```

### Release Process

47Chat uses automated semantic versioning with [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release):

#### How Releases Work

1. **Commit Analysis**: Every commit to `main` is analyzed for conventional commit format
2. **Version Calculation**: Based on commit types, the next version is calculated:
   - `feat` commits → Minor version bump
   - `fix` commits → Patch version bump
   - `breaking` commits → Major version bump
3. **Changelog Generation**: Automatic changelog generation from commit messages
4. **Package Building**: Automatic wheel and source distribution creation
5. **GitHub Release**: Automatic GitHub release creation with artifacts
6. **PyPI Publishing**: Optional PyPI package publishing

#### Release Examples

```bash
# After merging a feature branch
Input: feat: add OpenTelemetry tracing
Result: Version 0.1.0 → 0.2.0, GitHub release created

# After merging a bug fix
Input: fix: resolve memory leak in RAG processing
Result: Version 0.2.0 → 0.2.1, patch release

# After breaking changes
Input: breaking: remove deprecated API endpoints
Result: Version 0.2.1 → 1.0.0, major release
```

#### Manual Release

You can also trigger releases manually:

```bash
# Force a specific release type
semantic-release --major  # Force major version
semantic-release --minor  # Force minor version
semantic-release --patch  # Force patch version
```

#### Release Validation

Before merging to main:
- ✅ All commits follow conventional format
- ✅ CI checks pass (tests, linting, type checking)
- ✅ Breaking changes are clearly documented
- ✅ Commit messages are descriptive and actionable

#### Post-Release

After a release is created:
- 📦 Package is published to PyPI (if configured)
- 🚀 GitHub release is created with changelog
- 📋 CHANGELOG.md is automatically updated
- 🏷️ Git tag is created (e.g., `v1.0.0`)
- 📧 Release notifications can be configured

### Pull Requests
- Create descriptive PR titles and descriptions
- Reference any related issues
- Ensure all CI checks pass
- Request review from maintainers

## 🔧 Troubleshooting

### Common Issues

**uv command not found**
```bash
# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart your shell
```

**Dependencies not syncing**
```bash
# Clear uv cache
uv cache clean
# Try again
uv pip sync requirements.txt requirements-dev.txt
```

**Pre-commit hooks not working**
```bash
# Reinstall hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

## 📚 Resources

- [Project Documentation](./README.md)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🤝 Getting Help

If you need help:
1. Check this document first
2. Search existing issues on GitHub
3. Create a new issue with detailed information
4. Join our community discussions

## 🔒 Security Guidelines

### Secure Development Practices

#### Code Security
- **Input Validation**: Always validate user inputs using Pydantic models
- **Avoid Dangerous Patterns**: Never use `eval()`, `exec()`, or `subprocess(..., shell=True)` with user input
- **Secure Dependencies**: Review new dependencies for known vulnerabilities
- **Type Safety**: Use MyPy strict mode to catch type-related security issues

#### Secrets and Credentials
- **Never Commit Secrets**: Use environment variables for sensitive data
- **Environment Files**: Store secrets in `.env` files (automatically excluded from git)
- **API Keys**: Use secure storage mechanisms for API keys and tokens
- **Credential Rotation**: Regularly rotate API keys and credentials

### Security Testing

#### Automated Security Checks
```bash
# Run all security scans
python -m safety check
pip-audit --strict

# Check for secrets in code
git grep -i "password\|secret\|key\|token" -- "*.py"
```

#### Manual Security Review
- **Dependency Review**: Check new dependencies against vulnerability databases
- **Code Review**: Look for CWE patterns in pull requests
- **Secrets Audit**: Ensure no credentials are committed

### Reporting Security Vulnerabilities

#### Process
1. **Do not create public issues** for security vulnerabilities
2. **Contact maintainers directly** with security concerns
3. **Provide detailed information** about the vulnerability
4. **Allow time for remediation** before public disclosure

#### Responsible Disclosure
- Give maintainers reasonable time to fix issues
- Avoid accessing or modifying user data
- Don't perform DoS attacks or degrade service performance
- Keep vulnerability details confidential until fixed

### Security Tools

#### Required Tools
- **pip-audit**: Automated dependency vulnerability scanning
- **Safety**: Additional dependency security checks
- **MyPy**: Type safety and security through typing
- **Ruff**: Code quality and security linting

#### CI/CD Security
- Automated security scans on every push
- Dependency vulnerability monitoring
- Secrets detection in CI pipeline
- Security-focused code analysis

### Security Checklist

#### Before Committing
- [ ] No secrets or credentials in code
- [ ] All inputs properly validated
- [ ] Dependencies checked for vulnerabilities
- [ ] Type annotations complete
- [ ] Security patterns avoided

#### Before Merging
- [ ] Security review completed
- [ ] CI security checks pass
- [ ] No new high/critical vulnerabilities
- [ ] Secrets properly excluded from version control

### Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Database](https://cwe.mitre.org/)
- [PyPI Advisory Database](https://github.com/pypa/advisory-database)
- [Python Security Best Practices](https://bestpractices.coreinfrastructure.org/en/projects/2233)

Thank you for contributing to 47Chat! 🎉
