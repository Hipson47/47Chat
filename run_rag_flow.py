# run_rag_flow.py
"""
End-to-end runner script for the RAG-enabled Orchestrator.
This script demonstrates:
1. Uploading a document to the RAG backend.
2. Running an orchestrator round with RAG context.
"""

import requests
import os
import subprocess
import time

# Assuming the script is run from the root of the project
from orchestrator.agent import OrchestratorAgent

BACKEND_URL = "http://127.0.0.1:8000"
SAMPLE_DOC_PATH = "sample_doc.md"

def start_backend():
    """Starts the FastAPI backend as a subprocess."""
    # Note: This is a simplified way to manage the backend process.
    # In a real application, you might use a process manager.
    process = subprocess.Popen(["uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"])
    time.sleep(5) # Give the server time to start
    return process

def upload_document():
    """Uploads the sample document to the RAG backend."""
    try:
        with open(SAMPLE_DOC_PATH, "rb") as f:
            files = {"files": (os.path.basename(SAMPLE_DOC_PATH), f, "text/markdown")}
            response = requests.post(f"{BACKEND_URL}/upload/", files=files)
            response.raise_for_status()
            print("Document uploaded successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error uploading document: {e}")

def main():
    backend_process = start_backend()
    
    try:
        upload_document()

        # Initialize and run the orchestrator agent
        agent = OrchestratorAgent("orchestrator/meta_prompt.yaml", backend_url=BACKEND_URL)
        
        print("\n--- Running Orchestrator with RAG ---")
        agent.run_round("How can I improve my app's UI using modern tools?", use_rag=True)

        print("\n--- Running Orchestrator without RAG ---")
        agent.run_round("How can I improve my app's UI using modern tools?", use_rag=False)

    finally:
        # Clean up the backend process
        backend_process.terminate()
        backend_process.wait()
        print("\nBackend server stopped.")

if __name__ == "__main__":
    main()
