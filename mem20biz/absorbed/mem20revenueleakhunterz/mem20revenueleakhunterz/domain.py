"""Revenue leak hunter: detect billing leaks, anomalies, with estate report."""
from __future__ import annotations
import statistics
from . import ecosystem
__all__=["detect_leaks","anomaly_score","recoverable","hunter_health","leak_report","probe","estate_context"]

def detect_leaks(transactions, expected):
    leaks=[]
    for t in transactions:
        exp=expected.get(t.get("id"))
        if exp is not None and t.get("amount") != exp:
            leaks.append({"id": t.get("id"), "actual": t.get("amount"), "expected": exp, "delta": t.get("amount",0)-exp})
    return leaks

def anomaly_score(values):
    if len(values) < 2: return 0.0
    m=statistics.mean(values); sd=statistics.pstdev(values) or 1
    return round(max(abs((v-m)/sd) for v in values), 4)

def recoverable(leaks):
    return round(sum(abs(l["delta"]) for l in leaks), 4)

def hunter_health(leaks):
    return {"leaks": len(leaks), "recoverable": recoverable(leaks)}

def leak_report():
    tx=[{"id":"a","amount":90},{"id":"b","amount":100},{"id":"c","amount":70}]
    expected={"a":100,"b":100,"c":100}
    leaks=detect_leaks(tx,expected); anom=anomaly_score([90,100,70]); rec=recoverable(leaks)
    peers={
        "revenue_economics": ecosystem.revenue_economics(270, 300-rec),
        "deal_pricing": ecosystem.deal_pricing(rec if rec else 10),
        "leak_events": ecosystem.leak_events("leak.detected", {"leaks":len(leaks),"recoverable":rec}),
        "leak_containment": ecosystem.leak_containment("a"),
        "causal_analysis": ecosystem.causal_analysis({"delta":rec},{"delta":1}),
        "hunter_routing": ecosystem.hunter_routing("leaks", ["detect","anomaly","recover"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(leaks)>0,"leaks":len(leaks),"recoverable":rec,"anomaly_score":anom,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=leak_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
