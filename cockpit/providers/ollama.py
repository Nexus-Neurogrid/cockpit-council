"""Ollama local provider via LangChain."""

from __future__ import annotations


def create_ollama_provider(
    model: str = "llama3.1",
    base_url: str = "http://localhost:11434",
    **kwargs,
):
    """Create an Ollama local chat provider.

    Requires ``pip install cockpit-council[ollama]``.
    """
    try:
        from langchain_ollama import ChatOllama
    except ImportError as exc:
        raise ImportError(
            "Install the ollama extra: pip install cockpit-council[ollama]"
        ) from exc

    return ChatOllama(
        model=model,
        base_url=base_url,
        **kwargs,
    )
