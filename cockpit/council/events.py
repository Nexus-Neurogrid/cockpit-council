"""Event types emitted during council deliberation."""

from __future__ import annotations

from dataclasses import dataclass, field

from cockpit.council.state import AgentOpinion


@dataclass
class CouncilEvent:
    """A single event emitted during streaming deliberation.

    Event types:
        agent_start     — an agent has begun evaluating
        agent_chunk     — a streaming text chunk from an agent
        agent_complete  — an agent has finished
        chairman_start  — the chairman has begun synthesizing
        chairman_chunk  — a streaming text chunk from the chairman
        chairman_complete — the chairman has finished
    """

    type: str
    agent: str
    content: str | None = None


@dataclass
class CouncilResult:
    """Final result of a council deliberation."""

    query: str
    opinions: list[AgentOpinion] = field(default_factory=list)
    synthesis: str = ""
    artifacts: list = field(default_factory=list)
