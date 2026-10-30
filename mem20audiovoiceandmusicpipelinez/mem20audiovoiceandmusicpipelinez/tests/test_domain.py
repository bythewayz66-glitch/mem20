import importlib
MOD="mem20audiovoiceandmusicpipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_mix(): m=_m(); r=m.mix_tracks([{"id":"a","samples":[1,2]}]); assert "tracks" in r
def test_normalize(): m=_m(); r=m.normalize([0.5,1.0],-3); assert len(r)==2
def test_sync(): m=_m(); r=m.sync_to_beat(10,120); assert r["beats"]>0
def test_export(): m=_m(); r=m.export_format([1,2], "wav"); assert r["format"]=="wav"
def test_master(): m=_m(); r=m.mastering_chain(["limit"],[1.5,-1.5]); assert all(abs(x)<=0.99 for x in r)
