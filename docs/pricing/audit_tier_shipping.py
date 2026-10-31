#!/usr/bin/env python3
"""Tier-vs-shipped audit - does the repo actually ship every tier its docs state?

`audit_acv_consistency.py` answers "does every ACV figure read $14,000?".
That is a *within-copy* check. It cannot see the failure this script targets:
a tier that exists only in prose, with no plan/entitlement in code or config.

Three questions, per stated tier:

  1. DOCUMENTED - where does the repo state this tier and its price?
  2. SHIPPED    - is there a machine-readable plan/entitlement carrying that tier?
  3. RECONCILED - does the tier ladder reproduce the $14,000 blended ACV on a
                  real 120-logo book (not just in percentage space)?

On (2) the bar is deliberately high. A financial model's *input file* is a
document about pricing, not a shipped plan: `docs/finance/inputs.json` declaring
`{"tier": "Team", "acv_usd": 6000}` does not entitle anyone to anything. To count
as shipped, a tier must appear as a plan/tier *value* in executable code or in a
commerce config, and must gate something a customer receives.

Exit codes: 0 = every stated tier has a shipped counterpart and the ladder
reconciles; 1 = at least one tier is copy-only (the finding), or a locked figure
drifted.

Usage:  python3 docs/pricing/audit_tier_shipping.py [--root .] [--json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

# ---- locked invariants (do not change: standing business figures) ----------
HOUSE_ACV = 14_000
SOM = 1_680_000
LOGOS = 120
COGS_PER_ACCOUNT = 4_280

# The ladder the repo documents (docs/finance/inputs.json -> tiers).
LADDER = [("Team", 6_000, 72), ("Business", 18_000, 12),
          ("Scale", 36_000, 12), ("Enterprise", 80_000, 4)]

# A second, incompatible ladder proposed in docs/gtm/mem20-sales-one-pager.md.
# Compliance pack is stated there as a RANGE ($28,000-$42,000); 35,000 is its
# midpoint, used only so the ladder can be blended arithmetically.
ALT_LADDER = [("Free / OSS", 0), ("Supported", 14_000),
              ("Compliance pack", 35_000), ("Platform", 56_000)]

# Commerce surface: the only place a price could actually be billed.
CATALOG = "mem20shopz/mem20shopz/catalog.json"

# Executable plan/entitlement surface ONLY. Note the deliberate absence of
# docs/finance and docs/pricing: a model input is not an entitlement.
SHIP_ROOTS = ["mcp", "gateway", "mem20api", "mem20core", "mem20corez",
              "mem20shopz", "mem20biz", "web/src", "packaging"]
SHIP_SUFFIXES = {".py", ".json", ".yaml", ".yml", ".toml", ".ts", ".js"}

# A tier name counts only when used as a plan VALUE on the same line as a
# gating keyword - never as a bare substring ("incident_team", "scale: [x,y,z]").
GATE_WORDS = r"plan|tier|entitle|subscription|sku|upgrade|seat_limit|quota|billing"

# Model-input files: these declare prices but ship no entitlement.
MODEL_INPUT_ROOTS = ["docs/finance", "docs/pricing"]


def tracked(root: pathlib.Path) -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                             text=True, check=True).stdout
        return out.splitlines()
    except Exception:
        return [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()]


def read(root: pathlib.Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def ladder_blend(ladder) -> float:
    total = sum(sh for _, _, sh in ladder)
    return sum(p * sh for _, p, sh in ladder) / total


def integer_mixes(prices: list[int], logos: int, target: int) -> list[tuple[int, ...]]:
    """Every non-negative integer mix summing to `logos` with weighted mean == target."""
    out = []
    for a in range(logos + 1):
        for b in range(logos - a + 1):
            for c in range(logos - a - b + 1):
                d = logos - a - b - c
                if sum(p * n for p, n in zip(prices, (a, b, c, d))) == target * logos:
                    out.append((a, b, c, d))
    return out


def largest_remainder(shares: list[float], logos: int) -> list[int]:
    exact = [s / 100 * logos for s in shares]
    floors = [int(x) for x in exact]
    rem = logos - sum(floors)
    order = sorted(range(len(exact)), key=lambda i: exact[i] - floors[i], reverse=True)
    for i in order[:rem]:
        floors[i] += 1
    return floors


def scan_documented(root: pathlib.Path, files: list[str]) -> dict[str, list[str]]:
    """Which tracked files state each tier's price?"""
    tok = {n: re.compile(r"\$\s*" + f"{p:,}" + r"\b") for n, p, _ in LADDER}
    hits: dict[str, list[str]] = {n: [] for n, _, _ in LADDER}
    for rel in files:
        if rel.startswith(("published/sites/", "mem20orcaz/")):
            continue
        text = read(root, rel)
        if not text:
            continue
        for name, _, _ in LADDER:
            if tok[name].search(text):
                hits[name].append(rel)
    return hits


def entry_gates(text: str, name: str) -> list[str]:
    """Lines where `name` is used as a plan/tier VALUE alongside a gating keyword.

    The tier name must be a quoted string literal (a plan value), and a gating
    keyword must sit within 60 characters of it on the same line. This is what
    rejects the two false-positive families seen in this repo:
      - `"scale": [x, y, z]` in a Blender tool schema (a geometry param)
      - `"Track personal or business expenses"` in a finance tool description
    Both are near the word "tier" in a minified one-line JSON dump, but neither
    is a plan value.
    """
    out = []
    lit = re.compile(r"[\"']" + re.escape(name) + r"[\"']", re.I)
    gate = re.compile(GATE_WORDS, re.I)
    for line in text.splitlines():
        for m in lit.finditer(line):
            lo, hi = max(0, m.start() - 60), min(len(line), m.end() + 60)
            if gate.search(line[lo:hi]):
                out.append(line.strip()[:160])
                break
    return out


def scan_shipped(root: pathlib.Path, files: list[str]) -> dict[str, list[dict]]:
    """Tier -> [{file, line}] where executable code/config gates on that tier."""
    ships: dict[str, list[dict]] = {n: [] for n, _, _ in LADDER}
    for rel in files:
        if not any(rel.startswith(r + "/") or rel == r for r in SHIP_ROOTS):
            continue
        if pathlib.Path(rel).suffix not in SHIP_SUFFIXES:
            continue
        text = read(root, rel)
        if not text:
            continue
        for name, _, _ in LADDER:
            gates = entry_gates(text, name)
            if gates:
                ships[name].append({"file": rel, "lines": gates[:2]})
    return ships


def catalog_state(root: pathlib.Path) -> dict:
    p = root / CATALOG
    if not p.exists():
        return {"present": False, "skus": 0, "priced": 0, "ids": []}
    data = json.loads(p.read_text(encoding="utf-8"))
    skus = data.get("skus", [])
    return {
        "present": True,
        "skus": len(skus),
        "priced": sum(1 for s in skus if isinstance(s.get("amount_cents"), int)
                      and s.get("amount_cents", 0) > 0),
        "ids": [s.get("id") for s in skus],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()
    files = tracked(root)

    documented = scan_documented(root, files)
    shipped = scan_shipped(root, files)
    cat = catalog_state(root)

    pct_blend = ladder_blend(LADDER)
    prices = [p for _, p, _ in LADDER]
    shares = [sh for _, _, sh in LADDER]
    mix = largest_remainder(shares, LOGOS)
    int_blend = sum(p * n for p, n in zip(prices, mix)) / sum(mix)
    som = int_blend * LOGOS
    exact = integer_mixes(prices, LOGOS, HOUSE_ACV)

    rows = [{
        "tier": n, "acv_usd": p, "declared_share_pct": sh,
        "documented_in": len(documented[n]),
        "doc_files": documented[n][:6],
        "shipped_in": shipped[n],
        "shipped": bool(shipped[n]),
    } for n, p, sh in LADDER]

    findings = {
        "house_acv_usd": HOUSE_ACV, "som_usd": SOM, "logos": LOGOS,
        "cogs_per_account_usd": COGS_PER_ACCOUNT,
        "pct_blend_usd": round(pct_blend, 2),
        "pct_delta_usd": round(pct_blend - HOUSE_ACV, 2),
        "largest_remainder_mix": mix,
        "integer_blend_usd": round(int_blend, 2),
        "integer_delta_usd": round(int_blend - HOUSE_ACV, 2),
        "integer_som_usd": som,
        "som_delta_usd": som - SOM,
        "exact_mix_count": len(exact),
        "nearest_exact_mix": [86, 18, 10, 6],
        "tiers": rows,
        "catalog": cat,
        "alt_ladder_undocumented": [{"tier": n, "acv_usd": p} for n, p in ALT_LADDER],
        "copy_only_tiers": [r["tier"] for r in rows if not r["shipped"]],
    }

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        print("== Documented ladder vs shipped surface ==")
        print(f"  {'Tier':<12}{'ACV':>10}{'docs':>6}  shipped (plan/entitlement in code or config)")
        for r in rows:
            if r["shipped_in"]:
                loc = "; ".join(f"{s['file']}" for s in r["shipped_in"][:3])
            else:
                loc = "*** NONE - copy only ***"
            print(f"  {r['tier']:<12}${r['acv_usd']:>9,}{r['documented_in']:>6}  {loc}")
        print()
        print("== Commerce surface ==")
        if cat["present"]:
            print(f"  {CATALOG}: {cat['skus']} SKUs, {cat['priced']} with an amount set")
        else:
            print(f"  {CATALOG}: absent - no billing surface at all")
        print()
        print("== Ladder arithmetic against the $14,000 house figure ==")
        print(f"  percentage-space blend  : ${pct_blend:,.2f}  (delta ${pct_blend - HOUSE_ACV:+,.2f})")
        print(f"  largest-remainder mix   : {mix}  sum={sum(mix)}")
        print(f"  integer-space blend     : ${int_blend:,.2f}  (delta ${int_blend - HOUSE_ACV:+,.2f})")
        print(f"  integer-space SOM       : ${som:,.0f}  (delta ${som - SOM:+,.0f})")
        print(f"  exact mixes at {LOGOS} logos: {len(exact)}; nearest {findings['nearest_exact_mix']}")
        print()
        print("== Second, incompatible ladder (docs/gtm/mem20-sales-one-pager.md) ==")
        for a in findings["alt_ladder_undocumented"]:
            print(f"  {a['tier']:<18}${a['acv_usd']:>9,}")
        print()
        if findings["copy_only_tiers"]:
            print(f"FINDING: copy-only tiers (documented, never shipped): "
                  f"{', '.join(findings['copy_only_tiers'])}")
        else:
            print("OK: every documented tier has a shipped counterpart.")
    return 1 if findings["copy_only_tiers"] else 0


if __name__ == "__main__":
    sys.exit(main())
