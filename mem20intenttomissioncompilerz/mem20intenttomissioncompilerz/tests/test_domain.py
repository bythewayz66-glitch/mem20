import importlib
MOD="mem20intenttomissioncompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_compile(): m=_m(); r=m.compile_mission({"goal":"build","parts":["design","code"]}); assert len(r["steps"])==2
def test_assign(): m=_m(); r=m.compile_mission({"goal":"build"}); m.assign_agents(r,["a1","a2"]); assert r["steps"][0]["agent"] in ("a1","a2")
def test_progress(): m=_m(); r=m.compile_mission({"goal":"build"}); m.execute_step(r,r["steps"][0]["id"]); pr=m.mission_progress(r); assert pr["done"]==1
def test_validate(): m=_m(); r=m.compile_mission({"goal":"build"}); assert m.validate_mission(r) is True
def test_exec(): m=_m(); r=m.compile_mission({"goal":"build"}); m.execute_step(r,r["steps"][0]["id"]); assert r["steps"][0]["status"]=="done"
