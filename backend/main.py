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
    # Import observability modules
    from .observability.logging import setup_logging, get_logger
    from .observability.tracing import setup_tracing
    from .observability.middleware import RequestTrackingMiddleware
    from .observability.metrics import get_metrics_collector, update_health_status
except ImportError:
    from backend.config import settings
    from backend.orchestrator.agent import OrchestratorAgent
    from backend.rag_utils import RAGUtils
    # Import observability modules
    try:
        from backend.observability.logging import setup_logging, get_logger
        from backend.observability.tracing import setup_tracing
        from backend.observability.middleware import RequestTrackingMiddleware
        from backend.observability.metrics import get_metrics_collector, update_health_status
    except ImportError:
        # Fallback if observability modules are not available
        setup_logging = None
        get_logger = lambda name: __import__('logging').getLogger(name)
        setup_tracing = None
        RequestTrackingMiddleware = None
        get_metrics_collector = None
        update_health_status = None

# Initialize observability
if setup_logging:
    setup_logging(level="INFO", format_json=True)
if setup_tracing:
    setup_tracing(
        service_name="47chat",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),  # Optional: set for production
    )

# Create logger
logger = get_logger(__name__)

app = FastAPI(
    title="47Chat Orchestrator",
    description="Multi-agent AI orchestration with RAG capabilities",
)

# Add observability middleware
if RequestTrackingMiddleware:
    app.add_middleware(RequestTrackingMiddleware)
    logger.info("Request tracking middleware added")

# Initialize metrics collector
metrics_collector = get_metrics_collector() if get_metrics_collector else None

# Initialize components
rag_utils = RAGUtils()
orchestrator = None  # Will be initialized lazily

# Create a directory for uploads if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


class OrchestrationRequest(BaseModel):
    """Strict schema for orchestration requests with additionalProperties: false enforcement."""
    model_config = {"extra": "forbid"}

    question: str = Field(
        ..., min_length=1, max_length=2000, description="The question to orchestrate"
    )
    use_rag: bool = Field(default=True, description="Whether to use RAG context")


class HealthResponse(BaseModel):
    """Strict schema for health check responses."""
    model_config = {"extra": "forbid"}

    status: str = Field(..., pattern="^(healthy|unhealthy|degraded)$", description="Overall health status")
    ollama_available: bool = Field(..., description="Whether Ollama service is available")
    rag_store_exists: bool = Field(..., description="Whether RAG store exists")


class RootResponse(BaseModel):
    """Strict schema for root endpoint responses."""
    model_config = {"extra": "forbid"}

    message: str = Field(..., pattern=r"^47Chat.*", description="Service welcome message")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="API version")
    endpoints: dict[str, str] = Field(..., description="Available API endpoints")
    config: dict[str, str] = Field(..., description="Non-sensitive configuration")


class UploadFileResponse(BaseModel):
    """Schema for individual file upload results."""
    model_config = {"extra": "forbid"}

    filename: str = Field(..., min_length=1, max_length=255, description="Uploaded filename")
    status: str = Field(..., pattern="^success$", description="Upload status")
    chunks_created: int = Field(..., ge=0, description="Number of chunks created")


class UploadResponse(BaseModel):
    """Strict schema for upload responses."""
    model_config = {"extra": "forbid"}

    message: str = Field(
        ...,
        pattern=r"^Successfully uploaded and ingested \d+ files?\.$",
        description="Success message"
    )
    files: list[UploadFileResponse] = Field(..., min_items=1, max_items=10, description="Uploaded files")


class AgentContribution(BaseModel):
    """Schema for individual agent contributions in orchestration."""
    model_config = {"extra": "forbid"}

    agent: str = Field(..., min_length=1, max_length=100, description="Agent name")
    team: str = Field(..., min_length=1, max_length=50, description="Agent's team")
    content: str = Field(..., min_length=1, description="Contribution content")


class OrchestrationPhase(BaseModel):
    """Schema for orchestration discussion phases."""
    model_config = {"extra": "forbid"}

    phase: str = Field(
        ...,
        pattern="^(Brainstorm|CriticalReview|SelfVerify|Vote)$",
        description="Discussion phase name"
    )
    contributions: list[AgentContribution] = Field(..., min_items=1, description="Phase contributions")


class OrchestrationTranscript(BaseModel):
    """Schema for complete orchestration transcript."""
    model_config = {"extra": "forbid"}

    question: str = Field(..., min_length=1, max_length=2000, description="Original question")
    teams_assigned: list[str] = Field(..., min_items=1, max_items=10, description="Assigned teams")
    phases: list[OrchestrationPhase] = Field(..., min_items=1, max_items=4, description="Discussion phases")
    final_decision: str = Field(..., min_length=1, description="Final decision")


class OrchestrationResponse(BaseModel):
    """Strict schema for orchestration responses."""
    model_config = {"extra": "forbid"}

    status: str = Field(..., pattern="^success$", description="Operation status")
    transcript: OrchestrationTranscript = Field(..., description="Complete discussion transcript")


def get_orchestrator() -> OrchestratorAgent:
    """
    Lazy initialization of the orchestrator to avoid startup issues.
    """
    global orchestrator
    if orchestrator is None:
        orchestrator = OrchestratorAgent()
    return orchestrator


@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)) -> UploadResponse:
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

    # Create response objects for each successfully ingested file
    file_responses = [
        UploadFileResponse(
            filename=filename,
            status="success",
            chunks_created=1  # Simplified: assume 1 chunk per file for now
        )
        for filename in ingested_files
    ]

    return UploadResponse(
        message=f"Successfully uploaded and ingested {len(ingested_files)} files.",
        files=file_responses,
    )


@app.post("/orchestrate/")
async def orchestrate_discussion(request: OrchestrationRequest) -> OrchestrationResponse:
    """
    Runs a full multi-agent orchestrated discussion on the given question.

    This endpoint:
    1. Takes a user question
    2. Optionally retrieves relevant context from the RAG store
    3. Assigns appropriate teams based on the question
    4. Runs a multi-phase discussion (Brainstorm, CriticalReview, SelfVerify, Vote)
    5. Returns the full transcript and final decision
    """
    import time
    start_time = time.time()

    # Validate input
    if not request.question.strip():
        logger.warning("Empty question received", question_length=len(request.question))
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Get the orchestrator instance
        agent = get_orchestrator()

        # Run the orchestrated discussion
        result = agent.run_round(request.question, use_rag=request.use_rag)

        # Calculate duration
        duration = time.time() - start_time

        # Update metrics
        if metrics_collector:
            teams_count = len(result.get("teams_assigned", []))
            metrics_collector.record_orchestration_request("success", teams_count, duration)

        # Convert the result to our strict schema format
        # Note: This assumes result has the expected structure from OrchestratorAgent
        response = OrchestrationResponse(
            status="success",
            transcript=OrchestrationTranscript(
                question=request.question,
                teams_assigned=result.get("teams_assigned", []),
                phases=[
                    OrchestrationPhase(
                        phase=phase_data.get("phase", ""),
                        contributions=[
                            AgentContribution(
                                agent=contrib.get("agent", ""),
                                team=contrib.get("team", ""),
                                content=contrib.get("content", "")
                            )
                            for contrib in phase_data.get("contributions", [])
                        ]
                    )
                    for phase_data in result.get("phases", [])
                ],
                final_decision=result.get("final_decision", "")
            )
        )

        # Log successful orchestration
        logger.info(
            "Orchestration completed successfully",
            question_length=len(request.question),
            teams_count=len(result.get("teams_assigned", [])),
            phases_count=len(result.get("phases", [])),
            duration=duration,
            use_rag=request.use_rag
        )

        return response

    except Exception as e:
        # Calculate duration for failed requests
        duration = time.time() - start_time

        # Update error metrics
        if metrics_collector:
            metrics_collector.record_orchestration_request("error", 0, duration)

        # Log error
        logger.error(
            "Orchestration failed",
            error=str(e),
            error_type=type(e).__name__,
            question_length=len(request.question),
            duration=duration,
            use_rag=request.use_rag,
            exc_info=True
        )

        # Provide more context to frontend including quick hint when 'teams' path missing
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {e!s}")


@app.get("/")
def read_root() -> RootResponse:
    """
    Root endpoint providing service information.
    """
    return RootResponse(
        message="47Chat Orchestrator Service",
        version="1.0.0",
        endpoints={
            "/upload/": "Upload documents for RAG ingestion",
            "/orchestrate/": "Run multi-agent orchestrated discussions",
        },
        config={
            "OLLAMA_MODEL": settings.OLLAMA_MODEL,
            "META_PROMPT_PATH": settings.META_PROMPT_PATH,
            "FAISS_STORE_PATH": settings.FAISS_STORE_PATH,
            "CHUNKS_PATH": settings.CHUNKS_PATH,
        },
    )


@app.get("/health")
def health_check() -> HealthResponse:
    """
    Health check endpoint with metrics collection.
    """
    import time
    start_time = time.time()

    # Check if Ollama is available
    try:
        agent = get_orchestrator()
        # Keep health checks snappy to avoid frontend timeouts.
        ollama_available = agent.ollama_client.is_available()
    except Exception:
        ollama_available = False

    # Determine overall health status
    is_healthy = ollama_available  # Could add more health checks here
    rag_store_exists = os.path.exists(settings.FAISS_STORE_PATH)

    # Update metrics
    if update_health_status:
        update_health_status(is_healthy, ollama_available, rag_store_exists)

    # Log health check
    logger.info(
        "Health check performed",
        healthy=is_healthy,
        ollama_available=ollama_available,
        rag_store_exists=rag_store_exists,
        response_time=time.time() - start_time
    )

    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        ollama_available=ollama_available,
        rag_store_exists=rag_store_exists,
    )


@app.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint for monitoring and alerting.
    Returns metrics in Prometheus exposition format.
    """
    if metrics_collector:
        return metrics_collector.get_metrics()
    else:
        return "# Metrics collection not available\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
