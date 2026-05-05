"""
Team management functions for OpenManus.

Handles team CRUD operations and storage.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from app.team.team_models import Team, TeamMessage, TeamContext


class TeamManager:
    """Manager for team operations and persistence."""

    def __init__(self, storage_dir: str = "workspace/teams"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.teams: Dict[str, Team] = {}
        self._load_all_teams()

    def _load_all_teams(self) -> None:
        """Load all teams from storage."""
        for team_file in self.storage_dir.glob("*.json"):
            try:
                with open(team_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    team = Team(**data)
                    self.teams[team.id] = team
            except Exception as e:
                print(f"Error loading team {team_file}: {e}")

    def _save_team(self, team: Team) -> None:
        """Save a single team to storage."""
        file_path = self.storage_dir / f"{team.id}.json"
        team.updated_at = datetime.now()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(team.model_dump(mode="json"), f, indent=2, default=str)

    def _delete_team_file(self, team_id: str) -> None:
        """Delete a team file from storage."""
        file_path = self.storage_dir / f"{team_id}.json"
        if file_path.exists():
            file_path.unlink()

    def create_team(
        self, team_id: str, name: str, goal: str = "", rules: List[str] = None
    ) -> Team:
        """Create a new team.

        Args:
            team_id: Unique identifier for the team
            name: Team name
            goal: Team's core objective
            rules: List of team rules (optional)

        Returns:
            Created Team object
        """
        if team_id in self.teams:
            raise ValueError(f"Team {team_id} already exists")

        team = Team(
            id=team_id,
            name=name,
            goal=goal,
            rules=rules or [],
            agent_ids=[],
            messages=[],
        )
        self.teams[team_id] = team
        self._save_team(team)
        return team

    def get_team(self, team_id: str) -> Optional[Team]:
        """Get a team by ID."""
        return self.teams.get(team_id)

    def get_all_teams(self) -> List[Team]:
        """Get all teams."""
        return list(self.teams.values())

    def update_team_goal(self, team_id: str, goal: str) -> Team:
        """Update a team's goal."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        team.goal = goal
        self._save_team(team)
        return team

    def update_team_rules(self, team_id: str, rules: List[str]) -> Team:
        """Update a team's rules."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        team.rules = [r for r in rules if r.strip()]  # Remove empty rules
        self._save_team(team)
        return team

    def add_agent_to_team(self, team_id: str, agent_id: str) -> Team:
        """Add an agent to a team."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        if agent_id not in team.agent_ids:
            team.agent_ids.append(agent_id)
            self._save_team(team)
        return team

    def remove_agent_from_team(self, team_id: str, agent_id: str) -> Team:
        """Remove an agent from a team."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        if agent_id in team.agent_ids:
            team.agent_ids.remove(agent_id)
            self._save_team(team)
        return team

    def set_team_agents(self, team_id: str, agent_ids: List[str]) -> Team:
        """Set the complete list of agents in a team."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        team.agent_ids = agent_ids
        self._save_team(team)
        return team

    def add_message_to_team(
        self,
        team_id: str,
        message_id: str,
        role: str,
        content: str,
        sender_name: str,
        mention_target: str = "@all",
    ) -> TeamMessage:
        """Add a message to a team's chat history."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")

        msg = TeamMessage(
            id=message_id,
            role=role,
            content=content,
            sender_name=sender_name,
            mention_target=mention_target,
            timestamp=datetime.now(),
        )
        team.messages.append(msg)
        self._save_team(team)
        return msg

    def get_team_messages(self, team_id: str) -> List[TeamMessage]:
        """Get all messages in a team."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        return team.messages

    def get_team_context(self, team_id: str) -> TeamContext:
        """Get context for an agent working with this team."""
        team = self.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        return TeamContext(name=team.name, goal=team.goal, rules=team.rules)

    def dissolve_team(self, team_id: str) -> None:
        """Delete a team and all its data.

        Note: Agents are NOT deleted, only the team grouping is removed.
        """
        if team_id not in self.teams:
            raise ValueError(f"Team {team_id} not found")
        self._delete_team_file(team_id)
        del self.teams[team_id]

    def get_teams_for_agent(self, agent_id: str) -> List[Team]:
        """Get all teams that contain a specific agent."""
        return [t for t in self.teams.values() if agent_id in t.agent_ids]
