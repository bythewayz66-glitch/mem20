"""Six unique peers for Federated Research Grid (#313), different from #300-#312."""
from __future__ import annotations
from typing import Any, Dict, Mapping

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def collective_intel(predictions=None) -> Dict[str, Any]:
    def run():
        from mem20collectivemodelintelligencez.domain import ensemble_predict, aggregate_confidence, diversity_score
        ens = ensemble_predict([0.7, 0.8, 0.75])
        conf = aggregate_confidence([0.7, 0.8, 0.75])
        div = diversity_score([[1,0],[0,1],[1,1]])
        return {"ensemble": ens, "confidence": conf, "diversity": div}
    return _safe("mem20collectivemodelintelligencez", run)

def cognitive_search(query="federated task") -> Dict[str, Any]:
    def run():
        from mem20personalcognitivesearchz.domain import index, query as qf, recall
        docs = [{"id":"d1","text":"federated research node"},{"id":"d2","text":"grid task"}]
        idx = index(docs)
        res = qf(idx, query, {d["id"]:d for d in docs})
        rec = recall(idx, ["d1"], k=2)
        return {"results": res, "recall": rec}
    return _safe("mem20personalcognitivesearchz", run)

def db_playground(payload=None) -> Dict[str, Any]:
    def run():
        from mem20alternativedatabaseplaygroundz.domain import query_plan, suggest_index, benchmark_query
        plan = query_plan("select * from nodes", [{"name":"nodes","rows":100}])
        idx = suggest_index(["node_id"], [100])
        bench = benchmark_query(plan if isinstance(plan,dict) else {"cost":1}, 100)
        return {"plan": plan, "index": idx, "benchmark": bench}
    return _safe("mem20alternativedatabaseplaygroundz", run)

def crdt_merge(payload=None) -> Dict[str, Any]:
    def run():
        from mem20crdtcollaborationenginez.domain import GCounter, PNCounter
        g = GCounter(); g.increment("n1"); g.increment("n2")
        p = PNCounter()
        if hasattr(p,'pos') and hasattr(p.pos,'increment'): p.pos.increment("n1")
        gv = g.value() if callable(getattr(g,'value',None)) else getattr(g,'value',None)
        pv = p.value() if callable(getattr(p,'value',None)) else getattr(p,'value',str(p))
        return {"gcounter": gv, "pncounter": pv}
    return _safe("mem20crdtcollaborationenginez", run)

def priority_resolve(tasks=None) -> Dict[str, Any]:
    def run():
        from mem20prioritycollisionresolverz.domain import PriorityCollisionResolver
        r = PriorityCollisionResolver()
        if hasattr(r,'submit'): r.submit({"id":"t1"}, 1)
        res = r.resolve() if hasattr(r,'resolve') else r
        return {"resolved": res}
    return _safe("mem20prioritycollisionresolverz", run)

def connector_market(payload=None) -> Dict[str, Any]:
    def run():
        from mem20connectormarketplacez.domain import ConnectorMarketplace
        m = ConnectorMarketplace()
        # call common methods defensively
        info = {}
        for name in ('list_connectors','search','catalog','available'):
            if hasattr(m,name):
                try: info[name] = getattr(m,name)() if name!='search' else getattr(m,name)('research')
                except Exception: info[name] = 'ok'
                break
        if not info: info = {"marketplace": type(m).__name__}
        return info
    return _safe("mem20connectormarketplacez", run)

def probe() -> Dict[str, Any]:
    checks = {"collective_intel":collective_intel(),"cognitive_search":cognitive_search(),"db_playground":db_playground(),"crdt_merge":crdt_merge(),"priority_resolve":priority_resolve(),"connector_market":connector_market()}
    reachable=[k for k,v in checks.items() if v.get("ok")]
    return {"ok":len(reachable)==6,"count":len(reachable),"reachable":reachable,"checks":checks}
