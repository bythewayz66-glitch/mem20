"""Context compression forge: summarize, compress, retain key info, with estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["compress","extractive_summary","compression_ratio","key_terms","forge_context","compression_report","probe","estate_context"]

def compress(text, ratio=0.5):
    words = text.split(); keep = max(1, int(len(words) * ratio))
    if keep >= len(words): return text
    head = words[:keep // 2]; tail = words[-(keep - len(head)):]
    return " ".join(head + ["..."] + tail)

def extractive_summary(text, n_sentences=3):
    sents = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sents) <= n_sentences: return sents
    scored = sorted(enumerate(sents), key=lambda x: -len(x[1]))[:n_sentences]; scored.sort(key=lambda x: x[0])
    return [s for _, s in scored]

def compression_ratio(original, compressed):
    if not original: return 0.0
    return round(len(compressed) / len(original), 4)

def key_terms(text, top=5):
    from collections import Counter
    words = [w.lower().strip(".,!?") for w in text.split()]; c = Counter(w for w in words if len(w) > 3)
    return [w for w, _ in c.most_common(top)]

def forge_context(chunks, max_tokens=1000):
    out=[]; used=0
    for ch in chunks:
        if used + len(ch) > max_tokens: break
        out.append(ch); used += len(ch)
    return {"chunks": out, "used_tokens": used, "remaining": max_tokens - used}

def compression_report(text=None, ratio=0.5, max_tokens=200):
    text = text or "This is a long context that should be compressed while retaining the most important terms and meaning for downstream use."
    comp = compress(text, ratio); summ = extractive_summary(text, 2); keys = key_terms(text, 5); cr = compression_ratio(text, comp)
    forged = forge_context([text, comp], max_tokens=max_tokens)
    peers={
        "stream_compressed": ecosystem.stream_compressed("compression.report", {"ratio":cr,"keys":len(keys)}),
        "summary_quality": ecosystem.summary_quality("summarize: "+text[:80]),
        "focus_retention": ecosystem.focus_retention({"priority":1,"distractions":0,"relevance":0.8}),
        "strategy_routing": ecosystem.strategy_routing("compress-1", ["extractive","abstractive"]),
        "budget_forecast": ecosystem.budget_forecast([len(text), len(comp), max_tokens]),
        "keep_routing": ecosystem.keep_routing({"relevance":0.8,"length":len(text)/100.0},{"relevance":1.0,"length":-0.1}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"compression_ratio":cr,"key_terms":keys,"summary_count":len(summ),"forged":forged,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=compression_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
