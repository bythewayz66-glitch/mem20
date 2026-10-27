#!/usr/bin/env python3
"""Refresh the mem20 02:47Z push-checkpoint ledger from live git evidence.

Rules this script enforces (do not weaken):
  1. SHA columns are filled only from a real remote check (git ls-remote + a
     fetch of the advertised ref). An agent's chat claim is never an input.
     There is no flag to trust a claim.
  2. A commit counts as "pushed in this window" only if its committer date is
     later than the checkpoint baseline commit. A commit that merely sits on some
     long-lived branch is an old stranded commit, not this window's work.
  3. Attribution is per FILE, from an explicit path-ownership map, and each file
     is attributed to the NEWEST commit touching it. One branch can carry several
     agents' work, and one agent's "tool count fix" can delete another agent's
     deliverable. Aggregating per branch hides both.
  4. PUSHED is not DONE. Every owned file is screened: deleted, emptied, or
     placeholder-only => the row records a REGRESSION even though a push happened.
     Deleting README.md is not fixing the tool count.

Usage:
    python3 refresh_ledger.py --dry-run     # verify + print, write nothing
    python3 refresh_ledger.py              # verify + write ledger/commits/snapshot

Outputs (next to this script):
    ledger.md                       the scoreboard, one row per agent
    ledger-2026-10-27T0247Z.tsv     machine-readable twin of the scoreboard
    commits-2026-10-27T0247Z.tsv    one row per commit pushed in this window
    snapshot-2026-10-27T0247Z.json  program counters + full ref map

Requires a git clone of the repo with origin pointing at GitHub; the checkpoint
itself is pushed through the GitHub contents API (no push credentials needed).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = "bythewayz66-glitch/mem20"
REPO_URL = f"https://github.com/{REPO}.git"

# Baseline for this run: the ops-record commit carrying the owner's roster.
# main was c64c113e before it; it is BASELINE now.
BASELINE_SHA = "7c0b3e8d9525cd8c3a9f8f1825267aed52fac68a"
BASELINE_WHEN = "2026-10-27T01:50:05Z"
DEADLINE_UTC = "2026-10-27T02:47:00Z"
DEADLINE_LOCAL = "2026-10-27 20:47 MDT"

# Branch count immediately before the push window opened (16 at 01:52Z).
BRANCHES_AT_BASELINE = 16

PLACEHOLDER = re.compile(r"^\s*(<<.*>>|<[a-z-]*placeholder>|todo|tbd)\s*$", re.I)

# ---- who owns which path -------------------------------------------------
# (member, workstream, deliverable, expected ref/path, [glob patterns])
ROSTER = [
    ("Mem20 Content Creator", "a", "Rewrite the README narrative to 270 tools / 27 domains",
     "README.md", ["README.md"]),
    ("Webpage Developer", "a/b", "270/27 on the served page + rebuild/publish the launch page",
     "docs/index.html, docs/launch/", ["docs/index.html", "docs/launch/*"]),
    ("GitHub Repo Assistant", "a/c", "Tool-count authority; rebase fix/issues-5-18-complete and open a PR",
     "docs/02-tools-reference.md, docs/05-complete-tools-reference.md, docs/TOOL-DOMAINS.md",
     ["docs/02-tools-reference.md", "docs/05-complete-tools-reference.md", "docs/TOOL-DOMAINS.md"]),
    ("mem20 GTM Team Lead", "a", "Align launch copy to 270/27",
     "docs/gtm/*",
     ["docs/gtm/*"]),
    ("Slides Assistant", "b", "Commit the launch deck source under docs/launch/",
     "docs/launch/*", ["docs/launch/*"]),
    ("Super Agent", "c/e", "CI gate requiring a committed artifact or URL; work the 8 open issues",
     ".github/workflows/*", [".github/workflows/*"]),
    ("Mem20 Benchmark Dataset Builder", "d", "Land feat/scale-corpus-2000; re-run all 7 retrieval modes",
     "docs/benchmarks/*, benchmarks/*", ["docs/benchmarks/*", "benchmarks/*"]),
    ("Experiment Tracker", "d", "Register the 7 benchmark runs",
     "benchmarks/runs/*", ["benchmarks/runs/*"]),
    ("Market Research", "d", "TAM/SAM/SOM with a source per figure",
     "docs/market-research/*tam*", ["docs/*market*", "docs/*tam*"]),
    ("Server Builder", "e", "Green PR #103 (Syntax gate, Tests, Rust braid); close #30/#43",
     "mem20agentz/pyproject.toml, mem20agentz/tests/*",
     ["mem20agentz/pyproject.toml", "mem20agentz/tests/*"]),
    ("mem20-frontends", "e", "mem20controlz #35-#40 (Tauri shell, sidecar, tray, cmd-K, UX, packaging)",
     "mem20controlz/*", ["mem20controlz/*"]),
    ("UX Researcher", "e", "Task flows / wireframes for mem20controlz",
     "docs/design/mem20controlz/*", ["docs/design/*"]),
    ("Analytics Reporter", "e", "KPI definitions",
     "docs/analytics/*", ["docs/analytics/*"]),
    ("mem20-webdev", "f/g", "Triage 60 orphan commits; delete 3 merged refs; archive-tag 12",
     "docs/ops/branch-audit.md (+ ref deletions)", ["docs/ops/branch-audit.md"]),
    ("Mem20-admin", "f", "Co-lead orphan-commit triage; branch -> disposition -> SHA table",
     "docs/ops/*", ["docs/ops/*"]),
    ("Mem20 C++ Expert", "h", "Reconcile the 1.0.0 tarball; add ctest to CI",
     "sdk/cpp/*", ["sdk/cpp/*"]),
    ("Mem20-Perl-Expert", "h", "Land the SDK tree with packaging/examples/CI; state stubs",
     "sdk/perl/*", ["sdk/perl/*"]),
    ("Mem20-Ruby-Expert", "h", "Finish tests, gemspec and CI for mem20-sdk-ruby",
     "mem20-sdk-ruby/*", ["mem20-sdk-ruby/*"]),
    ("Pricing Analyst", "h", "$14,000 blended ACV model",
     "docs/finance/*acv*", ["docs/finance/*", "docs/*acv*"]),
    ("Finance Assistant", "h", "Tie cost-to-serve to ACV",
     "docs/finance/*cost*", ["docs/*cost*"]),
    ("Mem20-naration", "h", "60-90s launch narration script + shot list",
     "docs/media/*", ["docs/media/*"]),
    ("mem20 Orchestrator", "all", "Assignment + verification pass",
     "published/checkpoints/*", ["published/checkpoints/*"]),
]


def run(args, cwd):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def out_of(args, cwd):
    return run(args, cwd)[1]


def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repo-dir", default=str(Path(__file__).resolve().parents[2]))
    args = ap.parse_args()
    repo = Path(args.repo_dir)

    # ---- 1. live remote snapshot -----------------------------------------
    heads = {}
    for line in out_of(["git", "ls-remote", "--heads", REPO_URL], repo).splitlines():
        sha, ref = line.split("\t")
        heads[ref.replace("refs/heads/", "")] = sha
    main_sha = heads.get("main", "")
    verified_at = iso_now()

    # ---- 2. sync local mirror --------------------------------------------
    out_of(["git", "fetch", "--all", "--prune", "--quiet"], repo)

    # ---- 3. commits pushed inside the window -----------------------------
    commits = []
    for br, tip in heads.items():
        if run(["git", "rev-parse", "--verify", "--quiet", tip], repo)[0] != 0:
            continue  # advertised but not yet fetchable
        for s in out_of(["git", "rev-list", f"{BASELINE_SHA}..{tip}"], repo).split():
            meta = out_of(["git", "show", "-s", "--format=%cI%x09%an%x09%s", s], repo)
            when, author, subj = (meta.split("\t") + ["", "", ""])[:3]
            if not when or parse_iso(when) <= parse_iso(BASELINE_WHEN):
                continue  # old stranded commit, not this window
            numstat = out_of(["git", "show", "--numstat", "--format=", s], repo)
            adds = dels = 0
            files = []
            for ln in numstat.splitlines():
                parts = ln.split("\t")
                if len(parts) < 3:
                    continue
                a, d, f = parts[0], parts[1], parts[2]
                adds += int(a) if a.isdigit() else 0
                dels += int(d) if d.isdigit() else 0
                files.append((f, int(a) if a.isdigit() else 0, int(d) if d.isdigit() else 0))
            ph = []
            for f, a, d in files:
                if not f.endswith((".md", ".html", ".txt", ".py", ".json", ".patch")):
                    continue
                body = out_of(["git", "show", f"{s}:{f}"], repo)
                nonblank = [l for l in body.splitlines() if l.strip()]
                if not nonblank or all(PLACEHOLDER.match(l) for l in nonblank):
                    ph.append(f)
            commits.append({
                "branch": br, "sha": s, "when": when, "author": author, "subject": subj,
                "adds": adds, "dels": dels, "files": files, "placeholder": ph,
            })

    # ---- 4. per-agent, per-file attribution ------------------------------
    rows = []
    for member, ws, deliverable, expected, patterns in ROSTER:
        newest = {}  # one entry per owned file, from the newest commit touching it
        for c in commits:
            for f, a, d in c["files"]:
                if not any(fnmatch.fnmatch(f, p) for p in patterns):
                    continue
                if d and a == 0:
                    state = "DELETED"
                elif f in c["placeholder"]:
                    state = "PLACEHOLDER"
                elif a == 0 and d == 0:
                    state = "EMPTY"
                else:
                    state = "REAL"
                prev = newest.get(f)
                if prev is None or parse_iso(c["when"]) >= parse_iso(prev[0]["when"]):
                    newest[f] = (c, f, a, d, state)
        touched = list(newest.values())

        if not touched:
            rows.append({
                "member": member, "workstream": ws, "deliverable": deliverable,
                "expected": expected, "commit_sha": "—", "pushed": "no",
                "verdict": "NOT-PUSHED",
                "evidence": "no commit newer than the baseline touches an owned path on any live ref",
                "screening": "nothing to screen",
            })
            continue

        bad = [t for t in touched if t[4] in ("DELETED", "PLACEHOLDER", "EMPTY")]
        good = [t for t in touched if t[4] == "REAL"]
        last = sorted(touched, key=lambda t: parse_iso(t[0]["when"]))[-1][0]
        if bad and not good:
            verdict = "PUSHED-REGRESSION"
        elif bad:
            verdict = "PUSHED-PARTIAL"
        else:
            verdict = "PUSHED-SUBSTANTIVE"

        bits = []
        for st in ("REAL", "DELETED", "PLACEHOLDER", "EMPTY"):
            fs = [t[1] for t in touched if t[4] == st]
            if fs:
                bits.append(f"{st.lower()}: {', '.join(sorted(set(fs)))}")
        rows.append({
            "member": member, "workstream": ws, "deliverable": deliverable,
            "expected": expected, "commit_sha": last["sha"], "pushed": "yes",
            "verdict": verdict,
            "evidence": f"{last['sha'][:12]} on {last['branch']} at {last['when']} — {last['subject'][:64]}",
            "screening": "; ".join(bits),
        })

    # ---- 5. counters ------------------------------------------------------
    ahead = {}
    for b, tip in heads.items():
        if b == "main":
            continue
        n = out_of(["git", "rev-list", "--count", f"{BASELINE_SHA}..{tip}"], repo)
        ahead[b] = int(n) if n.isdigit() else 0

    deleted_refs = max(0, BRANCHES_AT_BASELINE - len(heads))
    by_verdict = {}
    for r in rows:
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1

    snapshot = {
        "checkpoint_utc": DEADLINE_UTC, "checkpoint_local": DEADLINE_LOCAL,
        "repo": f"https://github.com/{REPO}",
        "verified_at_utc": verified_at,
        "baseline_sha": BASELINE_SHA, "baseline_when_utc": BASELINE_WHEN,
        "main_head": main_sha, "main_head_short": main_sha[:12],
        "main_moved": main_sha != BASELINE_SHA,
        "remote_branch_count": len(heads),
        "branches_at_baseline": BRANCHES_AT_BASELINE,
        "branches_deleted_this_window": deleted_refs,
        "branches_ahead_of_baseline": ahead,
        "commits_pushed_this_window": len({c["sha"] for c in commits}),
        "agents": len(rows),
        "by_verdict": by_verdict,
        "heads": heads,
        "commits": [{k: v for k, v in c.items() if k != "files"} | {"file_count": len(c["files"])}
                    for c in commits],
    }

    print(f"verified_at  {verified_at}")
    print(f"main         {main_sha}  moved={main_sha != BASELINE_SHA}")
    print(f"branches     {len(heads)}  (deleted this window: {deleted_refs})")
    print(f"new commits  {snapshot['commits_pushed_this_window']} pushed inside the window")
    print(f"verdicts     {by_verdict}")

    if args.dry_run:
        for r in rows:
            print(f"  {r['verdict']:<19} {r['member']:<32} {r['commit_sha'][:12]:<13} {r['screening'][:95]}")
        return 0

    here = Path(__file__).resolve().parent
    (here / "snapshot-2026-10-27T0247Z.json").write_text(json.dumps(snapshot, indent=2) + "\n")

    hdr = ["member", "workstream", "deliverable", "expected_branch_or_path", "commit_sha",
           "pushed", "verdict", "verified_at_utc", "evidence", "file_screening"]
    lines = ["\t".join(hdr)]
    for r in rows:
        lines.append("\t".join([r["member"], r["workstream"], r["deliverable"], r["expected"],
                                r["commit_sha"], r["pushed"], r["verdict"], verified_at,
                                r["evidence"], r["screening"]]))
    (here / "ledger-2026-10-27T0247Z.tsv").write_text("\n".join(lines) + "\n")

    ch = ["sha", "branch", "committed_at", "author", "adds", "dels", "file_count",
          "placeholder_files", "subject"]
    cl = ["\t".join(ch)]
    for c in sorted(commits, key=lambda x: x["when"]):
        cl.append("\t".join([c["sha"], c["branch"], c["when"], c["author"], str(c["adds"]),
                             str(c["dels"]), str(len(c["files"])),
                             ",".join(c["placeholder"]) or "-", c["subject"]]))
    (here / "commits-2026-10-27T0247Z.tsv").write_text("\n".join(cl) + "\n")

    write_markdown(rows, here / "ledger.md", snapshot, verified_at)
    print(f"wrote 4 files in {here}")
    return 0


def write_markdown(rows, path, snap, verified_at):
    """Emit the scoreboard: one row per agent, verdict folded into a notes column."""
    n_yes = sum(1 for r in rows if r["pushed"] == "yes")
    n_no = sum(1 for r in rows if r["pushed"] == "no")
    n_unk = sum(1 for r in rows if r["pushed"] == "unknown")

    out = []
    out.append("# mem20 push-checkpoint ledger — 2026-10-27T02:47Z\n")
    out.append(f"Deadline **{snap['checkpoint_utc']}** ({snap['checkpoint_local']}) "
               f"against https://github.com/{REPO}.\n")
    out.append(f"**Verified at:** {verified_at} (single point-in-time snapshot)\n")
    out.append(f"**Baseline:** `{snap['baseline_sha']}` ({snap['baseline_when_utc']}) — the "
               "2026-10-26 ops record carrying the owner's assignment roster.\n")
    out.append(f"**main now:** `{snap['main_head']}` "
               f"({'moved' if snap['main_moved'] else 'unchanged'} vs baseline)\n")
    out.append(f"**Scoreboard:** {n_yes} pushed / {n_no} not pushed / {n_unk} unknown "
               f"out of {len(rows)} agents.\n")
    out.append("")
    out.append("Every SHA below came from `git ls-remote` plus a fetch of the advertised ref, "
               "then a per-file diff against the baseline. No SHA in this table was taken "
               "from anything an agent said in chat.\n")
    out.append("")
    out.append("| Member | Deliverable | Expected branch/path | Commit SHA | Pushed | Verified-at | Notes |")
    out.append("|---|---|---|---|---|---|---|")
    for r in rows:
        sha = r["commit_sha"] if r["pushed"] == "yes" else "—"
        note = r["verdict"] if r["pushed"] == "yes" else ""
        if r["pushed"] == "yes" and r["screening"]:
            note = f"{note}: {r['screening']}"
        if r["pushed"] == "no":
            note = "nothing on any live ref touches this path after the baseline"
        note = note.replace("|", "/")
        if len(note) > 150:
            note = note[:147].rsplit(",", 1)[0] + " …"
        out.append(f"| {r['member']} | {r['deliverable']} | `{r['expected']}` | "
                   f"{('`' + sha + '`') if sha != '—' else '—'} | {r['pushed']} | "
                   f"{verified_at} | {note} |")
    out.append("")
    out.append("## Program state at snapshot\n")
    out.append(f"- Remote branches: **{snap['remote_branch_count']}** "
               f"(baseline had {snap['branches_at_baseline']}; "
               f"{snap['branches_deleted_this_window']} ref(s) deleted this window)")
    out.append(f"- Commits pushed inside the window: **{snap['commits_pushed_this_window']}**")
    for c in snap["commits"]:
        flag = ""
        if c["placeholder"]:
            flag = f" — PLACEHOLDER ONLY: {', '.join(c['placeholder'])}"
        out.append(f"  - `{c['sha'][:12]}` {c['when']} on `{c['branch']}` "
                   f"(+{c['adds']}/−{c['dels']}) {c['subject']}{flag}")
    out.append("")
    out.append("## Read this before trusting a green row\n")
    out.append("A `pushed: yes` means a commit carrying the agent's path reached the remote "
               "after the baseline. It does not mean the deliverable is correct. The verify "
               "pass found one branch, `chore/tool-count-270-27`, whose tip **deletes** "
               "`README.md`, `docs/index.html`, `docs/02-tools-reference.md` and "
               "`docs/05-complete-tools-reference.md`, and whose `docs/ops/270-27.patch` "
               "is a one-line placeholder. Rows whose only change is a deletion or a "
               "placeholder file are marked `PUSHED-REGRESSION` in Notes. Do not merge that "
               "branch; do not count those rows as delivered.\n")
    out.append("Verified-at is the timestamp of one snapshot, not a running clock — the "
               "deadline itself is 02:47Z and pushes landing after this snapshot are not "
               "reflected here.\n")
    out.append("")
    out.append("---\n")
    out.append("As an AI Agent, I cannot provide legally protected, personalized investment "
               "advice. This analysis is for informational purposes only and does not "
               "constitute investment advice or recommendations. Consult a licensed "
               "financial advisor before making investment decisions.\n")
    path.write_text("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
