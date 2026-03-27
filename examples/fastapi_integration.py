"""FastAPI SSE integration example.

Run with:
    pip install fastapi uvicorn sse-starlette
    uvicorn examples.fastapi_integration:app --reload

Then: curl -N http://localhost:8000/council/stream -d '{"query": "Should we add AI features?"}'
"""

from fastapi import FastAPI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from cockpit import Council, TechAgent, ArtAgent, BizAgent
from cockpit.providers.anthropic import create_anthropic_provider

app = FastAPI(title="Cockpit Council API")


class CouncilRequest(BaseModel):
    query: str
    agents: list[str] = ["tech", "art", "biz"]


@app.post("/council/stream")
async def council_stream(request: CouncilRequest):
    provider = create_anthropic_provider()

    agent_map = {
        "tech": TechAgent,
        "art": ArtAgent,
        "biz": BizAgent,
    }

    agents = [agent_map[name](provider) for name in request.agents if name in agent_map]
    council = Council(agents=agents, provider=provider)

    async def event_generator():
        async for event in council.stream(request.query):
            yield {
                "event": event.type,
                "data": f'{{"agent": "{event.agent}", "content": "{(event.content or "").replace(chr(10), "\\n")}"}}'
            }

    return EventSourceResponse(event_generator())


@app.post("/council/deliberate")
async def council_deliberate(request: CouncilRequest):
    provider = create_anthropic_provider()

    agent_map = {
        "tech": TechAgent,
        "art": ArtAgent,
        "biz": BizAgent,
    }

    agents = [agent_map[name](provider) for name in request.agents if name in agent_map]
    council = Council(agents=agents, provider=provider)

    result = await council.deliberate(request.query)

    return {
        "query": result.query,
        "opinions": result.opinions,
        "synthesis": result.synthesis,
        "artifacts": [
            {"type": a.artifact_type, "content": a.content}
            for a in result.artifacts
        ],
    }
