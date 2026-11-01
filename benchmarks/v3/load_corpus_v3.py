#!/usr/bin/env python3
"""Load a mem20-scale-corpus-v3 directory into a mem20 memory store.

Two routes, because they answer different questions:

  --mode api     the real write path: ``mem20api.open_store(path)`` then
                 ``store.remember()`` for grounded records and
                 ``store.remember_simulated()`` for ungrounded/false ones.
                 Correct, and slow: ``remember()`` encodes one sentence per
                 record, so a 122k-record corpus is hours, not minutes.
  --mode ledger  append the ledger envelopes directly, then rebuild the
                 derived indexes once. Same field shapes as the engine's own
                 writers (copied from ``memory_engine/memory.py``), ~100x
                 faster, and the only practical route for a load test.

Both routes respect the firewall: grounded records go to ``ledger.jsonl``,
ungrounded and false records go to ``simulated_ledger.jsonl``. Nothing is
written to the grounded partition that is not grounded.

    # what would happen, no writes
    python benchmarks/v3/load_corpus_v3.py benchmarks/corpora/v3 --dry-run

    # bulk load into a scratch store, then rebuild indexes
    python benchmarks/v3/load_corpus_v3.py benchmarks/corpora/v3 \
        --mode ledger --store /tmp/mem20-v3-store --rebuild

    # count what is actually in a store (live ledger + rotated archives)
    python benchmarks/v3/load_corpus_v3.py --count --store /tmp/mem20-v3-store
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# mem20's own vocabulary, from memory_engine/memory.py.
GROUNDED_STATUS = "observed"
SIMULATED_STATUS = "imagined"


def _record_id(key: str) -> str:
    """Deterministic id, derived the same way for every load.

    A random id would make a re-load produce different ids for the same key,
    so an id-based hit check would silently never fire.
    """
    return "b" + hashlib.md5(key.encode("utf-8")).hexdigest()[:14]


def _iter_records(corpus: Path):
    shards = sorted(corpus.glob("records.part-*.jsonl"))
    if not shards:
        raise SystemExit(f"no records.part-*.jsonl under {corpus}")
    for shard in shards:
        with shard.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)


def _grounded_envelope(rec: dict) -> dict:
    """The exact shape ``memory_engine.memory.remember()`` appends.

    Field-for-field from the dict literal in that function; the benchmark
    metadata rides along in ``tags`` and ``source`` so it survives the load
    without inventing fields the engine does not write.
    """
    return {
        "id": _record_id(rec["key"]),
        "ts": rec["timestamp"],
        "actor": "benchmark-loader",
        "action": "remember",
        "topic": rec["topic"],
        "tags": list(rec["tags"]) + [f"bench-key:{rec['key']}"],
        "priority": "normal",
        "content": rec["content"],
        "valid_from": rec["timestamp"],
        "event_time_basis": "declared",
        "valid_to": None,
        "confidence": rec["confidence"],
        "epistemic_status": GROUNDED_STATUS,
        "source": rec["source"],
        "origin": "grounded",
        "store": "grounded",
        "secrets_detected": None,
    }


def _simulated_envelope(rec: dict) -> dict:
    """The exact shape ``memory_engine.memory.remember_simulated()`` appends."""
    return {
        "id": _record_id(rec["key"]),
        "ts": rec["timestamp"],
        "actor": "benchmark-loader",
        "action": "simulate",
        "store": "simulated",
        "origin": "simulated",
        "epistemic_status": SIMULATED_STATUS,
        "topic": rec["topic"],
        "tags": list(rec["tags"]) + [f"bench-key:{rec['key']}"],
        "priority": "normal",
        "content": rec["content"],
        "valid_from": rec["timestamp"],
        "valid_to": None,
        "ttl_days": None,
        "confidence": rec["confidence"],
        "source": None,
        "scenario": f"benchmark {rec['category']} claim",
        "sim_type": "counterfactual",
        "promoted_to": None,
        "quarantined": False,
        "secrets_detected": None,
    }


def _count_store(store: Path) -> dict:
    """Count a store's records, including rotated ledger archives.

    ``_append_ledger()`` rotates ``ledger.jsonl`` into
    ``backups/ledger_<epoch>.jsonl`` every 2,000 lines, so ``wc -l`` on the
    live file under-reports a bulk load by orders of magnitude.
    """
    live = store / "ledger.jsonl"
    archives = sorted((store / "backups").glob("ledger_*.jsonl"))
    sim = store / "simulated_ledger.jsonl"

    def lines(path: Path) -> int:
        if not path.is_file():
            return 0
        with path.open(encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())

    live_n = lines(live)
    archive_n = sum(lines(a) for a in archives)
    sim_n = lines(sim)
    return {
        "grounded_live": live_n,
        "grounded_archives": archive_n,
        "grounded_total": live_n + archive_n,
        "simulated": sim_n,
        "total": live_n + archive_n + sim_n,
        "archive_files": len(archives),
    }


def _load_ledger_mode(corpus: Path, store: Path, batch_size: int,
                      retries: int, skip_existing: bool) -> dict:
    store.mkdir(parents=True, exist_ok=True)
    grounded_path = store / "ledger.jsonl"
    sim_path = store / "simulated_ledger.jsonl"

    existing: set[str] = set()
    if skip_existing:
        for path in [grounded_path, sim_path, *sorted((store / "backups").glob("ledger_*.jsonl"))]:
            if not path.is_file():
                continue
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    for tag in rec.get("tags") or []:
                        if isinstance(tag, str) and tag.startswith("bench-key:"):
                            existing.add(tag.split(":", 1)[1])

    written = {"grounded": 0, "simulated": 0, "skipped": 0, "failed": 0}
    batch: list[tuple[Path, dict]] = []

    def flush() -> None:
        nonlocal batch
        if not batch:
            return
        for attempt in range(retries + 1):
            try:
                by_path: dict[Path, list[str]] = {}
                for path, rec in batch:
                    by_path.setdefault(path, []).append(
                        json.dumps(rec, ensure_ascii=False))
                for path, lines in by_path.items():
                    with path.open("a", encoding="utf-8") as fh:
                        fh.write("\n".join(lines) + "\n")
                for path, rec in batch:
                    if path == grounded_path:
                        written["grounded"] += 1
                    else:
                        written["simulated"] += 1
                batch = []
                return
            except OSError as exc:
                if attempt == retries:
                    written["failed"] += len(batch)
                    print(f"  batch failed after {retries} retries: {exc}",
                          file=sys.stderr)
                    batch = []
                    return
                time.sleep(2 ** attempt)

    for rec in _iter_records(corpus):
        if skip_existing and rec["key"] in existing:
            written["skipped"] += 1
            continue
        if rec["category"] == "grounded":
            batch.append((grounded_path, _grounded_envelope(rec)))
        else:
            batch.append((sim_path, _simulated_envelope(rec)))
        if len(batch) >= batch_size:
            flush()
    flush()
    return written


def _load_api_mode(corpus: Path, store: Path, batch_size: int,
                   retries: int, skip_existing: bool) -> dict:
    # MEM20_STORE_PATH is resolved at import time, so it must be set BEFORE the
    # engine is imported or the --store flag is silently ignored.
    os.environ["MEM20_STORE_PATH"] = str(store)
    for p in (str(REPO_ROOT / "mem20api"), str(REPO_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from mem20api import open_store
    except Exception as exc:  # noqa: BLE001
        return {"status": "UNAVAILABLE", "reason": f"cannot import mem20api: {exc}"}

    written = {"grounded": 0, "simulated": 0, "skipped": 0, "failed": 0}
    with open_store(store) as st:
        for i, rec in enumerate(_iter_records(corpus), start=1):
            for attempt in range(retries + 1):
                try:
                    if rec["category"] == "grounded":
                        st.remember(rec["topic"], rec["content"],
                                    tags=list(rec["tags"]) + [f"bench-key:{rec['key']}"],
                                    epistemic_status=GROUNDED_STATUS,
                                    source=rec["source"],
                                    confidence=rec["confidence"])
                        written["grounded"] += 1
                    else:
                        st.remember_simulated(
                            rec["topic"], rec["content"],
                            tags=list(rec["tags"]) + [f"bench-key:{rec['key']}"],
                            scenario=f"benchmark {rec['category']} claim",
                            sim_type="counterfactual")
                        written["simulated"] += 1
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == retries:
                        written["failed"] += 1
                        print(f"  {rec['key']}: {exc}", file=sys.stderr)
                    else:
                        time.sleep(2 ** attempt)
            if i % batch_size == 0:
                print(f"  {i} records...", flush=True)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus", nargs="?", default="benchmarks/corpora/v3")
    ap.add_argument("--store", default="/tmp/mem20-v3-store")
    ap.add_argument("--mode", choices=("ledger", "api"), default="ledger")
    ap.add_argument("--batch-size", type=int, default=2000)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--rebuild", action="store_true",
                    help="rebuild vector/bm25/graph indexes after loading")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse and validate only; write nothing")
    ap.add_argument("--count", action="store_true",
                    help="count what is in --store and exit")
    args = ap.parse_args(argv)

    store = Path(args.store)
    if args.count:
        print(json.dumps(_count_store(store), indent=2))
        return 0

    corpus = Path(args.corpus)
    if not corpus.is_absolute():
        corpus = REPO_ROOT / corpus
    if not corpus.is_dir():
        print(f"no corpus at {corpus}", file=sys.stderr)
        return 2

    if args.dry_run:
        counts = {"grounded": 0, "ungrounded": 0, "false": 0}
        keys: set[str] = set()
        dup = 0
        for rec in _iter_records(corpus):
            counts[rec["category"]] = counts.get(rec["category"], 0) + 1
            if rec["key"] in keys:
                dup += 1
            keys.add(rec["key"])
        total = sum(counts.values())
        print(json.dumps({
            "dry_run": True,
            "corpus": str(corpus),
            "records": total,
            "by_category": counts,
            "duplicate_keys": dup,
            "would_route": {
                "grounded -> ledger.jsonl": counts.get("grounded", 0),
                "ungrounded+false -> simulated_ledger.jsonl":
                    counts.get("ungrounded", 0) + counts.get("false", 0),
            },
            "store": str(store),
            "mode": args.mode,
        }, indent=2))
        return 0 if dup == 0 else 1

    started = time.time()
    if args.mode == "ledger":
        result = _load_ledger_mode(corpus, store, args.batch_size,
                                   args.retries, args.skip_existing)
    else:
        result = _load_api_mode(corpus, store, args.batch_size,
                                args.retries, args.skip_existing)

    if result.get("status") == "UNAVAILABLE":
        print(json.dumps(result, indent=2))
        return 3

    out = {
        "mode": args.mode,
        "store": str(store),
        "written": result,
        "elapsed_s": round(time.time() - started, 1),
        "store_counts": _count_store(store),
    }

    if args.rebuild:
        os.environ["MEM20_STORE_PATH"] = str(store)
        for p in (str(REPO_ROOT / "mem20api"), str(REPO_ROOT)):
            if p not in sys.path:
                sys.path.insert(0, p)
        try:
            from mem20api import open_store
            with open_store(store) as st:
                out["rebuild"] = st.rebuild("all")
                out["health"] = st.health()
        except Exception as exc:  # noqa: BLE001
            out["rebuild"] = {"status": "UNAVAILABLE", "reason": str(exc)}

    print(json.dumps(out, indent=2))
    return 0 if result.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
