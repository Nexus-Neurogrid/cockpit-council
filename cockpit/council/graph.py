"""Council — LangGraph-powered multi-agent deliberation."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from cockpit.agents.base import BaseAgent
from cockpit.artifacts.parser import ArtifactParser
from cockpit.council.events import CouncilEvent, CouncilResult
from cockpit.council.state import AgentOpinion, CouncilState
from cockpit.council.synthesis import Chairman
from cockpit.providers.base import ChatProvider


class Council:
    """Multi-agent deliberation council.

    Orchestrates a set of specialist agents followed by a chairman synthesis
    using LangGraph.

    Usage::

        council = Council(
            agents=[TechAgent(provider), BizAgent(provider)],
            provider=provider,
        )
        result = await council.deliberate("Should we adopt microservices?")

    """

    def __init__(
        self,
        agents: list[BaseAgent],
        provider: ChatProvider | None = None,
        chairman: Chairman | None = None,
        parallel: bool = False,
    ) -> None:
        if not agents:
            raise ValueError("Council requires at least one agent")

        self.agents = agents
        self.parallel = parallel

        # Chairman uses the explicitly provided one, or creates a default
        if chairman:
            self.chairman = chairman
        elif provider:
            self.chairman = Chairman(provider=provider)
        else:
            # Use first agent's provider as fallback
            self.chairman = Chairman(provider=agents[0].provider)

        self._artifact_parser = ArtifactParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def deliberate(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        agent_memories: dict[str, dict] | None = None,
    ) -> CouncilResult:
        """Run a full council deliberation (non-streaming).

        Returns a ``CouncilResult`` with opinions, synthesis, and artifacts.
        """
        result = CouncilResult(query=query)

        # Collect opinions
        if self.parallel:
            opinions = await self._run_parallel(query, context, agent_memories)
        else:
            opinions = await self._run_sequential(query, context, agent_memories)
        result.opinions = opinions

        # Chairman synthesis
        state = self._build_state(query, context, agent_memories)
        state["opinions"] = opinions
        chairman_opinion = await self.chairman.evaluate(state)
        result.synthesis = chairman_opinion["content"]

        # Parse artifacts from synthesis
        result.artifacts = self._artifact_parser.parse(result.synthesis)

        return result

    async def stream(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        agent_memories: dict[str, dict] | None = None,
    ) -> AsyncGenerator[CouncilEvent, None]:
        """Stream the council deliberation event by event.

        Yields ``CouncilEvent`` objects as agents produce output.
        """
        state = self._build_state(query, context, agent_memories)
        opinions: list[AgentOpinion] = []

        # Agent evaluation phase
        for agent in self.agents:
            yield CouncilEvent(type="agent_start", agent=agent.name)

            full_content = []
            async for chunk in agent.stream(state):
                full_content.append(chunk)
                yield CouncilEvent(
                    type="agent_chunk", agent=agent.name, content=chunk
                )

            content = "".join(full_content)
            opinion = AgentOpinion(agent=agent.name, content=content)
            opinions.append(opinion)
            state["opinions"] = opinions

            yield CouncilEvent(
                type="agent_complete", agent=agent.name, content=content
            )

        # Chairman synthesis phase
        yield CouncilEvent(type="chairman_start", agent="chairman")

        full_synthesis = []
        async for chunk in self.chairman.stream(state):
            full_synthesis.append(chunk)
            yield CouncilEvent(
                type="chairman_chunk", agent="chairman", content=chunk
            )

        synthesis = "".join(full_synthesis)
        yield CouncilEvent(
            type="chairman_complete", agent="chairman", content=synthesis
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_state(
        self,
        query: str,
        context: dict | None,
        agent_memories: dict | None,
    ) -> CouncilState:
        return CouncilState(
            query=query,
            opinions=[],
            synthesis=None,
            current_agent=None,
            context=context,
            agent_memories=agent_memories,
        )

    async def _run_sequential(
        self, query: str, context: dict | None, agent_memories: dict | None
    ) -> list[AgentOpinion]:
        state = self._build_state(query, context, agent_memories)
        opinions: list[AgentOpinion] = []
        for agent in self.agents:
            opinion = await agent.evaluate(state)
            opinions.append(opinion)
            state["opinions"] = opinions
        return opinions

    async def _run_parallel(
        self, query: str, context: dict | None, agent_memories: dict | None
    ) -> list[AgentOpinion]:
        state = self._build_state(query, context, agent_memories)

        async def run(agent: BaseAgent) -> AgentOpinion:
            return await agent.evaluate(state)

        return list(await asyncio.gather(*[run(a) for a in self.agents]))
