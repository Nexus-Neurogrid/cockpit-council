"""CFO / Financial Architect specialist agent."""

from cockpit.agents.base import BaseAgent
from cockpit.prompts.cfo import CFO_SYSTEM_PROMPT
from cockpit.providers.base import ChatProvider


class CFOAgent(BaseAgent):
    """CFO — evaluates financial feasibility, costs, and cash flow impact."""

    def __init__(self, provider: ChatProvider, system_prompt: str | None = None) -> None:
        super().__init__(
            name="cfo",
            role="CFO",
            system_prompt=system_prompt or CFO_SYSTEM_PROMPT,
            provider=provider,
        )
