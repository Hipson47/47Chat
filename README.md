# 47Chat - AI Multi-Agent Orchestrator

Welcome to 47Chat, an advanced AI-driven orchestrator bot designed for intelligent multi-agent task execution. This unified application combines FastAPI backend services, local Ollama LLM integration, optional OpenAI API, and Retrieval-Augmented Generation (RAG) to create a sophisticated multi-agent discussion system.

The orchestrator coordinates specialized AI "alters" (experts) organized into teams, running structured discussions through multiple phases (Brainstorm, CriticalReview, SelfVerify, Vote) to provide comprehensive, well-reasoned responses to complex questions.

## 🚀 Key Features

- **Multi-Agent Orchestration**: Coordinates multiple AI agents with specialized competencies organized into domain-specific teams (Backend, Frontend, Security, Operations, etc.)
- **Phase-Based Discussions**: Structured conversation flow through Brainstorm → CriticalReview → SelfVerify → Vote phases
- **Retrieval-Augmented Generation (RAG)**: Ingests and indexes documents (`.pdf`, `.md`, `.txt`) using FAISS vector store for contextually relevant responses
- **Local LLM Integration**: Uses Ollama for running models locally on your hardware (optimized for RTX 4060 Ti)
- **OpenAI Integration (optional)**: Uses OpenAI for final decision synthesis and moderation when `OPENAI_API_KEY` is provided
- **Unified API**: Single FastAPI backend serving both RAG and orchestration functionality
- **Interactive Frontend**: Streamlit-based UI for visualizing multi-agent discussions and results
- **Adaptive Capabilities**: Self-improvement, emergency handling, and performance optimization

## 🌳 Architecture Overview

The application follows a unified architecture where all components are integrated into a single, cohesive system:

### Project Structure

```
.
├── backend/
│   ├── orchestrator/           # Multi-agent orchestration engine
│   │   ├── clients/           # LLM and tool client wrappers
│   │   ├── utils/             # Core utilities (loading, team assignment, metrics)
│   │   ├── tests/             # Automated tests
│   │   ├── agent.py           # Main OrchestratorAgent and Alter classes
│   │   └── meta_prompt.yaml   # Agent configuration and team definitions
│   ├── main.py                # Unified FastAPI application
│   ├── rag_utils.py           # RAG processing and FAISS integration
│   └── requirements.txt       # All dependencies
├── frontend/
│   └── app.py                 # Streamlit UI for orchestration visualization
└── uploads/                   # Document storage directory
```

### System Flow

1. **Document Upload**: Users upload documents through the Streamlit UI or `/upload/` API
2. **RAG Ingestion**: Documents are processed, chunked, and stored in FAISS vector store
3. **Question Processing**: User questions are sent to the `/orchestrate/` endpoint
4. **Team Assignment**: The orchestrator analyzes the question and assigns relevant expert teams
5. **Multi-Phase Discussion**: Each assigned agent contributes through structured phases
6. **Final Decision**: OpenAI (or mock mode if no key) synthesizes all contributions into a final recommendation
7. **Visualization**: The Streamlit frontend displays the complete discussion transcript

## 🛠️ Setup and Usage

### Prerequisites

- **Python 3.10+**
- **NVIDIA GPU**: RTX 4060 Ti or better recommended for local Ollama models
- **Ollama**: Install from [ollama.com](https://ollama.com)
- **API Keys**: Create a `.env` file with (optional if using only Ollama):
  ```env
  OPENAI_API_KEY="your_openai_api_key_here"
  OPENAI_MODEL=gpt-5-nano
  # If chcesz, aby alters używali OpenAI zamiast Ollama:
  # ALTERS_LLM_PROVIDER=openai
  ```

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hipson47/47Chat.git
   cd 47Chat
   ```

2. **Install dependencies:**
   ```bash
   # Default (modern): Uses NumPy 2.x + FAISS 1.8+ (recommended)
   pip install -r backend/requirements.txt -c constraints.txt
   
   # Legacy: For older environments requiring NumPy 1.x + FAISS 1.7.4
   # Uncomment legacy options in constraints.txt, then:
   # pip install -r backend/requirements.txt -c constraints.txt
   ```

3. **Set up Ollama:**
   ```bash
   # Install and start Ollama service
   ollama pull llama3
   ollama serve
   ```

### Running the Application

1. **Start the Backend Service:**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Launch the Frontend (in a new terminal):**
   ```bash
   streamlit run frontend/app.py
   ```

3. **Access the Application:**
   - Frontend UI: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🐳 Running with Docker

The easiest way to run the full stack is with Docker and Docker Compose.

### Prerequisites

- Docker Desktop (with Compose) installed and running
- Optional: `.env` file with `OPENAI_API_KEY` in the project root

### Start the stack

```bash
docker-compose up --build
```

### What gets built and what gets pulled?

- Two images are built from this repo:
  - `backend` (FastAPI app) and `frontend` (Streamlit app)
- One service is pulled from Docker Hub:
  - `ollama` (official `ollama/ollama` image)

### Services

- `backend`: FastAPI at `http://localhost:8000`
- `frontend`: Streamlit at `http://localhost:8501`
- `ollama`: Local LLM server at `http://localhost:11434`

### Data & Storage

These artifacts are created at runtime and persisted via bind mounts/volumes:

- `rag_store.faiss` and `rag_chunks.json` – RAG index and chunks file
- `uploads/` – uploaded documents
- `ollama_models` volume – model cache for Ollama

They are git-ignored and safe to delete; they will be recreated on demand.

## 💡 Usage Examples

### Web Interface

1. Open the Streamlit frontend at http://localhost:8501
2. Upload documents using the sidebar file uploader
3. Enter your question in the main interface
4. Toggle "Use RAG Context" to include document knowledge
5. Click "Start Orchestration" to begin the multi-agent discussion
6. View the structured results showing each phase and agent contribution

### API Usage

**Upload Documents:**
```bash
curl -X POST -F "files=@document.pdf" http://localhost:8000/upload/
```

**Run Orchestration:**
```bash
curl -X POST "http://localhost:8000/orchestrate/" \
  -H "Content-Type: application/json" \
  -d '{"question": "How can I improve my application architecture?", "use_rag": true}'
```

### Python SDK Example

```python
import requests

# Upload a document
with open("document.pdf", "rb") as f:
    response = requests.post("http://localhost:8000/upload/", 
                           files={"files": ("document.pdf", f, "application/pdf")})

# Run orchestration
response = requests.post("http://localhost:8000/orchestrate/", 
                        json={"question": "Analyze this document", "use_rag": True})

result = response.json()
print(result["transcript"]["final_decision"])
```

## 🧪 Testing

The project includes automated tests for backend components.

### Quick start (cross-platform)

```bash
python run_tests.py
```

By default, slow tests are skipped. To include slow tests (e.g., ones that start a server and exercise FAISS):

```bash
SLOW=1 python run_tests.py
```

Filter tests (example: only RAG):

```bash
python -m pytest -q -k rag backend
```

### Dependency Management

The project uses constraints files to manage FAISS/NumPy compatibility:

- **Modern (default)**: NumPy 2.x + FAISS 1.8+ - eliminates deprecation warnings
- **Legacy**: NumPy 1.x + FAISS 1.7.4 - for older environments

To switch to legacy mode, edit `constraints.txt` and uncomment the legacy options.

### CI status

- Fast checks (lint + tests) run on pushes and pull requests with both modern and legacy dependency combinations.
- Full slow suite runs nightly.

Add a badge to your README once the workflow is live:

```
![CI](https://github.com/Hipson47/47Chat/actions/workflows/ci.yml/badge.svg)
```

### Test Coverage

- **Meta-Prompt Loading**: Validates YAML configuration parsing
- **RAG Integration**: Tests document upload, indexing, and retrieval
- **Orchestration Flow**: Verifies end-to-end multi-agent discussions
- **API Endpoints**: Ensures proper request/response handling

## 🔧 Configuration

The system behavior is controlled by `backend/orchestrator/meta_prompt.yaml`:

- **Teams**: Define expert groups and their assigned agents
- **Alters**: Configure individual AI agents with competencies and examples
- **Phases**: Customize discussion flow and phase-specific instructions
- **Emergency Rules**: Set up keyword-triggered special workflows
- **Adaptive Settings**: Configure performance optimization parameters

## 🚀 Advanced Features

- **Adaptive Scheduling**: Automatically adjusts discussion phases based on performance metrics
- **Emergency Handling**: Detects critical keywords to trigger specialized workflows
- **Self-Improvement**: Learns from past discussions to optimize team assignments
- **Tool Integration**: Supports file search, web search, Python analysis, and image generation
- **Health Monitoring**: Built-in health checks for all system components

## 📊 Monitoring and Metrics

Access system health and performance metrics:

- **Health Check**: GET `/health` - System status and component availability
- **Metrics Logging**: Automatic performance tracking and optimization
- **Frontend Status**: Real-time backend and Ollama connectivity indicators

## 🤝 Contributing

This project is designed for easy extension and customization. Key areas for contribution:

- Adding new agent types and competencies
- Implementing additional LLM providers
- Extending RAG capabilities with new document types
- Improving the frontend visualization
- Adding new orchestration phases or workflows

---

**Powered by 47Chat Multi-Agent Orchestrator** | Local LLMs + RAG + Multi-Agent Intelligence

---

### ℹ️ Demo status

- The natural-language orchestrator already routes phases (Brainstorm → CriticalReview → SelfVerify → Vote).
- The meta-prompt is intentionally exposed for demo and iteration.
- Role-specific prompts and deeper guardrails are planned next.