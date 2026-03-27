"""Chairman — synthesizes agent opinions into a final decision."""

from __future__ import annotations

from cockpit.agents.base import BaseAgent
from cockpit.council.state import CouncilState
from cockpit.prompts.chairman import CHAIRMAN_SYSTEM_PROMPT
from cockpit.providers.base import ChatProvider

DEFAULT_ROLE_MAP = {
    "tech": "Tech Lead",
    "art": "Art Director",
    "biz": "Growth Lead",
    "legal": "Legal Advisor",
    "cfo": "CFO",
    "security": "Security Consultant",
}


class Chairman(BaseAgent):
    """Chairman agent that synthesizes all opinions into a final decision.

    Unlike regular agents, the Chairman receives the assembled opinions
    of all other agents and produces a unified synthesis.
    """

    def __init__(
        self,
        provider: ChatProvider,
        system_prompt: str | None = None,
        role_map: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            name="chairman",
            role="Chairman",
            system_prompt=system_prompt or CHAIRMAN_SYSTEM_PROMPT,
            provider=provider,
        )
        self.role_map = role_map or dict(DEFAULT_ROLE_MAP)

    def _build_user_prompt(self, state: CouncilState) -> str:
        """Assemble the opinions summary for synthesis."""
        sections: list[str] = [f"## Original Query\n{state['query']}"]

        # Context sections
        ctx = state.get("context") or {}
        for key, value in ctx.items():
            if value:
                sections.append(f"## {key}\n{value}")

        # Opinions
        opinions = state.get("opinions") or []
        if opinions:
            sections.append("## Council Opinions")
            for opinion in opinions:
                role = self.role_map.get(opinion["agent"], opinion["agent"])
                sections.append(f"### {role}\n{opinion['content']}")

        # Memory
        memory_section = self._build_memory_section(state)
        if memory_section:
            sections.append(memory_section)

        sections.append(
            "\n---\nSynthesize these perspectives and produce your final decision."
        )
        return "\n\n".join(sections)
