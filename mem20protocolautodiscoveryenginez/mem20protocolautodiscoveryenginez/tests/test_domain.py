import importlib
MOD="mem20protocolautodiscoveryenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_detect(): m=_m(); assert m.detect_protocol("GET / HTTP/1.1")=="http"
def test_headers(): m=_m(); r=m.parse_headers("Host: x\nAccept: y"); assert r["Host"]=="x"
def test_reg(): m=_m(); r=m.register_protocol({}, "http", "h"); assert "http" in r["protocols"]
def test_list(): m=_m(); r=m.register_protocol({}, "http", "h"); assert "http" in m.list_protocols(r)
def test_health(): m=_m(); r=m.register_protocol({}, "http", "h"); assert m.protocol_health(r)["protocols"]==1
