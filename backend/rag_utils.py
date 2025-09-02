# backend/rag_utils.py
"""
Core utilities for the RAG service.
Includes text extraction, chunking, embedding, and FAISS vector store management.

Persistence:
- FAISS index is saved to 'rag_store.faiss'
- Chunk texts are saved to 'rag_chunks.json'

This ensures the store is automatically reloaded after application restarts.
"""

import json
import os

from bs4 import BeautifulSoup
import faiss
import markdown
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from .config import settings


class RAGUtils:
    def __init__(self, store_path: str | None = None, chunks_path: str | None = None):
        """
        Initializes the RAG utilities.
        - `store_path`: Path to the FAISS vector store file.
        """
        self.store_path = store_path or settings.FAISS_STORE_PATH
        self.chunks_path = chunks_path or settings.CHUNKS_PATH
        # Lazy-load model on first use to reduce startup time and avoid import failures
        self._embedding_model = None
        self.index = None
        self.chunks = []
        self.load_store()

    def load_store(self) -> None:
        """Loads the FAISS index and chunk texts from disk if they exist."""
        if os.path.exists(self.store_path):
            self.index = faiss.read_index(self.store_path)
            print(f"Loaded FAISS index from {self.store_path}")

        if os.path.exists(self.chunks_path):
            try:
                with open(self.chunks_path, encoding="utf-8") as f:
                    self.chunks = json.load(f)
                # Ensure chunks is a list of strings
                if not isinstance(self.chunks, list):
                    self.chunks = []
                print(f"Loaded {len(self.chunks)} chunks from {self.chunks_path}")
            except Exception:
                # Fallback to empty chunks on error
                self.chunks = []

    def save_store(self) -> None:
        """Saves the FAISS index and chunk texts to disk."""
        if self.index is not None:
            faiss.write_index(self.index, self.store_path)
            print(f"Saved FAISS index to {self.store_path}")

        try:
            with open(self.chunks_path, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False)
            print(f"Saved {len(self.chunks)} chunks to {self.chunks_path}")
        except Exception:
            # Do not crash on chunk save failure
            pass

    def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extracts text from a file, preserving line markers.
        - `file_path`: The path to the file.
        - `file_type`: The type of the file (.pdf, .md, .txt).
        """
        text = ""
        if file_type == ".pdf":
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text += f"[Page {page_num + 1}]\n{page_text}\n"
        elif file_type == ".md":
            with open(file_path, encoding="utf-8") as f:
                html = markdown.markdown(f.read())
                # A simple way to get text from HTML, could be improved.
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text()
        else:  # .txt
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        return text

    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> list:
        """
        Splits text into smaller chunks.
        - `text`: The text to chunk.
        - `chunk_size`: The size of each chunk.
        - `overlap`: The overlap between chunks.
        """
        # Simple chunking logic
        return [
            text[i : i + chunk_size] for i in range(0, len(text), chunk_size - overlap)
        ]

    def ingest(self, file_path: str) -> None:
        """
        Ingests a single file into the RAG store.
        - `file_path`: The path to the file to ingest.
        """
        file_type = os.path.splitext(file_path)[1]
        if file_type.lower() not in [".pdf", ".md", ".txt"]:
            raise ValueError("Unsupported file type")
        # Extract and chunk text
        text = self.extract_text(file_path, file_type)
        new_chunks = self.chunk_text(text)

        if new_chunks:
            self.chunks.extend(new_chunks)
            # Initialize embedding model once
            if self._embedding_model is None:
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = self._embedding_model.encode(
                new_chunks, convert_to_tensor=False
            )
            embeddings_array = np.array(embeddings, dtype="float32")

            if self.index is None:
                dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatL2(dimension)

            self.index.add(embeddings_array)
            # Persist both index and chunks
            self.save_store()
            print(f"Ingested {len(new_chunks)} chunks from {file_path}")

    def retrieve(self, query: str, k: int = 5) -> list:
        """
        Retrieves the top-k chunks for a given query.
        - `query`: The query text.
        - `k`: The number of chunks to retrieve.
        """
        if not self.index or self.index.ntotal == 0:
            return []

        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = self._embedding_model.encode([query])
        query_array = np.array(query_embedding, dtype="float32")
        distances, indices = self.index.search(query_array, k)
        # Filter out invalid indices
        valid_indices = [i for i in indices[0] if i != -1 and i < len(self.chunks)]

        results = [
            {"chunk": self.chunks[i], "score": float(distances[0][j])}
            for j, i in enumerate(valid_indices)
        ]

        return results
