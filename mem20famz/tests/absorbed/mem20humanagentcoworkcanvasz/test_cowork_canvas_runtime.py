from pathlib import Path
from mem20humanagentcoworkcanvasz.mem20humanagentcoworkcanvasz import ecosystem
from mem20humanagentcoworkcanvasz.mem20humanagentcoworkcanvasz.runtime import Engine, load_config
from mem20humanagentcoworkcanvasz.mem20humanagentcoworkcanvasz.domain import create_canvas, add_item, take_turn, contributions, canvas_summary

def test_legacy_domain_preserved_for_320():
    c = create_canvas("c", ["u1", "u2"]); assert c["name"] == "c"
    it = add_item(c, "u1", "hi"); assert it["id"] == 0
    r = take_turn(c, "u1"); assert r["ok"] is True
    assert contributions(c)["u1"] == 1
    assert "items" in canvas_summary(c)

def test_meaningful_sync_report():
    r = ecosystem.sync_report({"name":"ws","participants":["human","agent"],"items":[{"author":"human","content":"task","kind":"task"}]})
    assert r["integration_health"]["ok"] == 6 and r["sync_status"] == "synced"
    assert r["canvas"]["name"] == "ws"

def test_engine_sync_and_generic(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path/"cc.sqlite3"))
    out = eng.execute({"name":"ws","participants":["human","agent"],"items":[{"author":"human","content":"x"}]}, idem="s1")
    assert out["integration_health"]["ok"] == 6
    gen = eng.execute({"goal":"sync"}, idem="g1")
    assert "synced" in gen or "confidence" in gen or "decision" in gen

def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
