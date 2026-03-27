"""Memory-backed deliberation example.

Shows how to pass historical context to the council so agents
can reference past decisions.

Run with: python examples/with_memory.py
"""

import asyncio

from cockpit import Council, TechAgent, BizAgent
from cockpit.providers.anthropic import create_anthropic_provider


async def main():
    provider = create_anthropic_provider()

    # Simulate pre-loaded memory context
    agent_memories = {
        "tech": {
            "decisions": [
                "Chose Next.js over Remix for the frontend — better Vercel integration",
                "PostgreSQL selected over MongoDB — relational data model fits better",
            ],
            "learnings": [
                "Microservices added too much operational overhead for a 2-person team",
            ],
        },
        "biz": {
            "decisions": [
                "Target market: B2B SaaS companies with 10-50 employees",
                "Pricing: freemium model with $49/mo pro tier",
            ],
            "learnings": [
                "Enterprise sales cycle was too long — pivoted to self-serve",
            ],
        },
    }

    council = Council(
        agents=[TechAgent(provider), BizAgent(provider)],
        provider=provider,
    )

    result = await council.deliberate(
        "Should we add a marketplace for third-party integrations?",
        agent_memories=agent_memories,
    )

    print(result.synthesis)


if __name__ == "__main__":
    asyncio.run(main())
