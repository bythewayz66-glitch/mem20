import importlib
MOD="mem20versioncontrollargeassetandrecoverypipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_ver(): m=_m(); r=m.version_asset("a1","content"); assert "version" in r
def test_diff(): m=_m(); v1=m.version_asset("a1","c1"); v2=m.version_asset("a1","c2"); r=m.diff_versions(v1,v2); assert r["changed"] is True
def test_rec(): m=_m(); v=m.version_asset("a1","c1"); r=m.recover([v], v["version"]); assert r is not None
def test_health(): m=_m(); v=m.version_asset("a1","c1"); r=m.vc_health([v]); assert r["versions"]==1
