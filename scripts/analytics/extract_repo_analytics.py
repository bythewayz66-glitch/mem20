#!/usr/bin/env python3
"""Extract a real analytics dataset from the mem20 repository itself.

Sources (all in-repo, no external calls):
  * git history (commits, authors, branches, tags, file counts)
  * docs/surface.json at every commit that touched it (tool/domain growth)
  * benchmarks/results/latest.json (retrieval quality + latency)
  * docs/benchmarks/results-v1.json / results-v2.json (benchmark lineage)
  * docs/benchmarks/experiments.json (experiment registry)

Output: docs/analytics/data/repo-analytics.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO, "docs", "analytics", "data")
OUT = os.path.join(OUT_DIR, "repo-analytics.json")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout


def git_ok(*args: str) -> bool:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True
    ).returncode == 0


def base_ref() -> str:
    """The commit the analysis is pinned to.

    Defaults to ``origin/main`` so the dataset describes the branch point, not
    whatever commit happens to be checked out. Without this the run would count
    its own commit and every regeneration would shift the numbers, making the
    report impossible to reproduce. Override with MEM20_ANALYTICS_REF.
    """
    override = os.environ.get("MEM20_ANALYTICS_REF")
    if override:
        return override
    for candidate in ("origin/main", "main", "HEAD"):
        if git_ok("rev-parse", "--verify", f"{candidate}^{{commit}}"):
            return candidate
    return "HEAD"


def head_sha() -> str:
    return git("rev-parse", base_ref()).strip()


def commit_series() -> dict:
    """Commits per ISO week and per month, plus cumulative totals."""
    raw = git("log", base_ref(), "--format=%H|%aI|%an|%ae|%s").strip().splitlines()
    commits = []
    for line in raw:
        sha, date, name, email, subject = line.split("|", 4)
        commits.append(
            {"sha": sha, "date": date, "author": name, "email": email, "subject": subject}
        )

    by_month = Counter()
    by_week = Counter()
    by_day = Counter()
    by_author = Counter()
    by_author_email = Counter()
    for c in commits:
        dt = datetime.fromisoformat(c["date"])
        by_month[dt.strftime("%Y-%m")] += 1
        by_week[dt.strftime("%G-W%V")] += 1
        by_day[dt.strftime("%Y-%m-%d")] += 1
        by_author[c["author"]] += 1
        by_author_email[c["email"]] += 1

    # cumulative commits per month
    months = sorted(by_month)
    cum = 0
    monthly = []
    for m in months:
        cum += by_month[m]
        monthly.append({"month": m, "commits": by_month[m], "cumulative": cum})

    weeks = sorted(by_week)
    cum = 0
    weekly = []
    for w in weeks:
        cum += by_week[w]
        weekly.append({"week": w, "commits": by_week[w], "cumulative": cum})

    # conventional-commit type distribution
    types = Counter()
    for c in commits:
        subj = c["subject"]
        if ":" in subj and " " not in subj.split(":", 1)[0]:
            types[subj.split(":", 1)[0].strip().lower()] += 1
        else:
            types["(untyped)"] += 1

    return {
        "total_commits": len(commits),
        "first_commit": commits[-1] if commits else None,
        "latest_commit": commits[0] if commits else None,
        "monthly": monthly,
        "weekly": weekly,
        "daily": [{"day": d, "commits": n} for d, n in sorted(by_day.items())],
        "authors": [
            {"author": a, "commits": n} for a, n in by_author.most_common()
        ],
        "author_emails": [
            {"email": e, "commits": n} for e, n in by_author_email.most_common()
        ],
        "commit_types": [
            {"type": t, "count": n} for t, n in types.most_common()
        ],
    }


def branch_state() -> dict:
    remote = [b.strip() for b in git("branch", "-r").splitlines() if b.strip()]
    remote = [b for b in remote if "->" not in b]
    ahead = []
    for ref in remote:
        name = ref.replace("origin/", "", 1)
        if name == "main":
            continue
        try:
            n = int(git("rev-list", "--count", f"origin/main..{ref}").strip())
        except subprocess.CalledProcessError:
            continue
        if n > 0:
            ahead.append({"branch": name, "ahead": n})
    ahead.sort(key=lambda x: -x["ahead"])
    tags = [t for t in git("tag").splitlines() if t.strip()]
    return {
        "remote_branches": len(remote),
        "branches_ahead_of_main": ahead,
        "at_risk_commits": sum(b["ahead"] for b in ahead),
        "tags": len(tags),
    }


def tracked_files() -> dict:
    files = [
        f
        for f in git("ls-tree", "-r", "--name-only", base_ref()).splitlines()
        if f
    ]
    by_top = Counter()
    by_ext = Counter()
    for f in files:
        by_top[f.split("/", 1)[0] if "/" in f else "(root)"] += 1
        ext = os.path.splitext(f)[1].lower() or "(none)"
        by_ext[ext] += 1
    return {
        "total": len(files),
        "by_top_dir": [{"dir": d, "files": n} for d, n in by_top.most_common(25)],
        "by_extension": [{"ext": e, "files": n} for e, n in by_ext.most_common(20)],
    }


def surface_growth() -> dict:
    """Read docs/surface.json at every commit that touched it."""
    shas = [
        line.split("|")[0]
        for line in git(
            "log", base_ref(), "--format=%H|%aI", "--", "docs/surface.json"
        ).strip().splitlines()
        if line
    ]
    points = []
    for sha in shas:
        try:
            blob = git("show", f"{sha}:docs/surface.json")
            data = json.loads(blob)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        cc = data.get("cross_check", {})
        dc = data.get("domain_counts", {})
        date = git("show", "-s", "--format=%aI", sha).strip()
        points.append(
            {
                "sha": sha,
                "date": date,
                "tools": cc.get("ast_tools") or sum(dc.values()),
                "domains": cc.get("ast_domains") or len(dc),
                "unwired": len(data.get("unwired_tools", []) or []),
                "domain_counts": dc,
            }
        )
    points.sort(key=lambda p: p["date"])
    # Only the newest snapshot keeps its full domain map; older points are
    # reduced to scalars so the dataset does not carry 9 stale copies of it.
    if points:
        current_counts = points[-1].pop("domain_counts", {})
        for p in points[:-1]:
            p.pop("domain_counts", None)
    else:
        current_counts = {}
    return {
        "points": points,
        "current": points[-1] if points else None,
        "current_domain_counts": current_counts,
    }


def benchmark_data() -> dict:
    out = {"latest": None, "v1": None, "v2": None, "experiments": None}
    p = os.path.join(REPO, "benchmarks", "results", "latest.json")
    if os.path.exists(p):
        out["latest"] = json.load(open(p))
    for key, rel in (
        ("v1", "docs/benchmarks/results-v1.json"),
        ("v2", "docs/benchmarks/results-v2.json"),
        ("experiments", "docs/benchmarks/experiments.json"),
    ):
        fp = os.path.join(REPO, rel)
        if os.path.exists(fp):
            try:
                out[key] = json.load(open(fp))
            except json.JSONDecodeError:
                out[key] = None
    return out


def benchmark_summary(bench: dict) -> dict:
    """Flatten latest.json recall into per-mode / per-kind rows + mode aggregates."""
    latest = bench.get("latest") or {}
    recall = latest.get("recall") or {}
    rows = []
    mode_agg = {}
    for mode, kinds in recall.items():
        tot_n = 0
        weighted_hit = 0.0
        weighted_mrr = 0.0
        lat = []
        for kind, m in kinds.items():
            n = m.get("n", 0)
            rows.append(
                {
                    "mode": mode,
                    "kind": kind,
                    "n": n,
                    "hit_rate": m.get("hit_rate"),
                    "mrr": m.get("mrr"),
                    "leak_rate": m.get("leak_rate"),
                    "p50_ms": m.get("median_latency_ms"),
                }
            )
            tot_n += n
            weighted_hit += (m.get("hit_rate") or 0) * n
            weighted_mrr += (m.get("mrr") or 0) * n
            if m.get("median_latency_ms") is not None:
                lat.append(m["median_latency_ms"])
        if tot_n:
            mode_agg[mode] = {
                "mode": mode,
                "queries": tot_n,
                "hit_rate": round(weighted_hit / tot_n, 4),
                "mrr": round(weighted_mrr / tot_n, 4),
                "p50_ms": round(sum(lat) / len(lat), 1) if lat else None,
            }
    return {
        "corpus": latest.get("corpus"),
        "facts": latest.get("facts"),
        "simulated": latest.get("simulated"),
        "queries": latest.get("queries"),
        "environment": latest.get("environment"),
        "rows": rows,
        "mode_aggregates": sorted(
            mode_agg.values(), key=lambda x: -x["hit_rate"]
        ),
    }


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    bench = benchmark_data()
    dataset = {
        "schema": "mem20.docs.analytics.repo-analytics.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "Analytics Reporter",
        "repo": {
            "owner": "bythewayz66-glitch",
            "name": "mem20",
            "analyzed_ref": base_ref(),
            "head_sha": head_sha(),
            "head_date": git("show", "-s", "--format=%aI", base_ref()).strip(),
            "head_subject": git("show", "-s", "--format=%s", base_ref()).strip(),
            "version": open(os.path.join(REPO, "VERSION")).read().strip()
            if os.path.exists(os.path.join(REPO, "VERSION"))
            else None,
        },
        "commits": commit_series(),
        "branches": branch_state(),
        "files": tracked_files(),
        "surface": surface_growth(),
        "benchmarks": benchmark_summary(bench),
        "benchmark_lineage": {
            "v1_modes": (bench.get("v1") or {}).get("modes_measured"),
            "v2_supersedes": (bench.get("v2") or {}).get("supersedes"),
            "v2_what_changed": (bench.get("v2") or {}).get("what_changed"),
            "experiment_runs": [
                {
                    "id": r.get("id"),
                    "date": r.get("date"),
                    "corpus": r.get("corpus"),
                    "modes_scored": r.get("modes_scored"),
                    "modes_unscored": r.get("modes_unscored"),
                }
                for r in ((bench.get("experiments") or {}).get("runs") or [])
            ],
        },
    }
    with open(OUT, "w") as fh:
        # Compact on purpose: the report is the human-readable artifact, and the
        # dataset ships on every clone. Key order is preserved for stable diffs.
        json.dump(dataset, fh, separators=(",", ":"), sort_keys=False)
        fh.write("\n")
    print(f"wrote {OUT}")
    print(
        f"commits={dataset['commits']['total_commits']} "
        f"files={dataset['files']['total']} "
        f"branches={dataset['branches']['remote_branches']} "
        f"at_risk={dataset['branches']['at_risk_commits']} "
        f"surface_points={len(dataset['surface']['points'])} "
        f"bench_rows={len(dataset['benchmarks']['rows'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
