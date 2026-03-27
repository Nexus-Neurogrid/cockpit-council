"""Tests for memory store protocol and state integration."""

import pytest

from cockpit.council.state import CouncilState, AgentOpinion
from cockpit.agents.base import BaseAgent
from conftest import MockProvider


class TestMemoryInState:
    """Test that memory context flows correctly into agent prompts."""

    def test_empty_memories_no_section(self):
        provider = MockProvider()
        agent = BaseAgent(
            name="test", role="Test", system_prompt="test", provider=provider
        )
        state = CouncilState(
            query="test",
            opinions=[],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories=None,
        )
        section = agent._build_memory_section(state)
        assert section == ""

    def test_memories_included_in_prompt(self):
        provider = MockProvider()
        agent = BaseAgent(
            name="tech", role="Tech", system_prompt="test", provider=provider
        )
        state = CouncilState(
            query="test",
            opinions=[],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories={
                "tech": {
                    "decisions": ["Used PostgreSQL"],
                    "learnings": ["Microservices too complex"],
                    "preferences": [],
                }
            },
        )
        section = agent._build_memory_section(state)
        assert "PostgreSQL" in section
        assert "Microservices" in section
        assert "Decisions" in section
        assert "Learnings" in section

    def test_memories_truncated(self):
        provider = MockProvider()
        agent = BaseAgent(
            name="tech", role="Tech", system_prompt="test", provider=provider
        )
        long_memory = "x" * 500
        state = CouncilState(
            query="test",
            opinions=[],
            synthesis=None,
            current_agent=None,
            context=None,
            agent_memories={
                "tech": {
                    "decisions": [long_memory],
                }
            },
        )
        section = agent._build_memory_section(state)
        # Should be truncated to 200 chars
        assert len(section.split("\n")[-1]) <= 205  # "- " + 200 + buffer
