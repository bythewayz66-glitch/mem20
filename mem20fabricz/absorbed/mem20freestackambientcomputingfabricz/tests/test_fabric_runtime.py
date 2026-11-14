import importlib
import threading
from pathlib import Path

from mem20freestackambientcomputingfabricz.mem20freestackambientcomputingfabricz import ecosystem
from mem20freestackambientcomputingfabricz.mem20freestackambientcomputingfabricz.runtime import Engine, load_config

MOD = "mem20freestackambientcomputingfabricz"


def _d():
    return importlib.import_module(MOD + ".domain")


def _assert_signal(signal):
    assert isinstance(signal, dict) and "subsystem" in signal and "ok" in signal
    if not signal["ok"]:
        assert "error" in signal


def test_legacy_domain():
    m = _d()
    assert m.pool_resources([{"cpu": 2, "memory": 4}])["cpu"] == 2
    assert m.discover_services({"services": [{"id": "s", "capabilities": ["c"]}]}, "c")[0]["id"] == "s"
    a = m.allocate({"pool": {"cpu": 4, "memory": 8}}, {"cpu": 1, "memory": 2})
    assert a["allocated"] is True
    assert m.fabric_health({"nodes": [{"status": "online"}, {"status": "offline"}]})["health"] == 0.5
    assert 0 <= m.ambient_score({"pool": {"cpu": 2}, "total_cpu": 4}) <= 1


def test_ecosystem_six_peers_attempted():
    p = ecosystem.probe()
    assert set(p["checks"].keys()) == {"fabric_dispatch", "inference_compile", "capability_market", "microkernel", "workload_identity", "ambient_companion"}
    for v in p["checks"].values():
        _assert_signal(v)


def test_durable_heterogeneous_nodes_discovery_roaming_and_restart(tmp_path):
    m = _d()
    db = tmp_path / "fabric.sqlite3"
    fs = m.FabricStore(str(db))
    fs.upsert_node({"node_id": "desk1", "device_class": "desktop", "status": "online", "cpu": 8, "memory": 16, "capabilities": ["compute", "render"]})
    fs.upsert_node({"node_id": "phone1", "device_class": "mobile", "status": "online", "cpu": 2, "memory": 4, "capabilities": ["compute"]})
    fs.upsert_node({"node_id": "car1", "device_class": "vehicle", "status": "roaming", "cpu": 4, "memory": 8, "capabilities": ["compute", "nav"]})
    fs.upsert_node({"node_id": "edge1", "device_class": "edge", "status": "offline", "cpu": 4, "memory": 8, "capabilities": ["compute"]})
    snap = fs.fabric_snapshot()
    assert set(snap["device_classes"]) >= {"desktop", "mobile", "vehicle", "edge"}
    mobile = fs.discover(capability="compute", device_class="mobile")
    assert [n["node_id"] for n in mobile] == ["phone1"]
    roaming = fs.discover(capability="nav", include_roaming=True)
    assert any(n["node_id"] == "car1" for n in roaming)
    fs.mark_node_status("car1", "offline")  # disconnection
    assert fs.get_node("car1")["status"] == "offline"
    fs.mark_node_status("car1", "roaming")  # roaming/reconnect transition
    assert fs.get_node("car1")["status"] == "roaming"
    # restart recovery
    fs2 = m.FabricStore(str(db))
    assert fs2.get_node("desk1")["device_class"] == "desktop"
    assert any(n["node_id"] == "phone1" for n in fs2.list_nodes(device_class="mobile"))


def test_atomic_versioned_reservations_conflicts_release_and_expiry(tmp_path):
    m = _d()
    fs = m.FabricStore(str(tmp_path / "r.sqlite3"))
    fs.upsert_node({"node_id": "n1", "device_class": "server", "status": "online", "cpu": 4, "memory": 8, "capabilities": ["compute"]})
    r1 = fs.reserve({"cpu": 3, "memory": 4}, owner="a", lease_s=60)
    assert r1["allocated"] and r1["version"] == 1
    # cannot over-allocate
    r2 = fs.reserve({"cpu": 2, "memory": 2}, owner="b", lease_s=60)
    assert r2["allocated"] is False and r2["reason"] == "no_capacity"
    rel = fs.release(r1["reservation_id"], expected_version=1)
    assert rel["ok"] and rel["status"] == "released" and rel["version"] == 2
    r3 = fs.reserve({"cpu": 2, "memory": 2}, owner="b", lease_s=60)
    assert r3["allocated"] is True
    # idempotency
    r4 = fs.reserve({"cpu": 2, "memory": 2}, owner="b", lease_s=60, idem_key="same")
    r5 = fs.reserve({"cpu": 2, "memory": 2}, owner="b", lease_s=60, idem_key="same")
    # first idem may allocate or not depending on capacity; second must replay
    if r4.get("allocated"):
        assert r5.get("idempotent_replay") is True and r5["reservation_id"] == r4["reservation_id"]
    # expiry
    fs2 = m.FabricStore(str(tmp_path / "e.sqlite3"))
    fs2.upsert_node({"node_id": "n2", "device_class": "edge", "status": "online", "cpu": 2, "memory": 2, "capabilities": ["compute"]})
    ex = fs2.reserve({"cpu": 1}, lease_s=0.01)
    assert ex["allocated"]
    import time as _t; _t.sleep(0.03)
    expired = fs2.expire_leases()
    assert expired["expired"] >= 1
    got = fs2.get_reservation(ex["reservation_id"])
    assert got["status"] == "expired"


def test_concurrent_allocation_does_not_over_allocate(tmp_path):
    m = _d()
    fs = m.FabricStore(str(tmp_path / "c.sqlite3"))
    fs.upsert_node({"node_id": "shared", "device_class": "server", "status": "online", "cpu": 4, "memory": 8, "capabilities": ["compute"]})
    results = []
    lock = threading.Lock()

    def worker(i):
        r = fs.reserve({"cpu": 1, "memory": 1}, owner=f"w{i}", lease_s=120)
        with lock: results.append(r)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=10)
    allocated = [r for r in results if r.get("allocated")]
    assert len(allocated) <= 4, f"over-allocated: {len(allocated)} reservations on 4-cpu node"


def test_node_loss_orphans_active_reservations(tmp_path):
    m = _d()
    fs = m.FabricStore(str(tmp_path / "l.sqlite3"))
    fs.upsert_node({"node_id": "van1", "device_class": "vehicle", "status": "online", "cpu": 2, "memory": 2, "capabilities": ["compute"]})
    r = fs.reserve({"cpu": 1}, node_id="van1", lease_s=120)
    assert r["allocated"]
    fs.mark_node_status("van1", "lost")
    got = fs.get_reservation(r["reservation_id"])
    assert got["status"] == "orphaned"


def test_engine_fabric_signals(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "f.sqlite3"))
    out = eng.execute({"nodes": [{"cpu": 4, "memory": 8, "status": "online", "device_class": "edge"}], "capability": "compute", "request": {"cpu": 1, "memory": 1}, "values": [1, 2, 3]}, idem="f1", timeout_ms=30000)
    assert "fabric_health" in out and "allocation" in out
    sig = out.get("signals") or {}
    for k in ("fabric_dispatch", "inference_compile", "capability_market", "microkernel", "workload_identity", "ambient_companion"):
        _assert_signal(sig.get(k, {}))


def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    sim = eng.simulator()
    assert all(v.get("ok") for v in sim.values()), sim
