"""Tests for Claude Code CLI provider — unit tests (no actual CLI calls)."""

import os
import pytest
from unittest.mock import patch, AsyncMock

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from cockpit.providers.claude_code import (
    ClaudeCodeProvider,
    _messages_to_prompt,
)


class TestMessagesToPrompt:
    def test_extracts_system_and_user(self):
        messages = [
            SystemMessage(content="You are a tech lead"),
            HumanMessage(content="Should we use Rust?"),
        ]
        system, user = _messages_to_prompt(messages)
        assert system == "You are a tech lead"
        assert user == "Should we use Rust?"

    def test_no_system_message(self):
        messages = [HumanMessage(content="Hello")]
        system, user = _messages_to_prompt(messages)
        assert system == ""
        assert user == "Hello"

    def test_multiple_user_messages(self):
        messages = [
            SystemMessage(content="sys"),
            HumanMessage(content="First"),
            HumanMessage(content="Second"),
        ]
        system, user = _messages_to_prompt(messages)
        assert system == "sys"
        assert "First" in user
        assert "Second" in user

    def test_empty_messages(self):
        system, user = _messages_to_prompt([])
        assert system == ""
        assert user == ""


class TestClaudeCodeProviderInit:
    def test_raises_when_cli_not_found(self):
        with patch("cockpit.providers.claude_code.ClaudeCodeProvider._find_cli", return_value=None):
            with patch("os.path.isfile", return_value=False):
                with pytest.raises(RuntimeError, match="Claude Code CLI not found"):
                    ClaudeCodeProvider()

    def test_finds_direct_cli(self):
        with patch("cockpit.providers.claude_code.ClaudeCodeProvider._find_cli", return_value="/usr/bin/claude"):
            provider = ClaudeCodeProvider()
            assert provider._cli == "/usr/bin/claude"
            assert not provider._use_npx

    def test_falls_back_to_npx(self):
        with patch("cockpit.providers.claude_code.ClaudeCodeProvider._find_cli", return_value=None):
            with patch("os.path.isfile", side_effect=lambda p: p == "/opt/homebrew/bin/npx"):
                provider = ClaudeCodeProvider()
                assert provider._use_npx
                assert provider._cli == "/opt/homebrew/bin/npx"


class TestCommandBuilding:
    def _make_provider(self, use_npx=False):
        with patch("cockpit.providers.claude_code.ClaudeCodeProvider._find_cli", return_value="/usr/bin/claude"):
            provider = ClaudeCodeProvider()
        if use_npx:
            provider._use_npx = True
            provider._cli = "/opt/homebrew/bin/npx"
            provider._node_dir = "/opt/homebrew/bin"
        return provider

    def test_basic_command(self):
        provider = self._make_provider()
        cmd = provider._build_command("system prompt", "user query")
        assert cmd[0] == "/usr/bin/claude"
        assert "--print" in cmd
        assert "--system-prompt" in cmd
        assert "system prompt" in cmd
        assert "user query" == cmd[-1]

    def test_command_without_system(self):
        provider = self._make_provider()
        cmd = provider._build_command("", "user query")
        assert "--system-prompt" not in cmd
        assert "user query" == cmd[-1]

    def test_command_with_model(self):
        with patch("cockpit.providers.claude_code.ClaudeCodeProvider._find_cli", return_value="/usr/bin/claude"):
            provider = ClaudeCodeProvider(model="claude-opus-4-20250514")
        cmd = provider._build_command("sys", "query")
        assert "--model" in cmd
        assert "claude-opus-4-20250514" in cmd

    def test_npx_command(self):
        provider = self._make_provider(use_npx=True)
        cmd = provider._build_command("sys", "query")
        assert cmd[0] == "/opt/homebrew/bin/npx"
        assert "-y" in cmd
        assert "@anthropic-ai/claude-code" in cmd
        assert "--print" in cmd

    def test_env_with_npx(self):
        provider = self._make_provider(use_npx=True)
        env = provider._get_env()
        assert env is not None
        assert "/opt/homebrew/bin" in env["PATH"]

    def test_env_without_npx(self):
        provider = self._make_provider(use_npx=False)
        env = provider._get_env()
        assert env is None


class TestClaudeCodeProviderInvoke:
    @pytest.mark.asyncio
    async def test_ainvoke_success(self):
        with patch("cockpit.providers.claude_code.ClaudeCodeProvider._find_cli", return_value="/usr/bin/claude"):
            provider = ClaudeCodeProvider()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Agent response text", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await provider.ainvoke([
                SystemMessage(content="Be a tech lead"),
                HumanMessage(content="Evaluate this"),
            ])

        assert isinstance(result, AIMessage)
        assert result.content == "Agent response text"

    @pytest.mark.asyncio
    async def test_ainvoke_failure(self):
        with patch("cockpit.providers.claude_code.ClaudeCodeProvider._find_cli", return_value="/usr/bin/claude"):
            provider = ClaudeCodeProvider()

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error: invalid"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Claude Code CLI failed"):
                await provider.ainvoke([HumanMessage(content="Test")])
