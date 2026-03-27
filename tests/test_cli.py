"""Tests for CLI argument parsing and setup."""

import pytest
from unittest.mock import patch, AsyncMock

from cockpit.cli import main, _get_agents, AGENT_MAP


class TestCLIAgentResolution:
    def test_get_agents_default(self):
        from conftest import MockProvider
        provider = MockProvider()
        agents = _get_agents(["tech", "art", "biz"], provider)
        assert len(agents) == 3
        assert agents[0].name == "tech"
        assert agents[1].name == "art"
        assert agents[2].name == "biz"

    def test_get_agents_all_six(self):
        from conftest import MockProvider
        provider = MockProvider()
        agents = _get_agents(
            ["tech", "art", "biz", "legal", "cfo", "security"], provider
        )
        assert len(agents) == 6
        names = [a.name for a in agents]
        assert names == ["tech", "art", "biz", "legal", "cfo", "security"]

    def test_get_agents_unknown_exits(self):
        from conftest import MockProvider
        provider = MockProvider()
        with pytest.raises(SystemExit):
            _get_agents(["tech", "unknown_agent"], provider)

    def test_agent_map_complete(self):
        expected = {"tech", "art", "biz", "legal", "cfo", "security"}
        assert set(AGENT_MAP.keys()) == expected


class TestCLIEntryPoints:
    def test_version_command(self, capsys):
        with patch("sys.argv", ["cockpit", "version"]):
            main()
        captured = capsys.readouterr()
        assert "cockpit-council v" in captured.out

    def test_no_command_shows_help(self, capsys):
        with patch("sys.argv", ["cockpit"]):
            main()
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "cockpit" in captured.out.lower()

    def test_ask_no_query_stdin_empty(self):
        """cockpit ask with no query and empty stdin should exit."""
        import io
        with patch("sys.argv", ["cockpit", "ask"]):
            with patch("sys.stdin", io.StringIO("")):
                with patch("sys.stdin") as mock_stdin:
                    mock_stdin.isatty.return_value = False
                    mock_stdin.read.return_value = ""
                    with pytest.raises(SystemExit):
                        main()
