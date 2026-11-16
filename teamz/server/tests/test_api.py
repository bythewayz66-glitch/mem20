import json

import httpx
import pytest
from fastapi.testclient import TestClient

from server.app.main import app
from server.app import main as main_mod
from server.app.providers.base import ProviderResult, StreamEvent


class _FakeProvider:
    name = "fake"
    keyless = True
    api_key = ""
    base_url = "https://fake.test/v1"
    default_model = "fake-model"
    local_runtime = False


class FakeRouter:
    providers = [_FakeProvider()]

    async def complete(self, ctx, client=None):
        return ProviderResult(
            text="hello",
            model="fake-model",
            provider="fake",
            attempts=[type("A", (), {"to_dict": lambda self=None: {"provider": "fake", "model": "fake-model", "status": "success", "latency_ms": 5, "keyless": True}})()],
            usage={"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        )

    async def stream(self, ctx, client=None):
        a = {"provider": "fake", "model": "fake-model", "status": "success", "latency_ms": 5, "keyless": True}
        yield StreamEvent("meta", {"attempt": a, "attempts": [a]})
        yield StreamEvent("delta", {"delta": "he", "provider": "fake", "model": "fake-model"})
        yield StreamEvent("delta", {"delta": "llo", "provider": "fake", "model": "fake-model"})
        yield StreamEvent("done", {"text": "hello", "provider": "fake", "model": "fake-model", "usage": {"total_tokens": 3}, "attempts": [a], "fallback_used": False})


@pytest.fixture(autouse=True)
def _patch_router(monkeypatch):
    monkeypatch.setattr(main_mod, "router", FakeRouter())
    # Disable mem20 side effects in API tests
    monkeypatch.setattr(main_mod.settings, "mem20_enabled", False)
    yield


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["service"] == "teamz-orchestrator"


def test_status():
    client = TestClient(app)
    r = client.get("/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert "providers" in data
    assert "mem20" in data


def test_chat_completions_non_stream():
    client = TestClient(app)
    r = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}], "stream": False})
    assert r.status_code == 200
    data = r.json()
    assert data["choices"][0]["message"]["content"] == "hello"
    assert data["routing"]["selected_provider"] == "fake"
    assert data["usage"]["total_tokens"] == 3


def test_chat_completions_stream():
    client = TestClient(app)
    with client.stream("POST", "/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}], "stream": True}) as r:
        assert r.status_code == 200
        body = "".join(r.iter_text())
    assert "data:" in body
    assert '"delta"' in body or "hello" in body
    assert "[DONE]" in body
    assert '"type": "done"' in body or 'event: done' in body


def test_optimize_prompt():
    client = TestClient(app)
    r = client.post("/v1/optimize-prompt", json={"draft": "help me", "conversation": {"id": "c1", "name": "Build", "kind": "channel"}})
    assert r.status_code == 200
    data = r.json()
    assert data["original"] == "help me"
    assert isinstance(data["prompt"], str) and data["prompt"]
    assert "routing" in data


def test_optimize_prompt_requires_draft():
    client = TestClient(app)
    r = client.post("/v1/optimize-prompt", json={"draft": "   "})
    assert r.status_code == 400


def test_memory_endpoints_when_disabled():
    client = TestClient(app)
    r = client.post("/v1/memory/recall", json={"query": "x"})
    assert r.status_code == 200
    assert r.json()["enabled"] is False
    r = client.post("/v1/memory/store", json={"content": "x"})
    assert r.status_code == 503
    r = client.get("/v1/tools")
    assert r.status_code == 200
    assert r.json()["enabled"] is False
