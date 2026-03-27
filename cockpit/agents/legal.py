"""Legal Advisor specialist agent."""

from cockpit.agents.base import BaseAgent
from cockpit.prompts.legal import LEGAL_SYSTEM_PROMPT
from cockpit.providers.base import ChatProvider


class LegalAgent(BaseAgent):
    """Legal Advisor — evaluates compliance, contracts, and legal exposure."""

    def __init__(self, provider: ChatProvider, system_prompt: str | None = None) -> None:
        super().__init__(
            name="legal",
            role="Legal Advisor",
            system_prompt=system_prompt or LEGAL_SYSTEM_PROMPT,
            provider=provider,
        )
