"""Predictive Recall Engine (mem20prez) -- sits on the real mem20 memory substrate."""
from __future__ import annotations

import math
import os
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .store import StateStore, HALF_LIFE_SECONDS

__all__ = [
    "PredictiveRecallEngine", "Prediction", "PrefetchResult", "EngineHealth",
    "get_engine", "predict_next", "recall_score", "prefetch", "cache_hit_rate",
    "recall_health", "recall_report", "probe", "estate_context",
    "record_recall_event", "record_outcome",
]

MIN_SUPPORT = 2


def _default_store_dir() -> Path:
    base = os.environ.get("MEM20_STORE_PATH")
    if base:
        return Path(base).expanduser() / "predictive_recall"
    return Path.home() / ".mem20" / "store" / "predictive_recall"


@dataclass(frozen=True)
class Prediction:
    topic: str
    score: float
    reason: str
    tags: tuple[str, ...] = ()
    fact_ids: tuple[str, ...] = ()
    source: str = "model"


@dataclass(frozen=True)
class PrefetchResult:
    predictions: tuple[Prediction, ...]
    facts: tuple[dict[str, Any], ...]
    grounded_only: bool
    query_topics: tuple[str, ...]
    latency_ms: float
    event_id: str = ""


@dataclass
class EngineHealth:
    events: int
    outcomes: int
    topics_tracked: int
    transitions: int
    hit_rate: float
    store_path: str
    ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok, "events": self.events, "outcomes": self.outcomes,
            "topics_tracked": self.topics_tracked, "transitions": self.transitions,
            "hit_rate": self.hit_rate, "store_path": self.store_path,
        }


class PredictiveRecallEngine:
    def __init__(self, store_dir=None):
        self.store_dir = Path(store_dir) if store_dir else _default_store_dir()
        self._state = StateStore(self.store_dir / "models.sqlite3")

    def record_recall_event(self, *, context_topic=None, context_tags=None,
                            returned_facts=None, event_id=None):
        now = time.time()
        eid = event_id or str(uuid.uuid4())
        tags = list(context_tags or ())
        facts = list(returned_facts or ())
        returned_ids = [str(f.get("id", "")) for f in facts if f.get("id")]
        returned_topics = [str(f["topic"]) for f in facts if f.get("topic")]
        self._state.record_event(eid, now, context_topic, tags, returned_ids, returned_topics)
        return eid

    def record_outcome(self, prediction_id, used_fact_ids, useful):
        oid = str(uuid.uuid4())
        self._state.record_outcome(oid, prediction_id, time.time(), list(used_fact_ids), useful)
        return oid

    def predict_next(self, *, context_topic=None, context_tags=None, history=None,
                     candidates=None, k=8, include_ledger_boost=True):
        now = time.time()
        scores = defaultdict(float)
        reasons = defaultdict(list)
        if context_topic:
            for to_t, cnt in self._state.transitions_from(context_topic, now).items():
                if cnt >= MIN_SUPPORT * 0.25:
                    scores[to_t] += 1.5 * math.log1p(cnt)
                    reasons[to_t].append(f"transition:{context_topic}->{to_t}={cnt:.2f}")
        if history:
            for prev in history[-5:]:
                for to_t, cnt in self._state.transitions_from(prev, now).items():
                    scores[to_t] += 0.6 * math.log1p(cnt)
                    reasons[to_t].append(f"history:{prev}->{to_t}")
        for topic, sc in self._state.topic_scores(now).items():
            scores[topic] += 0.8 * math.log1p(sc)
            reasons[topic].append(f"access={sc:.2f}")
        if include_ledger_boost:
            for topic in self._ledger_topics():
                if topic in scores or not candidates:
                    scores[topic] += 0.35
                    reasons[topic].append("ledger_present")
        if candidates:
            cand_set = set(candidates)
            scores = {t: s for t, s in scores.items() if t in cand_set}
            for c in candidates:
                if c not in scores:
                    scores[c] = 0.01
                    reasons[c].append("candidate_base")
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:k]
        return [
            Prediction(topic=t, score=round(s, 4),
                       reason="; ".join(reasons.get(t, ["model"])[:4]),
                       source="hybrid" if include_ledger_boost else "model")
            for t, s in ranked
        ]

    def prefetch(self, *, context_topic=None, context_tags=None, history=None,
                 k=5, grounded_only=True):
        t0 = time.time()
        preds = self.predict_next(context_topic=context_topic, context_tags=context_tags,
                                  history=history, k=k, include_ledger_boost=True)
        facts, topics_queried = [], []
        mem_recall = None
        try:
            from memory_engine import recall as mem_recall
        except Exception:
            try:
                import memory as mem
                mem_recall = mem.recall
            except Exception:
                pass
        if mem_recall is not None:
            for p in preds:
                topics_queried.append(p.topic)
                try:
                    results = mem_recall(
                        topic=p.topic,
                        tags=list(context_tags) if context_tags else None,
                        k=3,
                        include_simulated=not grounded_only,
                    )
                    if isinstance(results, list):
                        for r in results:
                            if isinstance(r, dict):
                                facts.append(r)
                            else:
                                facts.append({
                                    "id": getattr(r, "id", ""),
                                    "topic": getattr(r, "topic", p.topic),
                                    "content": getattr(r, "content", str(r)),
                                    "origin": getattr(r, "origin", "grounded"),
                                })
                except Exception:
                    continue
        event_id = self.record_recall_event(
            context_topic=context_topic, context_tags=context_tags, returned_facts=facts)
        return PrefetchResult(
            predictions=tuple(preds), facts=tuple(facts), grounded_only=grounded_only,
            query_topics=tuple(topics_queried),
            latency_ms=round((time.time() - t0) * 1000, 2), event_id=event_id)

    def health(self):
        s = self._state.stats()
        return EngineHealth(
            events=s["events"], outcomes=s["outcomes"], topics_tracked=s["topics_tracked"],
            transitions=s["transitions"], hit_rate=s["hit_rate"],
            store_path=str(self.store_dir), ok=True)

    def _ledger_topics(self):
        try:
            from memory_engine import ledger_view
            rows = ledger_view(k=200)
            topics = set()
            for r in rows or []:
                if isinstance(r, dict) and r.get("topic"):
                    if r.get("origin", "grounded") == "grounded" or r.get("store") == "grounded":
                        topics.add(str(r["topic"]))
            return topics
        except Exception:
            return set()


_ENGINE = None
_ENGINE_LOCK = threading.Lock()


def get_engine(store_dir=None):
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is None or store_dir is not None:
            _ENGINE = PredictiveRecallEngine(store_dir)
        return _ENGINE


def predict_next(history=None, candidates=None, context_topic=None, **kwargs):
    eng = get_engine()
    if context_topic is None and history:
        context_topic = history[-1]
    return [p.topic for p in eng.predict_next(
        context_topic=context_topic, history=history, candidates=candidates, k=kwargs.get("k", 8))]


def recall_score(item, context):
    recency = float((context.get("recency") or {}).get(item, 0) or 0)
    frequency = float((context.get("frequency") or {}).get(item, 0) or 0)
    live = get_engine()._state.topic_scores().get(item, 0.0)
    return round(0.5 * math.log1p(live + frequency) + 0.3 * recency + 0.2 * frequency, 4)


def prefetch(predictions=None, k=3, context_topic=None, **kwargs):
    eng = get_engine()
    if predictions and all(isinstance(p, str) for p in predictions):
        result = eng.prefetch(
            context_topic=context_topic or (predictions[0] if predictions else None),
            k=k, grounded_only=kwargs.get("grounded_only", True))
        return list(result.facts)[:k]
    return list(eng.prefetch(context_topic=context_topic, k=k, grounded_only=True).facts)[:k]


def cache_hit_rate(hits, total):
    return 0.0 if total <= 0 else round(hits / total, 4)


def recall_health(predictions=None):
    d = get_engine().health().to_dict()
    if predictions is not None:
        d["predictions"] = len(predictions)
    return d


def record_recall_event(**kwargs):
    return get_engine().record_recall_event(**kwargs)


def record_outcome(prediction_id, used_fact_ids, useful):
    return get_engine().record_outcome(prediction_id, used_fact_ids, useful)


def recall_report(history=None, candidates=None, context_topic=None):
    eng = get_engine()
    preds = eng.predict_next(
        context_topic=context_topic or (history[-1] if history else None),
        history=history, candidates=candidates, k=8)
    health = eng.health()
    peers = _honest_peer_probe()
    return {
        "ok": health.ok,
        "predictions": [{"topic": p.topic, "score": p.score, "reason": p.reason, "source": p.source}
                        for p in preds],
        "prefetch_topics": [p.topic for p in preds[:3]],
        "health": health.to_dict(),
        "peers": peers,
        "peer_ok": all(v.get("ok") for v in peers.values()) if peers else True,
    }


def probe():
    h = get_engine().health()
    peers = _honest_peer_probe()
    return {"ok": h.ok, "health": h.to_dict(), "peers": peers, "checks": peers}


def estate_context(store_path=None):
    eng = PredictiveRecallEngine(store_path) if store_path else get_engine()
    h = eng.health()
    peers = _honest_peer_probe()
    return {
        "engine_status_checked": True, "peer_count": len(peers),
        "peers_ok": all(v.get("ok") for v in peers.values()) if peers else True,
        "checks": peers, "health": h.to_dict(),
    }


def _honest_peer_probe():
    results = {}
    try:
        from memory_engine import status as mem_status
        st = mem_status()
        results["memory_engine"] = {
            "ok": True, "subsystem": "memory_engine",
            "detail": "status_reachable", "status_type": type(st).__name__,
        }
    except Exception as exc:
        results["memory_engine"] = {
            "ok": False, "subsystem": "memory_engine",
            "error": f"{type(exc).__name__}: {exc}",
        }
    return results
