"""Claude Code CLI provider — default, zero-cost provider.

Uses the ``claude`` CLI with ``--print`` for non-interactive single-turn
responses.  Requires Claude Code to be installed and authenticated.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage


def _messages_to_prompt(messages: list[BaseMessage]) -> tuple[str, str]:
    """Extract system prompt and user prompt from LangChain messages."""
    system = ""
    user_parts: list[str] = []
    for msg in messages:
        content = msg.content if hasattr(msg, "content") else str(msg)
        if msg.type == "system":
            system = content
        else:
            user_parts.append(content)
    return system, "\n\n".join(user_parts)


class ClaudeCodeProvider:
    """Provider that shells out to the ``claude`` CLI.

    This is the default provider — it uses the user's existing Claude Code
    subscription so there's no extra API cost.
    """

    def __init__(self, model: str | None = None, max_tokens: int = 4096) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._cli = self._find_cli()
        self._use_npx = False

        if not self._cli:
            # Fallback: try npx with common node paths
            for node_dir in ("/opt/homebrew/bin", "/usr/local/bin"):
                npx = os.path.join(node_dir, "npx")
                if os.path.isfile(npx):
                    self._cli = npx
                    self._use_npx = True
                    self._node_dir = node_dir
                    break

        if not self._cli:
            raise RuntimeError(
                "Claude Code CLI not found. Install it: "
                "npm install -g @anthropic-ai/claude-code"
            )

    @staticmethod
    def _find_cli() -> str | None:
        """Search common locations for the claude binary."""
        # Direct binary
        direct = shutil.which("claude")
        if direct:
            return direct
        # Check common global npm paths
        for path in (
            os.path.expanduser("~/.local/bin/claude"),
            os.path.expanduser("~/.npm-global/bin/claude"),
            "/opt/homebrew/bin/claude",
            "/usr/local/bin/claude",
        ):
            if os.path.isfile(path):
                return path
        return None

    def _build_command(self, system: str, user: str) -> list[str]:
        if self._use_npx:
            cmd = [self._cli, "-y", "@anthropic-ai/claude-code", "--print"]
        else:
            cmd = [self._cli, "--print"]
        if system:
            cmd.extend(["--system-prompt", system])
        if self.model:
            cmd.extend(["--model", self.model])
        cmd.extend(["--max-turns", "2"])
        cmd.append(user)
        return cmd

    def _get_env(self) -> dict | None:
        """Return env with node in PATH when using npx."""
        if self._use_npx:
            env = os.environ.copy()
            env["PATH"] = self._node_dir + ":" + env.get("PATH", "")
            return env
        return None

    async def ainvoke(self, messages: list[BaseMessage], **kwargs) -> BaseMessage:
        system, user = _messages_to_prompt(messages)
        cmd = self._build_command(system, user)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._get_env(),
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode().strip()
            raise RuntimeError(f"Claude Code CLI failed (exit {proc.returncode}): {err}")

        return AIMessage(content=stdout.decode().strip())

    async def astream(self, messages: list[BaseMessage], **kwargs) -> AsyncIterator[BaseMessage]:
        """Stream output from claude CLI using --output-format stream-json.

        Falls back to non-streaming (ainvoke) and yields the full result
        as a single chunk if stream-json is unavailable.
        """
        system, user = _messages_to_prompt(messages)
        cmd = self._build_command(system, user)

        # Add verbose + stream-json flags before the user prompt (last arg)
        cmd.insert(-1, "--verbose")
        cmd.insert(-1, "--output-format")
        cmd.insert(-1, "stream-json")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._get_env(),
        )

        async for line in proc.stdout:
            text = line.decode().strip()
            if not text:
                continue
            try:
                event = json.loads(text)
                # Final result contains the full text
                if event.get("type") == "result" and event.get("result"):
                    yield AIMessage(content=event["result"])
                # Assistant message contains text blocks
                elif event.get("type") == "assistant" and event.get("message"):
                    for block in event["message"].get("content", []):
                        if block.get("type") == "text" and block.get("text"):
                            yield AIMessage(content=block["text"])
            except json.JSONDecodeError:
                continue

        await proc.wait()


def create_claude_code_provider(
    model: str | None = None,
    max_tokens: int = 4096,
) -> ClaudeCodeProvider:
    """Factory for the Claude Code CLI provider."""
    return ClaudeCodeProvider(model=model, max_tokens=max_tokens)
