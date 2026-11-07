import importlib

MOD = "mem20autonomousdealdeskz"


def _m():
    return importlib.import_module(MOD + ".domain")


def _eco():
    return importlib.import_module(MOD + ".ecosystem")


def test_price():
    m = _m()
    assert m.price_deal({"price": 100}, {"volume": 2000}) < 100


def test_terms():
    m = _m()
    assert 0 <= m.terms_score({"payment_days": 15, "contract_months": 12, "auto_renew": True}) <= 1


def test_approval():
    m = _m()
    assert m.approval_required(5000, 10000) is False


def test_negotiate():
    m = _m()
    assert m.negotiate_round(100, 80, 2) == 90


def test_health():
    m = _m()
    assert 0 <= m.deal_health({"signed": True, "paid": True}) <= 1


def test_ecosystem_economics_real_values():
    eco = _eco()
    r = eco.economics_model(100, 10.0, 200.0, 2.0)
    assert r["ok"] is True and r["subsystem"] == "mem20businessmodelsimulatorz"
    assert "margin" in r and "profit" in r and r["scenario_periods"] >= 1


def test_ecosystem_demand_signal_real_values():
    eco = _eco()
    r = eco.demand_signal([10, 12, 11, 13, 14])
    assert r["ok"] is True and r["subsystem"] == "mem20demandforecastandcapacitybrainz"
    assert r["point"] is not None and r["n"] >= 3


def test_ecosystem_partnership_fit_real_values():
    eco = _eco()
    r = eco.partnership_fit({"id": "us"}, {"id": "them"})
    assert r["ok"] is True and r["subsystem"] == "mem20acquisitionandpartnershipscoutz"
    assert "strategic_fit" in r and r["ranked_count"] >= 1


def test_ecosystem_approval_guardrail_real_values():
    eco = _eco()
    r = eco.approval_guardrail(1.0, {"deal": "ok"}, progress_evidence=True)
    assert r["ok"] is True and r["subsystem"] == "mem20antiexploitationrewardshieldz"
    assert "paid" in r and "exploit_ratio" in r


def test_ecosystem_capability_routing_real_values():
    eco = _eco()
    r = eco.capability_routing("deal-1", ["pricing", "legal"])
    assert r["ok"] is True and r["subsystem"] == "mem20capabilitymarketplacez"
    assert r["owner"] in ("pricing", "legal") and r["capabilities"] == 2


def test_ecosystem_pipeline_context_real_values():
    eco = _eco()
    r = eco.pipeline_context([{"deal_value": 5000, "budget": 3000, "authority": True, "need": True, "timeline_days": 20, "touches": 2}])
    assert r["ok"] is True and r["subsystem"] == "mem20autonomoussaleslaboratoryz"
    assert r["pipeline_value"] >= 0 and "segments" in r


def test_deal_report_and_probe_real_integrations():
    m = _m()
    report = m.deal_report(product={"price": 1200}, customer={"volume": 400}, deal={"signed": True, "paid": False, "deal_value": 1100})
    assert report["price"] > 0 and report["terms_score"] >= 0
    peers = report["peers"]
    assert len(peers) == 6
    for k in ("economics_model","demand_signal","partnership_fit","approval_guardrail","capability_routing","pipeline_context"):
        assert peers[k]["ok"] is True, (k, peers[k].get("error"))
    p = m.probe()
    assert p["ok"] is True and len(p["checks"]) == 6
    ctx = m.estate_context()
    assert ctx["engine_status_checked"] is True and ctx["peer_count"] == 6
