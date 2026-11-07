from mem20facez.mem20facez import ecosystem
from mem20facez.mem20facez.service import FacezService
from mem20facez.mem20facez.runtime import main
from mem20facez import MEMBERS, __version__

def test_legacy_compat():
    assert __version__ and len(MEMBERS) == 8
    assert "mem20visualagentblackboardz" in MEMBERS
    assert main(["--version"]) == 0 and main(["--members"]) == 0

def test_ecosystem_six_peers():
    p = ecosystem.probe(); assert p["ok"] and p["count"] == 6
    assert ecosystem.multimodal_capture({"text":"x"})["ok"]
    assert ecosystem.dataflow_compose({})["ok"]
    assert ecosystem.mission_compile("compose view")["ok"]
    assert ecosystem.automation_canvas({})["ok"]
    assert ecosystem.sandbox_world({})["ok"]
    assert ecosystem.agent_blackboard({})["ok"]

def test_service_compose_and_doctor():
    svc = FacezService()
    st = svc.status(); assert st["members"] == 8
    c = svc.compose("visual workspace", {"mode":"visual"})
    assert c["ok"] and c["plan"]["selected"]
    sig = c["signals"]
    for k in ("multimodal_capture","dataflow_compose","mission_compile","automation_canvas","sandbox_world","agent_blackboard"):
        assert sig.get(k,{}).get("ok") is True, (k,sig.get(k))
    doc = svc.doctor(); assert "peers" in doc and doc["members"]["total"] == 8
