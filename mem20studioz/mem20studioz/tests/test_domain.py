import importlib
MOD="mem20studioz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_eco_audio(): r=_eco().audio_pipeline(); assert r["ok"] and r["subsystem"]=="mem20audiovoiceandmusicpipelinez"
def test_eco_rig(): r=_eco().rig_pipeline(); assert r["ok"] and r["subsystem"]=="mem20rigginganimationandmotionpipelinez"
def test_eco_prod(): r=_eco().production_pipeline(); assert r["ok"] and r["subsystem"]=="mem20productionplanningandtaskorchestrationpipelinez"
def test_eco_events(): r=_eco().studio_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().studio_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_workcell(): r=_eco().workcell_dispatch(); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_report_and_probe():
    m=_m(); rep=m.studio_report(); assert len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
