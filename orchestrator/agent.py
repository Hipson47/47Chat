# orchestrator/agent.py
"""
Main entrypoint for the Orchestrator Agent.
This script orchestrates the entire round flow, including team assignment,
phase execution, model/tool invocation, and metrics logging.
"""

import yaml
import requests
from clients.ollama_client import LocalOllamaClient
from clients.gemini_client import GeminiAPIClient
from clients.tool_clients import ToolClient
from utils.loader import load_meta_prompt
from utils.team_assigner import auto_assign_teams
from utils.metrics import log_metrics

class OrchestratorAgent:
    def __init__(self, meta_prompt_path, backend_url="http://127.0.0.1:8000"):
        """
        Initializes the OrchestratorAgent.

        Args:
            meta_prompt_path (str): The path to the meta_prompt.yaml file.
            backend_url (str): The URL of the RAG backend service.
        """
        self.meta_prompt = load_meta_prompt(meta_prompt_path)
        self.ollama_client = LocalOllamaClient()
        self.gemini_client = GeminiAPIClient()
        self.tool_client = ToolClient()
        self.backend_url = backend_url

    def get_rag_context(self, query, k=3):
        """
        Retrieves context from the RAG backend.

        Args:
            query (str): The user's query.
            k (int): The number of chunks to retrieve.

        Returns:
            str: The formatted RAG context.
        """
        try:
            response = requests.post(f"{self.backend_url}/retrieve", json={"query": query, "k": k})
            response.raise_for_status()
            results = response.json().get("results", [])
            
            if not results:
                return ""

            context = "[RAG Context]\n"
            for i, res in enumerate(results):
                # Assuming chunk content is the most important part.
                # In a real app, you might include source file and line numbers.
                context += f"- Chunk {i+1}: \"...{res['chunk'][:100]}...\"\n"
            return context
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving RAG context: {e}")
            return ""

    def run_round(self, user_prompt, use_rag=False):
        """
        Executes a full round of the orchestration flow.

        Args:
            user_prompt (str): The user's input prompt.
            use_rag (bool): Whether to use the RAG for context retrieval.
        """
        rag_context = ""
        if use_rag:
            rag_context = self.get_rag_context(user_prompt)

        # 1. Assign teams based on the user prompt
        assigned_teams = auto_assign_teams(user_prompt, self.meta_prompt)
        print(f"Assigned teams: {', '.join(assigned_teams)}")

        # 2. Loop through the default sequence of phases
        for phase in self.meta_prompt['meta_prompt']['rounds']['default_sequence']:
            print(f"\n--- Running Phase: {phase} ---")
            
            # Prepend RAG context to the prompt for the moderator (or all alters)
            phase_prompt = f"{rag_context}\n{user_prompt}" if rag_context else user_prompt
            
            # This is a stub for invoking the models/tools
            print(f"Phase prompt (first 100 chars): {phase_prompt[:100]}...")

        # 3. Log metrics for the round
        log_metrics({"user_prompt": user_prompt, "assigned_teams": assigned_teams, "use_rag": use_rag})

        print("\nRound completed.")

if __name__ == "__main__":
    # This assumes the backend is running.
    agent = OrchestratorAgent("orchestrator/meta_prompt.yaml")
    agent.run_round("Refactor the frontend to use React and Tailwind CSS.", use_rag=True)
