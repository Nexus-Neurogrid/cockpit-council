# cockpit-council

**Multi-agent deliberation library** — get structured advice from a council of AI specialists.

If ChatGPT is a generalist, cockpit-council is a **boardroom**: Tech Lead, Art Director, Business Strategist, CFO, Legal Advisor, and Security Consultant evaluate your question in parallel, then a Chairman synthesizes their perspectives into a single decision with action items.

## Quick Start

```bash
pip install cockpit-council
```

No API key needed — uses your existing [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installation by default.

```python
import asyncio
from cockpit import Council, TechAgent, BizAgent, SecurityAgent
from cockpit.providers.claude_code import create_claude_code_provider

async def main():
    provider = create_claude_code_provider()
    council = Council(
        agents=[TechAgent(provider), BizAgent(provider), SecurityAgent(provider)],
        provider=provider,
    )
    result = await council.deliberate("Should we store user payment data ourselves or use Stripe?")
    print(result.synthesis)

asyncio.run(main())
```

## CLI

```bash
# Default: 3 agents (tech, art, biz) via Claude Code
cockpit ask "Should we adopt microservices?"

# Pick your agents
cockpit ask "Should we open-source our SDK?" --agents tech biz legal security

# Use a different provider
cockpit ask "Evaluate our pricing strategy" --provider anthropic --model claude-sonnet-4-20250514

# Pipe from stdin
echo "Should we build or buy a CRM?" | cockpit ask

# Initialize embedded database (for persistent memory & artifacts)
cockpit init
```

## How It Works

```
                    ┌─────────────┐
                    │   Query     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │Tech Lead │ │Art Dir   │ │Biz Lead  │  ← Specialist Agents
        │GO/NO-GO  │ │APPROVED/ │ │OPPORTUNITY│
        │          │ │REJECTED  │ │/RISKY    │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │            │
             └─────────────┼────────────┘
                           ▼
                    ┌──────────────┐
                    │  Chairman    │  ← Synthesizes all opinions
                    │  GO/NO-GO/  │
                    │  CONDITIONAL │
                    └──────┬───────┘
                           │
                    ┌──────┴──────┐
                    │   Result    │
                    │  - Decision │
                    │  - Actions  │
                    │  - Artifacts│
                    └─────────────┘
```

Each agent evaluates from their domain expertise and produces a **structured verdict**. The Chairman weighs all perspectives using decision rules (e.g., "if Tech says NO-GO for critical reason, favour caution") and produces a final decision with an action plan.

## Agents

| Agent | Verdict Taxonomy | Focus |
|-------|-----------------|-------|
| **Tech Lead** | GO / NO-GO / CONDITIONAL | Feasibility, architecture, risks, complexity |
| **Art Director** | APPROVED / REJECTED / NEEDS REVISION | UX, brand coherence, simplicity, emotion |
| **Growth Lead** | OPPORTUNITY / RISKY / AVOID | Market potential, ROI, timing, scalability |
| **Legal Advisor** | COMPLIANT / RISK / NON-COMPLIANT | Regulatory compliance, contracts, IP, liability |
| **CFO** | VIABLE / CAUTIOUS / NOT VIABLE | Cost, revenue, cash flow, unit economics |
| **Security Consultant** | SECURE / VULNERABLE / CRITICAL RISK | Threats, vulnerabilities, compliance, mitigations |

## Providers

cockpit-council is **provider-agnostic**. Default is Claude Code (zero-cost).

```python
# Claude Code (default — uses your existing subscription)
from cockpit.providers.claude_code import create_claude_code_provider
provider = create_claude_code_provider()

# Anthropic API
from cockpit.providers.anthropic import create_anthropic_provider
provider = create_anthropic_provider(model="claude-sonnet-4-20250514")

# OpenAI
from cockpit.providers.openai import create_openai_provider
provider = create_openai_provider(model="gpt-4o")

# Ollama (local)
from cockpit.providers.ollama import create_ollama_provider
provider = create_ollama_provider(model="llama3.1")

# Fallback: try Claude, fall back to GPT-4o
from cockpit.providers.fallback import FallbackProvider
provider = FallbackProvider(primary=claude_provider, fallback=openai_provider)
```

## Custom Agents

```python
from cockpit import BaseAgent, Council

class DevOpsAgent(BaseAgent):
    def __init__(self, provider):
        super().__init__(
            name="devops",
            role="DevOps Lead",
            system_prompt="You are the DevOps Lead. Evaluate infrastructure impact...",
            provider=provider,
        )

council = Council(agents=[DevOpsAgent(provider), TechAgent(provider)])
```

## Streaming

```python
async for event in council.stream("Should we migrate to Kubernetes?"):
    if event.type == "agent_start":
        print(f"\n=== {event.agent.upper()} ===")
    elif event.type in ("agent_chunk", "chairman_chunk"):
        print(event.content, end="", flush=True)
```

## Artifacts

Agents can produce structured artifacts (tasks, emails, estimates) embedded in their output:

```python
result = await council.deliberate("Plan the Q2 product launch")
for artifact in result.artifacts:
    print(f"{artifact.artifact_type}: {artifact.content}")
```

## Embedded Database

cockpit-council includes an embedded PostgreSQL for persistent storage:

```bash
cockpit init  # First-time setup
```

Stores: deliberation history, artifacts, agent memories (with pgvector semantic search).

Set `COCKPIT_DATABASE_URL` to use an external Postgres instead.

## Architecture

```
cockpit/
├── agents/      # 6 specialist agents + base class
├── council/     # LangGraph orchestration, chairman synthesis
├── artifacts/   # Parser + DB-backed store
├── db/          # Embedded PostgreSQL + migrations
├── memory/      # pgvector semantic memory
├── providers/   # Claude Code, Anthropic, OpenAI, Ollama
├── prompts/     # English system prompts with verdict taxonomies
└── cli.py       # Terminal interface
```

## License

MIT — built by [Neurogrid](https://neurogrid.io)
