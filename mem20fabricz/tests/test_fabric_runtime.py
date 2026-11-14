import json
from mem20fabricz.mem20fabricz import ecosystem
from mem20fabricz.mem20fabricz.service import FabricService
from mem20fabricz.mem20fabricz.runtime import main
from mem20fabricz import MEMBERS, __version__

def test_legacy_compat():
    assert __version__
    assert len(MEMBERS) >= 20
    assert len(MEMBERS) == len(set(MEMBERS))
    assert "mem20apishapeshiftinggatewayz" in MEMBERS
    assert main(["--version"]) == 0
    assert main(["--members"]) == 0

def test_ecosystem_core_and_expanded():
    p = ecosystem.probe()
    assert p["core_count"] == 6
    assert p.get("peer_surface_total", 0) >= 6
    assert ecosystem.api_gateway({"id": 1})["subsystem"] == "mem20apishapeshiftinggatewayz"
    assert ecosystem.integration_compiler({"fields": {"x": "y"}})["subsystem"] == "mem20universalintegrationcompilerz"
    assert ecosystem.episodic_traces("t")["subsystem"] == "mem20episodicmemorygraphz"
    assert ecosystem.event_autopilot({"type": "x"})["subsystem"] == "mem20realtimeeventautopilotz"
    assert ecosystem.team_radio("hi")["subsystem"] == "mem20ambientteamradioz"
    assert ecosystem.dispatch_value({"value": 500})["subsystem"] == "mem20autonomousdealdeskz"

def test_service_dispatch_and_doctor():
    svc = FabricService()
    st = svc.status()
    assert st["members"] == len(MEMBERS)
    assert st.get("absorbed_total", 0) == len(MEMBERS)
    d = svc.dispatch("integrate", {"kind": "api", "value": 2000, "mapping": {"fields": {"a": "b"}}})
    assert d["ok"] and d["plan"]["selected"]
    sig = d["signals"]
    for k in ("api_gateway", "integration_compiler", "episodic_traces", "event_autopilot", "team_radio", "dispatch_value"):
        assert k in sig
        assert "subsystem" in sig[k]
    doc = svc.doctor()
    assert "peers" in doc and "members" in doc
    assert doc.get("peer_surface_total", 0) >= 6
