"""Extended agent tests — edge cases, all 6 agents, prompt assembly."""

import pytest

from cockpit.agents.base import BaseAgent
from cockpit.agents.tech import TechAgent
from cockpit.agents.art import ArtAgent
from cockpit.agents.biz import BizAgent
from cockpit.agents.legal import LegalAgent
from cockpit.agents.cfo import CFOAgent
from cockpit.agents.security import SecurityAgent
from cockpit.council.state import CouncilState

from conftest import MockProvider


def _state(query="Test", context=None, memories=None):
    return CouncilState(
        query=query,
        opinions=[],
        synthesis=None,
        current_agent=None,
        context=context,
        agent_memories=memories,
    )


class TestAllAgentsEvaluate:
    """Run evaluate on every agent to catch import or prompt errors."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("agent_cls,name", [
        (TechAgent, "tech"),
        (ArtAgent, "art"),
        (BizAgent, "biz"),
        (LegalAgent, "legal"),
        (CFOAgent, "cfo"),
        (SecurityAgent, "security"),
    ])
    async def test_each_agent_evaluates(self, agent_cls, name):
        provider = MockProvider(response=f"{name} opinion")
        agent = agent_cls(provider)
        opinion = await agent.evaluate(_state("Should we do X?"))
        assert opinion["agent"] == name
        assert opinion["content"] == f"{name} opinion"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("agent_cls,name", [
        (TechAgent, "tech"),
        (ArtAgent, "art"),
        (BizAgent, "biz"),
        (LegalAgent, "legal"),
        (CFOAgent, "cfo"),
        (SecurityAgent, "security"),
    ])
    async def test_each_agent_streams(self, agent_cls, name):
        provider = MockProvider(response=f"{name} streamed")
        agent = agent_cls(provider)
        chunks = []
        async for chunk in agent.stream(_state()):
            chunks.append(chunk)
        assert len(chunks) > 0
        full = "".join(chunks).strip()
        assert name in full


class TestAgentEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_query(self):
        provider = MockProvider()
        agent = TechAgent(provider)
        opinion = await agent.evaluate(_state(query=""))
        assert opinion["agent"] == "tech"
        # Should still invoke the provider
        assert provider.call_count == 1

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        provider = MockProvider()
        agent = TechAgent(provider)
        long_query = "Should we " + "refactor the system " * 500
        opinion = await agent.evaluate(_state(query=long_query))
        assert opinion["agent"] == "tech"
        # Verify the full query was passed through
        user_msg = provider.last_messages[1].content
        assert "refactor the system" in user_msg

    @pytest.mark.asyncio
    async def test_unicode_query(self):
        provider = MockProvider()
        agent = ArtAgent(provider)
        opinion = await agent.evaluate(
            _state(query="Should we localize for 日本語 and العربية markets?")
        )
        assert opinion["content"] == "Mock response"
        user_msg = provider.last_messages[1].content
        assert "日本語" in user_msg
        assert "العربية" in user_msg

    @pytest.mark.asyncio
    async def test_multiline_query(self):
        provider = MockProvider()
        agent = BizAgent(provider)
        query = "Line 1: Should we pivot?\nLine 2: Market is shrinking.\nLine 3: Competitors emerging."
        opinion = await agent.evaluate(_state(query=query))
        user_msg = provider.last_messages[1].content
        assert "Line 1" in user_msg
        assert "Line 3" in user_msg

    @pytest.mark.asyncio
    async def test_multiple_context_sections(self):
        provider = MockProvider()
        agent = TechAgent(provider)
        context = {
            "Project": "E-commerce v2",
            "Sprint": "Sprint 14 — auth refactor",
            "GitHub": "5 open PRs, 2 failing CI",
        }
        await agent.evaluate(_state(context=context))
        user_msg = provider.last_messages[1].content
        assert "E-commerce v2" in user_msg
        assert "Sprint 14" in user_msg
        assert "5 open PRs" in user_msg

    @pytest.mark.asyncio
    async def test_empty_context_values_skipped(self):
        provider = MockProvider()
        agent = TechAgent(provider)
        context = {"Project": "MyApp", "Empty": "", "None": None}
        await agent.evaluate(_state(context=context))
        user_msg = provider.last_messages[1].content
        assert "MyApp" in user_msg
        # Empty and None values should not appear as sections
        assert "## Empty" not in user_msg
        assert "## None" not in user_msg

    @pytest.mark.asyncio
    async def test_memory_with_dict_items(self):
        """Memory items can be dicts with a 'content' key (from DB)."""
        provider = MockProvider()
        agent = TechAgent(provider)
        memories = {
            "tech": {
                "decisions": [
                    {"content": "Chose monolith over microservices", "importance": 0.9},
                    "Plain string decision",
                ],
                "learnings": [{"content": "Redis caching reduced latency 40%"}],
            }
        }
        await agent.evaluate(_state(memories=memories))
        user_msg = provider.last_messages[1].content
        assert "monolith" in user_msg
        assert "Plain string decision" in user_msg
        assert "Redis" in user_msg

    @pytest.mark.asyncio
    async def test_memory_for_wrong_agent_ignored(self):
        """Agent should only see its own memories."""
        provider = MockProvider()
        agent = TechAgent(provider)
        memories = {
            "biz": {"decisions": ["Target SME market"]},
        }
        await agent.evaluate(_state(memories=memories))
        user_msg = provider.last_messages[1].content
        assert "SME" not in user_msg

    @pytest.mark.asyncio
    async def test_system_prompt_present(self):
        provider = MockProvider()
        agent = TechAgent(provider)
        await agent.evaluate(_state())
        system_msg = provider.last_messages[0].content
        assert "Tech Lead" in system_msg
        assert "Verdict" in system_msg

    @pytest.mark.asyncio
    async def test_custom_agent_from_base(self):
        """Users can create agents from BaseAgent directly."""
        provider = MockProvider(response="Custom output")
        agent = BaseAgent(
            name="qa",
            role="QA Engineer",
            system_prompt="You are a QA engineer. Find bugs.",
            provider=provider,
        )
        opinion = await agent.evaluate(_state("Test the login flow"))
        assert opinion["agent"] == "qa"
        assert opinion["content"] == "Custom output"
        assert "QA Engineer" in provider.last_messages[1].content
