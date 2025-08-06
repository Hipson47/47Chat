# backend/main.py
"""
FastAPI backend for the RAG service.
Provides endpoints for document upload and retrieval.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import os
import shutil

from rag_utils import RAGUtils

app = FastAPI()
rag_utils = RAGUtils()

# Create a directory for uploads if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class RetrieveRequest(BaseModel):
    query: str
    k: int = 5

@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Uploads files, extracts text, and ingests them into the RAG vector store.
    Accepts .pdf, .md, and .txt files.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Ingest the file into the RAG store
        try:
            rag_utils.ingest(file_path)
        except Exception as e:
            # Clean up the uploaded file on failure
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Failed to ingest {file.filename}: {e}")

    return {"message": f"Successfully uploaded and ingested {len(files)} files."}

@app.post("/retrieve/")
async def retrieve_chunks(request: RetrieveRequest):
    """
    Retrieves the top-k chunks from the RAG store for a given query.
    Expects a JSON payload: {"query": "<text>", "k": 5}
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        results = rag_utils.retrieve(request.query, request.k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chunks: {e}")

@app.get("/")
def read_root():
    return {"message": "RAG service is running."}
