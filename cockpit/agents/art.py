"""Art Director specialist agent."""

from cockpit.agents.base import BaseAgent
from cockpit.prompts.art import ART_SYSTEM_PROMPT
from cockpit.providers.base import ChatProvider


class ArtAgent(BaseAgent):
    """Art Director — evaluates UX, brand coherence, and design quality."""

    def __init__(self, provider: ChatProvider, system_prompt: str | None = None) -> None:
        super().__init__(
            name="art",
            role="Art Director",
            system_prompt=system_prompt or ART_SYSTEM_PROMPT,
            provider=provider,
        )
