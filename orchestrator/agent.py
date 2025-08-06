# orchestrator/agent.py
"""
Main entrypoint for the Orchestrator Agent.
This script orchestrates the entire round flow, including team assignment,
phase execution, model/tool invocation, and metrics logging.
"""

import yaml
from clients.ollama_client import LocalOllamaClient
from clients.gemini_client import GeminiAPIClient
from clients.tool_clients import ToolClient
from utils.loader import load_meta_prompt
from utils.team_assigner import auto_assign_teams
from utils.metrics import log_metrics

class OrchestratorAgent:
    def __init__(self, meta_prompt_path):
        """
        Initializes the OrchestratorAgent.

        Args:
            meta_prompt_path (str): The path to the meta_prompt.yaml file.
        """
        self.meta_prompt = load_meta_prompt(meta_prompt_path)
        self.ollama_client = LocalOllamaClient()
        self.gemini_client = GeminiAPIClient()
        self.tool_client = ToolClient()

    def run_round(self, user_prompt):
        """
        Executes a full round of the orchestration flow.

        Args:
            user_prompt (str): The user's input prompt.
        """
        # 1. Assign teams based on the user prompt
        assigned_teams = auto_assign_teams(user_prompt, self.meta_prompt)
        print(f"Assigned teams: {', '.join(assigned_teams)}")

        # 2. Loop through the default sequence of phases
        for phase in self.meta_prompt['meta_prompt']['rounds']['default_sequence']:
            print(f"\n--- Running Phase: {phase} ---")
            
            # In a real implementation, you would invoke the appropriate model or tool
            # for each alter in the assigned teams.
            # For this stub, we'll just print the phase.

        # 3. Log metrics for the round
        log_metrics({"user_prompt": user_prompt, "assigned_teams": assigned_teams})

        print("\nRound completed.")

if __name__ == "__main__":
    agent = OrchestratorAgent("orchestrator/meta_prompt.yaml")
    agent.run_round("Refactor the frontend to use React and Tailwind CSS.")
