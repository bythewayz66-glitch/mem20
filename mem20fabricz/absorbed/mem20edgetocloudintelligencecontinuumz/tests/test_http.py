from __future__ import annotations

import json
import threading
import time
import urllib.request
import urllib.error

from mem20edgetocloudintelligencecontinuumz.runtime import serve
from mem20edgetocloudintelligencecontinuumz.service import ContinuumService


class Server:
    def __init__(self, tmp_path):
        self.svc = ContinuumService(tmp_path / "http.db")
        self.httpd = serve(self.svc, "127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.05)

    @property
    def base(self):
        return f"http://127.0.0.1:{self.port}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)


def req(base, method, path, body=None, parse_json=True):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            raw = resp.read().decode()
            parsed = json.loads(raw) if parse_json and raw else raw
            return resp.status, parsed, dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else None
        except Exception:
            parsed = raw
        return e.code, parsed, dict(e.headers)


def test_http_static_status_and_crud(tmp_path):
    s = Server(tmp_path)
    try:
        status, body, headers = req(s.base, "GET", "/", parse_json=False)
        assert status == 200 and "text/html" in (headers.get("Content-Type") or headers.get("content-type") or "")
        status, body, _ = req(s.base, "GET", "/app.js", parse_json=False)
        assert status == 200 and "api('/api/status')" in body

        status, data, headers = req(s.base, "GET", "/api/status")
        assert status == 200 and data["ok"]
        assert (headers.get("Access-Control-Allow-Origin") or headers.get("access-control-allow-origin")) == "*"

        status, data, _ = req(s.base, "POST", "/api/targets", {"target_id": "t1", "tier": "local", "capabilities": ["compute"], "cpu": 8, "memory_gb": 16, "latency_ms": 2})
        assert status == 200 and data["ok"] and data["target"]["tier"] == "local"
        status, data, _ = req(s.base, "GET", "/api/targets")
        assert data["targets"][0]["target_id"] == "t1"

        status, data, _ = req(s.base, "POST", "/api/workloads", {"workload_id": "w1", "cpu": 1, "memory_gb": 1, "required_capabilities": ["compute"]})
        assert status == 200 and data["ok"]
        status, data, _ = req(s.base, "POST", "/api/dispatch", {"workload_id": "w1"})
        assert data["dispatched"] == 1
        status, data, _ = req(s.base, "POST", "/api/complete", {"workload_id": "w1", "success": True, "reason": "done"})
        assert data["workload"]["state"] == "completed"
    finally:
        s.close()


def test_http_doctor_simulate_and_errors(tmp_path):
    s = Server(tmp_path)
    try:
        status, data, _ = req(s.base, "GET", "/api/doctor")
        assert status == 200 and data["ok"] and data["count"] == 6
        status, data, _ = req(s.base, "POST", "/api/simulate", {})
        assert status == 200 and data["ok"]
        status, data, _ = req(s.base, "GET", "/api/targets/missing")
        assert status == 404 and not data["ok"]
        status, data, _ = req(s.base, "POST", "/api/workloads", {"workload_id": "bad", "cpu": 0, "memory_gb": 1})
        assert status == 400 and not data["ok"]
        status, data, _ = req(s.base, "POST", "/api/snapshot", {"label": "t"})
        assert status == 200 and data["snapshot_id"]
        status, data, _ = req(s.base, "GET", "/api/events?limit=5")
        assert status == 200 and isinstance(data["events"], list)
    finally:
        s.close()
