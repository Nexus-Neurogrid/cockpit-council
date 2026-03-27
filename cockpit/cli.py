"""cockpit CLI — run council deliberations from the terminal."""

from __future__ import annotations

import argparse
import asyncio
import sys

# ANSI color codes
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"

AGENT_COLORS = {
    "tech": "\033[34m",      # blue
    "art": "\033[35m",       # magenta
    "biz": "\033[33m",       # yellow
    "legal": "\033[36m",     # cyan
    "cfo": "\033[32m",       # green
    "security": "\033[31m",  # red
    "chairman": "\033[37;1m",  # bold white
}

AGENT_MAP = {
    "tech": "TechAgent",
    "art": "ArtAgent",
    "biz": "BizAgent",
    "legal": "LegalAgent",
    "cfo": "CFOAgent",
    "security": "SecurityAgent",
}


def _get_provider(provider_name: str, model: str | None):
    """Create a provider from name."""
    if provider_name == "claude-code":
        from cockpit.providers.claude_code import create_claude_code_provider
        return create_claude_code_provider(model=model)
    elif provider_name == "anthropic":
        from cockpit.providers.anthropic import create_anthropic_provider
        return create_anthropic_provider(model=model or "claude-sonnet-4-20250514")
    elif provider_name == "openai":
        from cockpit.providers.openai import create_openai_provider
        return create_openai_provider(model=model or "gpt-4o")
    elif provider_name == "ollama":
        from cockpit.providers.ollama import create_ollama_provider
        return create_ollama_provider(model=model or "llama3.1")
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def _get_agents(agent_names: list[str], provider):
    """Instantiate agent classes from names."""
    from cockpit.agents.art import ArtAgent
    from cockpit.agents.biz import BizAgent
    from cockpit.agents.cfo import CFOAgent
    from cockpit.agents.legal import LegalAgent
    from cockpit.agents.security import SecurityAgent
    from cockpit.agents.tech import TechAgent

    classes = {
        "tech": TechAgent,
        "art": ArtAgent,
        "biz": BizAgent,
        "legal": LegalAgent,
        "cfo": CFOAgent,
        "security": SecurityAgent,
    }

    agents = []
    for name in agent_names:
        cls = classes.get(name)
        if cls is None:
            print(f"Unknown agent: {name}. Available: {', '.join(classes)}", file=sys.stderr)
            sys.exit(1)
        agents.append(cls(provider=provider))
    return agents


async def _run_ask(args):
    """Execute a council deliberation."""
    from cockpit.council.graph import Council

    provider = _get_provider(args.provider, args.model)
    agents = _get_agents(args.agents, provider)
    council = Council(agents=agents, provider=provider, parallel=args.parallel)

    query = args.query
    if not query:
        if sys.stdin.isatty():
            print("Enter your question (Ctrl+D to submit):")
        query = sys.stdin.read().strip()

    if not query:
        print("No query provided.", file=sys.stderr)
        sys.exit(1)

    if args.no_stream:
        result = await council.deliberate(query)
        for opinion in result.opinions:
            color = AGENT_COLORS.get(opinion["agent"], "")
            print(f"\n{color}{BOLD}=== {opinion['agent'].upper()} ==={RESET}")
            print(opinion["content"])
        print(f"\n{AGENT_COLORS['chairman']}{BOLD}=== CHAIRMAN ==={RESET}")
        print(result.synthesis)
    else:
        async for event in council.stream(query):
            color = AGENT_COLORS.get(event.agent, "")

            if event.type == "agent_start":
                print(f"\n{color}{BOLD}=== {event.agent.upper()} ==={RESET}")
            elif event.type == "agent_chunk":
                print(event.content or "", end="", flush=True)
            elif event.type == "agent_complete":
                print()
            elif event.type == "chairman_start":
                print(f"\n{color}{BOLD}=== CHAIRMAN ==={RESET}")
            elif event.type == "chairman_chunk":
                print(event.content or "", end="", flush=True)
            elif event.type == "chairman_complete":
                print()


def main():
    parser = argparse.ArgumentParser(
        prog="cockpit",
        description="Multi-agent deliberation council",
    )
    subparsers = parser.add_subparsers(dest="command")

    # cockpit ask
    ask_parser = subparsers.add_parser("ask", help="Run a council deliberation")
    ask_parser.add_argument("query", nargs="?", help="Question for the council")
    ask_parser.add_argument(
        "--agents",
        nargs="+",
        default=["tech", "art", "biz"],
        help="Agents to include (default: tech art biz)",
    )
    ask_parser.add_argument(
        "--provider",
        choices=["claude-code", "anthropic", "openai", "ollama"],
        default="claude-code",
        help="LLM provider (default: claude-code)",
    )
    ask_parser.add_argument("--model", help="Model name override")
    ask_parser.add_argument(
        "--no-stream", action="store_true", help="Disable streaming"
    )
    ask_parser.add_argument(
        "--parallel", action="store_true", help="Run agents in parallel"
    )

    # cockpit init
    subparsers.add_parser("init", help="Initialize database")

    # cockpit version
    subparsers.add_parser("version", help="Show version")

    args = parser.parse_args()

    if args.command == "ask":
        asyncio.run(_run_ask(args))
    elif args.command == "init":
        asyncio.run(_run_init())
    elif args.command == "version":
        from cockpit import __version__
        print(f"cockpit-council v{__version__}")
    else:
        parser.print_help()


async def _run_init():
    """Initialize the embedded database."""
    from cockpit.db.engine import ensure_running
    from cockpit.db.migrations import run_migrations

    print("Starting embedded PostgreSQL...")
    url = await ensure_running()
    print("Running migrations...")
    await run_migrations(url)
    print("Done. cockpit-council is ready.")


if __name__ == "__main__":
    main()
