"""LoRA RAG content generator: retrieve + generate with LoRA adapter."""
import math


def retrieve(docs, query, k=3):
    # simple keyword overlap
    qwords = set(query.lower().split())
    scored = []
    for d in docs:
        dw = set(d.get("text", "").lower().split())
        score = len(qwords & dw)
        scored.append((score, d))
    scored.sort(reverse=True)
    return [d for _, d in scored[:k]]


def generate(context_docs, prompt, adapter="default"):
    ctx = " ".join(d.get("text", "") for d in context_docs)
    return {"prompt": prompt, "context": ctx[:500], "adapter": adapter, "output": f"[{adapter}] {prompt} (ctx={len(ctx)} chars)"}


def rank_adapters(adapters, task):
    return sorted(adapters, key=lambda a: -a.get("score", 0))


def quality_score(output, reference):
    # token overlap
    ow = set(output.lower().split())
    rw = set(reference.lower().split())
    if not rw:
        return 0.0
    return round(len(ow & rw) / len(rw), 4)
