#!/usr/bin/env python3
"""Score the v3 probe set against a loaded mem20 store.

Reports hit@1 / hit@5 / hit@10 and MRR at the *evidence* level: did the store
return the record that actually holds the answer. Also reports the
``unanswerable`` control, which must score exactly 0.000 — a non-zero control
means the metric is handing out free hits.

    python benchmarks/v3/score_probes_v3.py benchmarks/corpora/v3 \
        --store /tmp/mem20-v3-store --limit 100
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_probes(corpus: Path, limit: int | None) -> list[dict]:
    path = corpus / "probes.jsonl"
    probes = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                probes.append(json.loads(line))
    if limit:
        # Keep the control class represented when subsampling.
        controls = [p for p in probes if p["kind"] == "unanswerable"]
        rest = [p for p in probes if p["kind"] != "unanswerable"]
        keep = max(1, limit - min(len(controls), max(1, limit // 5)))
        return rest[:keep] + controls[: max(1, limit // 5)]
    return probes


def _control_subject(text: str) -> str:
    """The fictional entity a control probe asks about.

    Control probes read "What is the <policy> of <Org A> <Org B> in <City>?".
    The subject is the two-word organisation name; if any returned record
    mentions it, the store answered a question about an entity that does not
    exist, which is a false positive.
    """
    m = re.search(r"of (.+?) in ", text)
    return m.group(1).lower() if m else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("corpus", nargs="?", default="benchmarks/corpora/v3")
    ap.add_argument("--store", default="/tmp/mem20-v3-store")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    corpus = Path(args.corpus)
    if not corpus.is_absolute():
        corpus = REPO_ROOT / corpus

    os.environ["MEM20_STORE_PATH"] = str(args.store)
    for p in (str(REPO_ROOT / "mem20api"), str(REPO_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    from mem20api import open_store

    probes = _load_probes(corpus, args.limit)
    by_kind: dict[str, dict] = {}
    started = time.time()

    with open_store(args.store) as st:
        for i, q in enumerate(probes, start=1):
            res = st.hybrid(q["text"], k=args.k, alpha=0.0)
            hits = res.get("hits") or []
            kind = q["kind"]
            agg = by_kind.setdefault(kind, {
                "n": 0, "hit@1": 0, "hit@5": 0, "hit@10": 0, "rr": 0.0})

            if kind == "unanswerable":
                # Control: no record can answer it. BM25 always returns k rows
                # regardless of relevance, so "any hit" is not a false positive
                # — the honest test is whether any returned record is actually
                # ABOUT the queried subject. A non-zero rate here means the
                # metric is handing out free hits.
                agg["n"] += 1
                subject = _control_subject(q["text"])
                if subject and any(
                        subject in (h.get("content") or "").lower()
                        for h in hits):
                    agg["hit@1"] += 1
                continue

            expect = [e.lower() for e in q["expect"]]
            rank = None
            for pos, h in enumerate(hits, start=1):
                content = (h.get("content") or "").lower()
                if any(e in content for e in expect):
                    rank = pos
                    break
            agg["n"] += 1
            if rank == 1:
                agg["hit@1"] += 1
            if rank and rank <= 5:
                agg["hit@5"] += 1
            if rank and rank <= 10:
                agg["hit@10"] += 1
            if rank:
                agg["rr"] += 1.0 / rank
            if i % 25 == 0:
                print(f"  {i}/{len(probes)} probes...", flush=True)

    out = {"store": str(args.store), "k": args.k, "probes": len(probes),
           "elapsed_s": round(time.time() - started, 1), "by_kind": {}}
    for kind, agg in by_kind.items():
        n = agg["n"] or 1
        out["by_kind"][kind] = {
            "n": agg["n"],
            "hit@1": round(agg["hit@1"] / n, 4),
            "hit@5": round(agg["hit@5"] / n, 4),
            "hit@10": round(agg["hit@10"] / n, 4),
            "mrr": round(agg["rr"] / n, 4),
        }
    text = json.dumps(out, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
