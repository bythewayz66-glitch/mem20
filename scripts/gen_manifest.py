#!/usr/bin/env python3
"""Regenerate published/MANIFEST.tsv from the files it describes.

The manifest is a claim: for every file under published/, this many bytes and
this SHA-256. It was maintained by hand, and by 2026-11-01 thirty-two of its
128 rows were wrong -- unchanged across four separate measurements, because
nothing regenerated it and nothing checked it.

This script is both halves:

    python3 scripts/gen_manifest.py            # rewrite the manifest
    python3 scripts/gen_manifest.py --check    # exit 1 if any row is wrong

The file format is TSV with a header row and CRLF line endings, matching what
was already committed. Rows are sorted by path so a regeneration produces a
stable diff.

Scope: every regular file under published/, excluding the manifest itself.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED = ROOT / "published"
MANIFEST = PUBLISHED / "MANIFEST.tsv"
HEADER = "repo_path\tbytes\tsha256"


def walk() -> list[Path]:
    out: list[Path] = []
    for p in sorted(PUBLISHED.rglob("*")):
        if not p.is_file():
            continue
        if p == MANIFEST:
            continue
        out.append(p)
    return out


def row_for(p: Path) -> tuple[str, int, str]:
    data = p.read_bytes()
    rel = p.relative_to(ROOT).as_posix()
    return rel, len(data), hashlib.sha256(data).hexdigest()


def read_manifest() -> dict[str, tuple[int, str]]:
    rows: dict[str, tuple[int, str]] = {}
    if not MANIFEST.exists():
        return rows
    text = MANIFEST.read_bytes().decode("utf-8")
    for i, line in enumerate(text.splitlines()):
        if i == 0 or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        path, size, sha = parts[0], parts[1], parts[2]
        try:
            rows[path] = (int(size), sha)
        except ValueError:
            rows[path] = (-1, sha)
    return rows


def main() -> int:
    files = walk()
    actual = {rel: (size, sha) for rel, size, sha in (row_for(p) for p in files)}
    recorded = read_manifest()

    if "--check" in sys.argv:
        bad = [p for p in actual if p in recorded and recorded[p] != actual[p]]
        missing = [p for p in actual if p not in recorded]
        extra = [p for p in recorded if p not in actual]
        print(f"files on disk      {len(actual)}")
        print(f"rows in manifest   {len(recorded)}")
        print(f"mismatched         {len(bad)}")
        print(f"on disk, no row    {len(missing)}")
        print(f"row, no file       {len(extra)}")
        for p in bad[:10]:
            print(f"  MISMATCH {p}")
        for p in missing[:10]:
            print(f"  UNLISTED {p}")
        for p in extra[:10]:
            print(f"  DANGLING {p}")
        if bad or missing or extra:
            print("::error::published/MANIFEST.tsv does not describe the tree")
            print("Fix: python3 scripts/gen_manifest.py")
            return 1
        print("OK: every row matches the file it describes")
        return 0

    lines = [HEADER]
    for rel in sorted(actual):
        size, sha = actual[rel]
        lines.append(f"{rel}\t{size}\t{sha}")
    MANIFEST.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
    print(f"wrote {len(actual)} rows to {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
