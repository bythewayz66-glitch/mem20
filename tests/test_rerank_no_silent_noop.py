"""CE-1 regression: the cross-encoder rerank must not silently no-op.

The defect
----------
`recall_hybrid` blended the cross-encoder score into only the top `k * 2`
candidates, left every other candidate at its raw RRF score, and then sorted
both kinds together in one list. ms-marco cross-encoders emit raw logits that
are routinely negative (measured on the reference host: -11.4 .. +3.3), so a
blended candidate scored ~0.5*rrf + 0.5*ce and could fall BELOW an unblended
candidate still sitting at its raw rrf (~0.007). The reranker could push the
best candidates out of the returned window while `_retrieval.cross_encoder`
still reported True.

Measured before the fix, on a 20-fact store with k=5: 4 of the 5 returned
results had never been reranked at all.

What these tests pin
--------------------
1. every returned candidate carries a `_ce_score` (no unblended stragglers)
2. an unblended candidate can never outrank a blended one
3. negative logits cannot invert the ordering
4. a short/raising `predict()` reverts atomically and surfaces the error
5. `_retrieval.cross_encoder` reports what happened, not what was configured

These stub the two retrieval halves and the encoder, so they exercise the
fusion + rerank plumbing directly and run without torch, faiss or
sentence-transformers installed. The plumbing is what broke, and the plumbing
is what is tested.
"""
import os

import pytest

from memory_engine import memory as M

QUERY = "unity licence path"
K = 5


def _cand(i, content):
    """A candidate in the shape recall_semantic returns."""
    return {
        "id": f"id{i:03d}",
        "ts": "2026-10-12T00:00:00+00:00",
        "topic": "unity",
        "tags": ["unity"],
        "priority": "normal",
        "content": content,
        "epistemic_status": "observed",
        "confidence": None,
        "source": None,
        "score": 0.5,
    }


# 20 candidates, so the rerank window (k*2 = 10) is strictly smaller than the
# candidate set - which is the condition that produced CE-1.
VECTOR = [_cand(i, f"candidate {i} about unity licence path") for i in range(20)]


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path))
    M.STORE_DIR = str(tmp_path)
    M.MEM_DIR = str(tmp_path.parent)
    M.LEDGER = os.path.join(M.STORE_DIR, "ledger.jsonl")
    M.ENTRIES = os.path.join(M.STORE_DIR, "entries")
    M.INDEX = os.path.join(M.STORE_DIR, "INDEX.md")
    M.BACKUP_DIR = os.path.join(M.STORE_DIR, "backups")
    M.VECTOR_INDEX = os.path.join(M.STORE_DIR, "vector_index.faiss")
    M.VECTOR_META = os.path.join(M.STORE_DIR, "vector_meta.jsonl")
    M.BM25_INDEX = os.path.join(M.STORE_DIR, "bm25_index.pkl")
    M.BM25_CORPUS = os.path.join(M.STORE_DIR, "bm25_corpus.jsonl")
    M.GRAPH_INDEX = os.path.join(M.STORE_DIR, "memory_graph.json")
    M.SIMULATED_LEDGER = os.path.join(M.STORE_DIR, "simulated_ledger.jsonl")
    os.makedirs(M.ENTRIES, exist_ok=True)
    # Stub the vector half so no model is loaded. BM25 is left unbuilt, which
    # is the real state after remember() - it does not build a BM25 index.
    monkeypatch.setattr(M, "recall_semantic",
                        lambda q, k=5, topic=None, tags=None: list(VECTOR))
    return tmp_path


class _FakeCE:
    """Deterministic stand-in. `mode` selects the failure shape under test."""

    def __init__(self, mode="descending"):
        self.mode = mode
        self.calls = 0

    def predict(self, pairs):
        import numpy as np
        self.calls += 1
        if self.mode == "short":
            return np.array([0.9])
        if self.mode == "raise":
            raise RuntimeError("model unavailable")
        if self.mode == "negative":
            # Raw logits, all negative - the real ms-marco shape.
            return np.linspace(-1.0, -11.0, len(pairs))
        return np.linspace(1.0, 0.0, len(pairs))


def _install(monkeypatch, fake):
    monkeypatch.setattr(M, "_get_cross_encoder", lambda: fake)
    monkeypatch.setattr(M, "USE_CROSS_ENCODER", True)


def test_every_returned_candidate_is_reranked(store, monkeypatch):
    """No candidate may be returned unblended while others were blended."""
    fake = _FakeCE()
    _install(monkeypatch, fake)

    res = M.recall_hybrid(QUERY, k=K)

    assert fake.calls == 1, "the cross-encoder should have been consulted"
    assert len(res) == K
    missing = [r["id"] for r in res if r.get("_ce_score") is None]
    assert not missing, (
        f"{len(missing)} of {len(res)} returned candidates were never reranked; "
        "they competed against reranked candidates on a different score scale"
    )


def test_unblended_candidate_cannot_outrank_blended(store, monkeypatch):
    """The CE-1 regression proper.

    With the old code the top `k*2` were blended and the rest were not, so a
    raw-RRF candidate could leapfrog a blended one. Every returned candidate
    must now carry a cross-encoder score, and the returned `score` must be the
    blended value rather than a raw RRF score.
    """
    _install(monkeypatch, _FakeCE())

    res = M.recall_hybrid(QUERY, k=K)

    for r in res:
        assert r.get("_ce_score") is not None, (
            f"candidate {r['id']} reached the caller unblended"
        )
        # The returned score is the blend, so it must sit between the two terms.
        assert r["score"] >= min(r["_ce_score"], 0.0), (
            f"candidate {r['id']} score {r['score']} is below its own blend"
        )


def test_negative_logits_do_not_invert_order(store, monkeypatch):
    """All-negative logits must not push reranked candidates below raw-RRF ones."""
    _install(monkeypatch, _FakeCE(mode="negative"))

    res = M.recall_hybrid(QUERY, k=K)

    assert len(res) == K
    # Squashed logits live in (0,1), so the blend stays commensurate with RRF
    # and the ordering cannot invert.
    for r in res:
        ce = r.get("_ce_score")
        assert ce is not None and 0.0 < ce < 1.0, (
            f"cross-encoder score {ce!r} is outside (0,1); raw logits leaked "
            "into the blend and can invert the ordering"
        )
    scores = [r["score"] for r in res]
    assert scores == sorted(scores, reverse=True), "results are not in score order"


def test_short_predict_reverts_atomically(store, monkeypatch):
    """A shape mismatch must not leave a half-mutated list."""
    _install(monkeypatch, _FakeCE(mode="short"))

    res = M.recall_hybrid(QUERY, k=K)

    assert len(res) == K, "results should still be returned (graceful degradation)"
    assert all(r.get("_ce_score") is None for r in res), (
        "a partial mutation survived the failure - some candidates were "
        "reranked and others were not"
    )


def test_raising_predict_reverts_atomically(store, monkeypatch):
    """An exception from the encoder must not leave a half-mutated list."""
    _install(monkeypatch, _FakeCE(mode="raise"))

    res = M.recall_hybrid(QUERY, k=K)

    assert len(res) == K
    assert all(r.get("_ce_score") is None for r in res)


def test_flag_reports_what_happened_not_what_was_configured(store, monkeypatch):
    """`_retrieval.cross_encoder` is the signal CE-1 hid behind."""
    # Happy path: applied -> True, no error.
    _install(monkeypatch, _FakeCE())
    res = M.recall_hybrid(QUERY, k=K)
    ret = res[0]["_retrieval"]
    assert ret["cross_encoder"] is True
    assert ret["cross_encoder_error"] is None

    # Failure path: not applied -> False, and the reason is reported.
    _install(monkeypatch, _FakeCE(mode="short"))
    res = M.recall_hybrid(QUERY, k=K)
    ret = res[0]["_retrieval"]
    assert ret["cross_encoder"] is False, (
        "the flag claimed reranking happened when it did not - this is exactly "
        "the silent no-op CE-1 was"
    )
    assert ret["cross_encoder_error"], "the failure reason was not surfaced"


def test_rerank_off_is_reported_as_off(store, monkeypatch):
    """With reranking disabled the flag must be False and no scores present."""
    monkeypatch.setattr(M, "USE_CROSS_ENCODER", False)

    res = M.recall_hybrid(QUERY, k=K)

    assert len(res) == K
    assert res[0]["_retrieval"]["cross_encoder"] is False
    assert all(r.get("_ce_score") is None for r in res)
