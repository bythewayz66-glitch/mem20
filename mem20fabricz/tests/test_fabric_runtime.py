import json
from mem20fabricz.mem20fabricz import ecosystem
from mem20fabricz.mem20fabricz.service import FabricService
from mem20fabricz.mem20fabricz.runtime import main
from mem20fabricz import MEMBERS, __version__

def test_legacy_compat():
    assert __version__
    assert len(MEMBERS) == 23
    assert "mem20apishapeshiftinggatewayz" in MEMBERS
    assert main(["--version"]) == 0
    assert main(["--members"]) == 0

def test_ecosystem_six_peers():
    p = ecosystem.probe()
    assert p["ok"] and p["count"] == 6
    assert ecosystem.api_gateway({"id": 1})["ok"]
    assert ecosystem.integration_compiler({"fields": {"x": "y"}})["ok"]
    assert ecosystem.episodic_traces("t")["ok"]
    assert ecosystem.event_autopilot({"type": "x"})["ok"]
    assert ecosystem.team_radio("hi")["ok"]
    assert ecosystem.dispatch_value({"value": 500})["ok"]

def test_service_dispatch_and_doctor():
    svc = FabricService()
    st = svc.status()
    assert st["members"] == 23
    d = svc.dispatch("integrate", {"kind": "api", "value": 2000, "mapping": {"fields": {"a": "b"}}})
    assert d["ok"] and d["plan"]["selected"]
    sig = d["signals"]
    for k in ("api_gateway", "integration_compiler", "episodic_traces", "event_autopilot", "team_radio", "dispatch_value"):
        assert sig.get(k, {}).get("ok") is True, (k, sig.get(k))
    doc = svc.doctor()
    assert "peers" in doc and "members" in doc
