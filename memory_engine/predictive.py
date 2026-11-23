"""Predictive recall -- first-class memory_engine capability.

Learns topic transitions and decayed access from real recall traffic,
predicts next topics, and prefetches grounded facts only (firewall respected).
Previously mem20prez subsystem; now part of the engine.
"""
from __future__ import annotations

import math
import os
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .predictive_store import StateStore, HALF_LIFE_SECONDS

MIN_SUPPORT = 2


def _store_dir() -> Path:
    base = os.environ.get("MEM20_STORE_PATH")
    root = Path(base).expanduser() if base else Path.home() / ".mem20" / "store"
    return root / "predictive"


@dataclass(frozen=True)
class Prediction:
    topic: str
    score: float
    reason: str
    source: str = "model"


@dataclass(frozen=True)
class PrefetchResult:
    predictions: tuple[Prediction, ...]
    facts: tuple[dict[str, Any], ...]
    grounded_only: bool
    query_topics: tuple[str, ...]
    latency_ms: float
    event_id: str = ""


class PredictiveRecall:
    """Engine-native predictive recall."""

    def __init__(self, store_dir: Path | None = None):
        self.store_dir = Path(store_dir) if store_dir else _store_dir()
        self._state = StateStore(self.store_dir / "models.sqlite3")

    def record_recall_event(self, *, context_topic=None, context_tags=None,
                            returned_facts=None, event_id=None) -> str:
        now = time.time()
        eid = event_id or str(uuid.uuid4())
        facts = list(returned_facts or ())
        returned_ids = [str(f.get("id", "")) for f in facts if f.get("id")]
        returned_topics = [str(f["topic"]) for f in facts if f.get("topic")]
        self._state.record_event(
            eid, now, context_topic, list(context_tags or ()), returned_ids, returned_topics)
        return eid

    def record_outcome(self, prediction_id: str, used_fact_ids, useful: bool) -> str:
        oid = str(uuid.uuid4())
        self._state.record_outcome(oid, prediction_id, time.time(), list(used_fact_ids or ()), useful)
        return oid

    def predict_next(self, *, context_topic=None, history=None, candidates=None,
                     k: int = 8) -> list[Prediction]:
        now = time.time()
        scores: dict[str, float] = defaultdict(float)
        reasons: dict[str, list] = defaultdict(list)
        if context_topic:
            for to_t, cnt in self._state.transitions_from(context_topic, now).items():
                if cnt >= MIN_SUPPORT * 0.25:
                    scores[to_t] += 1.5 * math.log1p(cnt)
                    reasons[to_t].append(f"transition:{context_topic}->{to_t}")
        if history:
            for prev in history[-5:]:
                for to_t, cnt in self._state.transitions_from(prev, now).items():
                    scores[to_t] += 0.6 * math.log1p(cnt)
        for topic, sc in self._state.topic_scores(now).items():
            scores[topic] += 0.8 * math.log1p(sc)
            reasons[topic].append(f"access={sc:.2f}")
        if candidates is not None:
            cand = set(candidates)
            scores = {t: s for t, s in scores.items() if t in cand}
            for c in candidates:
                scores.setdefault(c, 0.01)
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:k]
        return [
            Prediction(topic=t, score=round(s, 4),
                       reason="; ".join(reasons.get(t, ["model"])[:3]))
            for t, s in ranked
        ]

    def prefetch(self, *, context_topic=None, context_tags=None, history=None,
                 k: int = 5, grounded_only: bool = True) -> PrefetchResult:
        t0 = time.time()
        preds = self.predict_next(context_topic=context_topic, history=history, k=k)
        facts: list[dict] = []
        topics_queried: list[str] = []
        try:
            from memory_engine import recall as mem_recall
        except Exception:
            mem_recall = None
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
                    for r in results or []:
                        if isinstance(r, dict):
                            facts.append(r)
                        else:
                            facts.append({
                                "id": getattr(r, "id", ""),
                                "topic": getattr(r, "topic", p.topic),
                                "content": getattr(r, "content", str(r)),
                            })
                except Exception:
                    continue
        event_id = self.record_recall_event(
            context_topic=context_topic, context_tags=context_tags, returned_facts=facts)
        return PrefetchResult(
            predictions=tuple(preds), facts=tuple(facts), grounded_only=grounded_only,
            query_topics=tuple(topics_queried),
            latency_ms=round((time.time() - t0) * 1000, 2), event_id=event_id)

    def health(self) -> dict[str, Any]:
        s = self._state.stats()
        s["ok"] = True
        s["store_path"] = str(self.store_dir)
        return s


_PRED: PredictiveRecall | None = None
_PRED_LOCK = threading.Lock()


def get_predictive(store_dir=None) -> PredictiveRecall:
    global _PRED
    with _PRED_LOCK:
        if _PRED is None or store_dir is not None:
            _PRED = PredictiveRecall(store_dir)
        return _PRED


def predict_next(context_topic=None, history=None, candidates=None, k: int = 8) -> list[str]:
    return [p.topic for p in get_predictive().predict_next(
        context_topic=context_topic, history=history, candidates=candidates, k=k)]


def prefetch(context_topic=None, context_tags=None, k: int = 5, grounded_only: bool = True):
    return get_predictive().prefetch(
        context_topic=context_topic, context_tags=context_tags, k=k, grounded_only=grounded_only)


def record_recall_outcome(prediction_id: str, used_fact_ids, useful: bool) -> str:
    return get_predictive().record_outcome(prediction_id, used_fact_ids, useful)


def predictive_health() -> dict[str, Any]:
    return get_predictive().health()
