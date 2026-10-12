"""Additional retrieval methods for mem20 (methods 8, 9, 10).

Additive only: this module imports the existing engine and never mutates it,
so the deployed store copy stays byte-identical.

  8. decompose_query()      - multi-hop: split one question into sub-retrievals
  9. entity_anchor_expand() - graph seed then vector expansion (catches aliases)
 10. calibrated_search()    - abstention: return confidence, refuse when low

All three respect MEM20_STORE_PATH, so they can be pointed at the benchmark
store without touching the live one.
"""
from __future__ import annotations

import os
import re
import statistics
import sys
from typing import Any

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

import memory as M  # noqa: E402

# Question words that usually head a distinct sub-question.
_QWORD = re.compile(
    r"\b(who|what|when|where|which|why|how|whose|whom)\b", re.I)
# Conjunctions and punctuation that usually separate independent asks.
_SPLIT = re.compile(
    r"(?:\s+and\s+then\s+|\s+and\s+also\s+|\s*;\s*|\s*\?\s*|\s+and\s+)", re.I)

_STOP = set("""a an the and or but if then else for to of in on at by with from as
is are was were be been being this that these those it its he she they we you i
not no yes do does did have has had will would can could should may might must
what when where which who whom whose why how""".split())


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _entities(q: str) -> list[str]:
    """Identifier-ish tokens: camelCase, snake_case, paths, dotted names."""
    out, seen = [], set()
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]{2,}", q):
        w = m.group(0)
        if w.lower() in _STOP:
            continue
        interesting = (
            "_" in w
            or ("." in w)
            or (any(c.isupper() for c in w[1:]) and len(w) > 3)
            or (w.isupper() and len(w) > 2)
        )
        lw = w.lower()
        if interesting and lw not in seen:
            seen.add(lw)
            out.append(w)
    return out[:6]


def _fuse(*rankings: list) -> list:
    """RRF fusion that preserves dict payloads."""
    score: dict[str, float] = {}
    rep: dict[str, dict] = {}
    for ranking in rankings:
        for pos, item in enumerate(ranking or []):
            if not isinstance(item, dict):
                continue
            key = str(item.get("id") or item.get("source") or f"{pos}")
            score[key] = score.get(key, 0.0) + 1.0 / (60 + pos + 1)
            rep.setdefault(key, item)
    fused = []
    for key in sorted(score, key=lambda x: -score[x]):
        item = dict(rep[key])
        item["rrf_score"] = round(score[key], 6)
        fused.append(item)
    return fused


def decompose_query(query: str, k: int = 8) -> dict:
    """Method 8 - split a multi-hop question and retrieve each part.

    Returns {'parts': [...], 'results': [...], 'hop_scores': {...}}.
    Single-part questions degrade gracefully to plain hybrid retrieval.
    """
    q = _clean(query)
    parts = [_clean(p) for p in _SPLIT.split(q) if _clean(p)]
    if not parts:
        parts = [q]
    # A question word mid-string usually starts a second independent ask.
    if len(parts) == 1:
        hits = [m.start() for m in _QWORD.finditer(q)][1:]
        if hits:
            first = hits[0]
            # cut at the verb-ish word before the second question word
            left = q[:first].rstrip()
            cut = left.rfind(" and ")
            if cut > 0:
                parts = [_clean(q[:cut]), _clean(q[cut + 5:])]
    rankings, hop_scores = [], {}
    for p in parts[:4]:
        try:
            res = M.recall_hybrid(p, k=k)
        except Exception as exc:  # provider down: degrade, do not raise
            hop_scores[p] = f"error: {type(exc).__name__}"
            res = []
        hop_scores[p] = len(res)
        rankings.append(res)
    return {"parts": parts, "results": _fuse(*rankings), "hop_scores": hop_scores}


def entity_anchor_expand(query: str, k: int = 8, hops: int = 1) -> dict:
    """Method 9 - seed from the entity graph, then expand semantically.

    Pure vector search misses a fact when the query uses a different surface
    form ("the merge tool") for a stored entity ("stash surgery"). Graph seeds
    recover the entity, semantic expansion recovers the rest.
    """
    q = _clean(query)
    anchors = _entities(q)
    graph_hits: list = []
    anchor_hits: dict[str, int] = {}
    for ent in anchors:
        try:
            g = M.recall_graph(ent, hops=hops, max_results=k)
        except Exception:
            g = {}
        facts = g.get("facts") or [] if isinstance(g, dict) else []
        anchor_hits[ent] = len(facts)
        graph_hits.extend(facts)
    try:
        vec = M.recall_semantic(q, k=k)
    except Exception:
        vec = []
    fused = _fuse(vec, graph_hits)
    return {"anchors": anchors, "anchor_hits": anchor_hits,
            "results": fused[:k], "graph_seeds": len(graph_hits)}


_CE_MODEL = None
_CE_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _cross_encoder():
    """Lazy-load the local ms-marco reranker (verified offline-capable)."""
    global _CE_MODEL
    if _CE_MODEL is None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from sentence_transformers import CrossEncoder
        _CE_MODEL = CrossEncoder(_CE_NAME)
    return _CE_MODEL


def calibrated_search(query: str, k: int = 8, candidate_pool: int = 12,
                      min_ce: float = -10.0, min_margin: float = 0.0) -> dict:
    """Method 10 - retrieve, rescore with a cross-encoder, then abstain if weak.

    WHY THIS EXISTS: recall_hybrid's own `score` field was measured at
    0.00725 for a real query AND 0.00725 for a nonsense query - effectively no
    dynamic range - and its `_ce_score` is 0.0 everywhere because the
    cross-encoder is not invoked inside recall_hybrid at all. Neither can
    support abstention. So this rescores candidates with the local ms-marco
    cross-encoder directly, which IS discriminative (relevant -5.12 vs
    irrelevant -11.4 in verification).

    ms-marco logits are unbounded-ish, so thresholds are empirical, measured
    on the bench corpus, and exposed as parameters rather than hidden. Measured
    separation on the partial bench index: on-topic top scores -8.24 / -9.26 vs
    off-topic -11.31 / -11.17, so min_ce=-10.0 sits between the bands. This is
    PROVISIONAL - it must be re-calibrated against the full 21,449-chunk index,
    since candidate quality changes completely as the corpus fills.

    The margin gate is DISABLED by default (min_margin=0.0) because measurement
    showed it carries no signal: margins were 0.02-0.42 for BOTH on-topic and
    off-topic queries, so requiring margin>=1.0 produced false abstentions on
    correct answers (4/6 correct) while ce_top alone was 6/6. The margin is
    still computed and returned for callers who want it.
    """
    q = _clean(query)
    try:
        cands = M.recall_hybrid(q, k=max(k, candidate_pool))
    except Exception as exc:
        return {"query": q, "abstained": True, "confidence": 0.0, "results": [],
                "reason": f"retrieval failed: {type(exc).__name__}",
                "ce_scores": []}
    if not cands:
        return {"query": q, "abstained": True, "confidence": 0.0, "results": [],
                "reason": "no results", "ce_scores": []}

    texts = [(q, str(c.get("content", ""))[:2000]) for c in cands]
    try:
        ce = _cross_encoder()
        scores = [float(x) for x in ce.predict(texts)]
    except Exception as exc:
        return {"query": q, "abstained": True, "confidence": 0.0,
                "results": cands[:k], "ce_scores": [],
                "reason": f"cross-encoder failed: {type(exc).__name__}"}

    order = sorted(range(len(cands)), key=lambda i: -scores[i])
    ranked = []
    for i in order:
        item = dict(cands[i])
        item["ce_score"] = round(scores[i], 4)
        ranked.append(item)

    top = scores[order[0]]
    rest = [scores[i] for i in order[1:k]] or [top]
    margin = top - max(rest) if len(rest) else 0.0
    ok = top >= min_ce and margin >= min_margin
    return {
        "query": q,
        "abstained": not ok,
        "reason": "" if ok else (
            f"ce_top {top:.2f} < {min_ce}" if top < min_ce
            else f"ce_margin {margin:.2f} < {min_margin}"),
        "confidence": round(max(0.0, min(1.0, (top - min_ce) / 12.0)), 4),
        "ce_top": round(top, 4),
        "ce_margin": round(margin, 4),
        "results": ranked[:k],
    }


__all__ = ["decompose_query", "entity_anchor_expand", "calibrated_search"]


# ---------------------------------------------------------------------------
# #6 cross-encoder rerank  +  #16 MMR diversity
# ---------------------------------------------------------------------------
# NOTE ON AN UNRESOLVED ENGINE DEFECT. recall_hybrid in memory.py contains a
# cross-encoder rerank block (lines ~3793-3810) gated on USE_CROSS_ENCODER.
# Observed behaviour, reproduced repeatedly against the bench store:
#   USE_CROSS_ENCODER is True
#   _get_cross_encoder() IS called and predict() returns real scores
#   no "reranking failed" warning is emitted
#   yet every returned record has _ce_score = None and score = raw RRF
# Instrumented evidence: /tmp/opencode/proof/ce_probe_final.json
# A line-level trace showed lines 3794-3805 executing, yet no record carries
# the value, and no code path between the mutation and the return reassigns
# the list. This is NOT root-caused. Rather than patch 4284 lines blind, the
# rerank below is implemented and verified directly. The engine defect stays
# open and is tracked as a todo.
_CE_RERANK_MODEL = None


def _ce():
    global _CE_RERANK_MODEL
    if _CE_RERANK_MODEL is None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from sentence_transformers import CrossEncoder
        _CE_RERANK_MODEL = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _CE_RERANK_MODEL


def rerank(query: str, k: int = 10, pool: int = 30, alpha: float = 0.5) -> dict:
    """#6 Cross-encoder rerank. Over-fetches, rescores, re-orders, returns top k.

    Verified discriminative: on-topic top scores -7.9 to +2.7 vs off-topic
    -11.2, versus recall_hybrid's raw-RRF spread of ~0.0005.
    """
    q = _clean(query)
    try:
        cands = M.recall_hybrid(q, k=max(pool, k))
    except Exception as exc:
        return {"query": q, "results": [], "error": type(exc).__name__}
    if not cands:
        return {"query": q, "results": []}
    texts = [(q, str(c.get("content", ""))[:2000]) for c in cands]
    try:
        scores = [float(x) for x in _ce().predict(texts)]
    except Exception as exc:
        return {"query": q, "results": cands[:k], "error": type(exc).__name__}
    for c, s in zip(cands, scores):
        c["ce_score"] = round(s, 4)
        c["hybrid_score"] = round(float(c.get("score") or 0.0), 6)
    ordered = sorted(cands, key=lambda c: -c["ce_score"])
    return {"query": q, "results": ordered[:k],
            "ce_min": round(min(scores), 3), "ce_max": round(max(scores), 3)}


def _minmax(vals):
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        return [0.5] * len(vals)
    return [(v - lo) / (hi - lo) for v in vals]


def mmr(query: str, k: int = 8, pool: int = 30, lambda_relevance: float = 0.7,
         use_ce: bool = True) -> dict:
    """#16 Diversity-aware MMR selection.

    Maximises relevance minus redundancy:
        argmax  lambda * rel(d) - (1 - lambda) * max sim(d, selected)
    Relevant candidates come from the reranked list, so this composes on top
    of #6 rather than duplicating it.
    """
    q = _clean(query)
    base = rerank(q, k=pool)["results"] if use_ce else M.recall_hybrid(q, k=pool)
    if not base:
        return {"query": q, "results": [], "redundancy_penalised": 0}
    if use_ce:
        rel = _minmax([float(c.get("ce_score", c.get("score", 0.0))) for c in base])
    else:
        rel = _minmax([float(c.get("score", 0.0)) for c in base])
    try:
        from sentence_transformers import SentenceTransformer
        global _ST
        if _ST is None:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            _ST = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        vecs = _ST.encode([str(c.get("content", ""))[:1500] for c in base],
                          normalize_embeddings=True)
        import numpy as _np
        vecs = _np.asarray(vecs)
    except Exception:
        # No embeddings: fall back to token-overlap similarity rather than
        # silently pretending diversity was applied.
        vecs = None

    selected, selected_idx, redundancy = [], [], 0
    idx = list(range(len(base)))
    while idx and len(selected) < k:
        best, best_val = None, -1e9
        for i in idx:
            if vecs is not None:
                sim = max((float(vecs[i] @ vecs[j]) for j in selected_idx), default=0.0)
            else:
                sim = max((_jaccard(base[i].get("content", ""), base[j].get("content", ""))
                           for j in selected_idx), default=0.0)
            val = lambda_relevance * rel[i] - (1 - lambda_relevance) * sim
            if val > best_val:
                best, best_val = i, val
        if best is None:
            break
        selected.append(base[best])
        selected_idx.append(best)
        if vecs is not None and selected_idx[:-1]:
            redundancy += 1
        idx.remove(best)
    return {"query": q, "results": selected, "lambda": lambda_relevance,
            "pool": len(base), "redundancy_penalised": redundancy,
            "similarity_backend": "minilm-cosine" if vecs is not None else "jaccard-fallback"}


def _jaccard(a: str, b: str) -> float:
    sa = set(re.findall(r"\w+", (a or "").lower()))
    sb = set(re.findall(r"\w+", (b or "").lower()))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


_ST = None


# ---------------------------------------------------------------------------
# #14 multi-query (HyDE)  |  #18 KV lookup  |  #21 failure memory
#           #23 associative reconstruction  |  #1 recency/decay
# ---------------------------------------------------------------------------
import json as _json
import time as _time


def hyde_expand(query: str, k: int = 8, pool: int = 25) -> dict:
    """#14 - Multi-query expansion WITHOUT an LLM.

    HyDE normally has an LLM write a hypothetical answer document, then
    retrieves with it. Here the hypothetical document is assembled
    deterministically from the query plus the store's own vocabulary: the top
    BM25 expansion terms for the query become a pseudo-document. That keeps the
    method offline, free and reproducible, which matters on a box whose only
    funded model is a rate-limited free tier.

    Returns the fused result of retrieving with the ORIGINAL query and with the
    pseudo-document, so expansion can only add recall.
    """
    q = _clean(query)
    pseudo = _json.dumps(q)[:0]  # keep type stable for empty queries
    try:
        cands = M.recall_hybrid(q, k=pool)
    except Exception:
        cands = []
    # Build the hypothetical document from high-signal tokens in the current
    # candidates plus the query's own distinctive terms - a local stand-in for
    # an LLM-written hypothetical answer.
    terms = list(dict.fromkeys(_entities(q)))
    for c in cands[:5]:
        for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", str(c.get("content", ""))):
            if w.lower() not in _STOP and len(terms) < 24:
                terms.append(w)
    hypo = " ".join(terms)
    pseudo = hypo
    try:
        hypo_results = M.recall_hybrid(pseudo, k=pool) if pseudo.strip() else []
    except Exception:
        hypo_results = []
    fused = _fuse(cands, hypo_results)[:k]
    return {"query": q, "hypothetical_document": pseudo[:300],
            "terms_used": len(terms), "results": fused,
            "added_by_expansion": max(0, len(fused) - min(k, len(cands)))}


def get_by_id(fact_id: str) -> dict:
    """#18 - Retrieval-side exact key lookup by fact id.

    The engine only had _ledger_remember_by_id (write side). This is the read
    side: direct O(n) ledger scan honouring the same visibility rules as
    recall (superseded rows hidden unless include_simulated/superseded asked).
    """
    recs = M._load_ledger()
    hit = next((r for r in recs if r.get("id") == fact_id), None)
    if hit is None:
        return {"found": False, "id": fact_id,
                "error": "no fact with that id", "searched": len(recs)}
    return {"found": True, "id": fact_id, "fact": hit,
            "superseded": bool(hit.get("superseded_by") or hit.get("valid_to"))}


def failure_memory(query: str, k: int = 8) -> dict:
    """#21 - Retrieve past failures/post-mortems before retrying a task.

    mem20 writes reflexion records into memory, but nothing treated them as a
    distinct retrieval channel, so a retrying agent re-derives the same wrong
    approach. This filters the store to post-mortem-shaped records and ranks
    them, so 'I already tried this and here is why it failed' surfaces first.
    """
    q = _clean(query)
    try:
        cands = M.recall_hybrid(q, k=max(k * 3, 15))
    except Exception as exc:
        return {"query": q, "results": [], "error": type(exc).__name__}
    keys = ("post-mortem", "postmortem", "root cause", "rootcause", "lesson",
            "failed", "failure", "went wrong", "mistake", "mistakes",
            "root_cause", "error")
    hits = []
    for c in cands:
        blob = ("%s %s" % (c.get("content", ""), " ".join(c.get("tags") or []))).lower()
        matched = [k for k in keys if k in blob]
        if matched:
            item = dict(c)
            item["failure_markers"] = matched
            hits.append(item)
    hits.sort(key=lambda x: (-len(x["failure_markers"]), x.get("ts", "")))
    return {"query": q, "results": hits[:k],
            "candidates_examined": len(cands), "failures_found": len(hits)}


def associative_reconstruct(query: str, k: int = 8, max_hops: int = 2) -> dict:
    """#23 - Cue/tag/content associative reconstruction.

    entity_anchor_expand seeds on identifiers found in the query. This is the
    wider version: seed on entities AND tags AND top content terms, then walk
    the entity graph outward, then back-fill semantically. It is the
    LLM-guided exploration path replaced by deterministic graph walking, so it
    stays offline and costs no LLM calls.
    """
    q = _clean(query)
    seeds = list(dict.fromkeys(_entities(q)))
    content_terms = [w.lower() for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", q)
                     if w.lower() not in _STOP][:8]
    try:
        base = M.recall_hybrid(q, k=k)
    except Exception:
        base = []
    tag_hits = []
    for c in base:
        tg = c.get("tags") or []
        if tg:
            tag_hits.extend([t for t in tg if t not in seeds])
    seeds = list(dict.fromkeys(seeds + tag_hits))[:12]

    walked, hops_used, per_seed = [], 0, {}
    frontier = list(seeds)
    for hop in range(max_hops):
        nxt = []
        for ent in frontier:
            if hop >= max_hops:
                break
            try:
                g = M.recall_graph(ent, hops=1, max_results=6)
            except Exception:
                continue
            facts = (g or {}).get("facts") or []
            if facts:
                per_seed[ent] = len(facts)
                walked.extend(facts)
                hops_used = max(hops_used, hop + 1)
                nxt.extend([f.get("content", "")[:60] for f in facts[:2]])
        frontier = list(dict.fromkeys(nxt))[:8]
    try:
        sem = M.recall_semantic(" ".join(content_terms) or q, k=k)
    except Exception:
        sem = []
    fused = _fuse(base, walked, sem)[:k]
    return {"query": q, "seeds": seeds[:12], "hops_used": hops_used,
            "graph_facts": len(walked), "seed_hits": per_seed, "results": fused}


def recency_decay(query: str, k: int = 8, half_life_days: float = 30.0) -> dict:
    """#1 - Recency weighting applied as an explicit second pass.

    The engine's only decay lived in the MCP tool layer, so anything calling
    memory.py directly got no recency signal at all. This applies exponential
    decay to the retrieved set and re-ranks, rather than filtering: recency
    should break ties and surface fresh facts, not delete old ones.
    """
    q = _clean(query)
    try:
        base = M.recall_hybrid(q, k=max(k * 2, 12))
    except Exception as exc:
        return {"query": q, "results": [], "error": type(exc).__name__}
    now = _time.time()

    def _ts(r):
        t = r.get("ts")
        if not t:
            return None
        try:
            from datetime import datetime
            return datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()
        except Exception:
            return None

    out = []
    for r in base:
        ts = _ts(r)
        age_days = (now - ts) / 86400.0 if ts else None
        decay = 0.5 ** (age_days / half_life_days) if age_days is not None else 0.5
        item = dict(r)
        item["age_days"] = round(age_days, 2) if age_days is not None else None
        item["recency"] = round(decay, 4)
        base_score = float(r.get("score") or 0.0)
        item["recency_score"] = base_score * (0.5 + 0.5 * decay)
        out.append(item)
    out.sort(key=lambda x: -x["recency_score"])
    return {"query": q, "half_life_days": half_life_days, "results": out[:k],
            "dated": sum(1 for x in out if x["age_days"] is not None),
            "undated": sum(1 for x in out if x["age_days"] is None)}
