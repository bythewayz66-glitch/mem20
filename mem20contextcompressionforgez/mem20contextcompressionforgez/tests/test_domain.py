import importlib
MOD="mem20contextcompressionforgez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_compress(): assert "..." in _m().compress("a b c d e f g h", 0.5)
def test_summary(): assert isinstance(_m().extractive_summary("A. B. C. D.", 2), list)
def test_ratio(): assert 0<=_m().compression_ratio("hello","he")<=1
def test_terms(): assert isinstance(_m().key_terms("memory compression system memory"), list)
def test_forge(): r=_m().forge_context(["abc","def"],10); assert r["used_tokens"]==6
def test_eco_stream(): r=_eco().stream_compressed("x",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_summary(): r=_eco().summary_quality("x"); assert r["ok"] and r["subsystem"]=="mem20loreragcontentgeneratorz"
def test_eco_focus(): r=_eco().focus_retention({"priority":1,"distractions":0}); assert r["ok"] and r["subsystem"]=="mem20mixedinitiativefocusenginez"
def test_eco_strategy(): r=_eco().strategy_routing("k",["e"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_budget(): r=_eco().budget_forecast([200,300],1000); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_keep(): r=_eco().keep_routing({"r":1},{"r":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.compression_report(); assert rep["compression_ratio"]<=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
