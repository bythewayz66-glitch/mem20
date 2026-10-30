import importlib
MOD="mem20sensorymemoryingestz"
def _m(): return importlib.import_module(MOD+".domain")
def test_ingest(): m=_m(); r=m.ingest({"entries":[]},"hi","text"); assert r["modality"]=="text"
def test_filter(): m=_m(); s={"entries":[]}; m.ingest(s,"hi","text"); m.ingest(s,"img","image"); r=m.filter_by_modality(s,"text"); assert len(r)==1
def test_recent(): m=_m(); s={"entries":[]}; m.ingest(s,"a","text"); r=m.recent(s,5); assert len(r)==1
def test_health(): m=_m(); s={"entries":[]}; m.ingest(s,"a","text"); r=m.ingest_health(s); assert r["entries"]==1
