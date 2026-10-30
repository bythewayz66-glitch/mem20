import importlib
MOD="mem20realtimebusinesstwinz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_twin("biz"); assert r["business"]=="biz"
def test_update(): m=_m(); r=m.create_twin("biz"); m.update_kpi(r,"rev",100); assert r["kpis"]["rev"]==100
def test_alerts(): m=_m(); r=m.create_twin("biz"); m.update_kpi(r,"rev",100); a=m.check_alerts(r,{"rev":50}); assert len(a)==1
def test_scenario(): m=_m(); r=m.create_twin("biz"); m.update_kpi(r,"rev",100); s=m.scenario(r,{"rev":120}); assert s["delta"]["rev"]==20
def test_health(): m=_m(); r=m.create_twin("biz"); assert "kpis" in m.twin_health(r)
