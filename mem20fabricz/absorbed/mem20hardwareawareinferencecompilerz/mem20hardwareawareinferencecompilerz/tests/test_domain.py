import importlib
MOD="mem20hardwareawareinferencecompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_fuse(): m=_m(); r=m.fuse_ops([{"type":"matmul"},{"type":"relu"}]); assert r[0]["type"]=="fused_matmul_relu"
def test_quant(): m=_m(); r=m.quantize([0.0,0.5,1.0],4); assert "quantized" in r
def test_sched(): m=_m(); r=m.schedule([{"priority":1},{"priority":3}],{}); assert r[0]["priority"]==3
def test_mem(): m=_m(); assert m.memory_estimate([{"size":10}],4)==40
def test_opt(): m=_m(); r=m.optimize_graph({"nodes":[{"type":"identity"},{"type":"matmul"}]}); assert r["removed"]==1
