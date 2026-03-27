"""Basic council deliberation example.

Run with: python examples/basic_council.py
Requires: pip install cockpit-council[anthropic]
"""

import asyncio

from cockpit import Council, TechAgent, ArtAgent, BizAgent
from cockpit.providers.anthropic import create_anthropic_provider


async def main():
    provider = create_anthropic_provider()

    council = Council(
        agents=[
            TechAgent(provider),
            ArtAgent(provider),
            BizAgent(provider),
        ],
        provider=provider,
    )

    result = await council.deliberate(
        "Should we rebuild our authentication system with passkeys instead of passwords?"
    )

    print("=== OPINIONS ===")
    for opinion in result.opinions:
        print(f"\n--- {opinion['agent'].upper()} ---")
        print(opinion["content"])

    print("\n=== CHAIRMAN SYNTHESIS ===")
    print(result.synthesis)

    if result.artifacts:
        print(f"\n=== ARTIFACTS ({len(result.artifacts)}) ===")
        for artifact in result.artifacts:
            print(f"  - {artifact.artifact_type}: {artifact.content}")


if __name__ == "__main__":
    asyncio.run(main())
