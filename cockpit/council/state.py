"""Council state management for LangGraph orchestration."""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict


class AgentOpinion(TypedDict):
    """A single agent's opinion on the query."""

    agent: str
    content: str


class CouncilState(TypedDict):
    """State flowing through the LangGraph council deliberation.

    The ``opinions`` list uses LangGraph's ``add`` reducer so each agent node
    can append its opinion without overwriting previous ones.
    """

    query: str
    opinions: Annotated[list[AgentOpinion], add]
    synthesis: str | None
    current_agent: str | None
    context: dict[str, Any] | None
    agent_memories: dict[str, dict] | None
