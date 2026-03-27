"""Paperclip adapter example.

Shows how to expose a cockpit-council instance as an HTTP endpoint
that Paperclip can call as an agent via its HTTP adapter.

The adapter accepts Paperclip heartbeat payloads, runs a council
deliberation on the task description, and returns the synthesis.
"""

import asyncio
import json
import sys

from cockpit import Council, TechAgent, BizAgent, SecurityAgent
from cockpit.providers.claude_code import create_claude_code_provider


async def handle_heartbeat(payload: dict) -> dict:
    """Process a Paperclip heartbeat and return a council deliberation."""
    task = payload.get("task", {})
    query = task.get("description", task.get("title", ""))

    if not query:
        return {"status": "idle", "message": "No task to evaluate"}

    provider = create_claude_code_provider()
    council = Council(
        agents=[
            TechAgent(provider),
            BizAgent(provider),
            SecurityAgent(provider),
        ],
        provider=provider,
    )

    # Pass Paperclip context (goal ancestry, project info) as council context
    context = {}
    if task.get("goal"):
        context["Goal"] = task["goal"]
    if task.get("project"):
        context["Project"] = task["project"]

    result = await council.deliberate(query, context=context)

    return {
        "status": "completed",
        "synthesis": result.synthesis,
        "opinions": result.opinions,
        "artifacts": [
            {"type": a.artifact_type, "content": a.content}
            for a in result.artifacts
        ],
    }


async def main():
    """Example: simulate a Paperclip heartbeat."""
    payload = {
        "task": {
            "title": "Evaluate API rate limiting strategy",
            "description": "Should we implement rate limiting at the API gateway level or application level? Consider cost, complexity, and security.",
            "goal": "Build reliable API infrastructure for 10k concurrent users",
            "project": "Platform v2",
        }
    }

    result = await handle_heartbeat(payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
