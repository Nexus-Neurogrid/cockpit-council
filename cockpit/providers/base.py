"""Provider protocol — any LangChain-compatible chat model satisfies this."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from langchain_core.messages import BaseMessage


@runtime_checkable
class ChatProvider(Protocol):
    """Protocol for LLM providers.

    Any object exposing ``ainvoke`` and ``astream`` with LangChain message
    types satisfies this protocol.  ``ChatAnthropic``, ``ChatOpenAI``, and
    ``ChatOllama`` all conform out of the box.
    """

    async def ainvoke(
        self, messages: list[BaseMessage], **kwargs
    ) -> BaseMessage: ...

    async def astream(
        self, messages: list[BaseMessage], **kwargs
    ) -> AsyncIterator[BaseMessage]: ...
