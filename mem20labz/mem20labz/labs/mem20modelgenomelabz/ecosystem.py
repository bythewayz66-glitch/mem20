"""6 unique peers for Model Genome Lab (#335). Set differs from #330-334."""
from __future__ import annotations
from typing import Any, Callable, Dict, Mapping

def _safe(name: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    try:
        res = fn(); out={"ok":True,"subsystem":name}
        if isinstance(res,dict): out.update(res)
        else: out["result"]=res
        return out
    except Exception as e: return {"ok":False,"subsystem":name,"error":f"{type(e).__name__}: {e}"}

def runtime_compat_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try: from mem20runtimecompatibilityenginez.domain import check_python, compatibility_report
        except Exception: from mem20runtimecompatibilityenginez.mem20runtimecompatibilityenginez.domain import check_python, compatibility_report
        py=check_python((3,11)); rep=compatibility_report({"python":"3.11"}, {"python_min":"3.11"})
        return {"python_check":py,"report":rep}
    return _safe("mem20runtimecompatibilityenginez", run)

def cost_opt_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try: from mem20pipez.domain import stage_cost, pipeline_cost
        except Exception: from mem20pipez.mem20pipez.domain import stage_cost, pipeline_cost
        sc=stage_cost({"name":"genome-eval","cost_per_unit":0.01}, throughput=10); pc=pipeline_cost([{"name":"g","cost_per_unit":0.01}], throughput=10)
        return {"stage_cost":sc,"pipeline_cost":pc}
    return _safe("mem20pipez", run)

def kernel_opt_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try: from mem20selfoptimizingkernelz.domain import optimize, score
        except Exception: from mem20selfoptimizingkernelz.mem20selfoptimizingkernelz.domain import optimize, score
        opt=optimize({"lr":0.1}, {"loss":1.0}, lr=0.1); sc=score({"lr":0.1}, {"target":1.0})
        return {"optimized":opt,"score":sc}
    return _safe("mem20selfoptimizingkernelz", run)

def counterfactual_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try: from mem20simz.domain import counterfactual, compare
        except Exception: from mem20simz.mem20simz.domain import counterfactual, compare
        cf=counterfactual({"genome":"a"},{"genome":"b"}); cmp=compare({"fitness":0.5},{"fitness":0.8})
        return {"counterfactual":cf,"compare":cmp}
    return _safe("mem20simz", run)

def execution_twin_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try: from mem20twinz.domain import create_twin, simulate
        except Exception: from mem20twinz.mem20twinz.domain import create_twin, simulate
        t=create_twin({"id":"genome-twin","workload":"evolution"}); s=simulate(t,[{"event":"evolve"}])
        return {"twin":(t.get("id") if isinstance(t,dict) else "t"),"simulated":s is not None}
    return _safe("mem20twinz", run)

def eventstream_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try: from mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
        except Exception: from mem20eventstreamsuperhighwayz.mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
        s=create_stream("genome-lab"); publish(s,"evolution",{"ok":True},key="g"); th=throughput(s,window_s=60)
        return {"stream":(s.get("name") if isinstance(s,dict) else "genome-lab"),"throughput":th}
    return _safe("mem20eventstreamsuperhighwayz", run)

def genome_signals(ctx: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    c=dict(ctx or {"model":"probe"})
    checks={"runtime_compat":runtime_compat_signal(c),"cost_opt":cost_opt_signal(c),"kernel_opt":kernel_opt_signal(c),"counterfactual":counterfactual_signal(c),"execution_twin":execution_twin_signal(c),"eventstream":eventstream_signal(c)}
    reachable=[k for k,v in checks.items() if v.get("ok")]
    return {"ok":len(reachable)==6,"count":len(reachable),"reachable":reachable,"checks":checks}

def probe()->Dict[str,Any]: return genome_signals()
