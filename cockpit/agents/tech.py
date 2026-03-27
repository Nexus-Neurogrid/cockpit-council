"""Tech Lead specialist agent."""

from cockpit.agents.base import BaseAgent
from cockpit.prompts.tech import TECH_SYSTEM_PROMPT
from cockpit.providers.base import ChatProvider


class TechAgent(BaseAgent):
    """Tech Lead — evaluates feasibility, architecture, and technical risks."""

    def __init__(self, provider: ChatProvider, system_prompt: str | None = None) -> None:
        super().__init__(
            name="tech",
            role="Tech Lead",
            system_prompt=system_prompt or TECH_SYSTEM_PROMPT,
            provider=provider,
        )
