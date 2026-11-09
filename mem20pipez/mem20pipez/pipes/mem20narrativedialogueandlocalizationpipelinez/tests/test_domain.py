import importlib
MOD="mem20pipez"
def _m(): return importlib.import_module(MOD+".domain")
def test_parse(): m=_m(); r=m.parse_dialogue("Alice: hi\nBob: hello"); assert len(r)==2
def test_loc(): m=_m(); d=m.parse_dialogue("Alice: hi"); r=m.localize(d,"fr",{"fr":{"hi":"salut"}}); assert r[0]["text"]=="salut"
def test_validate(): m=_m(); r=m.validate_dialogue([{"speaker":"a","text":"hi"}]); assert r["valid"] is True
def test_wc(): m=_m(); d=m.parse_dialogue("Alice: hi there"); assert m.word_count(d)==2
def test_export(): m=_m(); d=m.parse_dialogue("Alice: hi"); r=m.export_script(d); assert "Alice: hi" in r

from mem20pipez import ecosystem
def _assert_signal(sig):
 assert isinstance(sig,dict) and "subsystem" in sig and "ok" in sig
 if not sig["ok"]: assert "error" in sig
def test_narrative_graph():
 m=_m(); r=m.export_narrative({"text":"NPC: Hi\nHERO: Go","target_languages":["en","es"]})
 assert "graph" in r and "nodes" in r["graph"] and "localizations" in r and "export" in r
def test_ecosystem():
 c={"text":"NPC: Hi","target_lang":"es"}; _assert_signal(ecosystem.level_world_signal(c)); _assert_signal(ecosystem.dynamic_narrative_signal(c)); _assert_signal(ecosystem.lore_content_signal(c)); _assert_signal(ecosystem.context_compression_signal(c)); _assert_signal(ecosystem.episodic_signal(c)); _assert_signal(ecosystem.eventstream_signal(c))
 r=ecosystem.narrative_signals(c); assert set(r["checks"].keys())=={"level_world","dynamic_narrative","lore_content","context_compression","episodic","eventstream"}
 for v in r["checks"].values(): _assert_signal(v)
