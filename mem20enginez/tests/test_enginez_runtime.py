"""Real tests for mem20enginez crew runtime (exercises 6 unique peers on covered lines)."""
from __future__ import annotations

import json
import threading
import time
import urllib.request

from mem20enginez.mem20enginez import MEMBERS, __version__, domain, ecosystem
from mem20enginez.mem20enginez.runtime import main, serve
from mem20enginez.mem20enginez.service import EngineRuntimeService


def test_version_and_members():
    assert __version__
    assert len(MEMBERS) == 30
    assert "mem20adaptiveachievementenginez" in MEMBERS
    # legacy CLI flags
    assert main(["--version"]) == 0
    assert main(["--members"]) == 0


def test_domain_registry_check_plan():
    reg = domain.member_registry(MEMBERS)
    assert len(reg) == 30
    st = domain.check_member("mem20enginez")
    assert st.name == "mem20enginez"
    statuses = [domain.check_member(n) for n in MEMBERS]
    report = domain.summarize(statuses)
    assert report.members_total == 30 and report.members_present >= 1
    plan = domain.dispatch_plan("protocol compatibility speculative dispatch prediction lifecycle", statuses)
    assert plan.plan_id and isinstance(plan.steps, list)
    compat = domain.compatibility()
    assert compat["ok"] is True


def test_ecosystem_six_unique_peers():
    p = ecosystem.probe()
    assert p["ok"] and p["count"] == 6
    assert ecosystem.compat_probe()["ok"]
    assert ecosystem.protocol_discovery()["ok"]
    assert ecosystem.speculative_plan()["ok"]
    assert ecosystem.capability_bundle()["ok"]
    assert ecosystem.predictive_routing()["ok"]
    assert ecosystem.runtime_lifecycle()["ok"]


def test_service_plan_status_doctor_http(tmp_path):
    svc = EngineRuntimeService(tmp_path / "e.db")
    st = svc.status()
    assert st["ok"] and st["members_total"] == 30
    assert st["signals"]["runtime_compatibility"]["ok"]
    assert st["signals"]["protocol_autodiscovery"]["ok"]
    assert st["signals"]["runtime_lifecycle"]["ok"]
    assert st["signals"]["service_bundling"]["ok"]

    mem = svc.members()
    assert mem["ok"] and mem["report"]["members_total"] == 30
    assert mem["signals"]["runtime_compatibility"]["ok"] and mem["signals"]["protocol_autodiscovery"]["ok"]

    plan = svc.plan("speculative protocol dispatch")
    assert plan["ok"] and plan["plan"]["plan_id"]
    assert plan["signals"]["speculative_workflow"]["ok"]
    assert plan["signals"]["predictive_recall"]["ok"]
    assert plan["signals"]["service_bundling"]["ok"]
    assert plan["signals"]["runtime_lifecycle"]["ok"]

    doc = svc.doctor()
    assert doc["ok"] and doc["probe"]["count"] == 6

    sim = svc.simulate()
    assert sim["ok"] and sim["passed"] == sim["total"]

    httpd = serve(svc, "127.0.0.1", 0)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as r:
            assert json.loads(r.read())["ok"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/doctor") as r:
            assert json.loads(r.read())["probe"]["count"] == 6
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/members") as r:
            assert json.loads(r.read())["report"]["members_total"] == 30
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            body = r.read().decode("utf-8", "ignore")
            assert "mem20enginez" in body
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/plan", data=json.dumps({"intent": "compatibility check"}).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            assert json.loads(r.read())["ok"]
    finally:
        httpd.shutdown()
        httpd.server_close()
        t.join(timeout=2)
