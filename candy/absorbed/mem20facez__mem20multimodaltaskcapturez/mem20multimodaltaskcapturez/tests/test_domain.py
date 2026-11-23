import importlib
MOD="mem20multimodaltaskcapturez"
def _m(): return importlib.import_module(MOD+".domain")
def test_capture(): m=_m(); r=m.capture(text="do x"); assert "text" in r["modalities"]
def test_merge(): m=_m(); a=m.capture(text="a"); b=m.capture(text="b"); r=m.merge_captures([a,b]); assert len(r["parts"])==2
def test_extract(): m=_m(); r=m.capture(text="Fix bug. Add test."); items=m.extract_action_items(r); assert len(items)==2
def test_health(): m=_m(); r=m.capture_health([m.capture(text="a")]); assert r["total"]==1

from mem20multimodaltaskcapturez import ecosystem
def _assert_signal(sig):
 assert isinstance(sig,dict) and "subsystem" in sig and "ok" in sig
 if not sig["ok"]: assert "error" in sig
def test_ingest_capture():
 m=_m(); r=m.ingest_capture({"text":"build api. test api","source":"chat"})
 assert r["ok"] and r["structured"]["executable"] and len(r["structured"]["action_items"])>=1
def test_ecosystem():
 c={"text":"build api","modality":"text"}; _assert_signal(ecosystem.modality_bridge_signal(c)); _assert_signal(ecosystem.sensory_ingest_signal(c)); _assert_signal(ecosystem.intent_compile_signal(c)); _assert_signal(ecosystem.task_capture_personal_signal(c)); _assert_signal(ecosystem.output_compile_signal(c)); _assert_signal(ecosystem.episodic_signal(c))
 r=ecosystem.capture_signals(c); assert set(r["checks"].keys())=={"modality_bridge","sensory_ingest","intent_compile","task_capture_personal","output_compile","episodic"}
 for v in r["checks"].values(): _assert_signal(v)
