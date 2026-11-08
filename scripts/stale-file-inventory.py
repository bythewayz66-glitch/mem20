#!/usr/bin/env python3
"""Build the machine-readable stale-file inventory for mem20 (reconnaissance).

Scans a mem20 clone and emits docs/recon/stale-file-inventory-<date>.json:
every file that references retired infrastructure, carries an outdated
tool/domain count, holds a dead link, is an orphaned doc, or is not reachable
from main.

Each record carries `path`, `category`, `stale_pattern` and `fix` (a key into
the top-level `fixes` map holding the suggested fix).

Run:  python3 scripts/stale-file-inventory.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import os
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SURFACE = ROOT / "docs" / "surface.json"

# Retired-infra allowlist (mirrors scripts/verify-retired-infra-purge.sh and
# docs/ops/retired-infra-allowlist-2026-11-01.md). Prefixes end in "/".
ALLOW = (
    "published/",
    ".sitemap/sitemap.json",
    "docs/ops/branch-inventory-2026-10-31.md",
    "docs/ops/branch-disposition-2026-10-31.md",
    "docs/ops/owner-directive-2026-11-01.md",
    "docs/ops/tag-audit-2026-10-31.md",
    "docs/ops/roster-verification-2026-10-27.md",
    "docs/gtm/claim-ledger.md",
    "docs/market/market-claims-consistency-2026-10-31.md",
    "docs/pricing/RECONCILIATION_NOTE.md",
    "scripts/sweep-tool-counts.py",
    "docs/ops/retired-infra-allowlist-2026-11-01.md",
    "scripts/verify-retired-infra-purge.sh",
)

FIX = {
    "retired_infra_purge": (
        "Purge the retired token (replace with the live rule: GitHub is the only "
        "publication channel), or add a justified entry to "
        "docs/ops/retired-infra-allowlist-2026-11-01.md and "
        "scripts/verify-retired-infra-purge.sh if it is a dated record or real path."
    ),
    "retired_infra_allowlisted": (
        "No action: covered by the documented retired-infra allowlist "
        "(immutable archive / dated record / real on-disk path)."
    ),
    "retired_infra_zone": (
        "Retired-zone reference outside the G8 gate's sidney|gabe pattern; confirm "
        "it is a dated retirement record, otherwise re-point to the live canonical URL."
    ),
    "retired_infra_false_positive": "No action: data file; tokens are unrelated proper nouns.",
    "outdated_tool_count": (
        "Run `python3 scripts/sweep-tool-counts.py --apply` to converge to the live pin."
    ),
    "dead_link_internal": "Repair or remove the link; point it at the current path.",
    "dead_link_retired_url": "Replace the retired-domain URL with the live GitHub / canonical URL.",
    "orphaned_doc": "Link it from docs/README.md (or the relevant index), or archive/remove it.",
    "not_reachable_from_main": "Merge the branch into main, or delete the branch if the file is obsolete.",
}

RETIRED = {
    "sidney_host_ip": re.compile(r"216\.198\.115\.91"),
    "retired_zone_host": re.compile(r"mem20\.jaysonai\.online", re.I),
    "retired_zone": re.compile(r"jaysonai\.online", re.I),
    "retired_host_name": re.compile(r"\bsidney\b", re.I),
    "retired_gate_name": re.compile(r"\bgabe\b", re.I),
}

COUNT_RX = re.compile(
    r"\b(?:257|258|259|260|265|268|270|306)\s+tools\b"
    r"|\b(?:26|27|38)\s+domains\b",
    re.I,
)
COUNT_SKIP_FILES = {
    "CHANGELOG.md",
    "bench/optionc/optionc.patch",
    "web/src/views/DocsFaq.tsx",
    "web/src/data/catalog.ts",
}
COUNT_SKIP_PREFIXES = ("published/daily-reports/", "docs/audit/")
COUNT_EXT = {".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".css", ".vue", ".json"}

FALSE_POSITIVE = {
    "reference/v3/cities15000.txt": (
        "GeoNames gazetteer: 'Sidney' (AU) and 'Gabela' (AO) are place names, "
        "not the retired host/gate."
    ),
}

LINK_RX = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
EXT_RX = re.compile(r"https?://[^\s)\"'<>\]}`]+")
RETIRED_URL_RX = re.compile(r"jaysonai\.online|216\.198\.115\.91", re.I)
LINK_NOISE = re.compile(r"^(\*\*|None$|/c:/|/api/|/v1/|/health$|/metrics$)")


def sh(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT).stdout


def read(path: str) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def allowlisted(path: str) -> bool:
    for e in ALLOW:
        if e.endswith("/"):
            if path.startswith(e):
                return True
        elif path == e:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=_dt.date.today().isoformat())
    a = ap.parse_args()

    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    tools, domains = str(surface["tools"]), str(surface["domains"])
    head = sh("git rev-parse HEAD").strip()
    tracked = sh("git ls-files").splitlines()
    main_files = set(sh("git ls-tree -r --name-only main").splitlines())

    recs: list[dict] = []

    def add(path, category, pattern, fix, severity, allow=None, reach=None, gate=None):
        recs.append({
            "path": path,
            "category": category,
            "stale_pattern": pattern,
            "fix": fix,
            "severity": severity,
            "allowlisted": allowlisted(path) if allow is None else allow,
            "reachable_from_main": (path in main_files) if reach is None else reach,
            "gate_enforced": gate,
        })

    # 1. retired infrastructure
    for f in sorted(tracked):
        txt = read(f)
        if not txt:
            continue
        hits = {k: len(rx.findall(txt)) for k, rx in RETIRED.items()}
        hits = {k: v for k, v in hits.items() if v}
        if not hits:
            continue
        pattern = ", ".join(f"{k} x{v}" for k, v in sorted(hits.items()))
        if f in FALSE_POSITIVE:
            add(f, "retired_infra", "false-positive: " + pattern,
                "retired_infra_false_positive", "low", allow=False, gate=False)
            continue
        gate = any(k in ("retired_host_name", "retired_gate_name") for k in hits)
        if allowlisted(f):
            add(f, "retired_infra", pattern, "retired_infra_allowlisted", "low", gate=gate)
        elif gate:
            add(f, "retired_infra", pattern, "retired_infra_purge", "high", gate=True)
        else:
            add(f, "retired_infra", pattern, "retired_infra_zone", "medium", gate=False)

    # 2. outdated tool/domain counts
    for f in sorted(tracked):
        if os.path.splitext(f)[1].lower() not in COUNT_EXT:
            continue
        if f in COUNT_SKIP_FILES or f.startswith(COUNT_SKIP_PREFIXES) or f.endswith(".patch"):
            continue
        txt = read(f)
        if not txt:
            continue
        matched = sorted({m.group(0).strip() for m in COUNT_RX.finditer(txt)})
        if matched:
            add(f, "outdated_tool_count", "; ".join(matched), "outdated_tool_count", "medium")

    # 3. dead links
    for f in sorted(tracked):
        if not f.lower().endswith((".md", ".html", ".htm")):
            continue
        txt = read(f)
        if not txt:
            continue
        base = (ROOT / f).parent
        dead = []
        for m in LINK_RX.finditer(txt):
            tgt = m.group(1).strip()
            if tgt.startswith(("http://", "https://", "mailto:", "#", "tel:", "data:")):
                continue
            if LINK_NOISE.match(tgt):
                continue
            clean = tgt.split("#")[0].split("?")[0]
            if not clean:
                continue
            cand = (ROOT / clean.lstrip("/")) if clean.startswith("/") else (base / clean)
            try:
                rel = cand.resolve().relative_to(ROOT.resolve()).as_posix()
            except Exception:
                rel = None
            if rel is None or not (ROOT / rel).exists():
                dead.append(tgt)
        if dead:
            add(f, "dead_link", "unresolved internal link(s): " + ", ".join(sorted(set(dead))[:8]),
                "dead_link_internal", "medium")
        retired_urls = sorted({m.group(0).rstrip(".,;:`") for m in EXT_RX.finditer(txt)
                               if RETIRED_URL_RX.search(m.group(0))})
        if retired_urls:
            add(f, "dead_link", "retired-domain URL(s): " + ", ".join(retired_urls[:5]),
                "dead_link_retired_url", "low" if allowlisted(f) else "high")

    # 4. orphaned docs
    docs_files = [f for f in tracked if f.startswith("docs/") and f.lower().endswith((".md", ".html"))]
    referenced = set()
    for f in sorted(tracked):
        if not f.lower().endswith((".md", ".html", ".htm", ".json", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx")):
            continue
        txt = read(f)
        if not txt:
            continue
        for d in docs_files:
            if d != f and (d in txt or os.path.basename(d) in txt):
                referenced.add(d)
    for d in sorted(docs_files):
        if d in referenced or os.path.basename(d).lower().startswith(("readme", "index")):
            continue
        add(d, "orphaned_doc", "not referenced by any index/README", "orphaned_doc", "low")

    # 5. not reachable from main
    branches = [b for b in sh("git for-each-ref --format='%(refname)' refs/remotes/origin").splitlines()
                if "HEAD" not in b]
    only_on: dict[str, set] = collections.defaultdict(set)
    for b in branches:
        for extra in set(sh(f"git ls-tree -r --name-only {b}").splitlines()) - main_files:
            only_on[extra].add(b.replace("refs/remotes/origin/", ""))
    for f in sorted(only_on):
        brs = sorted(only_on[f])
        add(f, "not_reachable_from_main",
            f"branches={len(brs)}: " + ", ".join(brs[:2]),
            "not_reachable_from_main", "medium", reach=False)

    # emit
    by_cat = collections.Counter(r["category"] for r in recs)
    gate_fail = sorted(r["path"] for r in recs
                       if r["category"] == "retired_infra" and r["gate_enforced"] and not r["allowlisted"])
    payload = {
        "schema_version": 1,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "repository": "https://github.com/bythewayz66-glitch/mem20",
        "main_head_sha": head,
        "live_pin": {"tools": tools, "domains": domains, "source": "docs/surface.json"},
        "tracked_files": len(tracked),
        "summary": {
            "total_records": len(recs),
            "by_category": dict(sorted(by_cat.items())),
            "non_allowlisted_retired_infra": sum(
                1 for r in recs if r["category"] == "retired_infra" and not r["allowlisted"]),
            "g8_gate_status": "FAIL" if gate_fail else "PASS",
            "g8_gate_failing_files": gate_fail,
        },
        "fixes": FIX,
        "records": sorted(recs, key=lambda r: (r["category"], r["path"])),
    }

    outdir = ROOT / "docs" / "recon"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"stale-file-inventory-{a.date}.json"

    # Records are emitted as positional arrays to keep the file compact:
    # [path, category, stale_pattern, fix, severity, allowlisted, reachable_from_main, gate_enforced]
    payload["record_fields"] = [
        "path", "category", "stale_pattern", "fix", "severity",
        "allowlisted", "reachable_from_main", "gate_enforced",
    ]
    rows = [[r["path"], r["category"], r["stale_pattern"], r["fix"], r["severity"],
             r["allowlisted"], r["reachable_from_main"], r["gate_enforced"]]
            for r in payload["records"]]

    head_json = {k: v for k, v in payload.items() if k != "records"}
    body = json.dumps(head_json, indent=2, ensure_ascii=False)
    body = body[:-2].rstrip() + ',\n  "records": [\n'
    body += ",\n".join("    " + json.dumps(r, ensure_ascii=False) for r in rows)
    body += "\n  ]\n}\n"
    out.write_text(body, encoding="utf-8")
    json.loads(out.read_text(encoding="utf-8"))  # validate

    print(f"HEAD {head}")
    print(f"live pin: {tools} tools / {domains} domains")
    print(f"records: {len(recs)}  by category: {dict(sorted(by_cat.items()))}")
    print(f"G8 gate: {payload['summary']['g8_gate_status']}  failing: {gate_fail}")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
