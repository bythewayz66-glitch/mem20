from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

__all__ = [
    "PredictiveRecallEngine", "Prediction", "PrefetchResult", "EngineHealth",
    "get_engine", "predict_next", "recall_score", "prefetch", "cache_hit_rate",
    "recall_health", "recall_report", "probe", "estate_context",
    "record_recall_event", "record_outcome",
]

HALF_LIFE_SECONDS = 7 * 24 * 3600
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
