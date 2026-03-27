"""Growth Lead / Business Strategist specialist agent."""

from cockpit.agents.base import BaseAgent
from cockpit.prompts.biz import BIZ_SYSTEM_PROMPT
from cockpit.providers.base import ChatProvider


class BizAgent(BaseAgent):
    """Growth Lead — evaluates market potential, ROI, and strategic alignment."""

    def __init__(self, provider: ChatProvider, system_prompt: str | None = None) -> None:
        super().__init__(
            name="biz",
            role="Growth Lead",
            system_prompt=system_prompt or BIZ_SYSTEM_PROMPT,
            provider=provider,
        )
