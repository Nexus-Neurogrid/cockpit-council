"""Tests for council orchestration."""

import pytest

from cockpit.council.graph import Council
from cockpit.council.events import CouncilEvent, CouncilResult
from cockpit.agents.tech import TechAgent
from cockpit.agents.biz import BizAgent

from conftest import MockProvider


class TestCouncilInit:
    def test_requires_agents(self):
        with pytest.raises(ValueError, match="at least one agent"):
            Council(agents=[])

    def test_creates_default_chairman(self):
        provider = MockProvider()
        council = Council(agents=[TechAgent(provider)], provider=provider)
        assert council.chairman.name == "chairman"

    def test_uses_first_agent_provider_as_fallback(self):
        provider = MockProvider()
        council = Council(agents=[TechAgent(provider)])
        assert council.chairman.provider is provider


class TestCouncilDeliberate:
    @pytest.mark.asyncio
    async def test_deliberate_returns_result(self):
        provider = MockProvider(response="Test opinion")
        chairman_provider = MockProvider(response="Final synthesis")

        from cockpit.council.synthesis import Chairman

        council = Council(
            agents=[TechAgent(provider), BizAgent(provider)],
            chairman=Chairman(chairman_provider),
        )

        result = await council.deliberate("Test query")
        assert isinstance(result, CouncilResult)
        assert result.query == "Test query"
        assert len(result.opinions) == 2
        assert result.opinions[0]["agent"] == "tech"
        assert result.opinions[1]["agent"] == "biz"
        assert result.synthesis == "Final synthesis"

    @pytest.mark.asyncio
    async def test_deliberate_parallel(self):
        provider = MockProvider(response="Parallel opinion")
        chairman_provider = MockProvider(response="Parallel synthesis")

        from cockpit.council.synthesis import Chairman

        council = Council(
            agents=[TechAgent(provider), BizAgent(provider)],
            chairman=Chairman(chairman_provider),
            parallel=True,
        )

        result = await council.deliberate("Test parallel")
        assert len(result.opinions) == 2

    @pytest.mark.asyncio
    async def test_deliberate_with_context(self):
        provider = MockProvider()
        council = Council(agents=[TechAgent(provider)], provider=provider)

        result = await council.deliberate(
            "Test", context={"Project": "MyApp"}
        )
        assert result.synthesis is not None


class TestCouncilStream:
    @pytest.mark.asyncio
    async def test_stream_yields_events(self):
        provider = MockProvider(response="Streamed output")
        council = Council(agents=[TechAgent(provider)], provider=provider)

        events = []
        async for event in council.stream("Test stream"):
            events.append(event)

        # Expect: agent_start, agent_chunk(s), agent_complete,
        #         chairman_start, chairman_chunk(s), chairman_complete
        types = [e.type for e in events]
        assert "agent_start" in types
        assert "agent_complete" in types
        assert "chairman_start" in types
        assert "chairman_complete" in types

    @pytest.mark.asyncio
    async def test_stream_event_order(self):
        provider = MockProvider(response="Output")
        council = Council(
            agents=[TechAgent(provider), BizAgent(provider)],
            provider=provider,
        )

        agents_seen = []
        async for event in council.stream("Order test"):
            if event.type == "agent_start":
                agents_seen.append(event.agent)

        assert agents_seen == ["tech", "biz"]
