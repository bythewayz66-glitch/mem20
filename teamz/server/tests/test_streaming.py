import json

import httpx
import pytest

from server.app.providers.base import RouteContext, StreamEvent
from server.app.providers.openai_compat import OpenAICompatProviderBase
from server.app.router import Router


class NonSSEProvider(OpenAICompatProviderBase):
    """Simulates a provider that returns JSON (non-SSE) even when stream=True."""
    def __init__(self):
        super().__init__(name="nonsse", base_url="https://nonsse.test/v1", default_model="m1", preferred_models=["m1"])
        self.calls = 0

    async def candidates(self, ctx, client):
        return [{"provider": self.name, "model": "m1", "url": self.chat_url, "headers": self.headers(), "keyless": True, "base_url": self.base_url, "local_runtime": False}]

    async def stream(self, ctx, candidate, client):
        # Regression: streaming produced empty answer for non-SSE providers.
        # Emit a done event synthesized from JSON body content (as our OpenAICompatProviderBase.stream does).
        yield StreamEvent("delta", {"delta": "hello", "provider": self.name, "model": "m1"})
        yield StreamEvent("done", {"text": "hello", "provider": self.name, "model": "m1", "usage": {"total_tokens": 3}, "raw_non_sse": True})


class EmptyStreamProvider(OpenAICompatProviderBase):
    def __init__(self):
        super().__init__(name="empty", base_url="https://empty.test/v1", default_model="m1", preferred_models=["m1"])
    async def candidates(self, ctx, client):
        return [{"provider": self.name, "model": "m1", "url": self.chat_url, "headers": self.headers(), "keyless": True, "base_url": self.base_url, "local_runtime": False}]
    async def stream(self, ctx, candidate, client):
        # Yields no content and no done -> router must treat as failure and try next
        if False:
            yield
        return


class GoodStreamProvider(OpenAICompatProviderBase):
    def __init__(self):
        super().__init__(name="good", base_url="https://good.test/v1", default_model="m1", preferred_models=["m1"])
    async def candidates(self, ctx, client):
        return [{"provider": self.name, "model": "m1", "url": self.chat_url, "headers": self.headers(), "keyless": True, "base_url": self.base_url, "local_runtime": False}]
    async def stream(self, ctx, candidate, client):
        yield StreamEvent("delta", {"delta": "world", "provider": self.name, "model": "m1"})
        yield StreamEvent("done", {"text": "world", "provider": self.name, "model": "m1", "usage": None})


@pytest.mark.asyncio
async def test_non_sse_provider_stream_not_empty():
    router = Router(providers=[NonSSEProvider()])
    ctx = RouteContext(messages=[{"role": "user", "content": "hi"}], stream=True)
    events = []
    async with httpx.AsyncClient() as client:
        async for ev in router.stream(ctx, client=client):
            events.append(ev)
    types = [e.type for e in events]
    assert "done" in types
    done = [e for e in events if e.type == "done"][0]
    assert (done.data.get("text") or "").strip() == "hello"
    assert not any(e.type == "error" for e in events)


@pytest.mark.asyncio
async def test_empty_stream_falls_back_to_next_provider():
    router = Router(providers=[EmptyStreamProvider(), GoodStreamProvider()])
    ctx = RouteContext(messages=[{"role": "user", "content": "hi"}], stream=True)
    events = []
    async with httpx.AsyncClient() as client:
        async for ev in router.stream(ctx, client=client):
            events.append(ev)
    assert any(e.type == "done" and e.data.get("provider") == "good" and e.data.get("text") == "world" for e in events)
    # meta/attempts should reflect failure then success
    metas = [e for e in events if e.type == "meta"]
    assert metas


@pytest.mark.asyncio
async def test_openai_compat_stream_handles_json_non_sse_response():
    # Directly test provider behavior: if upstream returns application/json, synthesize stream
    def handler(request: httpx.Request):
        body = json.loads(request.content)
        assert body.get("stream") is True
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"choices": [{"message": {"role": "assistant", "content": "json-reply"}}], "usage": {"total_tokens": 7}},
        )

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatProviderBase(name="p", base_url="https://api.test/v1", default_model="m1", preferred_models=["m1"])
    ctx = RouteContext(messages=[{"role": "user", "content": "hi"}], stream=True)
    candidate = {"provider": "p", "model": "m1", "url": provider.chat_url, "headers": provider.headers(), "keyless": True, "base_url": provider.base_url, "local_runtime": False}
    events = []
    async with httpx.AsyncClient(transport=transport) as client:
        async for ev in provider.stream(ctx, candidate, client):
            events.append(ev)
    assert any(e.type == "delta" and "json-reply" in e.data.get("delta", "") for e in events)
    done = [e for e in events if e.type == "done"][0]
    assert done.data.get("text") == "json-reply"
    assert done.data.get("raw_non_sse") is True
