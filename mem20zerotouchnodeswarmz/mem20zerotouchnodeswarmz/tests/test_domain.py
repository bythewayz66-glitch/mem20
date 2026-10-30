"""Zero-touch node swarm domain tests."""
import importlib
import pytest

MOD = "mem20zerotouchnodeswarmz"


def _m():
    return importlib.import_module(MOD + ".domain")


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
