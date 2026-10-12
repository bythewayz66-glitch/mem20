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
