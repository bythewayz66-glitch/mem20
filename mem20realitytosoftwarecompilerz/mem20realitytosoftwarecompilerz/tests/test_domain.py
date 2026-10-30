import importlib
MOD="mem20realitytosoftwarecompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_ingest(): m=_m(); r=m.ingest("name: app\nlang: py"); assert r["name"]=="app"
def test_compile(): m=_m(); r=m.compile_to_code({"name":"app"},"python"); assert "class App" in r
def test_validate(): m=_m(); r=m.validate_spec({"name":"app"}); assert r["valid"] is True
def test_diff(): m=_m(); r=m.diff_spec({"a":1},{"a":2}); assert "a" in r
def test_health(): m=_m(); r=m.compile_health({"name":"app"}); assert r["valid"] is True
