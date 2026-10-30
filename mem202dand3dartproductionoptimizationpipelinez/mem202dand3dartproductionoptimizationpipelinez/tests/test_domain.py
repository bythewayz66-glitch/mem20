import importlib
MOD="mem202dand3dartproductionoptimizationpipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_lod(): 
    m=_m(); assert m.lod_level(50000)>=1
def test_texture():
    m=_m(); assert m.texture_memory(512,512)>0
def test_batch():
    m=_m(); r=m.batch_efficiency(100); assert r["batches"]==2
def test_optimize():
    m=_m(); r=m.optimize_pipeline([{"id":"a","polys":1000,"tex_w":256,"tex_h":256}]); assert r["assets"][0]["lod"]==0
def test_frame_budget():
    m=_m(); assert m.frame_budget(60)>16
