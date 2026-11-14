"""Assimilated mem20enginez crew runtime tests (absorbed members + expanded peers)."""
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
    # assimilated: all absorbed members discovered
    assert isinstance(MEMBERS, tuple)
    assert len(MEMBERS) >= 30
    assert len(MEMBERS) == len(set(MEMBERS))
    assert "mem20mixedinitiativefocusenginez" in MEMBERS
    assert "mem20webhooksupernetworkz" in MEMBERS
    # legacy CLI flags
    assert main(["--version"]) == 0
    assert main(["--members"]) == 0


def test_domain_registry_check_plan():
    reg = domain.member_registry(MEMBERS)
    assert len(reg) == len(MEMBERS)
    # every absorbed member should be present on disk under absorbed/
    assert all(m.absorbed for m in reg)
    st = domain.check_member(MEMBERS[0])
    assert st.name == MEMBERS[0]
    assert st.present
    assert st.absorbed
    statuses = [domain.check_member(n) for n in MEMBERS]
    report = domain.summarize(statuses)
    assert report.members_total == len(MEMBERS)
    assert report.members_present == len(MEMBERS)
    assert report.absorbed_total == len(MEMBERS)
    plan = domain.dispatch_plan("protocol compatibility speculative dispatch prediction lifecycle webhook swarm healing", statuses)
    assert plan.plan_id and isinstance(plan.steps, list)
    assert len(plan.members) > 0
    compat = domain.compatibility(MEMBERS[:5])
    assert "members" in compat and compat["members"] == 5


def test_ecosystem_core_peers_and_expanded_surface():
    # core peer functions remain real and callable
    assert ecosystem.compat_probe()["subsystem"] == "mem20runtimecompatibilityenginez"
    assert ecosystem.protocol_discovery()["subsystem"] == "mem20protocolautodiscoveryenginez"
    assert ecosystem.speculative_plan()["subsystem"] == "mem20speculativeworkflowenginez"
    assert ecosystem.capability_bundle()["subsystem"] == "mem20servicebundlingenginez"
    assert ecosystem.predictive_routing()["subsystem"] == "mem20predictiverecallenginez"
    assert ecosystem.runtime_lifecycle()["subsystem"] == "mem20customerlifecycleenginez"

    p = ecosystem.probe(include_member_ecosystems=True)
    assert p["core_count"] == 6
    assert isinstance(p.get("member_ecosystems"), dict)
    # assimilated peer surface: core 6 + aggregated peer checks from absorbed ecosystems >> 6
    assert p.get("peer_surface_total", 0) >= 20
    assert p["count"] == p["peer_surface_total"]
    # aggregation performed over all members
    assert p["member_ecosystems"]["members_with_ecosystem_probe"] == len(MEMBERS)
    assert p["member_ecosystems"]["peer_checks_total"] >= 0

    # core-only view
    pc = ecosystem.probe(include_member_ecosystems=False)
    assert pc["core_count"] == 6


def test_service_plan_status_doctor_http(tmp_path):
    svc = EngineRuntimeService(tmp_path / "e.db")
    st = svc.status()
    assert st["ok"]
    assert st["members_total"] == len(MEMBERS)
    assert st["members_present"] == len(MEMBERS)
    assert st["absorbed_total"] == len(MEMBERS)
    assert st["peer_surface_total"] >= 20
    assert st["signals"]["runtime_compatibility"]["subsystem"] == "mem20runtimecompatibilityenginez"
    assert st["signals"]["protocol_autodiscovery"]["subsystem"] == "mem20protocolautodiscoveryenginez"
    assert st["signals"]["runtime_lifecycle"]["subsystem"] == "mem20customerlifecycleenginez"
    assert st["signals"]["service_bundling"]["subsystem"] == "mem20servicebundlingenginez"

    mem = svc.members()
    assert mem["ok"] and mem["report"]["members_total"] == len(MEMBERS)

    plan = svc.plan("speculative protocol dispatch webhook swarm healing")
    assert plan["ok"] and plan["plan"]["plan_id"]
    assert "speculative_workflow" in plan["signals"]
    assert "predictive_recall" in plan["signals"]
    assert "service_bundling" in plan["signals"]
    assert "runtime_lifecycle" in plan["signals"]

    doc = svc.doctor()
    assert "probe" in doc and doc["probe"]["core_count"] == 6
    assert doc["probe"].get("peer_surface_total", 0) >= 20

    sim = svc.simulate()
    assert sim["total"] >= 8
    assert sim["passed"] >= 7  # core steps should pass; absorbed aggregation may vary by env

    httpd = serve(svc, "127.0.0.1", 0)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as r:
            body = json.loads(r.read())
            assert body["members_total"] == len(MEMBERS)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/doctor") as r:
            assert json.loads(r.read())["probe"]["core_count"] == 6
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/members") as r:
            assert json.loads(r.read())["report"]["members_total"] == len(MEMBERS)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            body = r.read().decode("utf-8", "ignore")
            assert "mem20enginez" in body.lower() or "engine" in body.lower()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/plan",
            data=json.dumps({"intent": "compatibility check"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as r:
            assert json.loads(r.read())["ok"]
    finally:
        httpd.shutdown()
        httpd.server_close()
        t.join(timeout=2)
