import json
from fastapi.testclient import TestClient

from server.app import main as main_mod
from server.app.main import app
from server.app.providers.base import ProviderResult


class JsonRouter:
    providers = []
    def __init__(self, text):
        self.text = text
    async def complete(self, ctx, client=None):
        return ProviderResult(
            text=self.text,
            model="fake-model",
            provider="fake",
            attempts=[type("A", (), {"to_dict": lambda self=None: {"provider": "fake", "model": "fake-model", "status": "success", "latency_ms": 1}})()],
            usage={"total_tokens": 5},
        )
    async def stream(self, ctx, client=None):
        if False:
            yield None


def _disable_mem20(monkeypatch):
    monkeypatch.setattr(main_mod.settings, "mem20_enabled", False)


def test_connectors_status_endpoint(monkeypatch):
    _disable_mem20(monkeypatch)
    monkeypatch.setattr(main_mod, "connectors_status", lambda: {
        "github": {"name": "github", "configured": False, "available": True, "details": {}},
        "gh": {"name": "gh", "configured": False, "available": True, "details": {"path": "/usr/bin/gh"}},
        "google": {"name": "google", "configured": False, "available": False, "details": {}},
    })
    client = TestClient(app)
    r = client.get("/v1/connectors/status")
    assert r.status_code == 200
    data = r.json()
    assert "github" in data and "gh" in data and "google" in data
    assert data["gh"]["details"]["path"] == "/usr/bin/gh"


def test_gh_exec_requires_args(monkeypatch):
    _disable_mem20(monkeypatch)
    client = TestClient(app)
    r = client.post("/v1/connectors/gh/exec", json={})
    assert r.status_code == 400


def test_github_request_requires_path(monkeypatch):
    _disable_mem20(monkeypatch)
    client = TestClient(app)
    r = client.post("/v1/connectors/github/request", json={"method": "GET"})
    assert r.status_code == 400


def test_google_request_requires_url(monkeypatch):
    _disable_mem20(monkeypatch)
    client = TestClient(app)
    r = client.post("/v1/connectors/google/request", json={"method": "GET"})
    assert r.status_code == 400


def test_runtime_plan_structured_json(monkeypatch):
    _disable_mem20(monkeypatch)
    plan = {
        "summary": "Create a channel and delegate",
        "actions": [{"type": "create_channel", "name": "Ops", "agentNames": ["Atlas"]}],
        "delegations": [{"agent_name": "Atlas", "task": "bootstrap ops", "reason": "lead"}],
        "response": "Done."
    }
    monkeypatch.setattr(main_mod, "router", JsonRouter(json.dumps(plan)))
    client = TestClient(app)
    r = client.post("/v1/runtime/plan", json={"request": "create an ops channel and delegate to Atlas", "workspace": {"agents": [{"id":"a1","name":"Atlas","isLead":True}], "conversations": []}})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["summary"] == "Create a channel and delegate"
    assert len(data["actions"]) == 1
    assert data["actions"][0]["type"] == "create_channel"
    assert len(data["delegations"]) == 1


def test_runtime_plan_handles_non_json(monkeypatch):
    _disable_mem20(monkeypatch)
    monkeypatch.setattr(main_mod, "router", JsonRouter("I can help with that."))
    client = TestClient(app)
    r = client.post("/v1/runtime/plan", json={"request": "help"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert isinstance(data.get("actions"), list)
    assert isinstance(data.get("delegations"), list)


def test_opportunities_scan_parses_json(monkeypatch):
    _disable_mem20(monkeypatch)
    payload = {
        "opportunities": [{"type": "skill", "title": "Prompt design", "description": "Reusable prompting", "evidence": "msg", "reusable": True}],
        "portfolio_updates": [{"agent_name": "Atlas", "skill": "Prompt design", "skill_key": "prompt-design", "level": 4, "evidence": "helped others"}]
    }
    monkeypatch.setattr(main_mod, "router", JsonRouter(json.dumps(payload)))
    client = TestClient(app)
    r = client.post("/v1/opportunities/scan", json={"messages": [{"authorName": "User", "text": "help me design prompts"}], "agents": [{"name": "Atlas", "skills": []}]})
    assert r.status_code == 200
    data = r.json()
    assert len(data["opportunities"]) == 1
    assert len(data["portfolio_updates"]) == 1
    assert data["portfolio_updates"][0]["skill_key"] == "prompt-design"


def test_chat_includes_lead_runtime_context_does_not_break(monkeypatch):
    _disable_mem20(monkeypatch)
    captured = {}
    class CapRouter(JsonRouter):
        async def complete(self, ctx, client=None):
            captured['messages'] = ctx.messages
            return await super().complete(ctx, client)
    monkeypatch.setattr(main_mod, "router", CapRouter("ok"))
    client = TestClient(app)
    r = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "create a channel"}],
        "agent": {"id": "a1", "name": "Atlas", "isLead": True},
        "conversation": {"id": "c1", "name": "Build", "kind": "channel"},
        "metadata": {"workspace": {"agents": [{"id": "a1", "name": "Atlas", "isLead": True}], "conversations": []}}
    })
    assert r.status_code == 200
    msgs = captured.get('messages') or []
    joined = "\n".join([str(m.get('content','')) for m in msgs])
    assert "LEAD AGENT" in joined or "teamz-actions" in joined
    assert "Workspace runtime context" in joined
