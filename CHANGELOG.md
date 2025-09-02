# Changelog

All notable changes to **47Chat** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with FastAPI backend and Streamlit frontend
- Multi-agent orchestration system with brainstorming, review, and voting phases
- RAG (Retrieval-Augmented Generation) capabilities with FAISS vector store
- OpenTelemetry observability with structured logging and tracing
- Comprehensive API schema validation with JSON Schema
- Automated testing with pytest, coverage, and property-based testing
- Security hardening with dependency auditing and secrets protection
- Conventional commits and semantic release automation

### Changed
- Migrated to modern Python tooling (uv, Ruff, MyPy)
- Enhanced CI/CD pipeline with quality gates and security scanning

### Technical Improvements
- Added type safety throughout the codebase with strict MyPy configuration
- Implemented comprehensive error handling and logging
- Added performance benchmarking and optimization
- Enhanced API documentation with OpenAPI/Swagger

---

## Types of changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

---

## Release Process

This project uses [semantic-release](https://github.com/python-semantic-release/python-semantic-release)
with [Conventional Commits](https://conventionalcommits.org/) to automate versioning and changelog generation.

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Version Calculation

- `feat:` commits trigger **minor** version bumps (0.1.0 → 0.2.0)
- `fix:` commits trigger **patch** version bumps (0.1.0 → 0.1.1)
- `breaking:` or `!` suffix trigger **major** version bumps (0.1.0 → 1.0.0)

### Examples

```bash
feat: add OpenTelemetry tracing support
fix: resolve memory leak in RAG processing
breaking: remove deprecated API endpoints
```

---

*For older releases, see the [Git history](https://github.com/Hipson47/47Chat/commits/main).*
