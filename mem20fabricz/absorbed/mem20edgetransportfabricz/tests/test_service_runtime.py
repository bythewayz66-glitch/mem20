import json
import threading
import time
import urllib.request
from pathlib import Path

from mem20edgetransportfabricz.runtime import build_parser, serve
from mem20edgetransportfabricz.service import TransportFabricService


def test_service_admit_reroute_status_doctor(tmp_path):
    svc = TransportFabricService(tmp_path / "t.db")
    assert svc.put_node({"node_id": "a"})["ok"]
    assert svc.put_node({"node_id": "b"})["ok"]
    assert svc.put_node({"node_id": "c"})["ok"]
    assert svc.put_link({"src": "a", "dst": "b", "bandwidth_mbps": 100, "latency_ms": 5})["ok"]
    assert svc.put_link({"src": "b", "dst": "c", "bandwidth_mbps": 100, "latency_ms": 5})["ok"]
    assert svc.put_link({"src": "a", "dst": "c", "bandwidth_mbps": 10, "latency_ms": 80})["ok"]
    r = svc.admit({"flow_id": "f1", "src": "a", "dst": "c", "demand_mbps": 2, "priority": 2, "max_latency_ms": 50})
    assert r["ok"] and r["decision"]["path"] == ["a", "b", "c"]
    assert r["signals"]["causal"]["ok"] and r["signals"]["traffic"]["ok"] and r["signals"]["mesh"]["ok"]
    svc.set_link_status("a->b", "down")
    rr = svc.reroute("f1", avoid_links=["a->b"], reason="failure")
    assert rr["ok"] and rr["recovery_signal"]["ok"] and rr["containment_signal"]["ok"]
    st = svc.status()
    assert st["ok"] and st["health"]["links"] == 3 and st["telemetry"]["ok"]
    doc = svc.doctor()
    assert doc["ok"] and doc["probe"]["count"] == 6
    sim = svc.simulate()
    assert sim["ok"] and sim["passed"] == sim["total"]


def test_cli_and_http(tmp_path):
    db = tmp_path / "c.db"
    svc = TransportFabricService(db)
    # CLI parser smoke via service calls through same layer
    svc.put_node({"node_id": "n1"})
    svc.put_node({"node_id": "n2"})
    svc.put_link({"src": "n1", "dst": "n2", "bandwidth_mbps": 50, "latency_ms": 10})
    out = svc.route({"src": "n1", "dst": "n2", "demand_mbps": 1})
    assert out["ok"] and out["path"] == ["n1", "n2"]
    # HTTP
    httpd = serve(svc, "127.0.0.1", 0)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as r:
            j = json.loads(r.read())
            assert j["ok"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/doctor") as r:
            j = json.loads(r.read())
            assert j["probe"]["count"] == 6
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/route", data=json.dumps({"src":"n1","dst":"n2"}).encode(), headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req) as r:
            j = json.loads(r.read())
            assert j["ok"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            html = r.read().decode("utf-8", "ignore")
            assert "Edge Transport Fabric" in html
    finally:
        httpd.shutdown(); httpd.server_close(); t.join(timeout=2)
    # parser exists (CLI presence)
    p = build_parser()
    args = p.parse_args(["--db", str(db), "status"])
    assert args.cmd == "status"
