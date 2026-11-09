import importlib
MOD="mem20simz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_funnel(): assert _m().funnel(100,[{"conversion":0.5}])==[100,50]
def test_viral(): assert _m().viral_coefficient(2,0.1)==0.2
def test_retention(): r=_m().retention_curve(100,0.1,2); assert r[0]==100 and len(r)==3
def test_score(): assert _m().growth_score({"viral_k":0.3,"conversion":0.3,"retention":0.3})==0.3
def test_sim(): s=_m().simulate({"starting_users":100,"invites":2,"invite_conv":0.1}); assert s["viral_k"]==0.2
def test_eco_biz(): r=_eco().business_economics(100,10); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_lifecycle(): r=_eco().lifecycle_retention(); assert r["ok"] and r["subsystem"]=="mem20customerlifecycleenginez"
def test_eco_pipeline(): r=_eco().pipeline_conversion(); assert r["ok"] and r["subsystem"]=="mem20autonomoussaleslaboratoryz"
def test_eco_loyalty(): r=_eco().loyalty_expansion(); assert r["ok"] and r["subsystem"]=="mem20crossproductloyaltygraphz"
def test_eco_forecast(): r=_eco().growth_forecast([100,120]); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_events(): r=_eco().funnel_events("f",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_report_and_probe():
    m=_m(); rep=m.plg_report(); assert rep["viral_k"]==0.2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
