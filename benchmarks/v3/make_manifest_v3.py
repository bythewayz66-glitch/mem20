#!/usr/bin/env python3
"""Build the v3 corpus manifest: counts, bytes, schema, checksums.

Run this LAST, after every deliverable file exists. A manifest written before
a file is regenerated records a sha256 that no longer matches what ships.

    python benchmarks/v3/make_manifest_v3.py benchmarks/corpora/v3
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA = {
    "format": "JSONL, one JSON object per line, UTF-8, no BOM",
    "record": {
        "id": "stable unique id, prefix g/u/f + 7-digit ordinal",
        "key": "stable unique key, human-readable, category-prefixed",
        "category": "grounded | ungrounded | false",
        "family": "source family (element, country, mime, city, codepoint, "
                  "countrymeta, fiction) or <family>-dossier",
        "topic": "mem20 topic, bench.v3.<family>",
        "content": "the fact text, one or two sentences",
        "tags": "list; includes family, category, bench-v3",
        "epistemic_status": "mem20 vocabulary: observed | imagined | "
                            "agent_generated",
        "subject": "the entity the fact is about",
        "predicate": "the relation asserted",
        "object": "the value asserted (for false records: the WRONG value)",
        "confidence": "1.0 grounded, 0.4 ungrounded, 0.2 false",
        "source": "grounded only: the URL the value was transcribed from",
        "evidence": "grounded only: the verbatim source fields",
        "contradicts": "false only: the grounded key this claim denies",
        "true_value": "false only: the value that grounded key actually holds",
        "difficulty": "easy | medium | hard | control",
        "timestamp": "deterministic ISO-8601 instant derived from the key",
        "schema_version": "mem20-bench-v3",
        "provenance": "generator, seed, retrieval date, source URL",
    },
    "probe": {
        "qid": "unique probe id",
        "kind": "direct | adversarial | contradiction | unanswerable",
        "text": "the query",
        "expect": "list of literal substrings that prove the answer",
        "gold_key": "the record that holds the answer (null for controls)",
        "difficulty": "easy | medium | hard | control",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("corpus", nargs="?", default="benchmarks/corpora/v3")
    args = ap.parse_args(argv)

    corpus = Path(args.corpus)
    if not corpus.is_absolute():
        corpus = REPO_ROOT / corpus

    base = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))

    files = []
    for path in sorted(corpus.iterdir()):
        if path.name == "manifest.json" or not path.is_file():
            continue
        files.append({
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })

    # Reference cache hashes: a corpus generated from an uncommitted cache is
    # only reproducible for that exact cache, so pin the inputs too.
    ref_dir = REPO_ROOT / "reference" / "v3"
    references = []
    for path in sorted(ref_dir.iterdir()):
        if path.is_file():
            references.append({
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })

    out = {
        "name": base["name"],
        "schema_version": base["schema_version"],
        "seed": base["seed"],
        "records": base["records"],
        "by_category": base["by_category"],
        "by_family": base["by_family"],
        "probes": base["probes"],
        "probe_kinds": base["probe_kinds"],
        "total_bytes": base["total_bytes"],
        "total_mib": round(base["total_bytes"] / 1048576, 2),
        "bytes_per_record": base["bytes_per_record"],
        "shards": base["shards"],
        "sources": base["sources"],
        "generator": base["generator"],
        "schema": SCHEMA,
        "files": files,
        "reference_cache": references,
        "reproduce": (
            "python benchmarks/v3/build_corpus_v3.py --per-category 48000 "
            "--out benchmarks/corpora/v3"
        ),
        "validate": "python benchmarks/v3/validate_corpus_v3.py benchmarks/corpora/v3",
        "load": ("python benchmarks/v3/load_corpus_v3.py benchmarks/corpora/v3 "
                 "--mode ledger --store /tmp/mem20-v3-store --rebuild"),
    }
    (corpus / "manifest.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in
                      ("records", "by_category", "total_bytes", "total_mib",
                       "probes", "probe_kinds")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
