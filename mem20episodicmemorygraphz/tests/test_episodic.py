import json, threading, time, urllib.request
import importlib
from mem20episodicmemorygraphz import ecosystem
from mem20episodicmemorygraphz.runtime import serve
from mem20episodicmemorygraphz.service import EpisodicService

def _d(): return importlib.import_module("mem20episodicmemorygraphz.domain")

def test_legacy_api():
    d=_d()
    ep=d.create_episode("ship fix",[{"action":"debug"}])
    assert ep["id"] and ep["title"]=="ship fix"
    ep=d.add_event(ep,{"action":"deploy","place":"lab","person":"alice","outcome":"ok"})
    assert len(ep["events"])==2 and "lab" in ep["entities"]
    ep2=d.create_episode("retro")
    eps=d.link_episodes([ep,ep2], ep["id"], ep2["id"], "follows")
    g=d.episode_graph(eps); assert any(n["id"]==ep["id"] for n in g["nodes"]) and g["edges"]
    r=d.recall(eps,"alice"); assert r
    kept=d.forget(eps, 999999999); assert isinstance(kept,list)

def test_ecosystem_six_peers():
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    assert ecosystem.skill_graph([{"title":"t","events":[{"action":"a"}],"outcomes":["o"]}])["ok"]
    assert ecosystem.reversible_replay([{"id":"e1"}])["ok"]
    assert ecosystem.recall_focus({"attention":0.5},[{"id":"x","relevance":0.5}])["ok"]
    assert ecosystem.spatial_places([{"id":"p1","kind":"place"}])["ok"]
    assert ecosystem.relationship_graph([{"id":"a","entities":["x","y"]}])["ok"]
    assert ecosystem.deterministic_links([{"id":"a","links":[{"to":"b"}]},{"id":"b"}])["ok"]

def test_service_and_http(tmp_path):
    svc=EpisodicService(tmp_path/"e.db")
    c=svc.create_episode("ship fix", events=[{"action":"debug","place":"lab"}], entities=["alice"])
    assert c["ok"] and c["signals"]["focus_recall"]["ok"] and c["signals"]["spatial_places"]["ok"]
    eid=c["episode"]["id"]
    ev=svc.add_event(eid, {"action":"deploy","outcome":"fixed"})
    assert ev["ok"] and ev["signals"]["reversible_execution"]["ok"] and ev["signals"]["dynamic_skill_graph"]["ok"]
    c2=svc.create_episode("retro")
    lk=svc.link(eid,c2["episode"]["id"])
    assert lk["ok"] and lk["signals"]["relationship_graph"]["ok"] and lk["signals"]["deterministic_config"]["ok"]
    rc=svc.recall("lab"); assert rc["ok"] and rc["signals"]["focus_recall"]["ok"]
    q=svc.query({"entity":"alice"}); assert q["ok"]
    st=svc.status(); assert st["ok"] and st["signals"]["dynamic_skill_graph"]["ok"] and st["signals"]["spatial_places"]["ok"]
    doc=svc.doctor(); assert doc["ok"] and doc["probe"]["count"]==6
    sim=svc.simulate(); assert sim["ok"]
    httpd=serve(svc,"127.0.0.1",0); port=httpd.server_address[1]
    t=threading.Thread(target=httpd.serve_forever,daemon=True); t.start(); time.sleep(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as r: assert json.loads(r.read())["ok"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/doctor") as r: assert json.loads(r.read())["probe"]["count"]==6
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r: assert "Episodic" in r.read().decode("utf-8","ignore")
        req=urllib.request.Request(f"http://127.0.0.1:{port}/api/recall", data=json.dumps({"query":"lab"}).encode(), headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req) as r: assert json.loads(r.read())["ok"]
    finally:
        httpd.shutdown(); httpd.server_close(); t.join(timeout=2)
