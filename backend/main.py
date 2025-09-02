# backend/main.py
"""
FastAPI backend for the unified Orchestrator and RAG service.
Provides endpoints for document upload and orchestrated multi-agent discussions.
"""

import os
import shutil
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

# Support both package and script execution imports
try:
    from .config import settings
    from .orchestrator.agent import OrchestratorAgent
    from .rag_utils import RAGUtils
except ImportError:
    from config import settings
    from orchestrator.agent import OrchestratorAgent
    from rag_utils import RAGUtils

app = FastAPI(
    title="47Chat Orchestrator",
    description="Multi-agent AI orchestration with RAG capabilities",
)

# Initialize components
rag_utils = RAGUtils()
orchestrator = None  # Will be initialized lazily

# Create a directory for uploads if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


class OrchestrationRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=2000, description="The question to orchestrate"
    )
    use_rag: bool = Field(default=True, description="Whether to use RAG context")


def get_orchestrator() -> OrchestratorAgent:
    """
    Lazy initialization of the orchestrator to avoid startup issues.
    """
    global orchestrator
    if orchestrator is None:
        orchestrator = OrchestratorAgent()
    return orchestrator


@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    Uploads files, extracts text, and ingests them into the RAG vector store.
    Accepts .pdf, .md, and .txt files.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    # Validate file count
    if len(files) > 10:
        raise HTTPException(
            status_code=400, detail="Maximum 10 files allowed per upload."
        )

    ingested_files = []

    for file in files:
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=400, detail="File must have a valid filename."
            )

        # Validate file type
        allowed_extensions = {".pdf", ".md", ".txt"}
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{file_ext}'. Allowed: {', '.join(allowed_extensions)}",
            )

        # Validate file size (max 10MB)
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400, detail="File too large. Maximum size: 10MB"
            )

        safe_name = os.path.basename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        # Reset file pointer for reading
        await file.seek(0)

        # Save the uploaded file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Ingest the file into the RAG store
            rag_utils.ingest(file_path)
            ingested_files.append(file.filename)

        except Exception as e:
            # Clean up the uploaded file on failure
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500, detail=f"Failed to ingest {file.filename}: {e}"
            )

    return {
        "message": f"Successfully uploaded and ingested {len(ingested_files)} files.",
        "files": ingested_files,
    }


@app.post("/orchestrate/")
async def orchestrate_discussion(request: OrchestrationRequest) -> dict[str, Any]:
    """
    Runs a full multi-agent orchestrated discussion on the given question.

    This endpoint:
    1. Takes a user question
    2. Optionally retrieves relevant context from the RAG store
    3. Assigns appropriate teams based on the question
    4. Runs a multi-phase discussion (Brainstorm, CriticalReview, SelfVerify, Vote)
    5. Returns the full transcript and final decision
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Get the orchestrator instance
        agent = get_orchestrator()

        # Run the orchestrated discussion
        result = agent.run_round(request.question, use_rag=request.use_rag)

        return {"status": "success", "transcript": result}

    except Exception as e:
        # Provide more context to frontend including quick hint when 'teams' path missing
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {e!s}")


@app.get("/")
def read_root() -> dict[str, Any]:
    """
    Root endpoint providing service information.
    """
    return {
        "message": "47Chat Orchestrator Service",
        "version": "1.0.0",
        "endpoints": {
            "/upload/": "Upload documents for RAG ingestion",
            "/orchestrate/": "Run multi-agent orchestrated discussions",
        },
        "config": {
            "OLLAMA_MODEL": settings.OLLAMA_MODEL,
            "META_PROMPT_PATH": settings.META_PROMPT_PATH,
            "FAISS_STORE_PATH": settings.FAISS_STORE_PATH,
            "CHUNKS_PATH": settings.CHUNKS_PATH,
        },
    }


@app.get("/health")
def health_check() -> dict[str, Any]:
    """
    Health check endpoint.
    """
    # Check if Ollama is available
    try:
        agent = get_orchestrator()
        # Keep health checks snappy to avoid frontend timeouts.
        ollama_available = agent.ollama_client.is_available()
    except Exception:
        ollama_available = False

    return {
        "status": "healthy",
        "ollama_available": ollama_available,
        "rag_store_exists": os.path.exists(settings.FAISS_STORE_PATH),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
