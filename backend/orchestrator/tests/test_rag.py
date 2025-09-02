# orchestrator/tests/test_rag.py
"""
Tests for the RAG implementation.
Verifies file upload, retrieval, and end-to-end RAG flow.
"""

import unittest
import os
import sys
import time
import subprocess
import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.orchestrator.agent import OrchestratorAgent
from backend.rag_utils import RAGUtils

class TestRAG(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Start the backend server on a test port
        cls.backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8001"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5) # Give the server time to start

        # Create a sample document for testing
        cls.sample_doc_path = "test_sample_doc.md"
        with open(cls.sample_doc_path, "w") as f:
            f.write("# Test Document\n\nThis is a test document about software development.")
    
    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment."""
        # Stop the backend server
        cls.backend_process.terminate()
        cls.backend_process.wait()

        # Clean up created files
        if os.path.exists(cls.sample_doc_path):
            os.remove(cls.sample_doc_path)
        if os.path.exists("rag_store.faiss"):
            os.remove("rag_store.faiss")
        if os.path.exists("rag_chunks.json"):
            os.remove("rag_chunks.json")
        if os.path.exists("uploads/test_sample_doc.md"):
            os.remove("uploads/test_sample_doc.md")
        # Remove uploads directory if empty
        try:
            if os.path.isdir("uploads") and not os.listdir("uploads"):
                os.rmdir("uploads")
        except Exception:
            pass

    def test_1_upload(self):
        """Tests the file upload endpoint."""
        with open(self.sample_doc_path, "rb") as f:
            files = {"files": (os.path.basename(self.sample_doc_path), f, "text/markdown")}
            response = requests.post("http://127.0.0.1:8001/upload/", files=files)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully uploaded and ingested", response.json()["message"])
        self.assertTrue(os.path.exists("rag_store.faiss"))

    def test_2_retrieve(self):
        """Tests retrieval via a NEW RAGUtils instance to verify persistence after restart."""
        # Simulate application restart by creating a new RAGUtils instance
        rag = RAGUtils()
        # Ensure index and chunks are loaded from disk
        self.assertTrue(os.path.exists("rag_store.faiss"), "FAISS index file should exist")
        self.assertTrue(os.path.exists("rag_chunks.json"), "Chunks file should exist")

        results = rag.retrieve("software development", k=1)
        self.assertGreaterEqual(len(results), 1, "Should retrieve at least one result from persisted store")
        # Basic content assertion
        self.assertIsInstance(results[0].get("chunk"), str)
        self.assertGreater(len(results[0]["chunk"]), 0)

    def test_3_rag_in_orchestrator(self):
        """Tests the RAG integration in the OrchestratorAgent."""
        agent = OrchestratorAgent()
        
        # This is a functional test that checks if the context is retrieved.
        # It doesn't assert the final output, but ensures the flow works.
        context = agent.get_rag_context("software development")
        self.assertIn("[RAG Context]", context)
        self.assertIn("...", context)

if __name__ == "__main__":
    unittest.main()
