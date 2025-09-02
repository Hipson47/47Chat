# orchestrator/utils/team_assigner.py
"""
Utility for automatically assigning teams based on the user prompt.
"""


def auto_assign_teams(prompt, meta_prompt):
    """
    Assigns teams based on keyword matching in the user prompt.

    Args:
        prompt (str): The user's input prompt.
        meta_prompt (dict): The loaded meta_prompt content.

    Returns:
        list: A list of assigned team names.
    """
    assigned_teams = []
    prompt_lower = prompt.lower()

    # Support both legacy and new meta-prompt shapes
    teams_section = meta_prompt.get("teams")
    if teams_section is None and isinstance(meta_prompt.get("meta_prompt"), dict):
        teams_section = meta_prompt["meta_prompt"].get("teams")
    if teams_section is None:
        # Graceful fallback: if teams missing, default to core set
        return [
            "backend_team",
            "integration_team",
            "operations_team",
        ]

    # Simple keyword matching based on team descriptions
    for team_name, team_data in teams_section.items():
        if "description" in team_data:
            # Using simple keywords from description for assignment
            keywords = [kw for kw in team_data["description"].split() if len(kw) > 3]
            if any(keyword in prompt_lower for keyword in keywords):
                assigned_teams.append(team_name)

    # Fallback to core teams if no specific teams are matched
    if not assigned_teams:
        fallback_teams = [
            "backend_team",
            "integration_team",
            "operations_team",
        ]
        assigned_teams.extend(fallback_teams)

    return list(set(assigned_teams))
