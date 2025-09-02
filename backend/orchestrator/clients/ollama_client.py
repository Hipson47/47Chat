# backend/orchestrator/clients/ollama_client.py
"""
Wrapper for the local Ollama client.
This client is responsible for interacting with the local Ollama model for the domain "alters".
"""

import requests
import json
from typing import Dict, Any
from ...config import settings

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
        print(f"Initialized Ollama client with model: {self.model_name}")

    def invoke(self, prompt: str) -> str:
        """
        Invokes the Ollama model with a given prompt.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The model's response.
        """
        try:
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
            
        except requests.exceptions.ConnectionError:
            return f"Error: Could not connect to Ollama server at {self.base_url}. Please ensure Ollama is running."
        except requests.exceptions.Timeout:
            return "Error: Request to Ollama server timed out."
        except requests.exceptions.RequestException as e:
            return f"Error: Request failed: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Invalid response format from Ollama server."
        except Exception as e:
            return f"Error: Unexpected error: {str(e)}"

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