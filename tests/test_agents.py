"""Tests for agent implementations."""

import pytest

from cockpit.agents.base import BaseAgent
from cockpit.agents.tech import TechAgent
from cockpit.agents.art import ArtAgent
from cockpit.agents.biz import BizAgent
from cockpit.agents.legal import LegalAgent
from cockpit.agents.cfo import CFOAgent
from cockpit.agents.security import SecurityAgent
from cockpit.council.state import CouncilState


def _make_state(query="Test query", context=None, memories=None):
    return CouncilState(
        query=query,
        opinions=[],
        synthesis=None,
        current_agent=None,
        context=context,
        agent_memories=memories,
    )


class TestAgentInit:
    def test_tech_agent(self, mock_provider):
        agent = TechAgent(mock_provider)
        assert agent.name == "tech"
        assert agent.role == "Tech Lead"

    def test_art_agent(self, mock_provider):
        agent = ArtAgent(mock_provider)
        assert agent.name == "art"
        assert agent.role == "Art Director"

    def test_biz_agent(self, mock_provider):
        agent = BizAgent(mock_provider)
        assert agent.name == "biz"
        assert agent.role == "Growth Lead"

    def test_legal_agent(self, mock_provider):
        agent = LegalAgent(mock_provider)
        assert agent.name == "legal"
        assert agent.role == "Legal Advisor"

    def test_cfo_agent(self, mock_provider):
        agent = CFOAgent(mock_provider)
        assert agent.name == "cfo"
        assert agent.role == "CFO"

    def test_security_agent(self, mock_provider):
        agent = SecurityAgent(mock_provider)
        assert agent.name == "security"
        assert agent.role == "Security Consultant"

    def test_custom_prompt(self, mock_provider):
        agent = TechAgent(mock_provider, system_prompt="Custom prompt")
        assert agent.system_prompt == "Custom prompt"


class TestAgentEvaluate:
    @pytest.mark.asyncio
    async def test_evaluate_returns_opinion(self, mock_provider):
        agent = TechAgent(mock_provider)
        state = _make_state()
        opinion = await agent.evaluate(state)
        assert opinion["agent"] == "tech"
        assert opinion["content"] == "Mock response"
        assert mock_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_evaluate_includes_query(self, mock_provider):
        agent = TechAgent(mock_provider)
        state = _make_state(query="Should we use Rust?")
        await agent.evaluate(state)
        user_msg = mock_provider.last_messages[1].content
        assert "Should we use Rust?" in user_msg

    @pytest.mark.asyncio
    async def test_evaluate_includes_context(self, mock_provider):
        agent = TechAgent(mock_provider)
        state = _make_state(context={"Project": "E-commerce platform"})
        await agent.evaluate(state)
        user_msg = mock_provider.last_messages[1].content
        assert "E-commerce platform" in user_msg

    @pytest.mark.asyncio
    async def test_evaluate_includes_memory(self, mock_provider):
        agent = TechAgent(mock_provider)
        memories = {
            "tech": {
                "decisions": ["Chose PostgreSQL over MongoDB"],
                "learnings": [],
            }
        }
        state = _make_state(memories=memories)
        await agent.evaluate(state)
        user_msg = mock_provider.last_messages[1].content
        assert "PostgreSQL" in user_msg


class TestAgentStream:
    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self, mock_provider):
        agent = TechAgent(mock_provider)
        state = _make_state()
        chunks = []
        async for chunk in agent.stream(state):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert "".join(chunks).strip() == "Mock response"
