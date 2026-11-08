"""Zero-touch node swarm domain tests."""
import importlib
import pytest

MOD = "mem20zerotouchnodeswarmz"

def _m():
    return importlib.import_module(MOD + ".domain")
def _eco():
    return importlib.import_module(MOD + ".ecosystem")

def test_register_node():
    m = _m()
    swarm = {"nodes": []}
    out = m.register_node(swarm, {"id": "n1", "capacity": 2, "capabilities": ["code"]})
    assert out["count"] == 1
    # idempotent
    out2 = m.register_node(out, {"id": "n1", "capacity": 2, "capabilities": ["code"]})
    assert out2["count"] == 1

def test_discover_filter():
    m = _m()
    swarm = {"nodes": []}
    swarm = m.register_node(swarm, {"id": "n1", "capacity": 2, "capabilities": ["code"], "status": "ready"})
    swarm = m.register_node(swarm, {"id": "n2", "capacity": 1, "capabilities": ["data"], "status": "ready"})
    assert len(m.discover(swarm)) == 2
    assert len(m.discover(swarm, "code")) == 1

def test_assign_task():
    m = _m()
    swarm = {"nodes": []}
    swarm = m.register_node(swarm, {"id": "n1", "capacity": 2, "capabilities": ["code"], "status": "ready", "load": 0.1})
    task = {"capability": "code", "urgency": 0.5}
    res = m.assign_task(swarm, task)
    assert res["node"]["id"] == "n1"

def test_heal():
    m = _m()
    swarm = {"nodes": []}
    swarm = m.register_node(swarm, {"id": "n1", "capacity": 2, "status": "ready", "load": 0.5})
    swarm = m.register_node(swarm, {"id": "n2", "capacity": 1, "status": "ready", "load": 0.3})
    swarm = m.mark_failed(swarm, "n1")
    healed = m.heal(swarm)
    assert healed["healed"] == 1
    assert len(healed["nodes"]) == 1

def test_quorum():
    m = _m()
    swarm = {"nodes": []}
    swarm = m.register_node(swarm, {"id": "n1", "status": "ready"})
    swarm = m.register_node(swarm, {"id": "n2", "status": "ready"})
    assert m.quorum(swarm, 0.5) is True

def test_join_token():
    m = _m()
    t = m.join_token("n1")
    assert isinstance(t, str) and len(t) == 16

def test_estate_context_real_integrations(tmp_path):
    m = _m()
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["enrolment_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

def test_eco_scheduler(): r=_eco().workload_scheduler(); assert r["ok"] and r["subsystem"]=="mem20roamingworkloadschedulerz"
def test_eco_fleet(): r=_eco().edge_fleet(); assert r["ok"] and r["subsystem"]=="mem20edgefleetbrainz"
def test_eco_routing(): r=_eco().swarm_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_events(): r=_eco().swarm_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().swarm_containment("s"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_recovery(): r=_eco().recovery_director(); assert r["ok"] and r["subsystem"]=="mem20autonomousrecoverydirectorz"
def test_report_and_probe():
    m=_m(); rep=m.swarm_report(); assert rep["nodes"]==1 and len(rep["peers"])==6 and rep["assignment"]["node"] is not None
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
