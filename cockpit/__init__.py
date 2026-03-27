"""cockpit-council — Multi-agent deliberation library.

Get structured advice from a council of AI specialists.

Quick start::

    from cockpit import Council, TechAgent, BizAgent
    from cockpit.providers.claude_code import create_claude_code_provider

    provider = create_claude_code_provider()
    council = Council(
        agents=[TechAgent(provider), BizAgent(provider)],
        provider=provider,
    )
    result = await council.deliberate("Should we adopt microservices?")
    print(result.synthesis)

"""

__version__ = "0.1.0"

# Core
from cockpit.agents.art import ArtAgent

# Agents
from cockpit.agents.base import Agent, BaseAgent
from cockpit.agents.biz import BizAgent
from cockpit.agents.cfo import CFOAgent
from cockpit.agents.legal import LegalAgent
from cockpit.agents.security import SecurityAgent
from cockpit.agents.tech import TechAgent

# Artifacts
from cockpit.artifacts.parser import ArtifactParser
from cockpit.artifacts.types import ParsedArtifact
from cockpit.council.events import CouncilEvent, CouncilResult
from cockpit.council.graph import Council
from cockpit.council.state import AgentOpinion, CouncilState
from cockpit.council.synthesis import Chairman

# Providers
from cockpit.providers.base import ChatProvider
from cockpit.providers.fallback import FallbackProvider

__all__ = [
    "Council",
    "CouncilState",
    "CouncilEvent",
    "CouncilResult",
    "AgentOpinion",
    "Chairman",
    "Agent",
    "BaseAgent",
    "TechAgent",
    "ArtAgent",
    "BizAgent",
    "LegalAgent",
    "CFOAgent",
    "SecurityAgent",
    "ArtifactParser",
    "ParsedArtifact",
    "ChatProvider",
    "FallbackProvider",
]
