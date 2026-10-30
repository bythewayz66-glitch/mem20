import importlib
MOD="mem20autonomousdealdeskz"
def _m(): return importlib.import_module(MOD+".domain")
def test_price(): m=_m(); assert m.price_deal({"price":100},{"volume":2000})<100
def test_terms(): m=_m(); assert 0<=m.terms_score({"payment_days":15,"contract_months":12,"auto_renew":True})<=1
def test_approval(): m=_m(); assert m.approval_required(5000,10000) is False
def test_negotiate(): m=_m(); assert m.negotiate_round(100,80,2)==90
def test_health(): m=_m(); assert 0<=m.deal_health({"signed":True,"paid":True})<=1
