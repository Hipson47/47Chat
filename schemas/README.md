# 47Chat API Schemas

This directory contains versioned JSON Schema definitions for all 47Chat API contracts.

## 📁 Directory Structure

```
schemas/
├── v1/                          # Version 1 schemas (JSON Schema Draft 2020-12)
│   ├── orchestration_request.json    # POST /orchestrate/ request schema
│   ├── orchestration_response.json   # POST /orchestrate/ response schema
│   ├── health_response.json          # GET /health response schema
│   ├── root_response.json            # GET / response schema
│   ├── upload_response.json          # POST /upload/ response schema
│   ├── error_response.json           # Error response schema
│   └── index.json                    # Schema registry and endpoint mapping
└── README.md                 # This file
```

## 🛡️ Schema Enforcement Features

All schemas implement strict validation with:

- **`additionalProperties: false`** - Rejects any extra fields not defined in schema
- **Required field validation** - Ensures all mandatory fields are present
- **Type validation** - Enforces correct data types
- **Pattern validation** - Validates string formats (e.g., semantic versioning)
- **Length constraints** - Enforces min/max lengths where appropriate
- **Enum validation** - Restricts values to predefined sets

## 🔗 Schema-to-Model Mapping

Each JSON schema corresponds to a Pydantic model in `backend/main.py`:

| Schema File | Pydantic Model | Endpoint |
|-------------|----------------|----------|
| `orchestration_request.json` | `OrchestrationRequest` | `POST /orchestrate/` |
| `orchestration_response.json` | `OrchestrationResponse` | `POST /orchestrate/` |
| `health_response.json` | `HealthResponse` | `GET /health` |
| `root_response.json` | `RootResponse` | `GET /` |
| `upload_response.json` | `UploadResponse` | `POST /upload/` |
| `error_response.json` | N/A (HTTP status codes) | All endpoints |

## 🧪 Testing Schema Enforcement

Comprehensive tests in `tests/api/test_schema_enforcement.py` validate:

- ✅ **Valid payloads** are accepted
- ✅ **Missing required fields** are rejected (422)
- ✅ **Extra properties** are rejected (422)
- ✅ **Wrong data types** are rejected (422)
- ✅ **Invalid formats/patterns** are rejected (422)
- ✅ **Security attacks** (XSS, SQL injection, etc.) are handled safely

## 🚀 Usage Examples

### Valid Request
```json
{
  "question": "How can I improve my application architecture?",
  "use_rag": true
}
```

### Rejected Request (Extra Field)
```json
{
  "question": "How can I improve my application architecture?",
  "use_rag": true,
  "isAdmin": true  // ❌ Rejected: additionalProperties: false
}
```

### Valid Response
```json
{
  "status": "healthy",
  "ollama_available": true,
  "rag_store_exists": true
}
```

## 🔒 Security Benefits

- **Prevents data injection attacks** by rejecting extra fields
- **Ensures API contract compliance** across versions
- **Provides clear error messages** for invalid requests
- **Enables automated validation** in CI/CD pipelines
- **Supports API documentation** generation from schemas

## 📋 Schema Versioning

- **v1**: Initial schema version (JSON Schema Draft 2020-12)
- Future versions will be added as `v2/`, `v3/`, etc.
- Breaking changes require new major versions
- Backward-compatible changes can be made within the same version

## 🛠️ Development

### Adding New Schemas

1. Create new `.json` file in appropriate version directory
2. Follow JSON Schema Draft 2020-12 specification
3. Include `additionalProperties: false`
4. Update `index.json` with new schema reference
5. Create corresponding Pydantic model
6. Add comprehensive tests

### Validating Schemas

```bash
# Validate JSON syntax
python -c "import json; json.load(open('schemas/v1/health_response.json'))"

# Test against actual API
python -m pytest tests/api/test_schema_enforcement.py -v
```

## 📚 Related Files

- `backend/main.py` - Pydantic models and FastAPI endpoints
- `tests/api/test_schema_enforcement.py` - Schema enforcement tests
- `pyproject.toml` - Test configuration with coverage requirements
