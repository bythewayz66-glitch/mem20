#!/usr/bin/env python3
"""Render the benchmark results tables in this directory from a committed artifact.

Every published number in docs/benchmarks/README.md is emitted by this script from
`benchmarks/results/latest.json`. Nothing is hand-typed and nothing is estimated:
if a value is absent from the artifact, this script prints `not yet measured`
instead of inventing a number.

Usage
-----
    python docs/benchmarks/render.py            # rewrite table regions in README.md
    python docs/benchmarks/render.py --check    # exit 1 if README.md is stale
    python docs/benchmarks/render.py --stdout   # print the regions, write nothing
    python docs/benchmarks/render.py --snapshot # also write results-v1.json

Only the standard library is used, and the only input is the artifact itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "benchmarks" / "results" / "latest.json"
README = Path(__file__).resolve().parent / "README.md"
SNAPSHOT = Path(__file__).resolve().parent / "results-v1.json"

NOT_MEASURED = "not yet measured"

# The order the tables are presented in: strongest-evidence source first.
REGIONS = ("aggregate", "recall", "latency", "trust", "rerank")


def load_artifact() -> dict:
    with ARTIFACT.open(encoding="utf-8") as fh:
        return json.load(fh)


def git(*args: str) -> str | None:
    """Best-effort git lookup; None when git or history is unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def provenance() -> dict:
    """Where the artifact came from, read from git rather than asserted by hand."""
    rel = "benchmarks/results/latest.json"
    commit = git("log", "-1", "--format=%H", "--", rel)
    subject = git("log", "-1", "--format=%s", "--", rel)
    authored = git("log", "-1", "--format=%aI", "--", rel)
    blob = git("rev-parse", f"HEAD:{rel}")
    head = git("rev-parse", "HEAD")
    head_subject = git("log", "-1", "--format=%s")
    return {
        "artifact": rel,
        "introduced_by_commit": commit,
        "commit_subject": subject,
        "committed_at": authored,
        "artifact_blob_sha": blob,
        "observed_at_head": head,
        "head_subject": head_subject,
    }


def fmt(value, digits: int = 3) -> str:
    if value is None:
        return NOT_MEASURED
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_aggregate(d: dict) -> str:
    """Per-mode totals. Means are n-weighted across query kinds; the formula is stated."""
    recall = d.get("recall") or {}
    latency = d.get("latency_ms") or {}
    modes = sorted(recall)
    if not modes:
        return "_No mode blocks present in the artifact._\n"

    lines = [
        "| Mode | Queries (n) | Query kinds | Hit rate | MRR | Leak rate | p50 ms | p95 ms |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for mode in modes:
        kinds = recall[mode]
        n = sum(block.get("n", 0) for block in kinds.values())
        if n:
            hit = sum(b.get("hit_rate", 0.0) * b.get("n", 0) for b in kinds.values()) / n
            mrr = sum(b.get("mrr", 0.0) * b.get("n", 0) for b in kinds.values()) / n
            leak = sum(b.get("leak_rate", 0.0) * b.get("n", 0) for b in kinds.values()) / n
        else:
            hit = mrr = leak = None
        lat = latency.get(mode) or {}
        lines.append(
            f"| `{mode}` | {n} | {', '.join(sorted(kinds))} | {fmt(hit)} | {fmt(mrr)} | "
            f"{fmt(leak)} | {fmt(lat.get('p50'), 1)} | {fmt(lat.get('p95'), 1)} |"
        )

    lines.append("")
    lines.append(
        "Means are n-weighted across that mode's query kinds "
        "(`sum(rate x n) / sum(n)`), so a 5-query kind is not outweighed by a 2-query kind. "
        "Latency is reported as stored in the artifact, not re-averaged. "
        "`graph` covers only multi-hop queries and therefore carries a smaller n than the other modes."
    )
    return "\n".join(lines) + "\n"


def render_recall(d: dict) -> str:
    """Per mode x query-kind table, straight from the artifact."""
    recall = d.get("recall") or {}
    modes = sorted(recall)
    if not modes:
        return "_No recall blocks present in the artifact._\n"

    lines = [
        "| Mode | Query kind | n | Hit rate | MRR | Leak rate | median latency ms |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for mode in modes:
        for kind in sorted(recall[mode]):
            b = recall[mode][kind]
            lines.append(
                f"| `{mode}` | {kind} | {b.get('n', 0)} | {fmt(b.get('hit_rate'))} | "
                f"{fmt(b.get('mrr'))} | {fmt(b.get('leak_rate'))} | "
                f"{fmt(b.get('median_latency_ms'), 2)} |"
            )
    return "\n".join(lines) + "\n"


def render_latency(d: dict) -> str:
    latency = d.get("latency_ms") or {}
    if not latency:
        return "_No latency block present in the artifact._\n"
    lines = [
        "| Mode | n | p50 ms | p95 ms | p99 ms | max ms | mean ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in sorted(latency):
        m = latency[mode]
        lines.append(
            f"| `{mode}` | {m.get('n', 0)} | {fmt(m.get('p50'), 1)} | {fmt(m.get('p95'), 1)} | "
            f"{fmt(m.get('p99'), 1)} | {fmt(m.get('max'), 1)} | {fmt(m.get('mean'), 1)} |"
        )
    return "\n".join(lines) + "\n"


def render_trust(d: dict) -> str:
    t = d.get("trust") or {}
    if not t:
        return "_No trust block present in the artifact._\n"

    rows = [
        ("Contamination rate", t.get("contamination_rate"), "0.0", 3),
        ("Contamination violations", t.get("contamination_violations"), "0", None),
        ("Simulated records reachable from BM25", t.get("simulated_in_bm25"), "[]", None),
        ("Stale pointer rate", t.get("stale_pointer_rate"), "0.0", 6),
        ("Stale pointers", t.get("stale_pointers"), "0", None),
        ("Indexed entries", t.get("indexed_entries"), "—", None),
        ("Index healthy", t.get("index_healthy"), "True", None),
        ("Ledger records", t.get("ledger_records"), "—", None),
        ("Graph entities / edges", f"{t.get('graph_entities')} / {t.get('graph_edges')}", "—", None),
        ("Queries degraded to a fallback", t.get("degraded_queries"), "—", None),
        ("Queries reporting a drift diagnostic", t.get("queries_with_drift_diagnostic"), "—", None),
        ("All queries reported healthy", t.get("all_reported_healthy"), "True", None),
    ]

    lines = ["| Check | Observed | Required |", "|---|---:|---|"]
    for label, observed, required, digits in rows:
        if observed is None:
            rendered = NOT_MEASURED
        elif digits is None:
            rendered = str(observed)
        else:
            rendered = fmt(observed, digits)
        lines.append(f"| {label} | {rendered} | {required} |")
    return "\n".join(lines) + "\n"


def render_rerank(d: dict) -> str:
    cmp = (d.get("trust") or {}).get("rerank_off_comparison")
    if not cmp:
        return "_Rerank on/off comparison " + NOT_MEASURED + " in this artifact._\n"

    lines = [
        "| Setting | p50 ms | direct MRR | multi-hop MRR | direct hit rate | multi-hop hit rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, key in (("`MEM20_RERANK=1` (default)", "with"), ("`MEM20_RERANK=0`", "without")):
        c = cmp.get(key) or {}
        lines.append(
            f"| {label} | {fmt(c.get('p50_ms'), 1)} | {fmt(c.get('mrr_direct'))} | "
            f"{fmt(c.get('mrr_multi_hop'))} | {fmt(c.get('hit_direct'))} | "
            f"{fmt(c.get('hit_multi_hop'))} |"
        )
    return "\n".join(lines) + "\n"


RENDERERS = {
    "aggregate": render_aggregate,
    "recall": render_recall,
    "latency": render_latency,
    "trust": render_trust,
    "rerank": render_rerank,
}


def splice(text: str, name: str, body: str) -> str:
    begin = f"<!-- BEGIN:{name} -->"
    end = f"<!-- END:{name} -->"
    if begin not in text or end not in text:
        raise SystemExit(f"README.md is missing the {begin} … {end} markers")
    head, rest = text.split(begin, 1)
    _, tail = rest.split(end, 1)
    return f"{head}{begin}\n<!-- Generated by render.py from benchmarks/results/latest.json. Do not edit by hand. -->\n\n{body}{end}{tail}"


def build(text: str, d: dict) -> str:
    for name in REGIONS:
        text = splice(text, name, RENDERERS[name](d))
    return text


def snapshot(d: dict) -> dict:
    """Machine-readable copy: same numbers, plus provenance and explicit gaps."""
    prov = provenance()
    recall = d.get("recall") or {}
    modes = {}
    for mode, kinds in sorted(recall.items()):
        n = sum(b.get("n", 0) for b in kinds.values())
        modes[mode] = {
            "n": n,
            "query_kinds": sorted(kinds),
            "n_weighted": {
                "hit_rate": round(sum(b["hit_rate"] * b["n"] for b in kinds.values()) / n, 6) if n else None,
                "mrr": round(sum(b["mrr"] * b["n"] for b in kinds.values()) / n, 6) if n else None,
                "leak_rate": round(sum(b["leak_rate"] * b["n"] for b in kinds.values()) / n, 6) if n else None,
            },
            "per_kind": kinds,
            "latency_ms": (d.get("latency_ms") or {}).get(mode),
        }
    return {
        "schema": "mem20.docs.benchmarks.v1",
        "generated_by": "docs/benchmarks/render.py",
        "corpus": d.get("corpus"),
        "corpus_size": {
            "facts": d.get("facts"),
            "simulated": d.get("simulated"),
            "queries": d.get("queries"),
        },
        "provenance": prov,
        "environment": d.get("environment"),
        "modes_measured": sorted(recall),
        "modes_not_yet_measured": [
            "recall()",
            "recall_at()",
            "entities()",
            "ledger()",
        ],
        "modes": modes,
        "trust": d.get("trust"),
        "notes": d.get("notes", []),
    }


def verify(d: dict) -> list[str]:
    """Recompute every aggregate from the raw per_query rows and compare.

    The summary blocks in the artifact and its per-query rows are two independent
    encodings of the same run. If they disagree, one of them is wrong and none of
    the numbers here can be published. Returns a list of disagreements (empty = ok).
    """
    rows = d.get("per_query") or []
    recall = d.get("recall") or {}
    problems: list[str] = []

    if not rows:
        return ["artifact has no per_query rows; cannot verify aggregates"]

    if d.get("queries") is not None and d["queries"] != len({r.get("qid") for r in rows}):
        problems.append(
            f"declared queries={d['queries']} but per_query holds "
            f"{len({r.get('qid') for r in rows})} distinct qids"
        )

    for mode in sorted(recall):
        mrows = [r for r in rows if r.get("mode") == mode]
        if not mrows:
            problems.append(f"{mode}: present in recall block but absent from per_query")
            continue
        n = len(mrows)
        hit = sum(1 for r in mrows if r.get("hit")) / n
        mrr = sum(1.0 / r["rank"] for r in mrows if r.get("hit") and r.get("rank")) / n
        leak = sum(1 for r in mrows if r.get("leaked")) / n

        n_art = sum(b.get("n", 0) for b in recall[mode].values())
        if n != n_art:
            problems.append(f"{mode}: per_query n={n} but recall block n={n_art}")
            continue
        for label, mine, theirs in (
            ("hit_rate", hit, sum(b.get("hit_rate", 0.0) * b["n"] for b in recall[mode].values()) / n),
            ("mrr", mrr, sum(b.get("mrr", 0.0) * b["n"] for b in recall[mode].values()) / n),
            ("leak_rate", leak, sum(b.get("leak_rate", 0.0) * b["n"] for b in recall[mode].values()) / n),
        ):
            if abs(mine - theirs) > 1e-6:
                problems.append(f"{mode}.{label}: per_query={mine:.6f} vs block={theirs:.6f}")

    for mode in sorted({r.get("mode") for r in rows} - set(recall)):
        problems.append(f"{mode}: scored in per_query but missing from recall block")

    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="verify README.md matches the artifact")
    ap.add_argument("--stdout", action="store_true", help="print regions instead of writing")
    ap.add_argument("--snapshot", action="store_true", help="also write results-v1.json")
    ap.add_argument("--verify", action="store_true", help="recompute aggregates from per_query rows")
    args = ap.parse_args(argv)

    if not ARTIFACT.exists():
        print(f"missing artifact: {ARTIFACT.relative_to(REPO_ROOT)}", file=sys.stderr)
        print(
            "Refusing to render. Run `mem20benchmarkz run --out benchmarks/results` "
            "on the commit being reported, then re-run this script.",
            file=sys.stderr,
        )
        return 2

    d = load_artifact()

    problems = verify(d)
    if problems:
        print("artifact failed self-verification:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("Refusing to publish. Fix the artifact or the run, not this table.", file=sys.stderr)
        return 3

    if args.verify:
        modes = sorted((d.get("recall") or {}))
        n_rows = len(d.get("per_query") or [])
        print(f"ok: {len(modes)} modes recomputed from {n_rows} per_query rows")
        for mode in modes:
            mrows = [r for r in d["per_query"] if r.get("mode") == mode]
            hits = sum(1 for r in mrows if r.get("hit"))
            print(f"  {mode:9s} n={len(mrows):2d} hit={hits / len(mrows):.3f}")
        return 0

    original = README.read_text(encoding="utf-8")
    rendered = build(original, d)

    if args.stdout:
        for name in REGIONS:
            print(f"===== {name} =====")
            print(RENDERERS[name](d))
        return 0

    if args.check:
        if rendered != original:
            print("README.md is stale against benchmarks/results/latest.json", file=sys.stderr)
            print("run: python docs/benchmarks/render.py", file=sys.stderr)
            return 1
        print("README.md matches benchmarks/results/latest.json")
    else:
        README.write_text(rendered, encoding="utf-8")
        print(f"rendered {README.relative_to(REPO_ROOT)} from {ARTIFACT.relative_to(REPO_ROOT)}")

    if args.snapshot:
        SNAPSHOT.write_text(
            json.dumps(snapshot(d), indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
        print(f"wrote {SNAPSHOT.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
