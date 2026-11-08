import json
import threading
import time
import urllib.request
import importlib

from mem20episodicmemorygraphz import ecosystem
from mem20episodicmemorygraphz.runtime import serve
from mem20episodicmemorygraphz.service import ConflictError, EpisodicService


def _d():
    return importlib.import_module("mem20episodicmemorygraphz.domain")


def _assert_signal(signal):
    assert isinstance(signal, dict)
    assert "subsystem" in signal
    assert "ok" in signal
    if not signal["ok"]:
        assert "error" in signal and signal["error"]


def test_legacy_api():
    d = _d()
    ep = d.create_episode("ship fix", [{"action": "debug"}])
    assert ep["id"] and ep["title"] == "ship fix"
    ep = d.add_event(ep, {"action": "deploy", "place": "lab", "person": "alice", "outcome": "ok"})
    assert len(ep["events"]) == 2 and "lab" in ep["entities"]
    ep2 = d.create_episode("retro")
    eps = d.link_episodes([ep, ep2], ep["id"], ep2["id"], "follows")
    g = d.episode_graph(eps)
    assert any(n["id"] == ep["id"] for n in g["nodes"]) and g["edges"]
    r = d.recall(eps, "alice")
    assert r
    kept = d.forget(eps, 999999999)
    assert isinstance(kept, list)


def test_collision_resistant_ids_and_idempotency():
    d = _d()
    a = d.create_episode("same title")
    b = d.create_episode("same title")
    assert a["id"] != b["id"], "repeated titles must remain distinct without explicit id/key"
    explicit = d.create_episode("same title", episode_id="ep-explicit")
    assert explicit["id"] == "ep-explicit"
    k1 = d.create_episode("any", idempotency_key="deploy-123")
    k2 = d.create_episode("different", idempotency_key="deploy-123")
    assert k1["id"] == k2["id"], "same idempotency key must map to same episode id"


def test_ecosystem_six_peers_attempted():
    p = ecosystem.probe()
    assert isinstance(p, dict)
    assert set(p["checks"].keys()) == {
        "dynamic_skill_graph", "reversible_execution", "focus_recall",
        "spatial_places", "relationship_graph", "deterministic_config",
    }
    assert p["count"] == len(p["reachable"])
    for signal in p["checks"].values():
        _assert_signal(signal)
    assert ecosystem.skill_graph([{"title": "t", "events": [{"action": "a"}], "outcomes": ["o"]}])["ok"]
    assert ecosystem.reversible_replay([{"id": "e1"}])["ok"]
    _assert_signal(ecosystem.recall_focus({"attention": 0.5}, [{"id": "x", "relevance": 0.5}]))
    _assert_signal(ecosystem.spatial_places([{"id": "p1", "kind": "place"}]))
    _assert_signal(ecosystem.relationship_graph([{"id": "a", "entities": ["x", "y"]}]))
    _assert_signal(ecosystem.deterministic_links([{"id": "a", "links": [{"to": "b"}]}, {"id": "b"}]))


def test_service_duplicate_title_persistence_and_version_conflict(tmp_path):
    svc = EpisodicService(tmp_path / "e.db")
    c1 = svc.create_episode("same title", events=[{"action": "a"}])
    c2 = svc.create_episode("same title", events=[{"action": "b"}])
    assert c1["ok"] and c2["ok"]
    assert c1["episode"]["id"] != c2["episode"]["id"]
    for s in (c1, c2):
        _assert_signal(s["signals"]["focus_recall"])
        _assert_signal(s["signals"]["spatial_places"])
    listed = svc.list(100)["episodes"]
    same = [e for e in listed if e.get("title") == "same title"]
    assert len(same) == 2, "duplicate titles must be preserved as distinct episodes"
    # version conflict safety
    eid = c1["episode"]["id"]
    base = svc.get(eid)["episode"]["version"]
    svc.add_event(eid, {"action": "first"}, expected_version=base)
    try:
        svc.add_event(eid, {"action": "stale"}, expected_version=base)
        raise AssertionError("expected ConflictError for stale expected_version")
    except ConflictError:
        pass
    fresh = svc.get(eid)["episode"]
    assert any(ev.get("action") == "first" for ev in fresh["events"])
    assert not any(ev.get("action") == "stale" for ev in fresh["events"])


def test_snapshot_restore_removes_post_snapshot_records(tmp_path):
    db = tmp_path / "snap.db"
    svc = EpisodicService(db)
    a = svc.create_episode("before")["episode"]
    snap = svc.snapshot("baseline")
    b = svc.create_episode("after")["episode"]
    svc.add_event(a["id"], {"action": "post-snapshot"})
    restored = svc.restore(snap["snapshot_id"])
    assert restored["ok"] and restored["restored"] == 1
    ids = {e["id"] for e in svc.list(100)["episodes"]}
    assert a["id"] in ids
    assert b["id"] not in ids, "post-snapshot episode must be removed on restore"
    assert svc.get(a["id"])["episode"].get("events") == [], "post-snapshot mutations must be removed on restore"
    # restart persistence of restored state
    svc2 = EpisodicService(db)
    ids2 = {e["id"] for e in svc2.list(100)["episodes"]}
    assert ids2 == ids


def test_graph_temporal_entity_retrieval(tmp_path):
    svc = EpisodicService(tmp_path / "r.db")
    t0 = time.time() - 1000
    t1 = time.time() - 500
    e1 = _d().create_episode("incident alpha")
    e1["created_at"] = t0
    e1 = _d().add_event(e1, {"action": "triage", "person": "alice", "place": "lab"})
    svc.store.put_episode(e1)
    e2 = _d().create_episode("incident beta")
    e2["created_at"] = t1
    e2 = _d().add_event(e2, {"action": "deploy", "person": "bob", "place": "prod"})
    svc.store.put_episode(e2)
    svc.link(e1["id"], e2["id"], relation="follows")
    by_entity = svc.recall("", entity="alice", expand_graph=True)
    assert by_entity["ok"] and by_entity["retrieval"]["mode"] == "graph_temporal_entity"
    assert [r["id"] for r in by_entity["results"]] == [e1["id"]]
    assert e1["id"] in (by_entity.get("neighbors") or {})
    by_time = svc.recall("", since=t1 - 1)
    assert [r["id"] for r in by_time["results"]] == [e2["id"]]
    q = svc.query({"relation": "follows"})
    assert q["ok"] and any(ed.get("relation") == "follows" for ed in q["graph"]["edges"])


def test_service_and_http(tmp_path):
    svc = EpisodicService(tmp_path / "e.db")
    c = svc.create_episode("ship fix", events=[{"action": "debug", "place": "lab"}], entities=["alice"])
    assert c["ok"]
    _assert_signal(c["signals"]["focus_recall"])
    _assert_signal(c["signals"]["spatial_places"])
    eid = c["episode"]["id"]
    ev = svc.add_event(eid, {"action": "deploy", "outcome": "fixed"})
    assert ev["ok"]
    _assert_signal(ev["signals"]["reversible_execution"])
    _assert_signal(ev["signals"]["dynamic_skill_graph"])
    c2 = svc.create_episode("retro")
    lk = svc.link(eid, c2["episode"]["id"])
    assert lk["ok"]
    _assert_signal(lk["signals"]["relationship_graph"])
    _assert_signal(lk["signals"]["deterministic_config"])
    rc = svc.recall("lab")
    assert rc["ok"]
    _assert_signal(rc["signals"]["focus_recall"])
    q = svc.query({"entity": "alice"})
    assert q["ok"]
    st = svc.status()
    assert st["ok"]
    _assert_signal(st["signals"]["dynamic_skill_graph"])
    _assert_signal(st["signals"]["spatial_places"])
    doc = svc.doctor()
    assert "probe" in doc and "count" in doc["probe"]
    assert set(doc["probe"]["checks"].keys()) == set(ecosystem.probe()["checks"].keys())
    sim = svc.simulate()
    assert sim["ok"] or sim.get("scenarios", {}).get("peer_probe", {}).get("ok") is False
    httpd = serve(svc, "127.0.0.1", 0)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as r:
            assert json.loads(r.read())["ok"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/doctor") as r:
            body = json.loads(r.read())
            assert "probe" in body
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            page = r.read().decode("utf-8", "ignore")
            assert "Episodic" in page or "<html" in page.lower() or page
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/recall", data=json.dumps({"query": "lab", "expand_graph": True}).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            assert json.loads(r.read())["ok"]
    finally:
        httpd.shutdown()
        httpd.server_close()
        t.join(timeout=2)
