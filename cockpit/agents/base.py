"""Agent protocol and base implementation."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Protocol

from langchain_core.messages import HumanMessage, SystemMessage

from cockpit.council.state import AgentOpinion, CouncilState
from cockpit.providers.base import ChatProvider


class Agent(Protocol):
    """Protocol that all council agents must satisfy."""

    name: str
    role: str

    async def evaluate(self, state: CouncilState) -> AgentOpinion: ...

    async def stream(self, state: CouncilState) -> AsyncGenerator[str, None]: ...


class BaseAgent:
    """Concrete base class for council agents.

    Subclass this and set ``name``, ``role``, and ``system_prompt`` to create
    a new specialist.  Override ``_build_user_prompt`` or
    ``_build_system_prompt`` for custom behaviour.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        provider: ChatProvider,
    ) -> None:
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.provider = provider

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def evaluate(self, state: CouncilState) -> AgentOpinion:
        """Run the agent and return its opinion (non-streaming)."""
        messages = self._build_messages(state)
        response = await self.provider.ainvoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        return AgentOpinion(agent=self.name, content=content)

    async def stream(self, state: CouncilState) -> AsyncGenerator[str, None]:
        """Stream the agent's response chunk by chunk."""
        messages = self._build_messages(state)
        async for chunk in self.provider.astream(messages):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            if text:
                yield text

    # ------------------------------------------------------------------
    # Prompt building (override in subclasses for custom logic)
    # ------------------------------------------------------------------

    def _build_messages(self, state: CouncilState) -> list:
        return [
            SystemMessage(content=self._build_system_prompt(state)),
            HumanMessage(content=self._build_user_prompt(state)),
        ]

    def _build_system_prompt(self, state: CouncilState) -> str:
        """Return the system prompt.  Override for dynamic prompts."""
        return self.system_prompt

    def _build_user_prompt(self, state: CouncilState) -> str:
        """Assemble the user prompt from query + context + memory."""
        sections: list[str] = [f"## Query\n{state['query']}"]

        # Append generic context sections
        ctx = state.get("context") or {}
        for key, value in ctx.items():
            if value:
                sections.append(f"## {key}\n{value}")

        # Append memory context
        memory_section = self._build_memory_section(state)
        if memory_section:
            sections.append(memory_section)

        sections.append(
            f"\nAnalyze this situation from your perspective as **{self.role}** "
            f"and provide your structured assessment."
        )
        return "\n\n".join(sections)

    def _build_memory_section(self, state: CouncilState) -> str:
        """Format agent-specific memories into a prompt section."""
        memories = (state.get("agent_memories") or {}).get(self.name)
        if not memories:
            return ""

        parts: list[str] = ["## Relevant Memory"]
        for memory_type in ("decisions", "learnings", "preferences"):
            items = memories.get(memory_type, [])
            if items:
                parts.append(f"### {memory_type.title()}")
                for item in items[:3]:
                    text = item if isinstance(item, str) else item.get("content", "")
                    parts.append(f"- {text[:200]}")
        return "\n".join(parts) if len(parts) > 1 else ""
