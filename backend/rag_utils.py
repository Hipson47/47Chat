# backend/rag_utils.py
"""
Core utilities for the RAG service.
Includes text extraction, chunking, embedding, and FAISS vector store management.
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF
import markdown
import os

class RAGUtils:
    def __init__(self, store_path="rag_store.faiss"):
        """
        Initializes the RAG utilities.
        - `store_path`: Path to the FAISS vector store file.
        """
        self.store_path = store_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.chunks = []
        self.load_store()

    def load_store(self):
        """Loads the FAISS index and chunks from disk if they exist."""
        if os.path.exists(self.store_path):
            self.index = faiss.read_index(self.store_path)
            # In a real application, you'd also persist and load the chunk texts.
            # For this example, we'll keep it simple.
            print(f"Loaded FAISS index from {self.store_path}")

    def save_store(self):
        """Saves the FAISS index to disk."""
        if self.index:
            faiss.write_index(self.index, self.store_path)
            print(f"Saved FAISS index to {self.store_path}")

    def extract_text(self, file_path, file_type):
        """
        Extracts text from a file, preserving line markers.
        - `file_path`: The path to the file.
        - `file_type`: The type of the file (.pdf, .md, .txt).
        """
        text = ""
        if file_type == ".pdf":
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                text += f"[Page {page_num + 1}]\n{page.get_text()}\n"
        elif file_type == ".md":
            with open(file_path, 'r', encoding='utf-8') as f:
                html = markdown.markdown(f.read())
                # A simple way to get text from HTML, could be improved.
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
        else: # .txt
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        return text

    def chunk_text(self, text, chunk_size=512, overlap=50):
        """
        Splits text into smaller chunks.
        - `text`: The text to chunk.
        - `chunk_size`: The size of each chunk.
        - `overlap`: The overlap between chunks.
        """
        # Simple chunking logic
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]

    def ingest(self, file_path):
        """
        Ingests a single file into the RAG store.
        - `file_path`: The path to the file to ingest.
        """
        file_type = os.path.splitext(file_path)[1]
        if file_type not in [".pdf", ".md", ".txt"]:
            raise ValueError("Unsupported file type")

        text = self.extract_text(file_path, file_type)
        new_chunks = self.chunk_text(text)
        
        if new_chunks:
            self.chunks.extend(new_chunks)
            embeddings = self.embedding_model.encode(new_chunks, convert_to_tensor=False)
            
            if self.index is None:
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
            
            self.index.add(np.array(embeddings))
            self.save_store()
            print(f"Ingested {len(new_chunks)} chunks from {file_path}")

    def retrieve(self, query, k=5):
        """
        Retrieves the top-k chunks for a given query.
        - `query`: The query text.
        - `k`: The number of chunks to retrieve.
        """
        if not self.index or self.index.ntotal == 0:
            return []
        
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding), k)
        
        # Filter out invalid indices
        valid_indices = [i for i in indices[0] if i != -1 and i < len(self.chunks)]
        
        results = [{
            "chunk": self.chunks[i],
            "score": float(distances[0][j])
        } for j, i in enumerate(valid_indices)]
        
        return results
