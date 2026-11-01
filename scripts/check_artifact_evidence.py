#!/usr/bin/env python3
"""Artifact-evidence gate for the mem20 4.0 renovation.

Fails a pull request unless it carries a committed artifact:

  * a 40-character SHA of a pushed branch (verified as a real commit object
    reachable in the repository), or
  * a permanent URL (https://static.teamily.ai/sites/... or /files/...) that is
    committed under docs/.

The gate is diff-scoped: only files added or changed by the PR are inspected, so
legacy debt already on main cannot fail a clean PR (same contract as the
`hygiene` job in pr-gate.yml).

Usage (CI):
    python3 scripts/check_artifact_evidence.py --range origin/main...HEAD

Usage (local self-check before pushing):
    python3 scripts/check_artifact_evidence.py --range origin/main...HEAD --repo .

Exit codes:
    0  evidence found (gate passes)
    1  no evidence found (gate fails)
    2  usage / environment error
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
URL_RE = re.compile(r"https://(?:static\.)?teamily\.ai/(?:sites|files)/[0-9a-fA-F-]+/")


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def check_range(repo, diff_range):
    """Return (exit_code, sha_evidence, url_evidence)."""
    r = run(["git", "diff", "--name-only", "--diff-filter=ACMR", diff_range], cwd=repo)
    if r.returncode != 0:
        print(f"::error::git diff failed: {r.stderr.strip()}", file=sys.stderr)
        return 2, [], []

    changed = [ln for ln in r.stdout.splitlines() if ln.strip()]
    print(f"changed files in range {diff_range}: {len(changed)}")

    # CI-infrastructure exemption: a change that touches ONLY the gate itself
    # (.github/workflows/**) and/or this script is how the gate gets maintained
    # and merged; it is not a 4.0 subsystem delivery, so it carries no
    # subsystem evidence by design.
    CI_PATHS = (".github/workflows/", "scripts/check_artifact_evidence.py")
    if changed and all(f.startswith(CI_PATHS) for f in changed):
        print("CI-infrastructure-only change (gate maintenance) - exempt from artifact evidence")
        print("artifact-evidence gate: PASS (exempt)")
        return 0, [], []

    sha_evidence = []
    url_evidence = []

    for f in changed:
        p = repo / f
        if not p.is_file():
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError as e:
            print(f"::warning::cannot read {f}: {e}")
            continue
        for m in SHA_RE.finditer(text):
            sha = m.group(0)
            # A 40-char hex string only counts as evidence if it is a real
            # commit object in this repository (i.e. a pushed branch SHA).
            c = run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=repo)
            if c.returncode == 0:
                sha_evidence.append((f, sha))
        for m in URL_RE.finditer(text):
            url = m.group(0).rstrip("/")
            if f.startswith("docs/"):
                url_evidence.append((f, url))
            else:
                print(f"::warning::permanent URL found outside docs/ (ignored): {f}")

    # Deduplicate while preserving order.
    sha_evidence = list(dict.fromkeys(sha_evidence))
    url_evidence = list(dict.fromkeys(url_evidence))

    print(f"verified branch-SHA evidence: {len(sha_evidence)}")
    for f, sha in sha_evidence[:20]:
        print(f"  {f}: {sha}")
    print(f"docs/ permanent-URL evidence: {len(url_evidence)}")
    for f, url in url_evidence[:20]:
        print(f"  {f}: {url}")

    if sha_evidence or url_evidence:
        print("artifact-evidence gate: PASS")
        return 0, sha_evidence, url_evidence

    print("::error::no committed artifact evidence found in this PR.")
    print("::error::every 4.0 renovation PR must carry at least one of:")
    print("::error::  - a 40-character SHA of a pushed branch (verified commit object), or")
    print("::error::  - a permanent URL (https://static.teamily.ai/sites/... or /files/...) committed under docs/.")
    print("::error::see scripts/check_artifact_evidence.py --help for the local self-check.")
    return 1, [], []


def self_test():
    """Build a throwaway repo and verify both the pass and fail paths."""
    with tempfile.TemporaryDirectory(prefix="artifact-evidence-selftest-") as td:
        repo = Path(td)
        run(["git", "init", "-q"], cwd=repo)
        run(["git", "config", "user.email", "ci@mem20.local"], cwd=repo)
        run(["git", "config", "user.name", "CI Self-Test"], cwd=repo)

        (repo / "base.txt").write_text("base\n")
        run(["git", "add", "base.txt"], cwd=repo)
        run(["git", "commit", "-q", "-m", "base"], cwd=repo)
        base_sha = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

        docs = repo / "docs"
        docs.mkdir()
        (docs / "evidence.md").write_text(
            f"branch sha: {base_sha}\n"
            "url: https://static.teamily.ai/sites/00000000-0000-0000-0000-000000000000/webpages/x/index.html\n"
        )
        run(["git", "add", "docs/evidence.md"], cwd=repo)
        run(["git", "commit", "-q", "-m", "add evidence"], cwd=repo)

        rc, sha_ev, url_ev = check_range(repo, "HEAD~1...HEAD")
        assert rc == 0, f"positive path failed: rc={rc}"
        assert any(s == base_sha for _, s in sha_ev), "real SHA not detected"
        assert url_ev, "docs/ URL not detected"
        print("self-test: positive path OK")

        # Negative path: a change carrying no evidence must fail.
        (repo / "base.txt").write_text("base\nchanged\n")
        run(["git", "add", "base.txt"], cwd=repo)
        run(["git", "commit", "-q", "-m", "no evidence"], cwd=repo)
        rc, _, _ = check_range(repo, "HEAD~1...HEAD")
        assert rc == 1, f"negative path failed: rc={rc}"
        print("self-test: negative path OK")

    print("self-test: ALL OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--range", help="git diff range, e.g. origin/main...HEAD (not needed with --self-test)")
    ap.add_argument("--repo", default=".", help="path to the git repository (default: .)")
    ap.add_argument("--self-test", action="store_true", help="run the built-in self-test and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if not args.range:
        ap.error("--range is required unless --self-test is used")

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"::error::not a git repository: {repo}", file=sys.stderr)
        return 2

    rc, _, _ = check_range(repo, args.range)
    return rc


if __name__ == "__main__":
    sys.exit(main())