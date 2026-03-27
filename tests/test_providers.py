"""Tests for provider implementations."""

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from cockpit.providers.fallback import FallbackProvider
from conftest import MockProvider, FailingProvider


class TestFallbackProvider:
    @pytest.mark.asyncio
    async def test_uses_primary_on_success(self):
        primary = MockProvider(response="Primary response")
        fallback = MockProvider(response="Fallback response")
        provider = FallbackProvider(primary, fallback)

        messages = [HumanMessage(content="test")]
        result = await provider.ainvoke(messages)

        assert result.content == "Primary response"
        assert primary.call_count == 1
        assert fallback.call_count == 0

    @pytest.mark.asyncio
    async def test_falls_back_on_error(self):
        primary = FailingProvider()
        fallback = MockProvider(response="Fallback response")
        provider = FallbackProvider(primary, fallback)

        messages = [HumanMessage(content="test")]
        result = await provider.ainvoke(messages)

        assert result.content == "Fallback response"
        assert fallback.call_count == 1

    @pytest.mark.asyncio
    async def test_raises_when_should_not_fallback(self):
        primary = FailingProvider(error=ValueError("bad input"))
        fallback = MockProvider()
        provider = FallbackProvider(
            primary, fallback,
            should_fallback=lambda e: isinstance(e, RuntimeError),
        )

        messages = [HumanMessage(content="test")]
        with pytest.raises(ValueError, match="bad input"):
            await provider.ainvoke(messages)

    @pytest.mark.asyncio
    async def test_stream_fallback(self):
        primary = FailingProvider()
        fallback = MockProvider(response="Streamed fallback")
        provider = FallbackProvider(primary, fallback)

        messages = [HumanMessage(content="test")]
        chunks = []
        async for chunk in provider.astream(messages):
            chunks.append(chunk.content)

        assert len(chunks) > 0
        assert "Streamed" in "".join(chunks)


class TestMockProvider:
    @pytest.mark.asyncio
    async def test_invoke(self):
        provider = MockProvider(response="Hello")
        msg = await provider.ainvoke([HumanMessage(content="hi")])
        assert msg.content == "Hello"

    @pytest.mark.asyncio
    async def test_stream(self):
        provider = MockProvider(response="Hello world")
        chunks = []
        async for chunk in provider.astream([HumanMessage(content="hi")]):
            chunks.append(chunk.content)
        assert "Hello" in "".join(chunks)
