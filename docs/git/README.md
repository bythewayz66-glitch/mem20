# Git: push & merge discipline

**In force from 2026-10-22.** Applies to every contributor, human or agent.
This file is the authoritative rule set. The evidence behind each rule — verified
branch/issue/CI state, the full 29-item workstream label mapping, and the 12-branch
triage table — is held by Git Workflow Master as `PUSH-MERGE-DISCIPLINE.md`; ask in
the group before acting on any branch deletion, which needs the owner's approval anyway.

---

## Rule 0 — nobody commits to `main`

No direct commits to `main`, by anyone. Every change arrives as a pull request.

## Branch names

| Prefix | Use for |
|---|---|
| `feat/ws2-<slug>` | new capability in the code estate |
| `fix/ws2-<slug>` | repairing something red or broken |
| `docs/ws1-<slug>` | public-facing docs, README, site content |
| `content/ws3-<slug>` | sales / advertising collateral |
| `ci/ws2-<slug>` | `.github/workflows/**` only, no application code |
| `chore/ws2-<slug>` | lockfiles, dependency pins, `.gitignore` only |

One branch = one workstream = one issue. Lowercase, hyphenated. Branch from current `main`; rebase onto `main` before requesting review.
A branch with no linked issue is a draft, not a branch — create the issue first.

## Pull requests

`.github/pull_request_template.md` is mandatory. Five sections: linked issue, what changed,
**verbatim test evidence**, rollback, claim check. A PR missing any of them is closed, not left open.

A bare "tests pass" is not evidence. `pytest.ini` records that a bare `pytest` once ran 132 tests
and reported green while 1,400+ tests in other packages never executed — so **`collected` is as
important as `passed`**. A PR reporting "12 passed" while collection silently dropped 1,700 tests
is red, not green.

## Required checks

`.github/workflows/pr-gate.yml` runs two jobs.

**`hygiene` — required now.** Diff-scoped, so legacy debt already on `main` cannot fail every PR
while no new instance can land. Fails on newly added:

- `__pycache__/` or `*.pyc` (issue #22)
- `*.db` / `*.sqlite3` / `-wal` / `-shm` (issue #83)
- a dangling gitlink, mode `160000`
- an absolute host path: a home directory under `/home/` or `/Users/`, or the root account's
  `~/.venv` (issues #79, #80). This bullet deliberately names the shapes, not the literals, so the
  policy document does not itself fail the gate it defines.
- a secret-shaped line (`ghp_…`, `github_pat_…`, `sk-…`, `AKIA…`, private-key header). The count and
  rule are printed; the value never is, so the log cannot become the leak.

**`suite` — advisory until WS-2 item 1 lands, then required.** Always runs
`pytest --collect-only -q`, publishes `collected / baseline / exit` to the job summary, and fails if
`collected` drops below `docs/git/SUITE_BASELINE`. It tolerates a collection *error* only because
collection currently cannot succeed.

Arm it: set repository variable `MEM20_REQUIRE_GREEN_SUITE=1`, and set `docs/git/SUITE_BASELINE`
to the newly measured collection count.

> `SUITE_BASELINE` is `0` today — an honest placeholder. Anyone quoting a test number before the
> collection fix lands is quoting a number nobody can reproduce.

## Who merges

| Target | Merges | Reviewed by | Method |
|---|---|---|---|
| `fix/`, `ci/`, `chore/` → `main` | Git Workflow Master | 1 specialist from another workstream | rebase |
| `feat/ws2-*` → `main` | Git Workflow Master | Principal Architect + 1 specialist | rebase |
| `docs/`, `content/` → `main` | Market Research | 1 specialist | squash |
| anything touching `mcp/`, `pytest.ini`, `.github/workflows/` | Git Workflow Master only | Principal Architect + Git Workflow Master | rebase |

Default is **rebase and merge**, not squash: an atomic commit that reverts on its own is worth more
than a tidy first-parent line. Review is always by an agent other than the author.

## Hard constraint — WS-2 item 1 before any certification

`mcp/server.py:144` `exec()`s a bootstrap shim that raises a bare `SystemExit`, so `pytest.ini`'s
`testpaths = .` cannot collect. **Until that is fixed and collection is measured, no PR may be
certified and no green result may be quoted as evidence.** A suite that cannot collect cannot certify.

## Branch hygiene

`main` currently has 12 sibling branches, including three near-identical attempts at the same issue
set. The pathology is unmerged parallel attempts, not a missing branch model. Open one attempt at a
time; close the losers explicitly rather than leaving them to rot. Deleting branches requires the
repo owner's written approval — see the triage table in `PUSH-MERGE-DISCIPLINE.md` §9.

## Recovery

Never force-push `main` — revert forward in public:

```bash
git checkout -b fix/ws2-revert-<sha> main
git revert --no-edit <sha>
git push -u origin fix/ws2-revert-<sha>
```

Every rebase is recoverable via `git reflog` (90-day default) — recover onto a new branch, never reset a shared one.

```bash
git reflog
git branch rescue/ws2-<slug> <sha-from-reflog>
```

Updating a pushed branch: `git push --force-with-lease` — never `--force`, never on `main`.

Before anything destructive — history rewrite, `git filter-repo`, branch deletion, force-push to a
shared ref — post the command before running it. History shrinking is a coordinated step; #16 says so.
