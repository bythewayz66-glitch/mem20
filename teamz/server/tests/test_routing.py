import json

import httpx
import pytest

from server.app.providers.base import RouteContext
from server.app.providers.openai_compat import OpenAICompatProviderBase
from server.app.providers.common import is_dead_local_error
from server.app.router import Router


def make_client(handler):
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


class StaticProvider(OpenAICompatProviderBase):
    def __init__(self, name, response_text="ok", fail=False, status=200, model="m1", keyless=True, local_runtime=False, base_url="https://example.test/v1"):
        super().__init__(name=name, base_url=base_url, api_key="", keyless=keyless, default_model=model, preferred_models=[model], local_runtime=local_runtime)
        self._response_text = response_text
        self._fail = fail
        self._status = status

    async def candidates(self, ctx, client):
        return [{
            "provider": self.name,
            "model": self.default_model,
            "url": self.chat_url,
            "headers": self.headers(),
            "keyless": self.keyless and not self.api_key,
            "base_url": self.base_url,
            "local_runtime": self.local_runtime,
        }]

    async def complete(self, ctx, candidate, client):
        if self._fail:
            raise RuntimeError("boom")
        from server.app.providers.base import ProviderResult
        return ProviderResult(text=self._response_text, model=candidate["model"], provider=self.name, usage={"total_tokens": 5})

    async def stream(self, ctx, candidate, client):
        if self._fail:
            yield type("E", (), {"type": "error", "data": {"error": "boom"}})()
            return
        # Simulate provider yielding delta/done
        from server.app.providers.base import StreamEvent
        yield StreamEvent("delta", {"delta": self._response_text, "provider": self.name, "model": candidate["model"]})
        yield StreamEvent("done", {"text": self._response_text, "provider": self.name, "model": candidate["model"], "usage": {"total_tokens": 5}})


@pytest.mark.asyncio
async def test_router_fallback_chain_observable():
    p1 = StaticProvider("p1", fail=True)
    p2 = StaticProvider("p2", response_text="hello from p2")
    router = Router(providers=[p1, p2])
    ctx = RouteContext(messages=[{"role": "user", "content": "hi"}], stream=False)
    async with httpx.AsyncClient() as client:
        result = await router.complete(ctx, client=client)
    assert result.text == "hello from p2"
    assert result.provider == "p2"
    statuses = [a.status for a in result.attempts]
    assert "failed" in statuses
    assert "success" in statuses
    assert result.fallback_used is True


@pytest.mark.asyncio
async def test_agent_model_string_not_hard_filter():
    # Regression: agent's model string as hard filter caused total outage.
    # Requested model unavailable/failing on first provider must not prevent fallback to viable providers/models.
    class ModelAwareProvider(StaticProvider):
        async def candidates(self, ctx, client):
            req = ctx.requested_model
            # If router asks via requested_model preference, still expose own default as fallback candidate
            return [
                {"provider": self.name, "model": req or self.default_model, "url": self.chat_url, "headers": self.headers(), "keyless": True, "base_url": self.base_url, "local_runtime": False},
                {"provider": self.name, "model": self.default_model, "url": self.chat_url, "headers": self.headers(), "keyless": True, "base_url": self.base_url, "local_runtime": False},
            ]
        async def complete(self, ctx, candidate, client):
            if candidate["model"] == "wanted-model" and self.name == "p1":
                raise RuntimeError("model unavailable")
            if self._fail:
                raise RuntimeError("boom")
            from server.app.providers.base import ProviderResult
            return ProviderResult(text=f"ok:{candidate['model']}", model=candidate["model"], provider=self.name)

    p1 = ModelAwareProvider("p1")
    p2 = StaticProvider("p2", response_text="fallback-ok", model="other")
    router = Router(providers=[p1, p2])
    ctx = RouteContext(messages=[{"role": "user", "content": "hi"}], requested_model="wanted-model", strict_model=False, stream=False)
    async with httpx.AsyncClient() as client:
        result = await router.complete(ctx, client=client)
    assert "fallback-ok" in result.text or result.provider == "p2" or result.text.startswith("ok:")
    assert any(a.status == "success" for a in result.attempts)


@pytest.mark.asyncio
async def test_router_does_not_close_caller_owned_http_client():
    # Regression: router must not close a caller-owned HTTP client
    p = StaticProvider("p1", response_text="ok")
    router = Router(providers=[p])
    ctx = RouteContext(messages=[{"role": "user", "content": "hi"}], stream=False)
    async with httpx.AsyncClient() as client:
        result = await router.complete(ctx, client=client)
        assert result.text == "ok"
        # Client must still be usable after router completes
        assert client.is_closed is False
        r = await client.get("https://example.com", extensions={"timeout": None}) if False else None
    # caller closes it via context manager


@pytest.mark.asyncio
async def test_dead_local_runtime_does_not_consume_attempt_budget():
    # Regression: dead local runtimes must not consume the whole attempt budget
    class DeadLocalProvider(OpenAICompatProviderBase):
        def __init__(self):
            super().__init__(name="local-dead", base_url="http://127.0.0.1:65530/v1", api_key="", keyless=True, default_model="local", preferred_models=["local"], local_runtime=True)
        async def candidates(self, ctx, client):
            return [{"provider": self.name, "model": "local", "url": self.chat_url, "headers": self.headers(), "keyless": True, "base_url": self.base_url, "local_runtime": True}]
        async def complete(self, ctx, candidate, client):
            raise httpx.ConnectError("connection refused", request=None)
        async def stream(self, ctx, candidate, client):
            raise httpx.ConnectError("connection refused", request=None)

    good = StaticProvider("remote", response_text="remote-ok", base_url="https://remote.test/v1")
    # Put many dead local runtimes in front; remote must still be reached within budget
    router = Router(providers=[DeadLocalProvider(), DeadLocalProvider(), DeadLocalProvider(), good])
    router.cfg.max_attempts = 2  # tight budget for real attempts
    ctx = RouteContext(messages=[{"role": "user", "content": "hi"}], stream=False)
    async with httpx.AsyncClient() as client:
        result = await router.complete(ctx, client=client)
    assert result.text == "remote-ok"
    # Dead locals should be marked skipped (dead_local_runtime) and not starve remote
    skipped = [a for a in result.attempts if a.status == "skipped"]
    assert any(a.reason == "dead_local_runtime" for a in skipped)
    assert any(a.status == "success" and a.provider == "remote" for a in result.attempts)


def test_is_dead_local_error_detection():
    assert is_dead_local_error(httpx.ConnectError("refused"), "http://127.0.0.1:11434/v1") is True
    assert is_dead_local_error(httpx.ConnectTimeout("timeout"), "http://localhost:8000/v1") is True
    assert is_dead_local_error(httpx.ConnectError("refused"), "https://api.example.com/v1") is False
