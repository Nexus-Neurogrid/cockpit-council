"""Shared test fixtures."""

from __future__ import annotations

from typing import AsyncIterator

import pytest
from langchain_core.messages import AIMessage, BaseMessage


class MockProvider:
    """Deterministic mock provider for testing."""

    def __init__(self, response: str = "Mock response") -> None:
        self.response = response
        self.call_count = 0
        self.last_messages: list[BaseMessage] = []

    async def ainvoke(self, messages: list[BaseMessage], **kwargs) -> BaseMessage:
        self.call_count += 1
        self.last_messages = messages
        return AIMessage(content=self.response)

    async def astream(
        self, messages: list[BaseMessage], **kwargs
    ) -> AsyncIterator[BaseMessage]:
        self.call_count += 1
        self.last_messages = messages
        # Stream word by word
        for word in self.response.split():
            yield AIMessage(content=word + " ")


class FailingProvider:
    """Provider that always raises."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error or RuntimeError("Provider failed")

    async def ainvoke(self, messages, **kwargs):
        raise self.error

    async def astream(self, messages, **kwargs):
        raise self.error
        yield  # make it a generator  # noqa: E275


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def tech_response_provider():
    return MockProvider(
        response="**Verdict**: GO\n**Feasibility**: Technically achievable.\n"
        "**Risks**: None critical.\n**Recommendations**: Proceed."
    )


@pytest.fixture
def biz_response_provider():
    return MockProvider(
        response="**Verdict**: OPPORTUNITY\n**Market Potential**: Strong.\n"
        "**ROI**: High.\n**Recommendations**: Launch Q2."
    )
