# 47Chat - AI Multi-Agent Orchestrator

## 🎯 Project Purpose

47Chat is an advanced AI-driven orchestrator bot designed for intelligent multi-agent task execution. It combines FastAPI backend services, local Ollama LLM integration, optional OpenAI API, and Retrieval-Augmented Generation (RAG) to create a sophisticated multi-agent discussion system.

The orchestrator coordinates specialized AI "alters" (experts) organized into teams, running structured discussions through multiple phases (Brainstorm, CriticalReview, SelfVerify, Vote) to provide comprehensive, well-reasoned responses to complex questions.

## 🏗️ Architecture Overview

### Main Services

- **Backend**: FastAPI-based REST API (`backend/main.py`)
  - Port: 8000 (configurable via `BACKEND_PORT` environment variable)
  - Host: 127.0.0.1 (configurable via `BACKEND_HOST`)
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health

- **Frontend**: Streamlit-based web interface (`frontend/app.py`)
  - Port: 8501
  - Host: 127.0.0.1
  - URL: http://localhost:8501

### Key Components

- **Multi-Agent Orchestrator**: Coordinates AI agents through structured discussion phases
- **RAG System**: Document ingestion and retrieval using FAISS vector store
- **LLM Integration**: Support for both Ollama (local) and OpenAI (cloud) models
- **Document Processing**: Support for PDF, Markdown, and text files

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Ollama (for local LLM models)
- Git

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone https://github.com/Hipson47/47Chat.git
   cd 47Chat
   ```

2. **Install dependencies**:
   ```bash
   # Install uv (fast Python package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Sync dependencies
   uv pip sync requirements.txt requirements-dev.txt
   ```

3. **Set up Ollama**:
   ```bash
   ollama pull llama3
   ollama serve
   ```

4. **Start the application**:
   ```bash
   # One-click startup (Windows)
   .\start_local.bat

   # Or manually:
   # Backend (Terminal 1)
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

   # Frontend (Terminal 2)
   python -m streamlit run frontend/app.py --server.port 8501
   ```

### Ports Configuration

| Service | Default Port | Environment Variable | URL |
|---------|-------------|---------------------|-----|
| Backend API | 8000 | `BACKEND_PORT` | http://localhost:8000 |
| Frontend UI | 8501 | `FRONTEND_PORT` | http://localhost:8501 |
| Ollama | 11434 | - | http://localhost:11434 |

## 💻 Development Workflow

### Code Quality Standards

- **Linting**: Ruff (fast Python linter/formatter)
- **Type Checking**: MyPy with strict mode
- **Testing**: Pytest with coverage reporting
- **Import Sorting**: Ruff handles import organization

### Coding Standards

- **Type Hints**: Required for all function parameters and return values
- **Docstrings**: PEP 257 compliant
- **Line Length**: 88 characters (Ruff enforced)
- **Quote Style**: Double quotes preferred
- **Import Order**: Standard library → Third-party → Local (Ruff enforced)

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

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (async web framework)
- **Language**: Python 3.11+
- **Documentation**: Auto-generated OpenAPI/Swagger
- **CORS**: Configured for cross-origin requests

### Frontend
- **Framework**: Streamlit
- **Components**: Reactive UI with real-time updates
- **Integration**: Direct API calls to backend

### AI/ML Stack
- **Local LLM**: Ollama with llama3 model
- **Cloud LLM**: OpenAI API (optional)
- **Vector Store**: FAISS for document embeddings
- **Embeddings**: Sentence Transformers
- **Document Processing**: PyPDF, BeautifulSoup, Markdown

### Development Tools
- **Dependency Management**: uv (fast pip replacement)
- **Linting/Formatting**: Ruff
- **Type Checking**: MyPy
- **Testing**: Pytest + pytest-cov
- **Security**: Safety
- **Pre-commit**: Automated quality checks

## 📁 Project Structure

```
47Chat/
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── config.py           # Settings and configuration
│   ├── rag_utils.py        # RAG implementation
│   ├── orchestrator/       # Multi-agent orchestration
│   └── tests/              # Backend tests
├── frontend/               # Streamlit frontend
│   └── app.py              # Web interface
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml          # Project metadata and configuration
├── start_local.bat         # One-click startup script
└── .cursor/               # Cursor AI configuration
```

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Optional, for OpenAI integration
- `OLLAMA_MODEL`: Default model for Ollama (default: "llama3")
- `BACKEND_HOST`: Backend server host (default: "127.0.0.1")
- `BACKEND_PORT`: Backend server port (default: "8000")

### Python Virtual Environment

The project uses `.venv` directory for virtual environment:
```bash
# Activate (Windows)
.venv\Scripts\activate

# Activate (Unix)
source .venv/bin/activate
```

## 🚀 Deployment Notes

### Local Development
- Use `start_local.bat` for one-click startup
- Backend includes automatic port conflict resolution
- Frontend runs in headless mode to prevent duplicate browser tabs

### Production Considerations
- Set `OLLAMA_MODEL` environment variable for consistent model usage
- Configure `OPENAI_API_KEY` for cloud fallback
- Adjust ports if conflicts occur in deployment environment
- Consider using reverse proxy (nginx/Caddy) for production

### Docker Deployment
The project includes Docker Compose configuration for containerized deployment with:
- Backend container (FastAPI + Python)
- Frontend container (Streamlit)
- Ollama container (LLM models)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## 📚 API Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: The startup script automatically handles port conflicts
2. **Ollama connection**: Ensure Ollama is running with `ollama serve`
3. **Missing dependencies**: Run `uv pip sync requirements.txt requirements-dev.txt`
4. **Virtual environment**: Ensure `.venv` is properly activated

### Logs and Debugging

- Backend logs appear in the terminal where uvicorn runs
- Frontend logs appear in the Streamlit terminal
- Use `--reload` flag for backend to enable hot reloading during development

## 🎯 Key Features

- **Multi-Agent Coordination**: Intelligent agent orchestration with team-based discussions
- **RAG Integration**: Document-aware responses using vector similarity search
- **Flexible LLM Support**: Local (Ollama) and cloud (OpenAI) model integration
- **Structured Discussions**: Phase-based conversation flow (Brainstorm → Review → Verify → Vote)
- **Document Processing**: Support for PDF, Markdown, and text document ingestion
- **Real-time UI**: Interactive Streamlit interface with live discussion visualization
- **Health Monitoring**: Built-in health checks and metrics collection
- **Extensible Architecture**: Plugin-based design for adding new agent types and tools

---

**Ready to contribute?** Start by running `./start_local.bat` and exploring the API at http://localhost:8000/docs! 🚀
