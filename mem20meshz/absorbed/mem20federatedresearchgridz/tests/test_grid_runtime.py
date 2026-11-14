import importlib
from pathlib import Path

from mem20federatedresearchgridz.mem20federatedresearchgridz import ecosystem
from mem20federatedresearchgridz.mem20federatedresearchgridz.runtime import Engine, load_config

MOD = "mem20federatedresearchgridz"


def _d():
    return importlib.import_module(MOD + ".domain")


def _assert_signal(signal):
    assert isinstance(signal, dict) and "subsystem" in signal and "ok" in signal
    if not signal["ok"]:
        assert "error" in signal


def test_legacy_domain():
    m = _d()
    g = m.register_node({"nodes": []}, {"id": "n1"})
    assert len(g["nodes"]) == 1
    g = m.register_node({"nodes": []}, {"id": "n1", "status": "ready", "load": 0})
    assert m.distribute_task(g, {"cost": 1})["id"] == "n1"
    assert m.aggregate_results([1.0, 2.0, 3.0]) == 2.0
    g = m.register_node({"nodes": []}, {"id": "n1", "status": "ready"})
    assert m.grid_health(g)["health"] == 1.0
    g = m.register_node({"nodes": []}, {"id": "n1", "status": "ready", "load": 0, "compute": 2})
    assert m.federated_round(g, {"size": 3})["ok"] is True


def test_ecosystem_six_peers_attempted():
    p = ecosystem.probe()
    assert set(p["checks"].keys()) == {"collective_intel", "cognitive_search", "db_playground", "crdt_merge", "priority_resolve", "connector_market"}
    for v in p["checks"].values():
        _assert_signal(v)


def test_federated_execution_keeps_source_records_local():
    m = _d()
    grid = {"nodes": []}
    m.register_node(grid, {"id": "hospital-a", "status": "ready", "local_data": {"records": [{"label": "positive", "count": 2}, {"label": "positive", "count": 1}]}})
    m.register_node(grid, {"id": "hospital-b", "status": "ready", "local_data": {"records": [{"label": "negative", "count": 5}]}})
    out = m.federated_research_round(grid, {"task_id": "study-1", "query": "label", "type": "research"}, min_nodes=2)
    assert out["ok"] and out["local_data_isolated"] and out["provenance_complete"]
    assert set(out["nodes_selected"]) == {"hospital-a", "hospital-b"}
    # ensure no cross-node data leakage: each result provenance points to its own node and record count
    by_node = {r["node_id"]: r for r in out["results"]}
    assert by_node["hospital-a"]["provenance"]["local_record_count"] == 2
    assert by_node["hospital-b"]["provenance"]["local_record_count"] == 1
    assert by_node["hospital-a"]["value"] == "positive"
    assert by_node["hospital-b"]["value"] == "negative"
    # each node's local_data remains only its own
    nodes = {n["id"]: n for n in grid["nodes"]}
    assert len(nodes["hospital-a"]["local_data"]["records"]) == 2
    assert len(nodes["hospital-b"]["local_data"]["records"]) == 1


def test_aggregation_provenance_and_conflicting_outputs():
    m = _d()
    numeric = m.aggregate_results([{"value": 1.0, "validation": {"valid": True}, "provenance": {"x": 1}}, {"value": 3.0}])
    assert numeric == 2.0
    conflict = m.aggregate_results([{"value": "approve"}, {"value": "reject"}, {"value": "approve"}])
    assert conflict["type"] == "categorical_aggregate"
    assert conflict["majority"] == "approve" and conflict["conflict"] is True
    assert conflict["total"] == 3 and len(conflict["distribution"]) == 2
    consensus = m.aggregate_results(["yes", "yes"])
    assert consensus["consensus"] is True and consensus["conflict"] is False


def test_node_loss_retry_duplicate_idempotency_and_partial_recovery():
    m = _d()
    grid = {"nodes": []}
    m.register_node(grid, {"id": "n1", "status": "ready", "local_data": {"records": [{"label": "a"}]}})
    m.register_node(grid, {"id": "n2", "status": "lost", "local_data": {"records": [{"label": "b"}]}})
    # partial recovery when a selected node fails? select ready nodes only
    out = m.federated_research_round(grid, {"task_id": "t1", "query": "label"}, min_nodes=1)
    assert out["ok"] and any(r["node_id"] == "n1" for r in out["results"])
    # duplicate delivery/idempotency on same node
    node = [n for n in grid["nodes"] if n["id"] == "n1"][0]
    r1 = m.execute_task_on_node(node, {"task_id": "dup1", "query": "label"}, delivery_id="d1")
    r2 = m.execute_task_on_node(node, {"task_id": "dup1", "query": "label"}, delivery_id="d2")
    assert r1["task_id"] == r2["task_id"] and r2["duplicate_delivery"] is True and r2["idempotent_replay"] is True
    assert r1["value"] == r2["value"]
    # retry on transient failure: node lost then set ready is handled by federated_round; simulate by making a lost node and retry budget
    grid2 = {"nodes": [ {"id": "x1", "status": "ready", "load": 0, "compute": 1}]}
    fr = m.federated_round(grid2, {"task_id": "t2", "size": 2}, max_retries=2)
    assert fr["ok"] and fr["task_id"] == "t2" and fr["attempts"] >= 1


def test_engine_search_grid_signals(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "g.sqlite3"))
    out = eng.execute({"query": "federated research", "documents": [{"id": "d1", "text": "node task"}], "nodes": [{"id": "n1", "status": "ready", "load": 0, "compute": 2}], "task": {"cost": 1, "size": 3, "query": "research"}}, idem="g1", timeout_ms=30000)
    assert "results" in out and "grid_health" in out and "federated_round" in out
    sig = out.get("signals") or {}
    for k in ("collective_intel", "cognitive_search", "db_playground", "crdt_merge", "priority_resolve", "connector_market"):
        _assert_signal(sig.get(k, {}))


def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    sim = eng.simulator()
    assert all(v.get("ok") for v in sim.values()), sim
