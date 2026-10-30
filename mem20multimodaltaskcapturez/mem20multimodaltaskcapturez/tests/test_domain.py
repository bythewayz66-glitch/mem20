import importlib
MOD="mem20multimodaltaskcapturez"
def _m(): return importlib.import_module(MOD+".domain")
def test_capture(): m=_m(); r=m.capture(text="do x"); assert "text" in r["modalities"]
def test_merge(): m=_m(); a=m.capture(text="a"); b=m.capture(text="b"); r=m.merge_captures([a,b]); assert len(r["parts"])==2
def test_extract(): m=_m(); r=m.capture(text="Fix bug. Add test."); items=m.extract_action_items(r); assert len(items)==2
def test_health(): m=_m(); r=m.capture_health([m.capture(text="a")]); assert r["total"]==1
