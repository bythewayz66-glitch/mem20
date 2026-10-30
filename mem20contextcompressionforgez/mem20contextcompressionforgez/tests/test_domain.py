import importlib
MOD="mem20contextcompressionforgez"
def _m(): return importlib.import_module(MOD+".domain")
def test_compress(): m=_m(); r=m.compress("a b c d e f g h",0.5); assert "..." in r
def test_summary(): m=_m(); r=m.extractive_summary("First. Second. Third. Fourth.",2); assert len(r)==2
def test_ratio(): m=_m(); assert 0<=m.compression_ratio("hello world","hi")<=1
def test_terms(): m=_m(); r=m.key_terms("the quick brown fox jumps"); assert isinstance(r,list)
def test_forge(): m=_m(); r=m.forge_context(["abc","def"],10); assert "chunks" in r
