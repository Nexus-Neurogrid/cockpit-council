"""Custom agent example — create your own specialist.

Run with: python examples/custom_agent.py
"""

import asyncio

from cockpit import BaseAgent, Council
from cockpit.council.state import CouncilState
from cockpit.providers.anthropic import create_anthropic_provider


DEVOPS_PROMPT = """\
You are the DevOps / Infrastructure Lead of the council.

## Your Role
You evaluate infrastructure impact, deployment complexity, and operational
readiness. You think in terms of reliability, scalability, and cost.

## Response Format
- **Verdict**: READY / NEEDS WORK / BLOCKER
- **Infrastructure Impact**: [Assessment]
- **Deployment Complexity**: [simple / medium / complex]
- **Operational Risks**: [List]
- **Recommendations**: [Concrete actions]

Maximum 250 words.
"""


class DevOpsAgent(BaseAgent):
    """Custom DevOps specialist."""

    def __init__(self, provider, system_prompt=None):
        super().__init__(
            name="devops",
            role="DevOps Lead",
            system_prompt=system_prompt or DEVOPS_PROMPT,
            provider=provider,
        )


async def main():
    provider = create_anthropic_provider()

    council = Council(
        agents=[DevOpsAgent(provider)],
        provider=provider,
    )

    result = await council.deliberate(
        "Should we migrate from Heroku to Kubernetes?"
    )

    print(result.synthesis)


if __name__ == "__main__":
    asyncio.run(main())
