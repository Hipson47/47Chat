# backend/orchestrator/agent.py
"""
Main entrypoint for the Orchestrator Agent.
This script orchestrates the entire round flow, including team assignment,
phase execution, model/tool invocation, and metrics logging.
"""

import yaml
import json
from typing import List, Dict, Any
from .clients.ollama_client import LocalOllamaClient
from .clients.gemini_client import GeminiAPIClient
from .clients.tool_clients import ToolClient
from .utils.loader import load_meta_prompt
from .utils.team_assigner import auto_assign_teams
from .utils.metrics import log_metrics
from ..rag_utils import RAGUtils

class Alter:
    """
    Represents a single AI alter/agent with specific competencies and personality.
    """
    
    def __init__(self, alter_data: Dict[str, Any], ollama_client: LocalOllamaClient):
        self.id = alter_data.get('id')
        self.name = alter_data.get('name', f'Alter {self.id}')
        self.priority = alter_data.get('priority', 'Medium')
        self.competencies = alter_data.get('competencies', '')
        self.examples = alter_data.get('examples', [])
        self.ollama_client = ollama_client
    
    def build_prompt(self, phase: str, user_prompt: str, context: str = "", conversation_history: List[Dict] = None) -> str:
        """
        Builds a detailed prompt for this alter based on the current phase and context.
        """
        conversation_history = conversation_history or []
        
        # Build conversation context
        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious discussion:\n"
            for entry in conversation_history[-5:]:  # Last 5 entries for context
                history_text += f"[{entry['phase']}] {entry['alter_name']}: {entry['response'][:200]}...\n"
        
        # Phase-specific instructions
        phase_instructions = {
            "Brainstorm": "Generate creative ideas and initial approaches. Think outside the box and propose multiple solutions.",
            "CriticalReview": "Critically analyze the ideas presented. Point out potential issues, risks, and improvements.",
            "SelfVerify": "Verify the feasibility and correctness of the proposed solutions. Check for consistency.",
            "Vote": "Provide your final recommendation with clear reasoning. Vote for the best approach."
        }
        
        prompt = f"""You are {self.name}, an expert with the following competencies: {self.competencies}

Your priority level: {self.priority}

Current phase: {phase}
Phase instruction: {phase_instructions.get(phase, 'Contribute your expertise to the discussion.')}

User's question/request: {user_prompt}

{context}
{history_text}

Based on your expertise and the current phase, provide your contribution to the discussion. Be specific, actionable, and draw from your competencies. Keep your response focused and under 300 words."""

        return prompt
    
    def respond(self, phase: str, user_prompt: str, context: str = "", conversation_history: List[Dict] = None) -> str:
        """
        Gets a response from this alter for the given phase and context.
        """
        prompt = self.build_prompt(phase, user_prompt, context, conversation_history)
        response = self.ollama_client.invoke(prompt)
        return response

class OrchestratorAgent:
    """
    The main orchestrator that manages the multi-agent conversation flow.
    """
    
    def __init__(self, meta_prompt_path: str = "backend/orchestrator/meta_prompt.yaml"):
        """
        Initializes the OrchestratorAgent.
        """
        self.meta_prompt = load_meta_prompt(meta_prompt_path)
        self.ollama_client = LocalOllamaClient()
        self.gemini_client = GeminiAPIClient()
        self.tool_client = ToolClient()
        self.rag_utils = RAGUtils()
        self.alters = self._initialize_alters()

    def _initialize_alters(self) -> Dict[int, Alter]:
        """
        Initialize all alters from the meta-prompt configuration.
        """
        alters = {}
        for alter_data in self.meta_prompt.get('alters', []):
            alter_id = alter_data.get('id')
            if alter_id is not None:
                alters[alter_id] = Alter(alter_data, self.ollama_client)
        return alters

    def get_alters_for_teams(self, team_names: List[str]) -> List[Alter]:
        """
        Get all alters that belong to the specified teams.
        """
        alter_ids = set()
        teams = self.meta_prompt.get('teams', {})
        
        for team_name in team_names:
            if team_name in teams:
                team_alter_ids = teams[team_name].get('alters', [])
                alter_ids.update(team_alter_ids)
        
        return [self.alters[alter_id] for alter_id in alter_ids if alter_id in self.alters]

    def get_rag_context(self, query: str, k: int = 3) -> str:
        """
        Retrieves context from the RAG store.
        """
        try:
            results = self.rag_utils.retrieve(query, k)
            if not results:
                return ""

            context = "[RAG Context]\n"
            for i, res in enumerate(results):
                # Truncate long chunks for readability
                chunk_text = res['chunk'][:200] + "..." if len(res['chunk']) > 200 else res['chunk']
                context += f"- Chunk {i+1}: \"{chunk_text}\" [score: {res['score']:.3f}]\n"
            return context
        except Exception as e:
            print(f"Error retrieving RAG context: {e}")
            return ""

    def run_round(self, user_prompt: str, use_rag: bool = False) -> Dict[str, Any]:
        """
        Executes a full round of the orchestration flow.
        Returns a detailed transcript of the multi-agent discussion.
        """
        # Initialize the conversation transcript
        transcript = {
            "user_prompt": user_prompt,
            "use_rag": use_rag,
            "rag_context": "",
            "assigned_teams": [],
            "phases": [],
            "final_decision": "",
            "conversation_history": []
        }
        
        # Get RAG context if requested
        if use_rag:
            transcript["rag_context"] = self.get_rag_context(user_prompt)
        
        # Assign teams based on the user prompt
        assigned_teams = auto_assign_teams(user_prompt, self.meta_prompt)
        transcript["assigned_teams"] = assigned_teams
        
        # Get alters for the assigned teams
        participating_alters = self.get_alters_for_teams(assigned_teams)
        
        if not participating_alters:
            # Fallback to a default alter if none are found
            participating_alters = [alter for alter in self.alters.values()][:3]
        
        # Execute each phase
        phases = self.meta_prompt['meta_prompt']['rounds']['default_sequence']
        
        for phase in phases:
            phase_data = {
                "phase_name": phase,
                "contributions": []
            }
            
            print(f"\n--- Running Phase: {phase} ---")
            
            # Each alter contributes to this phase
            for alter in participating_alters:
                try:
                    response = alter.respond(
                        phase=phase,
                        user_prompt=user_prompt,
                        context=transcript["rag_context"],
                        conversation_history=transcript["conversation_history"]
                    )
                    
                    contribution = {
                        "alter_id": alter.id,
                        "alter_name": alter.name,
                        "response": response
                    }
                    
                    phase_data["contributions"].append(contribution)
                    
                    # Add to conversation history for context in next phases
                    transcript["conversation_history"].append({
                        "phase": phase,
                        "alter_name": alter.name,
                        "alter_id": alter.id,
                        "response": response
                    })
                    
                    print(f"{alter.name}: {response[:100]}...")
                    
                except Exception as e:
                    print(f"Error getting response from {alter.name}: {e}")
                    contribution = {
                        "alter_id": alter.id,
                        "alter_name": alter.name,
                        "response": f"Error: Could not generate response ({str(e)})"
                    }
                    phase_data["contributions"].append(contribution)
            
            transcript["phases"].append(phase_data)
        
        # Generate final decision using Gemini (moderator)
        try:
            decision_prompt = self._build_decision_prompt(transcript)
            final_decision = self.gemini_client.invoke(decision_prompt)
            transcript["final_decision"] = final_decision
        except Exception as e:
            transcript["final_decision"] = f"Error generating final decision: {str(e)}"
        
        # Log metrics
        log_metrics({
            "user_prompt": user_prompt,
            "assigned_teams": assigned_teams,
            "use_rag": use_rag,
            "num_alters": len(participating_alters),
            "num_phases": len(phases)
        })
        
        print("\nRound completed.")
        return transcript

    def _build_decision_prompt(self, transcript: Dict[str, Any]) -> str:
        """
        Builds a prompt for the moderator (Gemini) to make the final decision.
        """
        prompt = f"""You are the Moderator for a multi-agent discussion. Review the following discussion and provide a final decision or recommendation.

User's original question: {transcript['user_prompt']}

"""
        
        if transcript['rag_context']:
            prompt += f"Available context:\n{transcript['rag_context']}\n\n"
        
        prompt += "Discussion phases:\n\n"
        
        for phase in transcript['phases']:
            prompt += f"=== {phase['phase_name']} ===\n"
            for contrib in phase['contributions']:
                prompt += f"{contrib['alter_name']}: {contrib['response']}\n\n"
        
        prompt += """Based on this multi-agent discussion, provide:
1. A clear final decision or recommendation
2. Key supporting points from the discussion
3. Any remaining concerns or next steps

Keep your response concise but comprehensive."""
        
        return prompt

if __name__ == "__main__":
    # This assumes the backend is running.
    agent = OrchestratorAgent()
    result = agent.run_round("How can I improve my app's UI using modern tools?", use_rag=True)
    print(json.dumps(result, indent=2))