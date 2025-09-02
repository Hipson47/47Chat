# backend/orchestrator/agent.py
"""
Main entrypoint for the Orchestrator Agent.
This script orchestrates the entire round flow, including team assignment,
phase execution, model/tool invocation, and metrics logging.
"""

import json
from typing import Any

from .clients.ollama_client import LocalOllamaClient
from .clients.openai_chat_client import OpenAIChatClient
from .clients.openai_client import OpenAIModeratorClient
from .clients.tool_clients import ToolClient
from .utils.loader import load_meta_prompt
from .utils.metrics import log_metrics
from .utils.team_assigner import auto_assign_teams

# Support both package import (backend.orchestrator.agent) and top-level (orchestrator.agent)
try:
    from ..config import settings
    from ..rag_utils import RAGUtils
except (
    ImportError
):  # When 'backend' isn't the parent package and we're running from backend/ dir
    from config import settings
    from rag_utils import RAGUtils
from typing import TypedDict

from langgraph.graph import END, StateGraph


class Alter:
    """
    Represents a single AI alter/agent with specific competencies and personality.
    """

    def __init__(
        self,
        alter_data: dict[str, Any],
        ollama_client: LocalOllamaClient | None = None,
        openai_client: OpenAIChatClient | None = None,
    ):
        self.id = alter_data.get("id")
        self.name = alter_data.get("name", f"Alter {self.id}")
        self.priority = alter_data.get("priority", "Medium")
        self.competencies = alter_data.get("competencies", "")
        self.examples = alter_data.get("examples", [])
        self.ollama_client = ollama_client
        self.openai_client = openai_client

    def build_prompt(
        self,
        phase: str,
        user_prompt: str,
        context: str = "",
        conversation_history: list[dict] = None,
    ) -> str:
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
            "Vote": "Provide your final recommendation with clear reasoning. Vote for the best approach.",
        }

        prompt = f"""You are {self.name}, an expert with the following competencies: {self.competencies}

Your priority level: {self.priority}

Current phase: {phase}
Phase instruction: {phase_instructions.get(phase, "Contribute your expertise to the discussion.")}

User's question/request: {user_prompt}

{context}
{history_text}

Based on your expertise and the current phase, provide your contribution to the discussion. Be specific, actionable, and draw from your competencies. Keep your response focused and under 300 words."""

        return prompt

    def respond(
        self,
        phase: str,
        user_prompt: str,
        context: str = "",
        conversation_history: list[dict] = None,
    ) -> str:
        """
        Gets a response from this alter for the given phase and context.
        """
        prompt = self.build_prompt(phase, user_prompt, context, conversation_history)
        # Route to selected provider
        provider = settings.ALTERS_LLM_PROVIDER.lower()
        if provider == "openai" and self.openai_client is not None:
            response = self.openai_client.invoke(prompt)
        else:
            response = self.ollama_client.invoke(prompt)  # type: ignore[union-attr]
        return response


class OrchestratorAgent:
    """
    The main orchestrator that manages the multi-agent conversation flow.
    """

    def __init__(self, meta_prompt_path: str | None = None):
        """
        Initializes the OrchestratorAgent.
        """
        meta_path = meta_prompt_path or settings.META_PROMPT_PATH
        self.meta_prompt = load_meta_prompt(meta_path)
        self.ollama_client = LocalOllamaClient(model_name=settings.OLLAMA_MODEL)
        self.openai_alter_client = OpenAIChatClient()
        self.moderator_client = OpenAIModeratorClient()
        self.tool_client = ToolClient()
        self.rag_utils = RAGUtils(
            store_path=settings.FAISS_STORE_PATH,
            chunks_path=settings.CHUNKS_PATH,
        )
        self.alters = self._initialize_alters()

    def _get_teams_section(self) -> dict[str, Any]:
        """Return teams section from either legacy or new meta-prompt layout."""
        if isinstance(self.meta_prompt, dict):
            if "teams" in self.meta_prompt:
                return self.meta_prompt.get("teams", {})
            inner = self.meta_prompt.get("meta_prompt")
            if isinstance(inner, dict):
                return inner.get("teams", {})
        return {}

    def _initialize_alters(self) -> dict[int, Alter]:
        """
        Initialize all alters from the meta-prompt configuration.
        """
        alters: dict[int, Alter] = {}

        explicit_alters = (
            self.meta_prompt.get("alters")
            if isinstance(self.meta_prompt, dict)
            else None
        )
        if isinstance(explicit_alters, list) and explicit_alters:
            for alter_data in explicit_alters:
                alter_id = alter_data.get("id")
                if alter_id is not None:
                    alters[alter_id] = Alter(
                        alter_data,
                        ollama_client=self.ollama_client,
                        openai_client=self.openai_alter_client,
                    )
            return alters

        teams = self._get_teams_section()
        for team_name, team_data in teams.items():
            team_desc = team_data.get("description", team_name)
            for alter_id in team_data.get("alters", []):
                if alter_id in alters:
                    continue
                synthetic = {
                    "id": alter_id,
                    "name": f"{team_name.replace('_', ' ').title()} Specialist {alter_id}",
                    "priority": "Medium",
                    "competencies": team_desc,
                    "examples": [],
                }
                alters[alter_id] = Alter(
                    synthetic,
                    ollama_client=self.ollama_client,
                    openai_client=self.openai_alter_client,
                )

        if not alters:
            for alter_id in range(1, 4):
                synthetic = {
                    "id": alter_id,
                    "name": f"Generalist {alter_id}",
                    "priority": "Medium",
                    "competencies": "General software engineering and architecture.",
                    "examples": [],
                }
                alters[alter_id] = Alter(
                    synthetic,
                    ollama_client=self.ollama_client,
                    openai_client=self.openai_alter_client,
                )

        return alters

    def get_alters_for_teams(self, team_names: list[str]) -> list[Alter]:
        """
        Get all alters that belong to the specified teams.
        """
        alter_ids = set()
        teams = self._get_teams_section()

        for team_name in team_names:
            if team_name in teams:
                team_alter_ids = teams[team_name].get("alters", [])
                alter_ids.update(team_alter_ids)

        return [
            self.alters[alter_id] for alter_id in alter_ids if alter_id in self.alters
        ]

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
                chunk_text = (
                    res["chunk"][:200] + "..."
                    if len(res["chunk"]) > 200
                    else res["chunk"]
                )
                context += (
                    f'- Chunk {i + 1}: "{chunk_text}" [score: {res["score"]:.3f}]\n'
                )
            return context
        except Exception as e:
            print(f"Error retrieving RAG context: {e}")
            return ""

    class OrchestrationState(TypedDict, total=False):
        user_prompt: str
        use_rag: bool
        rag_context: str
        assigned_teams: list[str]
        participating_alters: list[Alter]
        phases: list[dict[str, Any]]
        conversation_history: list[dict[str, Any]]
        final_decision: str

    def _run_phase(
        self,
        state: "OrchestratorAgent.OrchestrationState",
        phase_name: str,
    ) -> "OrchestratorAgent.OrchestrationState":
        phase_data = {"phase_name": phase_name, "contributions": []}
        print(f"\n--- Running Phase: {phase_name} ---")

        for alter in state["participating_alters"]:
            try:
                response = alter.respond(
                    phase=phase_name,
                    user_prompt=state["user_prompt"],
                    context=state.get("rag_context", ""),
                    conversation_history=state.get("conversation_history", []),
                )
                contribution = {
                    "alter_id": alter.id,
                    "alter_name": alter.name,
                    "response": response,
                }
                phase_data["contributions"].append(contribution)
                state.setdefault("conversation_history", []).append(
                    {
                        "phase": phase_name,
                        "alter_name": alter.name,
                        "alter_id": alter.id,
                        "response": response,
                    }
                )
                print(f"{alter.name}: {response[:100]}...")
            except Exception as e:
                print(f"Error getting response from {alter.name}: {e}")
                contribution = {
                    "alter_id": alter.id,
                    "alter_name": alter.name,
                    "response": f"Error: Could not generate response ({e!s})",
                }
                phase_data["contributions"].append(contribution)

        state.setdefault("phases", []).append(phase_data)
        return state

    def run_round(self, user_prompt: str, use_rag: bool = False) -> dict[str, Any]:
        """
        Executes the orchestration flow using a LangGraph state machine.
        Returns a detailed transcript of the multi-agent discussion.
        """
        # Prepare initial state
        initial_state: OrchestratorAgent.OrchestrationState = {
            "user_prompt": user_prompt,
            "use_rag": use_rag,
            "rag_context": self.get_rag_context(user_prompt) if use_rag else "",
            "assigned_teams": auto_assign_teams(user_prompt, self.meta_prompt),
            "phases": [],
            "conversation_history": [],
            "final_decision": "",
        }

        participating_alters = self.get_alters_for_teams(
            initial_state["assigned_teams"]
        )
        if not participating_alters:
            participating_alters = [alter for alter in self.alters.values()][:3]
        initial_state["participating_alters"] = participating_alters

        # Define graph nodes (phase handlers)
        def brainstorm_node(state: OrchestratorAgent.OrchestrationState) -> OrchestratorAgent.OrchestrationState:
            return self._run_phase(state, "Brainstorm")

        def review_node(state: OrchestratorAgent.OrchestrationState) -> OrchestratorAgent.OrchestrationState:
            return self._run_phase(state, "CriticalReview")

        def selfverify_node(state: OrchestratorAgent.OrchestrationState) -> OrchestratorAgent.OrchestrationState:
            return self._run_phase(state, "SelfVerify")

        def vote_node(state: OrchestratorAgent.OrchestrationState) -> OrchestratorAgent.OrchestrationState:
            state = self._run_phase(state, "Vote")
            # Generate final decision using OpenAI moderator
            try:
                decision_prompt = self._build_decision_prompt(state)
                state["final_decision"] = self.moderator_client.invoke(decision_prompt)
            except Exception as e:
                state["final_decision"] = f"Error generating final decision: {e!s}"
            return state

        # Build state graph
        graph = StateGraph(OrchestratorAgent.OrchestrationState)
        graph.add_node("brainstorm", brainstorm_node)
        graph.add_node("review", review_node)
        graph.add_node("selfverify", selfverify_node)
        graph.add_node("vote", vote_node)

        # Edges: Brainstorm -> Review -> (optional SelfVerify) -> Vote
        graph.set_entry_point("brainstorm")
        graph.add_edge("brainstorm", "review")

        # Simple conditional: if there are at least 2 contributions, run SelfVerify
        def to_selfverify(state: OrchestratorAgent.OrchestrationState) -> str:
            last_phase = state.get("phases", [])[-1] if state.get("phases") else {}
            contribs = last_phase.get("contributions", []) if last_phase else []
            return "selfverify" if len(contribs) >= 2 else "vote"

        graph.add_conditional_edges(
            "review", to_selfverify, {"selfverify": "selfverify", "vote": "vote"}
        )
        graph.add_edge("selfverify", "vote")
        graph.add_edge("vote", END)

        # Execute graph
        app = graph.compile()
        final_state = app.invoke(initial_state)

        # Ensure the returned transcript is JSON-serializable.
        # The internal state contains Python objects (e.g., `Alter`) that
        # FastAPI cannot serialize directly. We strip those out as they are
        # not used by the frontend and keep only primitive structures.
        serializable_state: dict[str, Any] = {
            key: value
            for key, value in final_state.items()  # type: ignore[union-attr]
            if key != "participating_alters"
        }

        # Log metrics
        log_metrics(
            {
                "user_prompt": user_prompt,
                "assigned_teams": initial_state["assigned_teams"],
                "use_rag": use_rag,
                "num_alters": len(participating_alters),
                "num_phases": len(serializable_state.get("phases", [])),
            }
        )

        print("\nRound completed.")
        return serializable_state  # type: ignore[return-value]

    def _build_decision_prompt(self, transcript: dict[str, Any]) -> str:
        """
        Builds a prompt for the moderator (OpenAI) to make the final decision.
        """
        prompt = f"""You are the Moderator for a multi-agent discussion. Review the following discussion and provide a final decision or recommendation.

User's original question: {transcript["user_prompt"]}

"""

        if transcript["rag_context"]:
            prompt += f"Available context:\n{transcript['rag_context']}\n\n"

        prompt += "Discussion phases:\n\n"

        for phase in transcript["phases"]:
            prompt += f"=== {phase['phase_name']} ===\n"
            for contrib in phase["contributions"]:
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
    result = agent.run_round(
        "How can I improve my app's UI using modern tools?", use_rag=True
    )
    print(json.dumps(result, indent=2))
