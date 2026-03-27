"""Memory store protocol."""

from __future__ import annotations

from typing import Protocol


class MemoryStoreProtocol(Protocol):
    """Protocol for persistent agent memory backends."""

    async def store(
        self,
        agent_type: str,
        key: str,
        content: str,
        memory_type: str,
        importance: float = 0.5,
    ) -> None: ...

    async def recall(self, agent_type: str, key: str) -> dict | None: ...

    async def search(
        self,
        query: str,
        agent_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]: ...

    async def get_agent_context(self, agent_type: str) -> dict: ...
