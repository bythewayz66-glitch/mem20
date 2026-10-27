"""Bulk ingest for benchmark corpora.

`_seed()` in cli.py writes every record through `store.remember()`, and
`remember()` calls `_add_to_vector_index()` per record — one
`SentenceTransformer.encode([text])` each. Measured on the benchmark host that
is ~0.5 s per record, so a 700-record grounded load spends ~11 minutes encoding
single sentences and a 2,000-record corpus is unusable as a routine check. The
cost is not the model, it is the batch size of one.

This module appends the SAME ledger envelopes the engine writes and then builds
each index once, in batches, via the engine's own `rebuild_vectors()` /
`rebuild_bm25()` / `rebuild_graph()`. Records are not hand-rolled: the envelope
shapes below are copied field-for-field from `memory_engine.memory.remember()`
and `remember_simulated()`, and `verify()` re-reads the result through the
engine's own loaders so a shape drift shows up as a failure rather than as a
corpus that silently retrieves nothing.

Ordering matters for the store path: `memory_engine.memory` resolves
`STORE_DIR` from `MEM20_STORE_PATH` at import time, so the env var is set before
the import in `ingest()`. Setting it afterwards is silently ignored.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path

# --- engine envelope templates -------------------------------------------
# Field order and key names mirror memory_engine.memory exactly. `id` is a
# content hash here instead of the engine's time+urandom id so a re-run against
# a fresh store is reproducible; the engine only requires uniqueness.
_GROUNDED_TEMPLATE = {
    "actor": "agent",
    "action": "remember",
    "origin": "grounded",
    "store": "grounded",
    "event_time_basis": "assumed_ingestion",
    "valid_to": None,
    "confidence": None,
    "source": None,
    "secrets_detected": None,
}

_SIMULATED_TEMPLATE = {
    "actor": "agent",
    "action": "simulate",
    "store": "simulated",
    "origin": "simulated",
    "epistemic_status": "imagined",
    "promoted_to": None,
    "quarantined": False,
    "secrets_detected": None,
}


def _record_id(prefix: str, key: str) -> str:
    return f"{prefix}{hashlib.md5(key.encode()).hexdigest()[:14]}"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _grounded_row(rec: dict, ts: str) -> dict:
    row = dict(_GROUNDED_TEMPLATE)
    row.update({
        "id": _record_id("b", rec["key"]),
        "ts": ts,
        "topic": rec["topic"],
        "tags": list(rec.get("tags") or ()),
        "priority": "normal",
        "content": rec["content"],
        "valid_from": ts,
        "epistemic_status": rec.get("epistemic_status") or "observed",
        "source": rec.get("source"),
    })
    return row


def _simulated_row(rec: dict, ts: str, ttl_days: int) -> dict:
    row = dict(_SIMULATED_TEMPLATE)
    row.update({
        "id": _record_id("s", rec["key"]),
        "ts": ts,
        "topic": rec["topic"],
        "tags": list(rec.get("tags") or ()),
        "priority": "normal",
        "content": rec["content"],
        "valid_from": ts,
        "valid_to": None,
        "ttl_days": ttl_days,
        "confidence": rec.get("confidence"),
        "source": None,
        "scenario": "benchmark scale corpus",
        "sim_type": "counterfactual",
    })
    return row


def ingest(corpus_dir: str | Path, store_dir: str | Path, *,
           ttl_days: int = 30, progress: bool = True) -> dict:
    """Write a corpus directory into a store and build indexes once.

    Returns measured counts and the wall time spent on each phase. Index
    building is the part that is expensive; it runs a single batched pass.
    """
    import time

    corpus_dir, store_dir = Path(corpus_dir), Path(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)
    # Must precede the engine import: STORE_DIR is bound at import time.
    os.environ["MEM20_STORE_PATH"] = str(store_dir)

    t0 = time.time()
    with (corpus_dir / "grounded.jsonl").open(encoding="utf-8") as fh:
        grounded = [json.loads(l) for l in fh if l.strip()]
    with (corpus_dir / "simulated.jsonl").open(encoding="utf-8") as fh:
        simulated = [json.loads(l) for l in fh if l.strip()]

    ts = _now()
    ledger = store_dir / "ledger.jsonl"
    with ledger.open("a", encoding="utf-8") as fh:
        for rec in grounded:
            fh.write(json.dumps(_grounded_row(rec, ts), ensure_ascii=False) + "\n")
    sim_ledger = store_dir / "simulated_ledger.jsonl"
    with sim_ledger.open("a", encoding="utf-8") as fh:
        for rec in simulated:
            fh.write(json.dumps(_simulated_row(rec, ts, ttl_days),
                                ensure_ascii=False) + "\n")
    append_s = time.time() - t0

    if progress:
        print(f"appended {len(grounded)} grounded + {len(simulated)} simulated "
              f"in {append_s:.1f}s", flush=True)

    from memory_engine import memory as engine  # after STORE_DIR is set

    t1 = time.time()
    vec_msg = engine.rebuild_vectors()
    bm25_msg = engine.rebuild_bm25()
    # The graph is written at remember() time, so a ledger-only ingest leaves it
    # absent and store.health() then reports healthy=false and the harness
    # refuses to score. It is derived state, so rebuild it from the ledger.
    graph_msg = engine.rebuild_graph()
    index_s = time.time() - t1

    if progress:
        print(f"indexes built in {index_s:.1f}s: {vec_msg} / {bm25_msg} / "
              f"{graph_msg}", flush=True)

    return {
        "grounded_appended": len(grounded),
        "simulated_appended": len(simulated),
        "append_seconds": round(append_s, 2),
        "index_seconds": round(index_s, 2),
        "vector_message": vec_msg,
        "bm25_message": bm25_msg,
        "graph_message": graph_msg,
        "store": str(store_dir),
    }


def verify(store_dir: str | Path) -> dict:
    """Re-read the store through the engine's own loaders.

    Counting lines with `wc -l` would confirm the file, not the store. This asks
    the engine what it believes it holds, which is the number the harness will
    actually retrieve from.
    """
    os.environ["MEM20_STORE_PATH"] = str(store_dir)
    from memory_engine import memory as engine

    grounded = engine._load_ledger()
    simulated = engine._load_simulated_ledger()
    return {
        "ledger_records": len(grounded),
        "simulated_records": len(simulated),
        "vector_indexed": len(engine._load_vector_meta()),
        "bm25_indexed": len(engine._load_bm25_meta())
        if hasattr(engine, "_load_bm25_meta") else None,
    }
