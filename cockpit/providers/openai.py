"""OpenAI provider via LangChain."""

from __future__ import annotations


def create_openai_provider(
    model: str = "gpt-4o",
    api_key: str | None = None,
    **kwargs,
):
    """Create an OpenAI chat provider.

    Requires ``pip install cockpit-council[openai]``.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise ImportError(
            "Install the openai extra: pip install cockpit-council[openai]"
        ) from exc

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        streaming=True,
        **kwargs,
    )
