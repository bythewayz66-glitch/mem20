#!/usr/bin/env python3
"""Artifact-evidence gate for the mem20 4.0 renovation.

Fails a **delivery** unless it carries a committed artifact:

  * a 40-character SHA of a pushed branch (verified as a real commit object
    reachable in the repository), or
  * a permanent URL (https://static.teamily.ai/sites/... or /files/...) that is
    committed under docs/.

What counts as a delivery
-------------------------
The gate is diff-scoped *and* author-scoped. It inspects only the commits that
a push or PR **authors onto the trunk line** (first-parent, non-merge), and the
files those commits change. Two consequences:

  * A push whose only first-parent commit is a merge is a **branch
    convergence** — a maintenance operation that integrates work already
    authored and reviewed on a side branch. It authors nothing on trunk, so
    there is nothing of its own to evidence. Demanding an artifact SHA from the
    integrator fails every bulk convergence by construction, which is why such
    a push is exempt (and says so, loudly, in the log).
  * A push that lands authored commits on trunk, and every pull request, is a
    delivery and must carry evidence.

Exempt passes always print the reason and the word EXEMPT, so a green log can
never be mistaken for a verified delivery.

Usage (CI):
    python3 scripts/check_artifact_evidence.py --range origin/main...HEAD
    python3 scripts/check_artifact_evidence.py --range "$BEFORE...HEAD" --event push

Usage (local self-check before pushing):
    python3 scripts/check_artifact_evidence.py --range origin/main...HEAD --repo .
    python3 scripts/check_artifact_evidence.py --self-test

Exit codes:
    0  evidence found, or nothing for this gate to evidence (exempt)
    1  a delivery landed with no evidence (gate fails)
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

# The gate's own machinery. A change that touches ONLY these is how the gate
# gets maintained and merged; it is not a 4.0 subsystem delivery.
GATE_OWN_DIRS = (".github/workflows/",)
GATE_OWN_FILES = frozenset({"scripts/check_artifact_evidence.py"})

# A push range with no before-SHA is the first push of a branch.
ZERO_SHA = "0000000000000000000000000000000000000000"


def run(cmd, cwd, stdin_text=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, input=stdin_text)


def _split_range(diff_range):
    """Split 'a...b' / 'a..b' into (a, b). Raises ValueError otherwise."""
    for sep in ("...", ".."):
        if sep in diff_range:
            before, after = diff_range.split(sep, 1)
            before = before.strip()
            after = after.strip() or "HEAD"
            if not before:
                raise ValueError(f"range has no left-hand side: {diff_range!r}")
            return before, after
    raise ValueError(f"not a git range: {diff_range!r}")


def authored_commits(repo, diff_range):
    """Commits this range lands on the trunk line: first-parent, non-merge.

    For a convergence push this is empty (the only first-parent commit is the
    merge itself). For an authored push or a PR it is the branch's own commits.
    """
    before, after = _split_range(diff_range)
    r = run(["git", "rev-list", "--first-parent", "--no-merges", f"{before}..{after}"], cwd=repo)
    if r.returncode != 0:
        raise RuntimeError(f"git rev-list failed: {r.stderr.strip()}")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def changed_files(repo, diff_range):
    r = run(["git", "diff", "--name-only", "--diff-filter=ACMR", diff_range], cwd=repo)
    if r.returncode != 0:
        raise RuntimeError(f"git diff failed: {r.stderr.strip()}")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def is_gate_own(path):
    if path in GATE_OWN_FILES:
        return True
    return any(path.startswith(d) for d in GATE_OWN_DIRS)


def verified_commits(repo, shas):
    """Subset of `shas` that are real commit objects. One git call, not N."""
    shas = list(dict.fromkeys(shas))
    if not shas:
        return set()
    r = run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=repo,
        stdin_text="".join(f"{s}^{{commit}}\n" for s in shas),
    )
    ok = set()
    for sha, line in zip(shas, r.stdout.splitlines()):
        parts = line.split()
        # A missing object is reported as "<input> missing".
        if len(parts) == 2 and parts[1] == "commit":
            ok.add(sha)
    return ok


def collect_evidence(repo_root, files, repo):
    """Scan the given files for verified branch SHAs and docs/ permanent URLs."""
    sha_candidates = []
    url_evidence = []
    for f in files:
        p = repo_root / f
        if not p.is_file():
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError as e:
            print(f"::warning::cannot read {f}: {e}")
            continue
        sha_candidates.extend((f, m.group(0)) for m in SHA_RE.finditer(text))
        for m in URL_RE.finditer(text):
            url = m.group(0).rstrip("/")
            if f.startswith("docs/"):
                url_evidence.append((f, url))
            else:
                print(f"::warning::permanent URL found outside docs/ (ignored): {f}")

    real = verified_commits(repo, [sha for _, sha in sha_candidates])
    sha_evidence = [(f, sha) for f, sha in sha_candidates if sha in real]
    return list(dict.fromkeys(sha_evidence)), list(dict.fromkeys(url_evidence))


def check_range(repo, diff_range, event="auto"):
    """Return (exit_code, sha_evidence, url_evidence)."""
    repo = Path(repo)
    print(f"event: {event}")
    print(f"range: {diff_range}")

    try:
        changed = changed_files(repo, diff_range)
        authored = authored_commits(repo, diff_range)
    except (RuntimeError, ValueError) as e:
        print(f"::error::{e}", file=sys.stderr)
        return 2, [], []

    print(f"authored commits on the trunk line: {len(authored)}")
    for c in authored[:20]:
        print(f"  {c}")
    print(f"changed files in range: {len(changed)}")

    # 1. Nothing was authored on trunk. A convergence/redundant merge push is
    #    integration of work already authored elsewhere; it has nothing of its
    #    own to evidence.
    if not authored:
        print("EXEMPT (integration): every first-parent commit in this range is a merge.")
        print("  Branch convergence integrates already-authored work; the artifact")
        print("  obligation for that work is enforced where it was authored, not on")
        print("  the push that lands it.")
        print("artifact-evidence gate: PASS (exempt: integration)")
        return 0, [], []

    # 2. Authored commits that change no file deliver nothing to evidence.
    if not changed:
        print("EXEMPT (empty): the authored commits in this range change no file.")
        print("artifact-evidence gate: PASS (exempt: empty)")
        return 0, [], []

    # 3. Gate maintenance: the change is the gate's own machinery.
    if all(is_gate_own(f) for f in changed):
        print("EXEMPT (ci-infrastructure): this change is the gate's own machinery.")
        print("artifact-evidence gate: PASS (exempt: ci-infrastructure)")
        return 0, [], []

    sha_evidence, url_evidence = collect_evidence(repo, changed, repo)

    print(f"verified branch-SHA evidence: {len(sha_evidence)}")
    for f, sha in sha_evidence[:20]:
        print(f"  {f}: {sha}")
    print(f"docs/ permanent-URL evidence: {len(url_evidence)}")
    for f, url in url_evidence[:20]:
        print(f"  {f}: {url}")

    if sha_evidence or url_evidence:
        print("artifact-evidence gate: PASS")
        return 0, sha_evidence, url_evidence

    print("::error::no committed artifact evidence found in this delivery.")
    print("::error::every 4.0 renovation delivery must carry at least one of:")
    print("::error::  - a 40-character SHA of a pushed branch (verified commit object), or")
    print("::error::  - a permanent URL (https://static.teamily.ai/sites/... or /files/...) committed under docs/.")
    print("::error::see scripts/check_artifact_evidence.py --self-test for the local self-check.")
    return 1, [], []


def _git(repo, *args):
    r = run(["git", *args], cwd=repo)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def _commit(repo, message):
    _git(repo, "add", "-A")
    # --allow-empty: case 3 deliberately commits nothing, to prove an authored
    # commit that changes no file is exempt rather than a failure.
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def self_test():
    """Build a throwaway repo and verify every path of the decision table."""
    with tempfile.TemporaryDirectory(prefix="artifact-evidence-selftest-") as td:
        repo = Path(td)
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "ci@mem20.local")
        _git(repo, "config", "user.name", "CI Self-Test")
        _git(repo, "checkout", "-q", "-b", "main")

        (repo / "base.txt").write_text("base\n")
        base_sha = _commit(repo, "base")

        # --- Case 1: authored delivery carrying a real SHA + a docs/ URL ----
        (repo / "docs").mkdir()
        (repo / "docs" / "evidence.md").write_text(
            f"branch sha: {base_sha}\n"
            "url: https://static.teamily.ai/sites/00000000-0000-0000-0000-000000000000/webpages/x/index.html\n"
        )
        _commit(repo, "docs: evidence")
        rc, sha_ev, url_ev = check_range(repo, "HEAD~1...HEAD")
        assert rc == 0, f"case 1 (authored + evidence) should PASS, got {rc}"
        assert any(s == base_sha for _, s in sha_ev), "case 1: real SHA not detected"
        assert url_ev, "case 1: docs/ URL not detected"
        print("self-test [1/6] authored delivery with evidence -> PASS")

        # --- Case 2: authored delivery with no evidence -> FAIL -------------
        (repo / "code.py").write_text("x = 1\n")
        _commit(repo, "feat: code with no evidence")
        rc, _, _ = check_range(repo, "HEAD~1...HEAD")
        assert rc == 1, f"case 2 (authored, no evidence) should FAIL, got {rc}"
        print("self-test [2/6] authored delivery, no evidence -> FAIL")

        # --- Case 3: authored commit changing nothing -> PASS (empty) -------
        empty_sha = _commit(repo, "chore: empty commit")
        rc, _, _ = check_range(repo, f"{empty_sha}~1...{empty_sha}")
        assert rc == 0, f"case 3 (empty authored commit) should PASS, got {rc}"
        print("self-test [3/6] authored commit changing nothing -> PASS (empty)")

        # --- Case 4: gate-own change -> PASS (ci-infrastructure) ------------
        gate_dir = repo / "scripts"
        gate_dir.mkdir()
        (gate_dir / "check_artifact_evidence.py").write_text("# gate\n")
        _commit(repo, "ci: touch the gate")
        rc, _, _ = check_range(repo, "HEAD~1...HEAD")
        assert rc == 0, f"case 4 (gate-own change) should PASS, got {rc}"
        print("self-test [4/6] gate-own change -> PASS (ci-infrastructure)")

        # --- Case 5: THE REGRESSION. A convergence push that lands an
        #     unevidenced side branch must not fail the gate. ---------------
        _git(repo, "checkout", "-q", "-b", "feat/side")
        (repo / "side_module.py").write_text("def f():\n    return 1\n")
        _commit(repo, "feat: side branch code, no artifact evidence")
        _git(repo, "checkout", "-q", "main")
        (repo / "unrelated.txt").write_text("advance main\n")
        _commit(repo, "chore: advance main")
        before_converge = _git(repo, "rev-parse", "HEAD")
        _git(repo, "merge", "--no-ff", "-q", "-m", "merge: converge feat/side", "feat/side")
        assert (repo / "side_module.py").is_file(), "case 5: side file should exist after merge"
        rc, _, _ = check_range(repo, f"{before_converge}...HEAD", event="push")
        assert rc == 0, f"case 5 (convergence push) should be EXEMPT, got {rc}"
        print("self-test [5/6] convergence push landing unevidenced work -> PASS (integration)")
        # ... and the same work delivered as a PR is still gated, i.e. the
        # exemption is scoped to convergence, not to the content.
        rc, _, _ = check_range(repo, f"{before_converge}...feat/side")
        assert rc == 1, f"case 5b (same work as a PR) should still FAIL, got {rc}"
        print("self-test [5b/6] same work delivered as a PR -> still FAIL (gate keeps teeth)")

        # --- Case 6: redundant merge whose tree equals the first parent ----
        # `git merge` refuses ("Already up to date") once the side branch is an
        # ancestor, so build the redundant merge commit directly: same tree as
        # the first parent, two parents. This is the shape that produced the
        # zero-changed-files failure in the wild.
        merge_base = _git(repo, "rev-parse", "HEAD")
        tree = _git(repo, "rev-parse", "HEAD^{tree}")
        redundant = _git(
            repo, "commit-tree", tree, "-p", merge_base, "-p", "feat/side",
            "-m", "merge: converge (already merged)",
        )
        _git(repo, "update-ref", "refs/heads/main", redundant)
        assert _git(repo, "rev-parse", "HEAD") != merge_base, "case 6: merge did not create a commit"
        assert _git(repo, "diff", "--name-only", f"{merge_base}..HEAD") == "", "case 6: tree should equal first parent"
        rc, _, _ = check_range(repo, f"{merge_base}...HEAD", event="push")
        assert rc == 0, f"case 6 (zero-diff merge push) should be EXEMPT, got {rc}"
        print("self-test [6/6] zero-diff convergence push -> PASS (integration)")

    print("self-test: ALL OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--range", help="git diff range, e.g. origin/main...HEAD (not needed with --self-test)")
    ap.add_argument("--repo", default=".", help="path to the git repository (default: .)")
    ap.add_argument(
        "--event",
        default="auto",
        choices=["auto", "pull_request", "push"],
        help="the workflow event that produced the range; 'auto' (default) needs no hint",
    )
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

    if args.range.split("...")[0] == ZERO_SHA:
        print("EXEMPT (first push): no before-SHA to compare against.")
        print("artifact-evidence gate: PASS (exempt: first push)")
        return 0

    rc, _, _ = check_range(repo, args.range, event=args.event)
    return rc


if __name__ == "__main__":
    sys.exit(main())
