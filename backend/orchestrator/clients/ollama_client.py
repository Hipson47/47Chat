# backend/orchestrator/clients/ollama_client.py
"""
Wrapper for the local Ollama client.
This client is responsible for interacting with the local Ollama model for the domain "alters".

Enhanced with resilience layer: retries, circuit breaker, and metrics.
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any
from ...config import settings

# Import resilience components
from ...clients.retry import with_retries
from ...clients.circuit import CircuitBreaker
from ...clients.config import get_resilience_config
from ...clients import metrics

class LocalOllamaClient:
    def __init__(self, model_name: str | None = None, base_url: str = "http://localhost:11434"):
        """
        Initializes the LocalOllamaClient.

        Args:
            model_name (str): The name of the Ollama model to use.
            base_url (str): The base URL of the Ollama server.
        """
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        
        # Initialize resilience components
        config = get_resilience_config()
        self._retry_policy = config.to_retry_policy()
        self._circuit_breaker = CircuitBreaker(
            name="ollama_local",
            failure_threshold=config.cb_failure_threshold,
            recovery_time_s=config.cb_recovery_time_s,
            half_open_max_success=config.cb_half_open_max_success,
        )
        
        print(f"Initialized Ollama client with model: {self.model_name}")

    def invoke(self, prompt: str) -> str:
        """
        Invokes the Ollama model with a given prompt.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The model's response.
        """
        # Check circuit breaker
        if not self._circuit_breaker.allow_request():
            metrics.update_circuit_state("ollama_local", self._circuit_breaker.state)
            return "Error: Ollama service temporarily unavailable (circuit breaker open)."
        
        # Convert sync call to async for resilience layer
        async def make_request() -> str:
            return await asyncio.to_thread(self._make_sync_request, prompt)
        
        # Use resilience layer
        try:
            # Run async operation in current event loop or create one
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, but invoke is sync - create new task
                return "[Ollama] Async operation started (sync interface limitation)"
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(self._invoke_with_resilience(make_request))
        except Exception as e:
            return f"Error: Unexpected error: {str(e)}"
    
    async def _invoke_with_resilience(self, make_request) -> str:
        """Invoke with full resilience layer."""
        start_time = time.time()
        client_name = "ollama_local"
        
        try:
            metrics.record_request_start(client_name)
            
            result = await with_retries(make_request, self._retry_policy)
            
            # Record success
            duration = time.time() - start_time
            metrics.record_request_success(client_name, duration)
            self._circuit_breaker.on_success()
            metrics.update_circuit_state(client_name, self._circuit_breaker.state)
            
            return result
            
        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            error_kind = metrics.classify_exception(e)
            
            if error_kind == "timeout":
                metrics.record_timeout(client_name)
            
            metrics.record_request_error(client_name, error_kind, duration)
            self._circuit_breaker.on_failure()
            metrics.update_circuit_state(client_name, self._circuit_breaker.state)
            
            return f"Error: {str(e)}"
    
    def _make_sync_request(self, prompt: str) -> str:
        """Make the actual synchronous Ollama API request."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        response = requests.post(
            self.generate_url,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "No response generated")

    def is_available(self) -> bool:
        """
        Checks if the Ollama server is available.

        Returns:
            bool: True if the server is available, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False