"""6 unique peers for Modality Bridge (#334). Different set from #330-333."""
from __future__ import annotations
from typing import Any, Callable, Dict, Mapping

def _safe(name: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    try:
        res = fn()
        out = {"ok": True, "subsystem": name}
        if isinstance(res, dict): out.update(res)
        else: out["result"] = res
        return out
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def sensory_ingest_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20sensorymemoryingestz.domain import ingest, recent, ingest_health
        except Exception:
            from mem20sensorymemoryingestz.mem20sensorymemoryingestz.domain import ingest, recent, ingest_health
        stream = {"events": []}
        ingest(stream, {"text": ctx.get("payload") or "modality probe"}, modality=str(ctx.get("from") or "text"))
        rec = recent(stream, n=1)
        h = ingest_health(stream)
        return {"recent": rec, "health": h}
    return _safe("mem20sensorymemoryingestz", run)

def specialist_forge_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20rewardforgez.domain import forge, evaluate
        except Exception:
            from mem20rewardforgez.mem20rewardforgez.domain import forge, evaluate
        model = forge({"id": "base"}, specialty=str(ctx.get("to") or "multimodal"), data=[{"x": 1}])
        ev = evaluate(model, [{"x": 1}])
        return {"model": model, "evaluation": ev}
    return _safe("mem20rewardforgez", run)

def predictive_recall_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20predictiverecallenginez.domain import predict_next, recall_score
        except Exception:
            from mem20predictiverecallenginez.mem20predictiverecallenginez.domain import predict_next, recall_score
        preds = predict_next([str(ctx.get("from") or "text")], [str(ctx.get("to") or "image"), "audio", "video"])
        score = recall_score({"item": ctx.get("to", "image")}, {"modality": ctx.get("from", "text")})
        return {"predictions": preds, "score": score}
    return _safe("mem20predictiverecallenginez", run)

def output_compile_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20agentoutputcompilerz.domain import merge_outputs, validate_output
        except Exception:
            from mem20agentoutputcompilerz.mem20agentoutputcompilerz.domain import merge_outputs, validate_output
        outs = [{"modality": ctx.get("from","text"), "ok": True}, {"modality": ctx.get("to","image"), "ok": True}]
        merged = merge_outputs(outs)
        valid = validate_output(outs[0] if outs else {"ok": True})
        return {"merged": merged, "valid": valid}
    return _safe("mem20agentoutputcompilerz", run)

def compression_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20rewardforgez.domain import extractive_summary, key_terms, compression_ratio
        except Exception:
            from mem20rewardforgez.mem20rewardforgez.domain import extractive_summary, key_terms, compression_ratio
        text = str(ctx.get("payload") or f"bridge {ctx.get('from','text')} to {ctx.get('to','image')} representation")
        summary = extractive_summary(text, n_sentences=1)
        terms = key_terms(text, top=3)
        ratio = compression_ratio(text, summary)
        return {"summary": summary, "key_terms": terms, "ratio": ratio}
    return _safe("mem20rewardforgez", run)

def episodic_signal(ctx: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20episodicmemorygraphz.domain import create_episode, add_event, recall
        except Exception:
            from mem20episodicmemorygraphz.mem20episodicmemorygraphz.domain import create_episode, add_event, recall
        ep = create_episode("modality-bridge", [{"type": "bridge", "from": ctx.get("from"), "to": ctx.get("to")}])
        add_event(ep, {"type": "translated", "ok": True})
        rec = recall([ep], str(ctx.get("to") or "image"))
        return {"episode_id": ep.get("id") if isinstance(ep, dict) else None, "recall_count": len(rec) if isinstance(rec, list) else 1}
    return _safe("mem20episodicmemorygraphz", run)

def modality_signals(ctx: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    c = dict(ctx or {"from":"text","to":"image","payload":"probe"})
    checks = {
        "sensory_ingest": sensory_ingest_signal(c),
        "specialist_forge": specialist_forge_signal(c),
        "predictive_recall": predictive_recall_signal(c),
        "output_compile": output_compile_signal(c),
        "compression": compression_signal(c),
        "episodic": episodic_signal(c),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}

def probe() -> Dict[str, Any]:
    return modality_signals()
