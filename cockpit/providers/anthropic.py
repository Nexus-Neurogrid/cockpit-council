"""Anthropic Claude provider via LangChain."""

from __future__ import annotations


def create_anthropic_provider(
    model: str = "claude-sonnet-4-20250514",
    api_key: str | None = None,
    **kwargs,
):
    """Create an Anthropic Claude chat provider.

    Requires ``pip install cockpit-council[anthropic]``.
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as exc:
        raise ImportError(
            "Install the anthropic extra: pip install cockpit-council[anthropic]"
        ) from exc

    return ChatAnthropic(
        model=model,
        api_key=api_key,
        streaming=True,
        **kwargs,
    )
