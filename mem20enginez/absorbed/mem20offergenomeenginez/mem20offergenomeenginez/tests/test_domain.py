import importlib
MOD="mem20offergenomeenginez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_genome({"price":10,"components":["a"]}); assert "genes" in r
def test_mutate(): m=_m(); g=m.create_genome({"price":10,"components":["a"]}); g2=m.mutate(g,rate=1.0,seed=1); assert g2 is not None
def test_fit(): m=_m(); g=m.create_genome({"price":10,"components":["a"]}); r=m.fitness(g); assert 0<=r<=1
def test_evolve(): m=_m(); pop=[m.create_genome({"price":10,"components":["a"]}) for _ in range(4)]; r=m.evolve(pop,generations=2,seed=1); assert len(r)==4

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_fabric(): r=_eco().offer_fabric(); assert r["ok"] and r["subsystem"]=="mem20offerassemblyfabricz"
def test_eco_deal(): r=_eco().deal_desk(); assert r["ok"] and r["subsystem"]=="mem20autonomousdealdeskz"
def test_eco_plg(): r=_eco().plg_sim(); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_cf(): r=_eco().counterfactual(); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_events(): r=_eco().genome_events("g",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().genome_routing("k",["g"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.genome_report(); assert rep["population"]==4 and 0<=rep["fitness"]<=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
