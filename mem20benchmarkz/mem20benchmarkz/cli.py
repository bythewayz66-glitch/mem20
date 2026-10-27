"""CLI for mem20benchmarkz.

    mem20benchmarkz run --out benchmarks/results
    mem20benchmarkz drift --out benchmarks/results
    mem20benchmarkz render benchmarks/results

    # Scale corpus (mem20-scale-corpus-v2: 2000 records, 250 probes)
    mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
    mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2
    mem20benchmarkz ingest-scale --corpus /tmp/mem20-scale-corpus-v2 \\
        --store /tmp/mem20-scale-store --bulk
    mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \\
        --modes keyword,semantic --out benchmarks/results
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (str(_REPO_ROOT / "mem20api"), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from .bench import Report, render_markdown, run, save  # noqa: E402
from .bulk_ingest import ingest as bulk_ingest, verify as bulk_verify  # noqa: E402
from .corpus import load  # noqa: E402
from .scale_corpus import (  # noqa: E402
    build_scale_corpus,
    load_jsonl_corpus,
    validate as validate_corpus,
    write_scale_corpus,
)


def _seed(store, corpus) -> None:
    """Write the corpus through the real write path."""
    for f in corpus.facts:
        store.remember(
            f.topic,
            f.content,
            tags=list(f.tags),
            priority=f.priority,
            epistemic_status=f.epistemic_status,
        )
    for f in corpus.simulated:
        store.remember_simulated(
            f.topic,
            f.content,
            scenario="benchmark adversarial probe",
            sim_type="counterfactual",
        )


def _trust_exit(report: Report) -> int:
    t = report.trust
    bad = []
    if t.get("contamination_rate") != 0.0:
        bad.append(f"contamination_rate={t.get('contamination_rate')}")
    if t.get("stale_pointer_rate") not in (0.0, 0, None):
        # allow missing key on older reports
        if t.get("stale_pointer_rate") not in (0.0, 0):
            bad.append(f"stale_pointer_rate={t.get('stale_pointer_rate')}")
    for mode, kinds in (report.recall or {}).items():
        for kind, m in kinds.items():
            # Every kind that carries a leak column must be clean. Checking only
            # `adversarial` let a regression in adversarial_hard or contradiction
            # pass as long as the plain class stayed clean.
            if "leak_rate" in m and kind != "direct" and m["leak_rate"] != 0.0:
                bad.append(f"{mode}/{kind} leaked {m['leak_rate']} of queries")
    if bad:
        print("\nFAILED TRUST CHECKS:", file=sys.stderr)
        for b in bad:
            print(f"  - {b}", file=sys.stderr)
        return 1
    print("\nall trust checks passed", file=sys.stderr)
    return 0


def cmd_run(args) -> int:
    from mem20api import open_store

    corpus = load()
    tmp = tempfile.mkdtemp(prefix="mem20-bench-")
    print(f"isolated store: {tmp}", file=sys.stderr)

    with open_store(tmp) as store:
        _seed(store, corpus)
        h = store.health()
        if not h["healthy"]:
            print(
                "ERROR: freshly seeded store is unhealthy; not publishing "
                "numbers from a broken index",
                file=sys.stderr,
            )
            print(json.dumps(h, indent=2, default=str), file=sys.stderr)
            return 2

        report = run(
            store,
            k=args.k,
            corpus=corpus,
            compare_rerank=not args.no_rerank_compare,
        )

    paths = save(report, args.out)
    print(render_markdown(report))
    print(f"\nwrote {paths['json']}", file=sys.stderr)
    print(f"wrote {paths['markdown']}", file=sys.stderr)
    return _trust_exit(report)


def cmd_drift(args) -> int:
    from mem20api import open_store

    corpus = load()
    tmp = tempfile.mkdtemp(prefix="mem20-drift-")
    with open_store(tmp) as store:
        _seed(store, corpus)
        before = store.health()
        print("baseline healthy:", before["healthy"])

        ledger = Path(tmp) / "ledger.jsonl"
        lines = ledger.read_text().splitlines()
        ledger.write_text("\n".join(lines[: len(lines) // 2]) + "\n")

        after = store.health()
        print("after truncation healthy:", after["healthy"])
        v = after["indexes"]["vector"]
        print(f"  stale pointers: {v['missing_from_ledger']} of {v['indexed']}")

        r = store.semantic("what build is prod on", k=3)
        print("  semantic healthy flag:", r["healthy"])
        print("  reported:", json.dumps(r["diagnostic"], default=str))

        ok = (
            after["healthy"] is False
            and v["missing_from_ledger"] > 0
            and r["healthy"] is False
        )
        print("\ndrift detection:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


def cmd_render(args) -> int:
    src = Path(args.dir) / "latest.json"
    if not src.is_file():
        print(f"no results at {src}; run mem20benchmarkz run first", file=sys.stderr)
        return 2
    data = json.loads(src.read_text())
    r = Report(**{k: v for k, v in data.items()})
    md = render_markdown(r)
    out = Path(args.dir) / "latest.md"
    out.write_text(md)
    print(f"wrote {out}")
    return 0


def cmd_generate_scale(args) -> int:
    out = write_scale_corpus(args.out, n_facts=args.facts)
    man = json.loads((out / "manifest.json").read_text())
    val = json.loads((out / "validation.json").read_text())
    print(json.dumps(man, indent=2))
    print(f"\nvalidation: {val['status']} "
          f"({val['error_count']} errors, "
          f"{val['answerable_probes_checked']} answerable probes checked)",
          file=sys.stderr)
    for e in val["errors"]:
        print(f"  - {e}", file=sys.stderr)
    print(f"wrote corpus under {out}", file=sys.stderr)
    # Non-zero on failure. Printing the manifest and returning 0 regardless
    # would let a corpus the validator rejected land in a pipeline as success.
    return 0 if val["status"] == "PASS" else 1


def cmd_validate_scale(args) -> int:
    """Re-validate a corpus on disk.

    This exists so a generated corpus can be checked without re-generating it,
    and so CI can fail on an answer-free probe instead of shipping one.
    """
    corpus = load_jsonl_corpus(args.corpus)
    report = validate_corpus(corpus)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


def cmd_ingest_scale(args) -> int:
    from mem20api import open_store

    corpus_dir = Path(args.corpus)
    if not (corpus_dir / "grounded.jsonl").is_file():
        print(f"missing grounded.jsonl in {corpus_dir}; run generate-scale first", file=sys.stderr)
        return 2
    corpus = load_jsonl_corpus(corpus_dir)
    store_path = Path(args.store)
    store_path.mkdir(parents=True, exist_ok=True)
    print(
        f"ingesting {len(corpus.facts)} facts + {len(corpus.simulated)} simulated -> {store_path}",
        file=sys.stderr,
    )
    if args.bulk:
        stats = bulk_ingest(corpus_dir, store_path, progress=args.progress)
        check = bulk_verify(store_path)
        print(json.dumps({"ingest": stats, "verify": check}, indent=2), flush=True)
        if check["vector_indexed"] != len(corpus.facts):
            print(f"ERROR: indexed {check['vector_indexed']} of "
                  f"{len(corpus.facts)} grounded records", file=sys.stderr)
            return 2
        print("ingest ok (bulk)", file=sys.stderr)
        return 0

    with open_store(str(store_path)) as store:
        n = 0
        for f in corpus.facts:
            store.remember(
                f.topic,
                f.content,
                tags=list(f.tags),
                priority=f.priority,
                epistemic_status=f.epistemic_status,
            )
            n += 1
            if args.progress and n % 200 == 0:
                print(f"  ... {n}/{len(corpus.facts)}", file=sys.stderr)
        for f in corpus.simulated:
            store.remember_simulated(
                f.topic,
                f.content,
                scenario="scale corpus adversarial",
                sim_type="counterfactual",
            )
        h = store.health()
        c = store.contamination()
        print(json.dumps({"health": h, "contamination": c}, indent=2, default=str))
        if not h.get("healthy"):
            print("ERROR: store unhealthy after ingest", file=sys.stderr)
            return 2
        rate = c.get("contamination_rate", c.get("rate"))
        if rate not in (0.0, 0, None) and rate != 0.0:
            print(f"ERROR: contamination_rate={rate}", file=sys.stderr)
            return 1
    print("ingest ok", file=sys.stderr)
    return 0


def cmd_run_scale(args) -> int:
    from mem20api import open_store

    if args.corpus:
        corpus = load_jsonl_corpus(args.corpus)
    else:
        corpus = build_scale_corpus(n_facts=args.facts)
        print(
            f"in-memory {corpus.name}: {len(corpus.facts)} facts, "
            f"{len(corpus.queries)} queries",
            file=sys.stderr,
        )

    if args.store:
        store_path = args.store
        seed = False
        print(f"using existing store {store_path}", file=sys.stderr)
    else:
        store_path = tempfile.mkdtemp(prefix="mem20-scale-")
        seed = True
        print(f"isolated scale store: {store_path}", file=sys.stderr)

    if seed and args.bulk:
        # Per-record remember() encodes one sentence at a time (~0.5s/record
        # measured). Bulk writes the same ledger envelopes and builds each
        # index in one batched pass, then the store is opened normally below.
        corpus_dir = args.corpus or write_scale_corpus(
            Path(store_path) / "corpus", n_facts=args.facts)
        stats = bulk_ingest(corpus_dir, store_path)
        print(json.dumps(stats, indent=2), file=sys.stderr)
        seed = False

    with open_store(store_path) as store:
        if seed:
            _seed(store, corpus)
        h = store.health()
        if not h["healthy"]:
            print("ERROR: store unhealthy; refusing to score", file=sys.stderr)
            print(json.dumps(h, indent=2, default=str), file=sys.stderr)
            return 2
        report = run(
            store,
            k=args.k,
            corpus=corpus,
            compare_rerank=not args.no_rerank_compare,
            modes=tuple(args.modes.split(",")) if args.modes
            else ("keyword", "semantic", "hybrid"),
        )

    paths = save(report, args.out)
    print(render_markdown(report))
    print(f"\nwrote {paths['json']}", file=sys.stderr)
    print(f"wrote {paths['markdown']}", file=sys.stderr)
    return _trust_exit(report)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="mem20benchmarkz",
        description="mem20 retrieval benchmarks: quality, latency, trustworthiness.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="full suite on isolated store (14-fact regression corpus)")
    r.add_argument("--out", default="benchmarks/results")
    r.add_argument("-k", type=int, default=5)
    r.add_argument("--no-rerank-compare", action="store_true")

    d = sub.add_parser("drift", help="prove index-drift diagnostics under induced failure")
    d.add_argument("--out", default="benchmarks/results")

    n = sub.add_parser("render", help="re-render markdown from latest.json")
    n.add_argument("dir", nargs="?", default="benchmarks/results")

    g = sub.add_parser("generate-scale",
                       help="write mem20-scale-corpus-v2 JSONL (2000 records)")
    g.add_argument("--out", default="benchmarks/corpora/mem20-scale-corpus-v2")
    g.add_argument("--facts", type=int, default=None,
                   help="cap grounded records (smoke runs); default builds the full set")

    ing = sub.add_parser("ingest-scale", help="seed a store from a scale corpus directory")
    ing.add_argument("--corpus", required=True, help="directory with grounded.jsonl")
    ing.add_argument("--store", required=True, help="target store path")
    ing.add_argument("--progress", action="store_true")
    ing.add_argument("--bulk", action="store_true",
                     help="append ledgers + build indexes once (~40x faster)")

    vs = sub.add_parser("validate-scale", help="re-validate a corpus directory on disk")
    vs.add_argument("corpus", help="directory written by generate-scale")

    rs = sub.add_parser("run-scale", help="run suite on mem20-scale-corpus-v2")
    rs.add_argument("--out", default="benchmarks/results-scale")
    rs.add_argument("-k", type=int, default=5)
    rs.add_argument("--no-rerank-compare", action="store_true")
    rs.add_argument("--corpus", default=None, help="JSONL dir from generate-scale")
    rs.add_argument("--store", default=None, help="existing store; if omitted, temp + seed")
    rs.add_argument("--facts", type=int, default=None,
                   help="when no --corpus, cap grounded records")
    rs.add_argument("--bulk", action="store_true",
                   help="bulk-ingest into a fresh store instead of per-record remember()")
    rs.add_argument(
        "--modes",
        default="keyword,semantic,hybrid",
        help="comma list; default skips graph for speed at scale",
    )

    args = p.parse_args(argv)
    return {
        "run": cmd_run,
        "drift": cmd_drift,
        "render": cmd_render,
        "generate-scale": cmd_generate_scale,
        "validate-scale": cmd_validate_scale,
        "ingest-scale": cmd_ingest_scale,
        "run-scale": cmd_run_scale,
    }[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
