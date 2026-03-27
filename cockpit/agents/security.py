"""Security Consultant specialist agent."""

from cockpit.agents.base import BaseAgent
from cockpit.prompts.security import SECURITY_SYSTEM_PROMPT
from cockpit.providers.base import ChatProvider


class SecurityAgent(BaseAgent):
    """Security Consultant — evaluates threats, vulnerabilities, and compliance."""

    def __init__(self, provider: ChatProvider, system_prompt: str | None = None) -> None:
        super().__init__(
            name="security",
            role="Security Consultant",
            system_prompt=system_prompt or SECURITY_SYSTEM_PROMPT,
            provider=provider,
        )
