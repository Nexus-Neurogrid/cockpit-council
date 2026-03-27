"""Fallback provider — tries primary, falls back on error."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable

from langchain_core.messages import BaseMessage

from cockpit.providers.base import ChatProvider

logger = logging.getLogger(__name__)


class FallbackProvider:
    """Wraps a primary and fallback provider.

    On any exception from the primary that matches ``should_fallback``,
    transparently retries with the fallback provider.
    """

    def __init__(
        self,
        primary: ChatProvider,
        fallback: ChatProvider,
        should_fallback: Callable[[Exception], bool] | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self._should_fallback = should_fallback or (lambda _: True)

    async def ainvoke(self, messages: list[BaseMessage], **kwargs) -> BaseMessage:
        try:
            return await self.primary.ainvoke(messages, **kwargs)
        except Exception as exc:
            if self._should_fallback(exc):
                logger.warning("Primary provider failed (%s), falling back", exc)
                return await self.fallback.ainvoke(messages, **kwargs)
            raise

    async def astream(
        self, messages: list[BaseMessage], **kwargs
    ) -> AsyncIterator[BaseMessage]:
        try:
            async for chunk in self.primary.astream(messages, **kwargs):
                yield chunk
        except Exception as exc:
            if self._should_fallback(exc):
                logger.warning("Primary provider failed (%s), falling back", exc)
                async for chunk in self.fallback.astream(messages, **kwargs):
                    yield chunk
            else:
                raise
