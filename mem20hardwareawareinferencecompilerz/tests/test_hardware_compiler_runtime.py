from pathlib import Path
from mem20hardwareawareinferencecompilerz.mem20hardwareawareinferencecompilerz import ecosystem
from mem20hardwareawareinferencecompilerz.mem20hardwareawareinferencecompilerz.runtime import Engine, load_config
from mem20hardwareawareinferencecompilerz.mem20hardwareawareinferencecompilerz.domain import fuse_ops, quantize, schedule, memory_estimate, optimize_graph

def test_legacy_domain_preserved_for_314():
    r=fuse_ops([{"type":"matmul"},{"type":"relu"}]); assert r[0]["type"]=="fused_matmul_relu"
    q=quantize([0.0,0.5,1.0],4); assert "quantized" in q
    s=schedule([{"priority":1},{"priority":3}],{}); assert s[0]["priority"]==3
    assert memory_estimate([{"size":10}],4)==40
    assert optimize_graph({"nodes":[{"type":"identity"},{"type":"matmul"}]})["removed"]==1

def test_meaningful_compile_report():
    r=ecosystem.compile_report({"ops":[{"type":"matmul","size":10},{"type":"relu","size":10}],"weights":[0.0,1.0],"device":{"id":"cpu"}})
    assert r["integration_health"]["ok"]==6 and "fused_ops" in r and "memory_estimate" in r

def test_engine_search_compile_and_generic(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"h.sqlite3"))
    out=eng.execute({"compile":True,"ops":[{"type":"matmul","size":10}],"weights":[0.0,1.0],"device":{"id":"cpu"}}, idem="c1", timeout_ms=30000)
    assert out["integration_health"]["ok"]==6 and "results" in out
    gen=eng.execute({"query":"matmul","documents":[{"op":"matmul"},{"op":"conv"}]}, idem="s1")
    assert "results" in gen

def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
