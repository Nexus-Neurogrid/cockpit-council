"""Extended council tests — integration, chairman, edge cases."""

import pytest

from cockpit.council.graph import Council
from cockpit.council.events import CouncilEvent, CouncilResult
from cockpit.council.synthesis import Chairman, DEFAULT_ROLE_MAP
from cockpit.council.state import AgentOpinion, CouncilState
from cockpit.agents.tech import TechAgent
from cockpit.agents.art import ArtAgent
from cockpit.agents.biz import BizAgent
from cockpit.agents.legal import LegalAgent
from cockpit.agents.cfo import CFOAgent
from cockpit.agents.security import SecurityAgent

from conftest import MockProvider


class TestChairmanSynthesis:
    @pytest.mark.asyncio
    async def test_chairman_receives_all_opinions(self):
        provider = MockProvider(response="Synthesis complete")
        chairman = Chairman(provider)

        state = CouncilState(
            query="Test query",
            opinions=[
                AgentOpinion(agent="tech", content="Tech says GO"),
                AgentOpinion(agent="biz", content="Biz says OPPORTUNITY"),
            ],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories=None,
        )

        opinion = await chairman.evaluate(state)
        user_msg = provider.last_messages[1].content
        assert "Tech says GO" in user_msg
        assert "Biz says OPPORTUNITY" in user_msg
        assert "Test query" in user_msg

    @pytest.mark.asyncio
    async def test_chairman_role_mapping(self):
        provider = MockProvider(response="Done")
        chairman = Chairman(provider)

        state = CouncilState(
            query="Q",
            opinions=[
                AgentOpinion(agent="tech", content="opinion"),
                AgentOpinion(agent="art", content="opinion"),
                AgentOpinion(agent="cfo", content="opinion"),
            ],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories=None,
        )

        await chairman.evaluate(state)
        user_msg = provider.last_messages[1].content
        assert "Tech Lead" in user_msg
        assert "Art Director" in user_msg
        assert "CFO" in user_msg

    @pytest.mark.asyncio
    async def test_chairman_custom_role_map(self):
        provider = MockProvider(response="Done")
        chairman = Chairman(provider, role_map={"tech": "CTO", "biz": "CEO"})

        state = CouncilState(
            query="Q",
            opinions=[AgentOpinion(agent="tech", content="x")],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories=None,
        )

        await chairman.evaluate(state)
        user_msg = provider.last_messages[1].content
        assert "CTO" in user_msg

    @pytest.mark.asyncio
    async def test_chairman_with_context(self):
        provider = MockProvider(response="Done")
        chairman = Chairman(provider)

        state = CouncilState(
            query="Q",
            opinions=[AgentOpinion(agent="tech", content="GO")],
            synthesis=None,
            current_agent=None,
            context={"Project": "Cockpit v2", "Sprint": "Sprint 5"},
            agent_memories=None,
        )

        await chairman.evaluate(state)
        user_msg = provider.last_messages[1].content
        assert "Cockpit v2" in user_msg
        assert "Sprint 5" in user_msg

    @pytest.mark.asyncio
    async def test_chairman_no_opinions(self):
        provider = MockProvider(response="No data to synthesize")
        chairman = Chairman(provider)

        state = CouncilState(
            query="Q",
            opinions=[],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories=None,
        )

        opinion = await chairman.evaluate(state)
        assert opinion["content"] == "No data to synthesize"

    @pytest.mark.asyncio
    async def test_chairman_streams(self):
        provider = MockProvider(response="Streaming synthesis")
        chairman = Chairman(provider)

        state = CouncilState(
            query="Q",
            opinions=[AgentOpinion(agent="tech", content="GO")],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories=None,
        )

        chunks = []
        async for chunk in chairman.stream(state):
            chunks.append(chunk)
        assert len(chunks) > 0

    def test_default_role_map_covers_all_agents(self):
        expected = {"tech", "art", "biz", "legal", "cfo", "security"}
        assert expected == set(DEFAULT_ROLE_MAP.keys())


class TestCouncilIntegration:
    """Full deliberation flow with all agent types."""

    @pytest.mark.asyncio
    async def test_full_council_all_6_agents(self):
        provider = MockProvider(response="Agent analysis complete")
        chairman_provider = MockProvider(response="Chairman: GO with conditions")

        council = Council(
            agents=[
                TechAgent(provider),
                ArtAgent(provider),
                BizAgent(provider),
                LegalAgent(provider),
                CFOAgent(provider),
                SecurityAgent(provider),
            ],
            chairman=Chairman(chairman_provider),
        )

        result = await council.deliberate("Should we launch in the EU market?")

        assert len(result.opinions) == 6
        agents = [o["agent"] for o in result.opinions]
        assert agents == ["tech", "art", "biz", "legal", "cfo", "security"]
        assert result.synthesis == "Chairman: GO with conditions"
        # Provider was called 6 times for agents
        assert provider.call_count == 6
        # Chairman provider called once
        assert chairman_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_full_council_stream_all_6(self):
        provider = MockProvider(response="Analysis")
        chairman_provider = MockProvider(response="Synthesis")

        council = Council(
            agents=[
                TechAgent(provider),
                ArtAgent(provider),
                BizAgent(provider),
                LegalAgent(provider),
                CFOAgent(provider),
                SecurityAgent(provider),
            ],
            chairman=Chairman(chairman_provider),
        )

        events = []
        async for event in council.stream("EU launch?"):
            events.append(event)

        # 6 agents × (start + chunks + complete) + chairman × (start + chunks + complete)
        starts = [e for e in events if e.type == "agent_start"]
        completes = [e for e in events if e.type == "agent_complete"]
        chairman_starts = [e for e in events if e.type == "chairman_start"]
        chairman_completes = [e for e in events if e.type == "chairman_complete"]

        assert len(starts) == 6
        assert len(completes) == 6
        assert len(chairman_starts) == 1
        assert len(chairman_completes) == 1

        # Verify agent order
        agent_order = [e.agent for e in starts]
        assert agent_order == ["tech", "art", "biz", "legal", "cfo", "security"]

    @pytest.mark.asyncio
    async def test_parallel_all_6_agents(self):
        provider = MockProvider(response="Parallel opinion")
        chairman_provider = MockProvider(response="Parallel synthesis")

        council = Council(
            agents=[
                TechAgent(provider),
                ArtAgent(provider),
                BizAgent(provider),
                LegalAgent(provider),
                CFOAgent(provider),
                SecurityAgent(provider),
            ],
            chairman=Chairman(chairman_provider),
            parallel=True,
        )

        result = await council.deliberate("Parallel test")
        assert len(result.opinions) == 6
        # All agents should have been called
        assert provider.call_count == 6

    @pytest.mark.asyncio
    async def test_context_flows_to_all_agents(self):
        """Verify context is visible to every agent in the chain."""
        providers = {}
        agents = []
        for name, cls in [
            ("tech", TechAgent),
            ("biz", BizAgent),
            ("security", SecurityAgent),
        ]:
            p = MockProvider(response=f"{name} ok")
            providers[name] = p
            agents.append(cls(p))

        chairman_p = MockProvider(response="synthesis")
        council = Council(agents=agents, chairman=Chairman(chairman_p))

        await council.deliberate(
            "Test context flow",
            context={"Budget": "$50k", "Timeline": "Q3 2026"},
        )

        for name, p in providers.items():
            user_msg = p.last_messages[1].content
            assert "$50k" in user_msg, f"{name} didn't receive Budget context"
            assert "Q3 2026" in user_msg, f"{name} didn't receive Timeline context"

    @pytest.mark.asyncio
    async def test_opinions_accumulate_sequentially(self):
        """In sequential mode, later agents should see earlier opinions in state."""
        call_order = []

        class TrackingProvider:
            async def ainvoke(self, messages, **kwargs):
                from langchain_core.messages import AIMessage
                # Record the user prompt to verify context
                user_msg = messages[1].content
                call_order.append(user_msg)
                return AIMessage(content="opinion")

            async def astream(self, messages, **kwargs):
                from langchain_core.messages import AIMessage
                yield AIMessage(content="opinion")

        provider = TrackingProvider()
        chairman_p = MockProvider(response="synthesis")

        council = Council(
            agents=[TechAgent(provider), BizAgent(provider)],
            chairman=Chairman(chairman_p),
        )

        await council.deliberate("Test accumulation")
        assert len(call_order) == 2

    @pytest.mark.asyncio
    async def test_council_with_single_agent(self):
        provider = MockProvider(response="Solo opinion")
        council = Council(agents=[TechAgent(provider)], provider=provider)

        result = await council.deliberate("Solo test")
        assert len(result.opinions) == 1
        assert result.synthesis is not None

    @pytest.mark.asyncio
    async def test_council_deliberate_with_memory(self):
        provider = MockProvider(response="Memory-aware opinion")
        council = Council(agents=[TechAgent(provider)], provider=provider)

        result = await council.deliberate(
            "Test with memory",
            agent_memories={
                "tech": {"decisions": ["Chose Rust for performance"]},
                "chairman": {"decisions": ["Always validate with security"]},
            },
        )

        assert result.opinions[0]["content"] == "Memory-aware opinion"

    @pytest.mark.asyncio
    async def test_artifacts_extracted_from_synthesis(self):
        """If chairman output contains artifact blocks, they should be parsed."""
        synthesis_with_artifact = '''Here's my decision: GO

```task
{"title": "Implement auth migration", "priority": "high"}
```

Proceed with caution.'''

        provider = MockProvider(response="Agent ok")
        chairman_p = MockProvider(response=synthesis_with_artifact)

        council = Council(
            agents=[TechAgent(provider)],
            chairman=Chairman(chairman_p),
        )

        result = await council.deliberate("Auth migration plan")
        assert len(result.artifacts) == 1
        assert result.artifacts[0].artifact_type == "task"
        assert result.artifacts[0].content["title"] == "Implement auth migration"
