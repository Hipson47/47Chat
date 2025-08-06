# 47Chat - AI Orchestrator Bot

Welcome to the 47Chat repository, an advanced AI-driven orchestrator bot designed for modular, team-based task execution. This project leverages a powerful combination of FastAPI, LangChain RAG, local Ollama models, and the Gemini 2.5 Pro API to create a sophisticated multi-agent system.

The orchestrator is built around a meta-prompt engine that coordinates specialized "alters" (AI experts) grouped into teams. It dynamically assigns tasks, manages conversational flows, and continuously improves its performance through adaptive learning.

## 🚀 Key Features

- **Meta-Prompt Engine**: A central YAML-based configuration (`meta_prompt.yaml`) drives the multi-agent coordination, allowing for dynamic team assignment and phased task execution (e.g., Brainstorm, CriticalReview, Vote).
- **Retrieval-Augmented Generation (RAG)**: Ingests and indexes documents (`.pdf`, `.md`, `.txt`) into a FAISS vector store. The orchestrator uses this knowledge base to provide contextually relevant information to the agents.
- **Robust API**: Built with FastAPI, providing a clean and efficient interface for interacting with the orchestrator.
  - `POST /upload`: Upload and ingest documents into the RAG store.
  - `POST /retrieve`: Query the RAG store to get the most relevant context chunks.
- **Modular Client Architecture**:
  - `OllamaClient`: Wrapper for running local LLMs on your own hardware.
  - `GeminiClient`: Wrapper for leveraging the powerful Gemini 2.5 Pro model for moderator and complex reasoning tasks.
  - `ToolClient`: Provides a unified interface for various tools, including `file_search`, `web_search`, `python` (for analysis), and `image_gen`.
- **Advanced Orchestration Capabilities**:
  - **Adaptive Scheduling**: Dynamically adjusts the execution flow based on performance metrics.
  - **Self-Improvement**: Learns from past interactions to optimize team assignments and phase sequences.
  - **Emergency Handling**: Detects critical keywords to trigger special workflows, such as involving the security team.
  - **Tool Management**: Tracks and optimizes the usage of external tools.

## 🌳 Architecture Overview

The project is designed with a modular and scalable architecture to facilitate extensibility and maintainability.

### Folder Structure

```
.
├── orchestrator/
│   ├── clients/          # Wrappers for external services (Ollama, Gemini, Tools)
│   ├── utils/            # Core utilities (YAML loading, team assignment, metrics)
│   ├── tests/            # Automated tests for the orchestrator and RAG
│   ├── agent.py          # Main entrypoint for the OrchestratorAgent
│   └── meta_prompt.yaml  # Core configuration for agents, teams, and phases
├── backend/
│   ├── rag_utils.py      # Core RAG logic (ingestion, chunking, FAISS store)
│   └── main.py           # FastAPI application for RAG services
├── uploads/              # Directory for uploaded documents
└── run_rag_flow.py       # Example script to run an end-to-end RAG-powered round
```

### High-Level Flow

1.  **Upload**: Documents are sent to the `/upload` endpoint of the FastAPI backend.
2.  **Ingest**: The backend's `RAGUtils` processes the documents, creates embeddings, and stores them in the `rag_store.faiss` vector store.
3.  **Retrieve**: When a user prompt is received with `use_rag=True`, the `OrchestratorAgent` calls the `/retrieve` endpoint to get relevant context.
4.  **Orchestrate**: The agent uses the `meta_prompt.yaml` to assign teams, prepend the RAG context to the prompt, and execute the defined phases, invoking the appropriate models and tools for each step.

## 🛠️ Setup and Usage

Follow these steps to get the orchestrator running on your local machine.

### Prerequisites

- Python 3.10+
- **NVIDIA GPU**: An RTX 4060 Ti or better is recommended for running local models with Ollama.
- **API Keys**:
  - Create a `.env` file in the root directory.
  - Add your API keys to the `.env` file:
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Hipson47/47Chat.git
    cd 47Chat
    ```

2.  **Install dependencies:**
    This project uses separate requirements files for the backend and orchestrator.
    ```bash
    pip install -r backend/requirements.txt
    pip install -r orchestrator/requirements.txt # (Assuming one exists or consolidate them)
    ```

### Running the Application

1.  **Start the FastAPI Server:**
    The RAG service must be running for the orchestrator to function correctly.
    ```bash
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
    ```

2.  **Run a Sample Round:**
    Use the `run_rag_flow.py` script to see an end-to-end example. This will start the backend, upload a sample document, and run the orchestrator.
    ```bash
    python run_rag_flow.py
    ```

## ⚙️ API and SDK Examples

### `curl` Examples

**1. Upload a document:**
```bash
curl -X POST -F "files=@/path/to/your/document.md" http://127.0.0.1:8000/upload/
```

**2. Retrieve context:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"query": "modern frontend development", "k": 2}' http://127.0.0.1:8000/retrieve/
```

### Python SDK Example

The `OrchestratorAgent` can be used as an SDK to run orchestrated rounds within your own Python applications.

```python
from orchestrator.agent import OrchestratorAgent

# Initialize the agent (ensure the backend service is running)
agent = OrchestratorAgent("orchestrator/meta_prompt.yaml")

# Define a user prompt
user_prompt = "How can I build a more interactive UI with React?"

# Run a round with RAG-enabled context retrieval
print("--- Running Orchestrator with RAG ---")
agent.run_round(user_prompt, use_rag=True)
```

## ✅ Testing

The project includes a suite of automated tests to ensure correctness and stability.

- **Test Directory**: All tests are located in the `orchestrator/tests/` directory.
- **Running Tests**: Use `pytest` to run the test suite.
  ```bash
  pytest orchestrator/tests/
  ```

### Test Coverage

- **Meta-Prompt Loading**: Verifies that the `meta_prompt.yaml` loads correctly.
- **RAG Ingestion & Retrieval**: Ensures that the document upload, indexing, and retrieval processes work as expected.
- **End-to-End Round**: Tests a full orchestrator round to confirm that all components integrate correctly.
