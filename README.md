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

2. **Install uv (fast Python package manager):**
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Install dependencies:**
   ```bash
   # Sync all dependencies (runtime + development)
   uv pip sync requirements.txt requirements-dev.txt

   # Or install from source for development
   uv pip install -e .[dev]
   ```

4. **Set up Ollama:**
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

The project includes comprehensive automated tests. From the project root, run:

```powershell
./run_tests.ps1
```

This script will enter the `backend` directory and execute `python -m pytest`, ensuring proper test discovery.

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

## 📊 Observability & Monitoring

47Chat includes comprehensive observability features for production monitoring and debugging.

### Structured Logging

All logs are formatted as JSON with consistent structure:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "backend.main",
  "message": "Orchestration completed successfully",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_length": 42,
  "teams_count": 3,
  "phases_count": 4,
  "duration": 2.34,
  "use_rag": true
}
```

#### Key Features:
- **Request ID tracking** across all log entries
- **Trace ID correlation** for distributed tracing
- **Structured data** for easy parsing and analysis
- **Performance metrics** included in logs
- **Error context** with stack traces

### Distributed Tracing

OpenTelemetry tracing provides end-to-end visibility:

#### Automatic Instrumentation:
- FastAPI request/response tracing
- HTTP client call tracing
- Database operation tracing
- AI model inference tracing

#### Custom Spans:
- Orchestration phases
- RAG retrieval operations
- Agent contributions
- Error handling flows

### Metrics & Monitoring

Prometheus-compatible metrics for alerting and dashboards:

#### HTTP Metrics:
```prometheus
# Request count by method and endpoint
http_requests_total{method="POST", endpoint="/orchestrate/", status_code="200"} 42

# Request duration percentiles
http_request_duration_seconds{method="POST", endpoint="/orchestrate/", quantile="0.95"} 3.2
```

#### Business Metrics:
```prometheus
# Orchestration success/failure rates
orchestration_requests_total{status="success", teams_count="3"} 38

# AI model inference times
ai_model_inference_duration_seconds{model_name="llama3", provider="ollama", quantile="0.95"} 1.8
```

#### Health Metrics:
```prometheus
# Service health status
health_status 1

# Component availability
ollama_available 1
rag_store_exists 1
```

### Local Development Setup

#### 1. Install Observability Dependencies:
```bash
# Install with observability features
uv pip install -e .[observability]

# Or install individual packages
uv pip install structlog opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp prometheus-client
```

#### 2. Run with Local Tracing:
```bash
# Set environment variable for local development
export OTLP_ENDPOINT="http://localhost:4317"

# Or run without OTLP (uses console exporter)
unset OTLP_ENDPOINT

# Start the application
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. View Logs:
```bash
# Logs appear in JSON format
tail -f /dev/stdout | jq .
```

#### 4. Access Metrics:
```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics

# Health check with metrics
curl http://localhost:8000/health
```

### Production Setup

#### OpenTelemetry Collector:
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  jaeger:
    endpoint: jaeger:14268
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
```

#### Docker Compose with Observability:
```yaml
# Add to docker-compose.yml
services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    volumes:
      - ./otel-collector-config.yaml:/etc/otelcol/config.yaml
    ports:
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
      - "8889:8889"    # Prometheus metrics

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

#### Environment Variables:
```bash
# Production configuration
export OTLP_ENDPOINT="http://otel-collector:4317"
export LOG_LEVEL="INFO"
export SERVICE_NAME="47chat"
export SERVICE_VERSION="1.0.0"
```

### Monitoring Dashboards

#### Grafana Dashboard Example:
```json
{
  "dashboard": {
    "title": "47Chat Observability",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Orchestration Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(orchestration_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "5xx Error Rate %"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

#### Prometheus Alerting Rules:
```yaml
groups:
  - name: 47chat
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"[45].."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | printf \"%.2f\" }}%"

      - alert: OrchestrationSlow
        expr: histogram_quantile(0.95, rate(orchestration_duration_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Orchestration requests are slow"
          description: "95th percentile orchestration duration is {{ $value | printf \"%.2f\" }}s"

      - alert: OllamaUnavailable
        expr: ollama_available == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Ollama service is unavailable"
          description: "Ollama service has been unavailable for 2 minutes"
```

### Troubleshooting

#### Common Issues:

**Logs not appearing in JSON format:**
```bash
# Check if structlog is installed
python -c "import structlog; print('structlog available')"

# Verify logging configuration
python -c "from backend.observability.logging import setup_logging; setup_logging()"
```

**Traces not being exported:**
```bash
# Check OTLP endpoint connectivity
curl -v http://localhost:4317/v1/traces

# Verify environment variables
echo $OTLP_ENDPOINT
```

**Metrics not updating:**
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Verify prometheus_client is installed
python -c "import prometheus_client; print('prometheus_client available')"
```

#### Log Analysis:
```bash
# Filter logs by request ID
cat logs/app.log | jq 'select(.request_id == "550e8400-e29b-41d4-a716-446655440000")'

# Find slow requests
cat logs/app.log | jq 'select(.duration > 5)'

# Count errors by type
cat logs/app.log | jq -r 'select(.level == "ERROR") | .error_type' | sort | uniq -c
```

---

**Powered by 47Chat Multi-Agent Orchestrator** | Local LLMs + RAG + Multi-Agent Intelligence

---

## 🔒 Security

### Vulnerability Management

47Chat takes security seriously and implements multiple layers of protection:

#### Dependency Security
- **Automated Scanning**: CI/CD pipeline runs `pip-audit` and `safety` scans on every push
- **Regular Updates**: Dependencies are monitored for known vulnerabilities
- **Pinned Versions**: All dependencies are pinned to prevent unexpected updates

#### Secrets Management
- **Environment Variables**: Never commit secrets - use `.env` files (excluded from version control)
- **Credential Exclusion**: Comprehensive `.gitignore` and `.cursorignore` rules prevent accidental commits
- **AI Context Protection**: Sensitive files are excluded from AI assistant context

### Security Best Practices

#### For Contributors
1. **Never commit secrets**: Use environment variables for sensitive data
2. **Validate inputs**: All user inputs are validated using Pydantic models
3. **Review dependencies**: Check for vulnerabilities before adding new packages
4. **Follow secure coding**: Adhere to OWASP guidelines and CWE recommendations

#### For Users
1. **Secure API keys**: Store OpenAI API keys securely in `.env` files
2. **Network security**: Run services on secure networks only
3. **Regular updates**: Keep dependencies updated to latest secure versions
4. **Monitor logs**: Review application logs for security events

### Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do not create public issues** for security vulnerabilities
2. **Email security concerns** to the maintainers directly
3. **Allow time for fixes** before public disclosure
4. **Follow responsible disclosure** practices

### Security Features

- ✅ **Input Validation**: Pydantic models for all API inputs
- ✅ **Dependency Auditing**: Automated vulnerability scanning
- ✅ **Secrets Protection**: Comprehensive exclusion rules
- ✅ **Command Restrictions**: AI agent command execution controls
- ✅ **Type Safety**: MyPy strict mode for runtime safety
- ✅ **Code Quality**: Ruff linting with security rules

---

### ℹ️ Demo status

- The natural-language orchestrator already routes phases (Brainstorm → CriticalReview → SelfVerify → Vote).
- The meta-prompt is intentionally exposed for demo and iteration.
- Role-specific prompts and deeper guardrails are planned next.