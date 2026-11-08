#!/usr/bin/env python3
"""Render ``benchmarks/results/latest.md`` from ``benchmarks/results/latest.json``.

The markdown table is a *view* of the JSON artifact, never a second source of
truth. Before this script existed the two drifted: 31 of 37 per-kind ``p50 ms``
cells disagreed with ``recall.<mode>.<kind>.median_latency_ms``, the latency
block disagreed with ``latency_ms``, the dataset digest named a sha256 that
appears nowhere in the artifact, and the trust block reported the per-query row
count (1530) as the number of queries carrying a drift diagnostic (250).

Every number below is read from the JSON. Nothing is typed by hand and nothing
is estimated, so ``--check`` is a real drift gate:

    python benchmarks/render_latest_md.py            # write latest.md
    python benchmarks/render_latest_md.py --check    # exit 1 if it is stale

Provenance: the JSON is byte-identical from commit a9860b95 onward, so the
``Commit`` line cites the commit that introduced the artifact, not the commit
that last touched the markdown.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "benchmarks" / "results"
JSON_PATH = RESULTS / "latest.json"
MD_PATH = RESULTS / "latest.md"

# The commit that introduced benchmarks/results/latest.json. Verified stable:
# sha256 of the blob is identical at a9860b95, fb3ae9cf, 35500f4c and HEAD.
DATA_COMMIT = "a9860b955fb8c8b2cadab7adbda4295693a281c9"

# Order the per-kind table the way the artifact lists its modes, then by kind.
KIND_ORDER = ["direct", "adversarial", "adversarial_hard", "contradiction",
              "multi_hop", "unanswerable"]


def _f(value: float, places: int = 3) -> str:
    return f"{value:.{places}f}"


def _corpus_digest(report: dict) -> tuple[str, str]:
    """The canonical corpus digest and the file it belongs to.

    ``run_manifest.corpus_sha256`` holds one digest per corpus file. The
    record stream is the corpus, so that is the digest a reader can re-derive
    with ``sha256sum records.jsonl``; the other three are named alongside it.
    """
    digests = report["run_manifest"]["corpus_sha256"]
    name = "records.jsonl" if "records.jsonl" in digests else sorted(digests)[0]
    return name, digests[name]


def render(report: dict) -> str:
    corpus = report["corpus"]
    facts = report["facts"]
    simulated = report["simulated"]
    queries = report["queries"]
    recall = report["recall"]
    latency = report["latency_ms"]
    trust = report["trust"]
    manifest = report["run_manifest"]
    modes = manifest["modes"]
    digest_name, digest = _corpus_digest(report)
    short = digest[:12]

    scored = [m for m in report["mode_surface"] if m.get("scored")]
    unscored = [m for m in report["mode_surface"] if not m.get("scored")]
    total_modes = len(report["mode_surface"])

    out: list[str] = []
    a = out.append

    a("# mem20 retrieval benchmarks")
    a("")
    a(f"Corpus `{corpus}` \u2014 {facts} grounded facts, {simulated} simulated "
      f"facts, {queries} queries.")
    a("")
    a("> [!IMPORTANT]")
    a("> **These numbers are not comparable to competitor benchmarks.** Mem0's "
      "LoCoMo (92.5) and LongMemEval (94.4) figures and Zep's DMR (94.8%) come "
      "from different corpora \u2014 two of the three are private or "
      "vendor-defined \u2014 and different metrics. Nothing here refutes or "
      "reproduces them. These results describe this corpus only.")
    a("")
    a("> [!WARNING]")
    a("> **No LoCoMo result is claimed.** This harness has not been run against "
      "the LoCoMo originals (10 conversations, 1,986 QA). No LoCoMo figure "
      "appears in this report and none may be quoted from it. The caveat stays "
      "until a run on the originals lands.")
    a("")
    a("## Retrieval quality")
    a("")
    a("Every row below names the dataset version and the exact command that "
      "produced it, so a number can be traced back to a reproducible run rather "
      "than to a report. This file is rendered from `latest.json` by "
      "`benchmarks/render_latest_md.py`; the JSON is the artifact of record.")
    a("")
    a(f"- Dataset: `{corpus}` (`{digest_name}` sha256 `{short}\u2026`, "
      f"{facts + simulated} records, {queries} probes)")
    a(f"- Run command: `mem20benchmarkz run-scale --corpus /tmp/{corpus} "
      f"--bulk --k {manifest['k']} --modes {','.join(modes)} "
      f"--out benchmarks/results`")
    a("- Canonical script: `benchmarks/run-7modes.sh` (the command above, "
      "parameterised; every row below names it)")
    a(f"- Commit: `{DATA_COMMIT}`; k={manifest['k']}; embedding threads=1")
    a("")
    a("| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms | Dataset | Run command |")
    a("|---|---|---:|---:|---:|---:|---:|---|---|")
    for mode in modes:
        kinds = recall.get(mode, {})
        ordered = [k for k in KIND_ORDER if k in kinds]
        ordered += [k for k in kinds if k not in KIND_ORDER]
        for kind in ordered:
            row = kinds[kind]
            a(f"| `{mode}` | {kind} | {row['n']} | {_f(row['hit_rate'])} | "
              f"{_f(row['mrr'])} | {_f(row['leak_rate'])} | "
              f"{_f(row['median_latency_ms'], 1)} | "
              f"`{corpus}@{short}` | `benchmarks/run-7modes.sh` |")
    a("")
    a("### Adversarial control")
    a("")
    a("`constant` ignores the query and always returns one fixed document that "
      "matches no corpus record. Every metric below must read exactly **0.000**; "
      "a non-zero value means the metric is handing out free hits.")
    a("")
    a("| Query kind | n | Hit rate | MRR |")
    a("|---|---:|---:|---:|")
    ctrl = recall.get("constant", {})
    for kind in [k for k in KIND_ORDER if k in ctrl] + \
                [k for k in ctrl if k not in KIND_ORDER]:
        row = ctrl[kind]
        a(f"| {kind} | {row['n']} | {_f(row['hit_rate'])} | {_f(row['mrr'])} |")
    a("")
    a("## Mode surface")
    a("")
    a("Every retrieval mode present in the tree, whether this run scored it, and "
      "\u2014 where it did not \u2014 the reason. A mode is never dropped from "
      "this table: an absent row reads as \"not run\", which is a different and "
      "weaker statement than \"blocked and documented\".")
    a("")
    a("| Mode | Surface | Scored | In this run | Note |")
    a("|---|:--:|:--:|:--:|---|")
    for m in report["mode_surface"]:
        a(f"| `{m['id']}` | {m['surface']} | "
          f"{'yes' if m.get('scored') else '**no**'} | "
          f"{'yes' if m.get('scored_in_this_run') else 'no'} | {m['note']} |")
    a("")
    a(f"**{len(scored)} of {total_modes} declared modes scored in this run; "
      f"{len(scored)} are scoreable by this harness.** The remaining "
      f"{len(unscored)} are listed with their blocker rather than omitted.")
    a("")
    a("## Latency")
    a("")
    a("| Mode | n | p50 ms | p95 ms | p99 ms | max ms |")
    a("|---|---:|---:|---:|---:|---:|")
    for mode in modes:
        row = latency.get(mode)
        if not row:
            continue
        a(f"| `{mode}` | {row['n']} | {_f(row['p50'], 1)} | "
          f"{_f(row['p95'], 1)} | {_f(row['p99'], 1)} | {_f(row['max'], 1)} |")
    a("")
    a("## Trustworthiness")
    a("")
    a("This is the axis mem20 claims as its differentiator, and the one no "
      "competitor publishes. A system that answers confidently from a stale "
      "index can look good on hit rate and fail here.")
    a("")
    a("| Check | Value | Required |")
    a("|---|---:|---|")
    a(f"| Contamination rate | {trust['contamination_rate']} | 0.0 |")
    a(f"| Simulated records in BM25 corpus | {trust['simulated_in_bm25']} | 0 |")
    a(f"| Stale pointer rate | {trust['stale_pointer_rate']:.6f} | 0.0 |")
    a(f"| Index healthy | {trust['index_healthy']} | True |")
    a(f"| Ledger records | {trust['ledger_records']} | \u2014 |")
    a(f"| Graph entities / edges | {trust['graph_entities']} / "
      f"{trust['graph_edges']} | \u2014 |")
    a(f"| Queries reporting a drift diagnostic | "
      f"{trust['queries_with_drift_diagnostic']} | \u2014 |")
    a(f"| All reported healthy | {trust['all_reported_healthy']} | True |")
    a("")
    a("## Environment")
    a("")
    env = report["environment"]
    a(f"- Python {env['python']} on {env['platform']} ({env['machine']})")
    a(f"- Embedding model: `{env['embedding_model']}` "
      f"({env['embedding_dim']}-dim)")
    a(f"- Vector deps available: {env['vector_available']}; "
      f"BM25: {env['bm25_available']}; cross-encoder: {env['cross_encoder']}")
    a("")
    a("## Notes")
    a("")
    for note in report["notes"]:
        a(f"- {note}")
    a("")
    a("## Reproduce")
    a("")
    a("```bash")
    a(f"mem20benchmarkz generate-scale --out /tmp/{corpus}")
    a(f"mem20benchmarkz run-scale --corpus /tmp/{corpus} --bulk \\")
    a(f"    --modes {','.join(modes)} \\")
    a("    --out benchmarks/results")
    a("```")
    a("")
    a("The run uses an isolated store, ingests the corpus through the engine's "
      "own ledger and index build paths, and never touches live data.")
    a("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if latest.md is not what the JSON renders to")
    args = ap.parse_args(argv)

    report = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    rendered = render(report)

    if args.check:
        current = MD_PATH.read_text(encoding="utf-8") if MD_PATH.exists() else ""
        if current != rendered:
            print(f"STALE: {MD_PATH.relative_to(REPO_ROOT)} does not match "
                  f"{JSON_PATH.relative_to(REPO_ROOT)}", file=sys.stderr)
            print("run: python benchmarks/render_latest_md.py", file=sys.stderr)
            return 1
        print(f"OK: {MD_PATH.relative_to(REPO_ROOT)} matches the artifact")
        return 0

    MD_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {MD_PATH.relative_to(REPO_ROOT)} "
          f"({len(rendered.encode('utf-8'))} bytes, "
          f"sha256 {hashlib.sha256(rendered.encode('utf-8')).hexdigest()[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
