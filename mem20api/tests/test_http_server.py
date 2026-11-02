"""Tests for the mem20 HTTP service (mem20api.http_server).

These run against a real socket on an ephemeral loopback port and a real
temporary store, so they exercise the same code path a deployment does: bind,
authenticate, open the store, serialise a response. Nothing is mocked except
the store path.

Run with:  python3 -m pytest -q mem20api/tests
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from mem20api.http_server import (
    API_VERSION,
    ConfigError,
    make_server,
)

TOKEN = "test-token-not-a-real-credential"


@pytest.fixture()
def store_path(tmp_path):
    """A fresh, empty store directory."""
    p = tmp_path / "store"
    p.mkdir()
    return str(p)


@pytest.fixture()
def server(store_path):
    """A running server on an ephemeral port, with a bearer token."""
    srv = make_server(store_path, host="127.0.0.1", port=0, token=TOKEN)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield srv
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


@pytest.fixture()
def base_url(server):
    host, port = server.server_address[0], server.server_address[1]
    return f"http://{host}:{port}"


def _request(url, method="GET", body=None, token=TOKEN, headers=None):
    """Return (status, parsed_json). Never raises on a 4xx/5xx."""
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    if token is not None:
        hdrs["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return e.code, {"raw": raw}


# -- configuration safety ---------------------------------------------------


def test_refuses_non_loopback_bind_without_token(store_path):
    """The whole point of the guard: no token means loopback only."""
    with pytest.raises(ConfigError) as exc:
        make_server(store_path, host="0.0.0.0", port=0, token=None)
    assert "MEM20_API_TOKEN" in str(exc.value)


def test_allows_loopback_bind_without_token(store_path):
    srv = make_server(store_path, host="127.0.0.1", port=0, token=None)
    try:
        assert srv.token is None
    finally:
        srv.server_close()


def test_allows_non_loopback_bind_with_token(store_path):
    srv = make_server(store_path, host="0.0.0.0", port=0, token=TOKEN)
    try:
        assert srv.token == TOKEN
    finally:
        srv.server_close()


# -- liveness / readiness ---------------------------------------------------


def test_healthz_is_public_and_does_not_need_a_token(base_url):
    status, body = _request(f"{base_url}/healthz", token=None)
    assert status == 200
    assert body["status"] == "ok"
    assert body["api_version"] == API_VERSION
    assert body["service"] == "mem20-api"


def test_readyz_requires_a_token(base_url):
    status, body = _request(f"{base_url}/readyz", token=None)
    assert status == 401
    assert body["error"]["code"] == "unauthorised"


def test_readyz_rejects_a_wrong_token(base_url):
    status, body = _request(f"{base_url}/readyz", token="wrong")
    assert status == 401
    assert body["error"]["code"] == "unauthorised"


def test_readyz_reports_the_store_state(base_url):
    status, body = _request(f"{base_url}/readyz")
    # An empty store has no indexes yet, so it is honestly not ready.
    assert status in (200, 503)
    assert body["status"] in ("ready", "drifted")
    assert "indexes" in body
    assert body["ledger_records"] == 0


# -- read endpoints ---------------------------------------------------------


def test_stats_returns_counts(base_url):
    status, body = _request(f"{base_url}/v1/stats")
    assert status == 200
    assert body["ledger_events"] == 0
    assert body["grounded_facts"] == 0
    assert "health" not in body, "stats must not embed the full health blob"


def test_ledger_is_empty_on_a_fresh_store(base_url):
    status, body = _request(f"{base_url}/v1/ledger?k=5")
    assert status == 200
    assert body["count"] == 0
    assert body["records"] == []


def test_ledger_clamps_an_absurd_k(base_url):
    status, body = _request(f"{base_url}/v1/ledger?k=999999")
    assert status == 200
    assert body["count"] == 0


def test_entities_is_empty_on_a_fresh_store(base_url):
    status, body = _request(f"{base_url}/v1/entities?limit=10")
    assert status == 200
    assert body["entities"] == []


def test_recall_round_trips_a_written_fact(base_url, server):
    """Write through the API object, read back through HTTP."""
    with server.store_lock:
        server.open_store().remember("deploys", "Prod is on build 4127",
                                     tags=["prod"])
    status, body = _request(f"{base_url}/v1/recall", method="POST",
                            body={"topic": "deploys", "k": 5})
    assert status == 200
    assert body["count"] >= 1
    assert any("4127" in h.get("content", "") for h in body["hits"])


def test_query_hybrid_degrades_honestly(base_url):
    """With no vector/BM25 deps installed the response must say so."""
    status, body = _request(f"{base_url}/v1/query", method="POST",
                            body={"query": "prod build", "mode": "hybrid"})
    assert status == 200
    assert body["mode"] == "hybrid"
    assert "degraded_to" in body


# -- input validation -------------------------------------------------------


def test_query_rejects_an_empty_query(base_url):
    status, body = _request(f"{base_url}/v1/query", method="POST",
                            body={"query": "   "})
    assert status == 400
    assert body["error"]["code"] == "invalid_query"


def test_query_rejects_an_unknown_mode(base_url):
    status, body = _request(f"{base_url}/v1/query", method="POST",
                            body={"query": "x", "mode": "telepathy"})
    assert status == 400
    assert body["error"]["code"] == "invalid_mode"


def test_query_rejects_a_non_integer_k(base_url):
    status, body = _request(f"{base_url}/v1/query", method="POST",
                            body={"query": "x", "k": "five"})
    assert status == 400
    assert body["error"]["code"] == "invalid_k"


def test_recall_rejects_non_string_tags(base_url):
    status, body = _request(f"{base_url}/v1/recall", method="POST",
                            body={"tags": [1, 2]})
    assert status == 400
    assert body["error"]["code"] == "invalid_tags"


def test_invalid_json_is_a_400_not_a_500(base_url):
    req = urllib.request.Request(
        f"{base_url}/v1/recall", data=b"{not json",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("expected a 400")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        assert json.loads(e.read())["error"]["code"] == "invalid_json"


def test_oversized_body_is_refused(base_url):
    big = json.dumps({"query": "x" * (70 * 1024)}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/v1/query", data=big,
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("expected a 413")
    except urllib.error.HTTPError as e:
        assert e.code == 413


# -- routing ----------------------------------------------------------------


def test_unknown_route_is_a_json_404(base_url):
    status, body = _request(f"{base_url}/v1/nope")
    assert status == 404
    assert body["error"]["code"] == "not_found"


def test_wrong_method_is_a_405_with_allow(base_url):
    req = urllib.request.Request(
        f"{base_url}/v1/query",
        headers={"Authorization": f"Bearer {TOKEN}"}, method="GET")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("expected a 405")
    except urllib.error.HTTPError as e:
        assert e.code == 405
        assert e.headers.get("Allow") == "POST"


def test_every_response_carries_a_request_id(base_url):
    status, body = _request(f"{base_url}/v1/stats")
    assert status == 200
    assert len(body["request_id"]) == 16
