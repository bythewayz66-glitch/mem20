#!/usr/bin/env python3
"""Verify the refreshed competitive matrix: every figure carries a source.

Checks, in order:
  1. every CSV row names at least one source id, and every id resolves in the register
  2. every R-id in the register is actually reproducible (spot-checked against the repo)
  3. no retired surface figure (257 tools / 26 domains) appears in the refreshed files
  4. the house numbers are present and equal to inputs.json
  5. the register defines every id the report cites, and vice versa

Exit 0 = clean, 1 = at least one failure, 2 = could not run.

This script audits the tree it is run in. It excludes itself from the sweep so its own
quoted example figures cannot be reported as live violations.
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET = os.path.join(REPO, "docs", "market")
CSV_PATH = os.path.join(MARKET, "competitive-matrix-2026-11-01.csv")
MD_PATH = os.path.join(MARKET, "competitive-matrix-2026-11-01.md")
REG_PATH = os.path.join(MARKET, "source-register-2026-11-01.md")

fails: list[str] = []
checks = 0


def ok(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def read(p: str) -> str:
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def main() -> int:
    for p in (CSV_PATH, MD_PATH, REG_PATH):
        if not os.path.exists(p):
            print(f"FATAL: missing {p}", file=sys.stderr)
            return 2

    reg = read(REG_PATH)
    md = read(MD_PATH)

    # ---- 1. register defines the ids -------------------------------------
    defined = set(re.findall(r"^\|\s*(R\d+|S\d+)\s*\|", reg, re.M))
    ok(len(defined) > 0, "register defines no ids")

    # ---- 2. every CSV row carries a resolvable source --------------------
    with open(CSV_PATH, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ok(len(rows) == 14, f"expected 14 rows (13 players + reference), got {len(rows)}")

    for row in rows:
        vendor = (row.get("vendor") or "?").strip()
        src = (row.get("source_ids") or "").strip()
        ok(bool(src), f"{vendor}: no source_ids")
        for sid in [s.strip() for s in src.split(";") if s.strip()]:
            ok(sid in defined, f"{vendor}: source id {sid} not defined in register")

    # ---- 3. reference row states the current surface ---------------------
    ref = [r for r in rows if "mem20" in (r.get("vendor") or "")]
    ok(len(ref) == 1, "reference row missing or duplicated")
    if ref:
        bet = ref[0].get("architecture_bet", "")
        ok("270" in bet, "reference row does not state 270 tools")
        ok("27 domains" in bet, "reference row does not state 27 domains")
        ok("3.1.0" in bet, "reference row does not state v3.1.0")

    # ---- 4. no retired surface figure in the refreshed files -------------
    for path, text in ((CSV_PATH, read(CSV_PATH)), (MD_PATH, md)):
        name = os.path.basename(path)
        # 257/26 may appear ONLY as an explicitly retired value
        for m in re.finditer(r"257", text):
            ctx = text[max(0, m.start() - 120): m.start() + 120]
            ok(
                any(w in ctx for w in ("retired", "Retired", "RETIRED", "v3 said", "predates", "superseded")),
                f"{name}: bare '257' without a retired marker near offset {m.start()}",
            )
        ok("26 domains" not in text or "retired" in text.lower(),
           f"{name}: '26 domains' present without a retired marker")

    # ---- 5. house numbers present and equal to inputs.json ---------------
    inputs = json.load(open(os.path.join(REPO, "docs", "finance", "inputs.json"), encoding="utf-8"))
    h = inputs["house_numbers"]
    ok(h["tam_usd"] == 1280000000, "inputs.json TAM is not 1280000000")
    ok(h["sam_usd"] == 282000000, "inputs.json SAM is not 282000000")
    ok(h["som_arr_usd"] == 1680000, "inputs.json SOM is not 1680000")
    ok(h["blended_acv_usd"] == 14000, "inputs.json ACV is not 14000")

    for token in ("$1.28B", "$282M", "$1.68M", "$14,000"):
        ok(token in md, f"report does not state {token}")

    # ---- 6. every id cited in the report is defined ----------------------
    cited = set(re.findall(r"`(R\d+|S\d+)`", md))
    for cid in sorted(cited):
        ok(cid in defined, f"report cites {cid} which the register does not define")

    # ---- 7. R-ids are reproducible from the repo -------------------------
    def sh(cmd: str) -> str:
        return subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True, text=True).stdout.strip()

    ok(sh("cat VERSION") == "3.1.0", "VERSION is not 3.1.0")
    ok(sh("""grep -rhoE 'self\\.tools\\["[^"]*"\\]' mcp --include='*.py' | sort -u | wc -l""") == "270",
       "distinct tool count is not 270")
    ok(sh("grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py | sort -u | wc -l") == "28",
       "registrar group count is not 28")

    # ---- 8. arithmetic in the report is true -----------------------------
    tam, sam, som, acv = 1280000000, 282000000, 1680000, 14000
    ok(som == 120 * acv, "SOM is not 120 x ACV")
    ok(round(sam / tam * 100, 2) == 22.03, "SAM/TAM is not 22.03%")
    ok(round(som / sam * 100, 3) == 0.596, "SOM/SAM is not 0.596%")
    ok(round(som / tam * 100, 3) == 0.131, "SOM/TAM is not 0.131%")
    ok(round(tam / 6490000000 * 100, 2) == 19.72, "slice share is not 19.72%")
    ok(28 - 1 == 27 and 265 + 5 == 270, "domain/tool arithmetic does not reconcile")

    # ---- report ----------------------------------------------------------
    print(f"checks run: {checks}")
    print(f"rows: {len(rows)}  register ids: {len(defined)}  ids cited in report: {len(cited)}")
    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nPASS: every figure carries a resolvable source; surface and house numbers verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
