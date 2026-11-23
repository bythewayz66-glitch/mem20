from __future__ import annotations
import os, sys, tempfile
from pathlib import Path
_PKG_ROOT = Path(__file__).resolve().parents[2]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
_STORE = tempfile.mkdtemp(prefix="mem20prez_")
os.environ["MEM20_STORE_PATH"] = _STORE
import pytest
from mem20prez.domain import PredictiveRecallEngine, predict_next, cache_hit_rate
import mem20prez.domain as domain_mod

@pytest.fixture
def eng(tmp_path):
    return PredictiveRecallEngine(tmp_path / "pred")

def test_learns_transitions(eng):
    for _ in range(5):
        eng.record_recall_event(
            context_topic="auth",
            returned_facts=[{"id": "f1", "topic": "session"}, {"id": "f2", "topic": "token"}],
        )
    preds = eng.predict_next(context_topic="auth", k=5)
    topics = [p.topic for p in preds]
    assert "session" in topics or "token" in topics
    assert preds[0].score > 0

def test_outcome_hit_rate(eng):
    eid = eng.record_recall_event(context_topic="plan", returned_facts=[{"id": "p1", "topic": "roadmap"}])
    eng.record_outcome(eid, ["p1"], True)
    assert eng.health().hit_rate > 0

def test_candidates_filter(eng):
    eng.record_recall_event(context_topic="x", returned_facts=[{"id": "1", "topic": "alpha"}])
    preds = eng.predict_next(context_topic="x", candidates=["alpha", "gamma"], k=5)
    topics = {p.topic for p in preds}
    assert "alpha" in topics and "gamma" in topics

def test_prefetch_grounded_default(eng):
    r = eng.prefetch(context_topic="t", k=2, grounded_only=True)
    assert r.grounded_only is True

def test_legacy_api(tmp_path):
    domain_mod._ENGINE = PredictiveRecallEngine(tmp_path / "legacy")
    domain_mod._ENGINE.record_recall_event(context_topic="a", returned_facts=[{"id": "1", "topic": "b"}])
    out = predict_next(history=["a"], candidates=["b", "c"])
    assert all(isinstance(x, str) for x in out)

def test_cache_hit_rate():
    assert cache_hit_rate(0, 0) == 0.0
    assert cache_hit_rate(1, 4) == 0.25
