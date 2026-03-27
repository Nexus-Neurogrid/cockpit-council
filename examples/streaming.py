"""Streaming deliberation example — real-time output.

Run with: python examples/streaming.py
"""

import asyncio

from cockpit import Council, TechAgent, BizAgent, SecurityAgent
from cockpit.providers.claude_code import create_claude_code_provider


BOLD = "\033[1m"
RESET = "\033[0m"
COLORS = {
    "tech": "\033[34m",
    "biz": "\033[33m",
    "security": "\033[31m",
    "chairman": "\033[37;1m",
}


async def main():
    provider = create_claude_code_provider()

    council = Council(
        agents=[
            TechAgent(provider),
            BizAgent(provider),
            SecurityAgent(provider),
        ],
        provider=provider,
    )

    async for event in council.stream(
        "Should we store user payment data ourselves or use Stripe?"
    ):
        color = COLORS.get(event.agent, "")

        if event.type in ("agent_start", "chairman_start"):
            label = event.agent.upper()
            print(f"\n{color}{BOLD}=== {label} ==={RESET}")
        elif event.type in ("agent_chunk", "chairman_chunk"):
            print(event.content or "", end="", flush=True)
        elif event.type in ("agent_complete", "chairman_complete"):
            print()


if __name__ == "__main__":
    asyncio.run(main())
