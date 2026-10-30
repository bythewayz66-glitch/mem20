import importlib
MOD="mem20narrativedialogueandlocalizationpipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_parse(): m=_m(); r=m.parse_dialogue("Alice: hi\nBob: hello"); assert len(r)==2
def test_loc(): m=_m(); d=m.parse_dialogue("Alice: hi"); r=m.localize(d,"fr",{"fr":{"hi":"salut"}}); assert r[0]["text"]=="salut"
def test_validate(): m=_m(); r=m.validate_dialogue([{"speaker":"a","text":"hi"}]); assert r["valid"] is True
def test_wc(): m=_m(); d=m.parse_dialogue("Alice: hi there"); assert m.word_count(d)==2
def test_export(): m=_m(); d=m.parse_dialogue("Alice: hi"); r=m.export_script(d); assert "Alice: hi" in r
