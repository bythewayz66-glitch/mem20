"""HTTP surface tests against a real ThreadingHTTPServer.

The server is bound to an ephemeral port and driven with ``http.client``, so the
socket, the JSON encoder and the error-status mapping all run for real.
"""

from __future__ import annotations

import http.client
import json
import threading

import pytest

from mem20edgefleetbrainz.runtime import make_server
from mem20edgefleetbrainz.service import FleetService


@pytest.fixture()
def live(tmp_path):
    service = FleetService(tmp_path / "http.db")
    server, url = make_server(service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host_port = url.split("//", 1)[1]
    host, port = host_port.rsplit(":", 1)
    try:
        yield service, host, int(port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(host: str, port: int, method: str, path: str,
            body=None) -> tuple[int, bytes, str]:
    connection = http.client.HTTPConnection(host, port, timeout=15)
    headers = {}
    payload = None
    if body is not None:
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    connection.request(method, path, body=payload, headers=headers)
    response = connection.getresponse()
    data = response.read()
    status = response.status
    content_type = response.getheader("Content-Type") or ""
    connection.close()
    return status, data, content_type


def as_json(data: bytes):
    return json.loads(data.decode("utf-8"))


def test_static_cockpit_and_health(live):
    _, host, port = live

    status, body, content_type = request(host, port, "GET", "/")
    assert status == 200
    assert content_type.startswith("text/html")
    assert b"Edge Fleet Brain" in body
    assert b"app.js" in body

    status, body, content_type = request(host, port, "GET", "/app.js")
    assert status == 200
    assert content_type.startswith("text/javascript")
    assert b"/api/status" in body

    status, body, content_type = request(host, port, "GET", "/style.css")
    assert status == 200
    assert content_type.startswith("text/css")
    assert b"--accent" in body

    status, body, _ = request(host, port, "GET", "/api/healthz")
    assert status == 200
    payload = as_json(body)
    assert payload["ok"] is True
    assert payload["health"]["nodes"] == 0

    status, body, _ = request(host, port, "GET", "/api/status")
    assert status == 200
    payload = as_json(body)
    assert payload["ok"] is True
    assert payload["metrics"]["nodes"] == 0
    assert "sleep" in payload and payload["sleep"]["ok"] is True


def test_full_node_and_workload_lifecycle(live):
    _, host, port = live

    status, body, _ = request(host, port, "POST", "/api/nodes", {
        "node_id": "edge-1", "cpu_cores": 8, "memory_gb": 16,
        "capabilities": ["cpu"], "reliability": 0.99, "price_per_hour": 0.1,
    })
    assert status == 201
    registered = as_json(body)
    assert registered["ok"] is True
    assert registered["swarm"]["ok"] is True
    assert registered["device"]["tier"] == "high"

    status, body, _ = request(host, port, "GET", "/api/nodes")
    assert status == 200
    assert [node["node_id"] for node in as_json(body)["nodes"]] == ["edge-1"]

    status, body, _ = request(host, port, "POST", "/api/workloads", {
        "workload_id": "w1", "cpu": 2, "memory_gb": 2,
        "required_capabilities": ["cpu"], "priority": 70,
    })
    assert status == 201
    assert as_json(body)["created"] is True

    status, body, _ = request(host, port, "POST", "/api/dispatch",
                              {"workload_id": "w1"})
    assert status == 200
    dispatched = as_json(body)
    assert dispatched["dispatched"] == 1
    assert dispatched["decisions"][0]["decision"]["chosen"] == "edge-1"

    status, body, _ = request(host, port, "GET", "/api/workloads/w1")
    assert status == 200
    assert as_json(body)["workload"]["state"] == "running"

    status, body, _ = request(host, port, "GET", "/api/workloads?state=running")
    assert status == 200
    assert len(as_json(body)["workloads"]) == 1

    status, body, _ = request(host, port, "POST",
                              "/api/workloads/w1/complete",
                              {"success": True, "reason": "http test"})
    assert status == 200
    assert as_json(body)["workload"]["state"] == "completed"

    status, body, _ = request(host, port, "GET", "/api/workloads?state=completed")
    assert status == 200
    assert len(as_json(body)["workloads"]) == 1


def test_observability_endpoints(live):
    _, host, port = live
    request(host, port, "POST", "/api/nodes", {
        "node_id": "n1", "cpu_cores": 8, "memory_gb": 16,
        "capabilities": ["cpu", "gpu"], "gpu_count": 1,
    })
    request(host, port, "POST", "/api/workloads", {
        "workload_id": "w1", "cpu": 1, "memory_gb": 1,
    })

    status, body, _ = request(host, port, "GET", "/api/events?since=0&limit=20")
    assert status == 200
    events = as_json(body)["events"]
    assert events and events[0]["seq"] >= 1

    status, body, _ = request(host, port, "GET", "/api/metrics")
    assert status == 200
    metrics = as_json(body)["metrics"]
    assert metrics["nodes"] == 1
    assert metrics["workloads"] == 1

    status, body, _ = request(host, port, "GET", "/api/predict?horizon_s=7200")
    assert status == 200
    forecasts = as_json(body)["forecasts"]
    assert forecasts[0]["node_id"] == "n1"
    assert forecasts[0]["horizon_s"] == 7200.0

    status, body, _ = request(host, port, "GET", "/api/energy?hours=6")
    assert status == 200
    assert as_json(body)["energy"]["hours"] == 6.0

    status, body, _ = request(host, port, "GET", "/api/benchmark?iterations=3")
    assert status == 200
    assert as_json(body)["iterations"] == 3

    status, body, _ = request(host, port, "GET", "/api/doctor")
    assert status == 200
    assert len(as_json(body)["ecosystem"]["reachable"]) == 6


def test_snapshot_restore_over_http(live):
    _, host, port = live
    request(host, port, "POST", "/api/nodes", {"node_id": "keep"})
    request(host, port, "POST", "/api/nodes", {"node_id": "drop"})

    status, body, _ = request(host, port, "POST", "/api/snapshot",
                              {"label": "before"})
    assert status == 201
    snapshot_id = as_json(body)["snapshot_id"]

    status, _, _ = request(host, port, "DELETE", "/api/nodes/drop")
    assert status == 200
    status, body, _ = request(host, port, "GET", "/api/nodes")
    assert len(as_json(body)["nodes"]) == 1

    status, body, _ = request(host, port, "POST", "/api/restore",
                              {"snapshot_id": snapshot_id})
    assert status == 200
    assert as_json(body)["nodes"] == 2
    status, body, _ = request(host, port, "GET", "/api/nodes")
    assert len(as_json(body)["nodes"]) == 2


def test_drain_evacuate_status_and_delete(live):
    _, host, port = live
    request(host, port, "POST", "/api/nodes", {
        "node_id": "a", "cpu_cores": 16, "memory_gb": 32, "reliability": 0.99,
    })
    request(host, port, "POST", "/api/nodes", {
        "node_id": "b", "cpu_cores": 8, "memory_gb": 16, "reliability": 0.9,
    })
    request(host, port, "POST", "/api/workloads", {
        "workload_id": "w1", "cpu": 2, "memory_gb": 2, "priority": 80,
    })
    request(host, port, "POST", "/api/dispatch", {"workload_id": "w1"})
    _, body, _ = request(host, port, "GET", "/api/workloads/w1")
    source = as_json(body)["workload"]["assigned_node"]
    target = "b" if source == "a" else "a"

    status, body, _ = request(host, port, "POST", f"/api/nodes/{source}/drain")
    assert status == 200
    assert as_json(body)["node"]["status"] == "draining"

    status, body, _ = request(host, port, "POST", f"/api/nodes/{source}/evacuate")
    assert status == 200
    evacuated = as_json(body)
    assert evacuated["drained"] is True
    assert evacuated["moves"][0]["to"] == target

    status, body, _ = request(host, port, "POST", f"/api/nodes/{source}/status",
                              {"status": "online"})
    assert status == 200
    assert as_json(body)["node"]["status"] == "online"

    status, _, _ = request(host, port, "DELETE", f"/api/nodes/{target}")
    assert status == 200


def test_error_status_mapping_and_safety(live):
    _, host, port = live

    status, body, _ = request(host, port, "POST", "/api/nodes", b"{not json")
    assert status == 400
    assert as_json(body)["kind"] == "validation"

    status, body, _ = request(host, port, "POST", "/api/workloads",
                              {"workload_id": "bad", "cpu": 0})
    assert status == 400
    assert as_json(body)["kind"] == "validation"

    status, body, _ = request(host, port, "GET", "/api/workloads/missing")
    assert status == 404
    assert as_json(body)["kind"] == "not_found"

    status, body, _ = request(host, port, "POST", "/api/nodes/missing/drain")
    assert status == 404

    status, body, _ = request(host, port, "GET", "/api/does-not-exist")
    assert status == 404

    status, body, _ = request(host, port, "DELETE", "/api/nope")
    assert status == 404

    # Traversal must be refused before any file is read.
    status, body, _ = request(host, port, "GET", "/../conftest.py")
    assert status == 400
    assert b"path traversal refused" in body

    status, body, content_type = request(host, port, "OPTIONS", "/api/nodes")
    assert status == 204
    assert body == b""

    status, body, _ = request(host, port, "POST", "/api/rebalance",
                              {"threshold": 0.8, "apply": False})
    assert status == 200
    assert as_json(body)["ok"] is True

    status, body, _ = request(host, port, "POST", "/api/simulate", {})
    assert status == 200
    report = as_json(body)
    assert report["ok"] is True
    assert report["passed"] == report["total"] == 6
