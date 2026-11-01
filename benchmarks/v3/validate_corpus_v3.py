#!/usr/bin/env python3
"""Validate a mem20-scale-corpus-v3 directory.

Checks, in order, and fails the build on any of them:

  1. every line parses as JSON and carries the required envelope keys;
  2. ``category`` is one of grounded / ungrounded / false;
  3. grounded records carry a real ``source`` URL and non-empty ``evidence``;
     ungrounded records carry neither; false records carry ``contradicts``
     pointing at a grounded key that exists, plus a ``true_value`` that differs
     from the ``object`` the claim asserts;
  4. ``epistemic_status`` is in mem20's own vocabulary and matches the category;
  5. no duplicate ``key`` and no duplicate ``id`` across all shards;
  6. category balance is within 1% of one third each;
  7. the record count meets the minimum (15,000) and the byte total is reported;
  8. every non-control probe's gold record exists and its expected evidence is
     a literal substring of that record's content, and is NOT in the probe text
     (an answer-free or self-answering probe is a build failure, not a warning).

    python benchmarks/v3/validate_corpus_v3.py benchmarks/corpora/v3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_KEYS = (
    "id", "key", "category", "family", "topic", "content", "tags",
    "epistemic_status", "subject", "predicate", "object", "confidence",
    "source", "evidence", "contradicts", "true_value", "difficulty",
    "timestamp", "schema_version",
)

EPISTEMIC = {"grounded": "observed", "ungrounded": "imagined",
             "false": "agent_generated"}

MIN_RECORDS = 15_000
BALANCE_TOLERANCE = 0.01

# A source may carry a trailing parenthetical provenance note; validate the URL
# prefix, not the whole string, or legitimate citations read as errors.
URL_RE = re.compile(r"^https?://\S+")


def _iter_records(corpus: Path):
    shards = sorted(corpus.glob("records.part-*.jsonl"))
    if not shards:
        raise SystemExit(f"no records.part-*.jsonl under {corpus}")
    for shard in shards:
        with shard.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                try:
                    yield shard.name, lineno, json.loads(line)
                except json.JSONDecodeError as exc:
                    yield shard.name, lineno, {"__parse_error__": str(exc)}


def _restates_truth(content: str, asserted: str, true_value: str) -> bool:
    """True if the record's own text also states the value it is denying.

    A false record must assert only the wrong value. If its prose also carries
    the true one, the claim contradicts itself in the same sentence and the
    category is meaningless.

    Two traps this avoids:
      * short values ("AF", "Po", "ON") occur inside ordinary words, so the
        search is word-bounded rather than a raw substring test;
      * the true value is often a substring of the asserted one
        ("compressible" inside "non-compressible"), so the asserted value is
        removed from the text before searching.
    """
    if not true_value:
        return False
    text = content
    if asserted:
        text = text.replace(asserted, " ")
    pattern = r"(?<![A-Za-z0-9])" + re.escape(true_value) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def validate(corpus: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    keys: dict[str, str] = {}
    ids: dict[str, str] = {}
    by_category: dict[str, int] = {}
    by_family: dict[str, int] = {}
    grounded_keys: set[str] = set()
    records: list[dict] = []
    total_bytes = 0

    for shard in sorted(corpus.glob("records.part-*.jsonl")):
        total_bytes += shard.stat().st_size

    for shard_name, lineno, rec in _iter_records(corpus):
        where = f"{shard_name}:{lineno}"
        if "__parse_error__" in rec:
            errors.append(f"{where}: JSON parse error: {rec['__parse_error__']}")
            continue

        missing = [k for k in REQUIRED_KEYS if k not in rec]
        if missing:
            errors.append(f"{where}: missing keys {missing}")
            continue

        cat = rec["category"]
        if cat not in EPISTEMIC:
            errors.append(f"{where}: bad category {cat!r}")
            continue

        if rec["epistemic_status"] != EPISTEMIC[cat]:
            errors.append(
                f"{where}: epistemic_status {rec['epistemic_status']!r} does not "
                f"match category {cat!r} (expected {EPISTEMIC[cat]!r})")

        if cat == "grounded":
            src = rec["source"]
            if not src:
                errors.append(f"{where}: grounded record has no source")
            elif not URL_RE.match(str(src)):
                errors.append(f"{where}: grounded source is not a URL: {src!r}")
            if not rec["evidence"]:
                errors.append(f"{where}: grounded record has no evidence")
            if rec["contradicts"] is not None:
                errors.append(f"{where}: grounded record carries contradicts")
            grounded_keys.add(rec["key"])

        elif cat == "ungrounded":
            if rec["source"] is not None:
                errors.append(f"{where}: ungrounded record carries a source")
            if rec["contradicts"] is not None:
                errors.append(f"{where}: ungrounded record carries contradicts")

        else:  # false
            if rec["source"] is not None:
                errors.append(f"{where}: false record carries a source")
            if not rec["contradicts"]:
                errors.append(f"{where}: false record has no contradicts target")
            if not rec["true_value"]:
                errors.append(f"{where}: false record has no true_value")
            elif rec["true_value"] == rec["object"]:
                errors.append(
                    f"{where}: false record's object equals its true_value — "
                    "the claim is not actually wrong")
            elif _restates_truth(rec["content"], rec["object"], rec["true_value"]):
                errors.append(
                    f"{where}: false record's content restates its own "
                    f"true_value {rec['true_value']!r} — the claim contradicts "
                    "itself in the same sentence")

        if rec["key"] in keys:
            errors.append(
                f"{where}: duplicate key {rec['key']!r} "
                f"(first seen {keys[rec['key']]})")
        else:
            keys[rec["key"]] = where

        if rec["id"] in ids:
            errors.append(
                f"{where}: duplicate id {rec['id']!r} (first seen {ids[rec['id']]})")
        else:
            ids[rec["id"]] = where

        by_category[cat] = by_category.get(cat, 0) + 1
        by_family[rec["family"]] = by_family.get(rec["family"], 0) + 1
        records.append(rec)

    # contradicts must point at a grounded key that exists in this corpus.
    for rec in records:
        if rec.get("category") == "false" and rec.get("contradicts"):
            if rec["contradicts"] not in grounded_keys:
                errors.append(
                    f"false record {rec['key']!r} contradicts "
                    f"{rec['contradicts']!r}, which is not a grounded key here")

    total = len(records)
    if total < MIN_RECORDS:
        errors.append(f"only {total} records; minimum is {MIN_RECORDS}")

    if total:
        for cat in EPISTEMIC:
            share = by_category.get(cat, 0) / total
            if abs(share - 1 / 3) > BALANCE_TOLERANCE:
                errors.append(
                    f"category {cat!r} is {share:.4f} of the corpus; "
                    f"expected 1/3 +/- {BALANCE_TOLERANCE}")

    # ---- probes -----------------------------------------------------------
    probes_path = corpus / "probes.jsonl"
    probes_checked = 0
    controls = 0
    if not probes_path.is_file():
        errors.append("probes.jsonl is missing")
    else:
        by_key = {r["key"]: r for r in records}
        with probes_path.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                q = json.loads(line)
                qid = q.get("qid", f"line{lineno}")
                if q.get("kind") == "unanswerable":
                    controls += 1
                    if q.get("expect") or q.get("gold_key"):
                        errors.append(
                            f"{qid}: control probe must not expect evidence")
                    continue
                expect = q.get("expect") or []
                if not expect:
                    errors.append(f"{qid}: answerable probe has no expected evidence")
                    continue
                gold = by_key.get(q.get("gold_key") or "")
                if gold is None:
                    errors.append(
                        f"{qid}: gold record {q.get('gold_key')!r} not in corpus")
                    continue
                needle = expect[0].lower()
                if needle not in gold["content"].lower():
                    errors.append(
                        f"{qid}: expected evidence {needle!r} absent from gold "
                        f"record {gold['key']!r} — the answer is not in the corpus")
                    continue
                if needle in q["text"].lower():
                    errors.append(
                        f"{qid}: expected evidence {needle!r} appears in the probe "
                        "text — the probe leaks its own answer")
                    continue
                probes_checked += 1

    return {
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors[:100],
        "warnings": warnings[:100],
        "records": total,
        "by_category": by_category,
        "by_family": by_family,
        "dup_keys": total - len(keys),
        "dup_ids": total - len(ids),
        "total_bytes": total_bytes,
        "bytes_per_record": round(total_bytes / total, 2) if total else 0,
        "probes_checked": probes_checked,
        "control_probes": controls,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("corpus", nargs="?", default="benchmarks/corpora/v3")
    ap.add_argument("--out", default=None, help="write the report JSON here")
    args = ap.parse_args(argv)

    corpus = Path(args.corpus)
    if not corpus.is_absolute():
        corpus = Path(__file__).resolve().parents[2] / corpus
    report = validate(corpus)
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
