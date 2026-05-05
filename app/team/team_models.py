"""
Team data models for OpenManus.

Defines Team and TeamMessage structures for multi-agent collaboration.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schema import Message


class TeamMessage(BaseModel):
    """Represents a message in team chat."""

    id: str = Field(..., description="Unique message ID")
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    sender_name: str = Field(..., description="Who sent this message")
    mention_target: str = Field(
        default="@all", description="@all or @agent_name for targeting"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class Team(BaseModel):
    """Represents a team of agents working together."""

    id: str = Field(..., description="Unique team ID")
    name: str = Field(..., description="Team name")
    goal: str = Field(..., description="Team's core objective")
    rules: List[str] = Field(default_factory=list, description="Team rules to follow")
    agent_ids: List[str] = Field(
        default_factory=list, description="List of agent IDs in the team"
    )
    messages: List[TeamMessage] = Field(
        default_factory=list, description="Team chat history"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


class TeamContext(BaseModel):
    """Context passed to agents when executing team messages."""

    name: str
    goal: str
    rules: List[str]

    def to_prompt_string(self) -> str:
        """Convert to a string for injection into system prompt."""
        prompt = f'You are a member of team "{self.name}".\n'
        if self.goal:
            prompt += f"Team goal: {self.goal}\n"
        if self.rules:
            prompt += "Team rules you must follow:\n"
            for i, rule in enumerate(self.rules, 1):
                prompt += f"{i}. {rule}\n"
        return prompt
