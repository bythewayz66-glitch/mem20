from mem20facez.mem20facez import ecosystem
from mem20facez.mem20facez.service import FacezService
from mem20facez.mem20facez.runtime import main
from mem20facez import MEMBERS, __version__


def _assert_signal(signal):
    assert isinstance(signal, dict) and "subsystem" in signal and "ok" in signal
    if not signal["ok"]:
        assert "error" in signal


def test_legacy_compat():
    assert __version__ and len(MEMBERS) == 8
    assert "mem20visualagentblackboardz" in MEMBERS
    assert main(["--version"]) == 0 and main(["--members"]) == 0


def test_ecosystem_six_peers_attempted():
    p = ecosystem.probe()
    assert set(p["checks"].keys()) == {"multimodal_capture", "dataflow_compose", "mission_compile", "automation_canvas", "sandbox_world", "agent_blackboard"}
    for v in p["checks"].values():
        _assert_signal(v)


def test_service_compose_and_doctor(tmp_path):
    svc = FacezService(str(tmp_path / "facez.db"))
    st = svc.status()
    assert st["members"] == 8 and "durable" in st
    c = svc.compose("visual workspace", {"mode": "visual"})
    assert c["ok"] and c["plan"]["selected"] and c["composition_id"]
    assert c["status"] in ("completed", "partial")
    sig = c["signals"]
    for k in ("multimodal_capture", "dataflow_compose", "mission_compile", "automation_canvas", "sandbox_world", "agent_blackboard"):
        _assert_signal(sig.get(k, {}))
    doc = svc.doctor()
    assert "peers" in doc and doc["members"]["total"] == 8


def test_durable_composition_lifecycle_persistence_and_restart(tmp_path):
    db = tmp_path / "d.db"
    svc = FacezService(str(db))
    c = svc.compose("workspace", {"mode": "visual", "text": "design"})
    assert c["ok"] and c["version"] >= 1
    got = svc.get_composition(c["composition_id"])
    assert got["ok"] and got["composition"]["composition_id"] == c["composition_id"]
    assert got["composition"]["status"] in ("completed", "partial")
    assert len(got["history"]) >= 3  # validated/step events/finished
    # restart
    svc2 = FacezService(str(db))
    got2 = svc2.get_composition(c["composition_id"])
    assert got2["ok"] and got2["composition"]["version"] == got["composition"]["version"]
    assert got2["composition"]["plan"] == got["composition"]["plan"]


def test_invalid_input_and_rollback_and_recovery(tmp_path):
    svc = FacezService(str(tmp_path / "r.db"))
    try:
        svc.compose("", {})
        raise AssertionError("expected ValidationError")
    except Exception as e:
        assert "intent" in str(e).lower() or e.__class__.__name__ == "ValidationError"
    c = svc.compose("recover me", {"mode": "test"})
    rb = svc.rollback(c["composition_id"], reason="test")
    assert rb["ok"] and rb["composition"]["status"] == "rolled_back"
    rec = svc.recover(c["composition_id"])
    assert rec["ok"]


def test_peer_failure_surfaces_partial_completion(tmp_path, monkeypatch):
    import mem20facez.mem20facez.ecosystem as eco

    def boom(_payload=None):
        return {"ok": False, "subsystem": "mem20visualagentblackboardz", "error": "InjectedError: simulated peer failure"}
    monkeypatch.setattr(eco, "agent_blackboard", boom)
    svc = FacezService(str(tmp_path / "p.db"))
    c = svc.compose("workspace", {"mode": "visual"})
    assert c["composition_id"]
    assert c["status"] in ("partial", "completed", "failed")
    assert c["signals"]["agent_blackboard"]["ok"] is False
    assert c["errors"] or c["status"] == "partial" or any(not s["ok"] for s in c["steps"])
    got = svc.get_composition(c["composition_id"])
    assert got["ok"] and any(ev["kind"].startswith("step.") for ev in got["history"])
