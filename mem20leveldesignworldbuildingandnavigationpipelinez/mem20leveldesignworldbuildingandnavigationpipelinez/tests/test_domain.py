import importlib
MOD="mem20leveldesignworldbuildingandnavigationpipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_navmesh(): m=_m(); r=m.generate_navmesh([[0,1],[0,0]]); assert (0,0) in r
def test_path(): m=_m(); r=m.pathfind([[0,0],[0,0]],(0,0),(1,1)); assert len(r)>0
def test_props(): m=_m(); r=m.place_props({"width":5,"height":5},["tree"],1); assert len(r)==1
def test_validate(): m=_m(); r=m.validate_level({"rooms":[{"w":1,"h":1}]}); assert r["valid"] is True

from mem20leveldesignworldbuildingandnavigationpipelinez import ecosystem


def _assert_signal(sig):
    assert isinstance(sig, dict) and "subsystem" in sig and "ok" in sig
    if not sig["ok"]:
        assert "error" in sig


def test_build_and_run_pipeline():
    m = _m()
    p = m.build_pipeline({"id": "lvl1", "width": 6, "height": 6, "rooms": [{"id": "r1"}], "props": ["spawn", "goal"], "stages": ["blockout", "navigation", "playability_tests"]})
    assert p["status"] == "planned" and len(p["stages"]) == 3
    assert p["stages"][1]["depends_on"] == [p["stages"][0]["id"]]
    m.run_pipeline_stage(p, p["stages"][1]["id"])
    assert p["stages"][1]["status"] == "blocked"
    m.run_pipeline_stage(p, "blockout"); m.run_pipeline_stage(p, "navigation"); m.run_pipeline_stage(p, "playability_tests")
    assert p["status"] in ("completed", "failed") and m.pipeline_progress(p)["done"] >= 2


def test_compile_level_plan():
    m = _m()
    r = m.compile_level_plan({"id": "lvl2", "grid": [[0, 0, 0], [0, 1, 0], [0, 0, 0]], "rooms": [{"id": "r1"}], "stages": ["blockout", "navigation", "encounters", "streaming", "lighting", "playability_tests"]})
    assert r["ok"] and r["summary"]["stages"] == 6 and r["summary"]["dependencies"] == 5
    assert r["pipeline"]["status"] == "completed" and r["progress"]["progress"] == 1.0


def test_ecosystem_peers():
    spec = {"id": "lvl", "stages": ["blockout", "navigation"], "narrative": "NPC: Hi"}
    _assert_signal(ecosystem.production_control_signal(spec))
    _assert_signal(ecosystem.asset_intake_signal(spec))
    _assert_signal(ecosystem.gameplay_balance_signal(spec))
    _assert_signal(ecosystem.level_architect_signal(spec))
    _assert_signal(ecosystem.narrative_signal(spec))
    _assert_signal(ecosystem.orchestration_signal(spec))
    sig = ecosystem.pipeline_signals(spec)
    assert set(sig["checks"].keys()) == {"production_control", "asset_intake", "gameplay_balance", "level_architect", "narrative", "orchestration"}
    for v in sig["checks"].values():
        _assert_signal(v)
