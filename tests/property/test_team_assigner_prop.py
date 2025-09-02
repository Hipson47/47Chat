"""
Property-based tests for team_assigner module using Hypothesis.
Tests critical pure functions with comprehensive input generation.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, rule

from backend.orchestrator.utils.team_assigner import auto_assign_teams


class TeamAssignerStateMachine(RuleBasedStateMachine):
    """State machine for testing team assignment behavior."""

    def __init__(self):
        super().__init__()
        self.teams_data = {}
        self.last_assignment = []

    @rule(
        team_name=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters=['\n', '\r'])),
        description=st.text(min_size=10, max_size=200),
        keywords=st.lists(st.text(min_size=3, max_size=15), min_size=1, max_size=5)
    )
    def add_team(self, team_name, description, keywords):
        """Add a team to the meta prompt structure."""
        # Ensure team name is valid
        assume(team_name.strip())
        assume(team_name not in self.teams_data)

        self.teams_data[team_name] = {
            "description": " ".join(keywords) + " " + description,
            "competencies": ["general"]
        }

    @rule(
        prompt=st.text(min_size=5, max_size=500),
        target_teams=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=3)
    )
    def assign_teams(self, prompt, target_teams):
        """Test team assignment with various prompts."""
        # Filter to only teams that exist
        existing_target_teams = [t for t in target_teams if t in self.teams_data]

        meta_prompt = {"teams": self.teams_data}
        if not self.teams_data:
            # Empty teams case
            meta_prompt = {}

        result = auto_assign_teams(prompt, meta_prompt)
        self.last_assignment = result

        # Basic invariants
        assert isinstance(result, list)
        assert all(isinstance(team, str) for team in result)

        # No duplicates in result
        assert len(result) == len(set(result))

        # If we have teams data, result should contain valid team names
        if self.teams_data:
            valid_team_names = set(self.teams_data.keys())
            assert all(team in valid_team_names for team in result)


# Property-based tests for individual functions
@given(
    prompt=st.text(min_size=1, max_size=1000),
    meta_prompt=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.dictionaries(
            keys=st.sampled_from(["description", "competencies"]),
            values=st.one_of(
                st.text(min_size=1, max_size=500),
                st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10)
            )
        ),
        min_size=0,
        max_size=10
    )
)
def test_auto_assign_teams_properties(prompt, meta_prompt):
    """Test properties of auto_assign_teams function."""
    # Ensure prompt is not empty after stripping
    assume(prompt.strip())

    # Ensure teams section exists or is handled gracefully
    if "teams" not in meta_prompt:
        meta_prompt = {"teams": {}}

    result = auto_assign_teams(prompt, meta_prompt)

    # Invariants that should always hold
    assert isinstance(result, list)
    assert all(isinstance(team, str) for team in result)
    assert len(result) == len(set(result))  # No duplicates

    # If no teams defined, should return fallback teams
    if not meta_prompt.get("teams"):
        expected_fallbacks = {"backend_team", "integration_team", "operations_team"}
        assert set(result).issubset(expected_fallbacks)
        assert len(result) >= 1  # Should have at least one fallback team


@given(
    prompt=st.text(min_size=0, max_size=1000),
    team_name=st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_characters=['\n', '\r', '\t'])),
    description=st.text(min_size=10, max_size=200)
)
def test_auto_assign_teams_with_specific_team(prompt, team_name, description):
    """Test team assignment with a specific team configuration."""
    assume(team_name.strip())
    assume(description.strip())

    meta_prompt = {
        "teams": {
            team_name: {
                "description": description,
                "competencies": ["test"]
            }
        }
    }

    result = auto_assign_teams(prompt, meta_prompt)

    # Should either return the specific team or fallbacks
    if prompt.strip():
        # If prompt contains keywords from description, might match the team
        assert isinstance(result, list)
    else:
        # Empty prompt should return fallbacks
        assert len(result) >= 1


@given(
    prompt=st.text(min_size=1, max_size=500),
    num_teams=st.integers(min_value=1, max_value=5)
)
def test_auto_assign_teams_multiple_teams(prompt, num_teams):
    """Test with multiple teams configured."""
    assume(prompt.strip())

    teams = {}
    for i in range(num_teams):
        team_name = f"team_{i}"
        teams[team_name] = {
            "description": f"This is team {i} that handles specific functionality",
            "competencies": [f"skill_{i}"]
        }

    meta_prompt = {"teams": teams}
    result = auto_assign_teams(prompt, meta_prompt)

    # Result should be valid
    assert isinstance(result, list)
    assert all(isinstance(team, str) for team in result)

    # All returned teams should be from the configured teams
    valid_team_names = set(teams.keys())
    assert all(team in valid_team_names for team in result)


# Test the state machine
TestTeamAssignerMachine = TeamAssignerStateMachine.TestCase


@pytest.mark.property
@settings(max_examples=50, deadline=None)
@given(
    prompt=st.text(min_size=1, max_size=200),
    meta_prompt=st.fixed_dictionaries({
        "teams": st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.fixed_dictionaries({
                "description": st.text(min_size=5, max_size=100),
                "competencies": st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3)
            }),
            min_size=0,
            max_size=3
        )
    })
)
def test_auto_assign_teams_comprehensive(prompt, meta_prompt):
    """Comprehensive property test with realistic data structures."""
    assume(prompt.strip())

    result = auto_assign_teams(prompt, meta_prompt)

    # Basic properties
    assert isinstance(result, list)
    assert len(result) >= 1  # Should always return at least one team

    # If teams exist, all results should be valid team names
    if meta_prompt.get("teams"):
        valid_teams = set(meta_prompt["teams"].keys())
        assert all(team in valid_teams for team in result)

    # No duplicates
    assert len(result) == len(set(result))

    # Teams should be strings
    assert all(isinstance(team, str) and team.strip() for team in result)
