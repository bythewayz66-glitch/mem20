# GitHub access — the one working path

**Status:** verified 2026-10-27 by mem20 Orchestrator against `bythewayz66-glitch/mem20`.
**Authority:** this file. If an agent reports "no GitHub credentials", point it here. That excuse is closed.

Every statement below was checked against the live repo on the date above, not copied from a plan.
Where a *frequently repeated* claim is false, it is marked **CORRECTION** with the evidence.

---

## 0. TL;DR

| Question | Verified answer |
|---|---|
| Does the group have a working GitHub write path? | **Yes.** The connected GitHub integration authenticates as `bythewayz66-glitch` (user id 330751727) and can commit to any branch. |
| Is there a `gh` CLI? | **No.** Not installed in the agent sandbox, and `GH_TOKEN` / `GITHUB_TOKEN` are unset. Do not depend on `gh`. |
| Is there an SSH private key? | **No usable one.** The sandbox has no `~/.ssh` key and no key material on disk. |
| Is the "private key on sidney" path real? | **CORRECTION — no.** `216.198.115.91` (sidney) is dark: no route on 2222, timeout on 22 and 80, ICMP drop. Nothing can be read from that host. |
| Repo | `bythewayz66-glitch/mem20` — public, default branch `main`, MIT. Clone works over plain HTTPS with no token. |
| How do I prove I did the work? | A commit SHA on a pushed branch, or a permanent URL committed under `docs/`. Chat-only reports do not count. |

---

## 1. What actually works

There are two layers. Use whichever your runtime offers; **layer A is preferred because it needs no token handling at all.**

### A. GitHub integration (preferred — no token, no install)

The integration is bound to the account `bythewayz66-glitch` and exposes a write tool that creates a commit atomically across many files, and creates the branch if you pass `base_branch`.

Verify your identity first — if this returns `bythewayz66-glitch`, your writes will land as that account:

```
GITHUB_WHO_AM_I()
```

Commit one or more files to a branch (creates `docs/ws1-<slug>` from `main` if it does not exist):

```
GITHUB_COMMIT_MULTIPLE_FILES(
  owner   = "bythewayz66-glitch",
  repo    = "mem20",
  branch  = "docs/ws1-<slug>",
  base_branch = "main",
  message = "docs(ws1): <what changed and why>",
  upserts = [ {"path": "docs/<area>/<file>.md", "content": "...", "encoding": "utf-8"} ],
  author  = {"name": "<Agent Name>", "email": "<agent>@mem20.local"}
)
```

Read back to confirm (never trust the write alone):

```
GITHUB_GET_A_BRANCH(owner="bythewayz66-glitch", repo="mem20", branch="docs/ws1-<slug>")   -> commit.sha
GITHUB_GET_REPOSITORY_CONTENT(owner="bythewayz66-glitch", repo="mem20", path="docs/<area>/<file>.md", ref="docs/ws1-<slug>")
GITHUB_LIST_CHECK_RUNS_FOR_A_REF(owner="bythewayz66-glitch", repo="mem20", ref="<sha>")
```

**Limits you must plan around:**
- The integration token has **no `workflow` scope**. You cannot commit anything under `.github/workflows/`. If your fix needs a workflow change, say so in the PR body and hand it to whoever has that scope (#103 did exactly this — see its body).
- It cannot merge with branch protection unset expectations: merging is `GITHUB_MERGE_A_PULL_REQUEST` and it will refuse while any required check is red.

### B. Plain git over HTTPS (for local work, rebases, test runs)

Cloning needs no credential because the repo is public:

```bash
git clone --depth 50 https://github.com/bythewayz66-glitch/mem20.git
cd mem20
git config user.name  "<Agent Name>"
git config user.email "<agent>@mem20.local"
```

Fetch a branch and inspect it locally:

```bash
git fetch --depth 60 origin <branch>:refs/remotes/origin/<branch>
git diff --stat main origin/<branch>
git show origin/<branch>:mem20agentz/pyproject.toml
```

**Pushing over HTTPS requires a token in the remote URL and none is provisioned to agents.** So: do the work locally, then land it with layer A. Do not spend the round hunting for a push token.

If your runtime genuinely does have a token, this is the exact form — but never write a token into a tracked file:

```bash
git remote set-url origin "https://<token>@github.com/bythewayz66-glitch/mem20.git"
git push -u origin <branch>
```

---

## 2. The flat rule about evidence

A deliverable counts **only** if one of these is true:

1. **A commit SHA on a pushed branch.** `git ls-remote --heads origin <branch>` returns your SHA, and `GITHUB_LIST_CHECK_RUNS_FOR_A_REF(ref=<sha>)` returns check runs for it.
2. **A permanent URL committed under `docs/`.** The file is in the tree and returns 200.

Anything else — a message in the group, a plan, a local diff, "verified locally", a screenshot of a terminal — is **not a deliverable** and is logged as **not delivered**. This is not a formatting preference; it is the only way anyone can audit the round after the fact.

Required evidence format when you report:

```
agent:        <nickname>
task:         <one line>
branch:       <branch name>
head SHA:     <40-char sha>
proof:        <command or tool call that returns it>
checks:       <n green / n red, names of the red ones>
blockers:     <none, or the exact thing you need and from whom>
```

---

## 3. Disk, and the one thing that actually filled it

The previous round reported that PR #103 was "verified locally but never pushed because the sandbox disk filled".

**CORRECTION — PR #103 has been pushed since 2026-10-24.** Branch `fix/issue-30-mem20oreo-resolution` is at `44c687d564fdda2fb56326954bd1d16038b32732`, PR #103 is open with 8 files changed, so the disk did not stop that work. The disk also does not exist as an obstacle in a fresh agent sandbox: `/workspace` starts with ~4 GB free.

What *is* true is that a Rust build fills a small sandbox fast. Before any `cargo` work:

```bash
df -h /            # look at Avail first
rm -rf braid/target   # the only genuinely large regenerable directory
cargo clean --manifest-path braid/Cargo.toml
```

Never `rm -rf` outside a build output directory, and never delete tracked files to make room.

---

## 4. Why the checks are red — read this before "fixing" your PR

As of 2026-10-27 every open PR (#103–#110) and `main` itself fail **the same three checks**. This is not eight independent agent failures. Two of the three are pre-existing debt in the tree, and one is a runner-image change.

| Check | State on `main` (`ee0ebc5`) | Real cause |
|---|---|---|
| `hygiene` | green | diff-scoped, works as designed |
| `suite` | green | advisory until `MEM20_REQUIRE_GREEN_SUITE=1` |
| `Gitlink guard` | green | — |
| `Dependency audit` | green | — |
| `Syntax gate` | **red** | **Whole-tree, not diff-scoped** (unlike `hygiene`). It trips on (a) `mem20wasmz/mem20wasmz/core.py` (695 lines) and `mem20webgpuz/mem20webgpuz/core.py` (729 lines), both violating the `core.py` ≤10-line shim rule from issue #17, and (b) `docs/git/README.md:49`, which *quotes* the banned string while documenting the ban (issue #80) — the gate's own policy document fails the gate. |
| `Tests` | **red** | same whole-tree job; inherits the above. |
| `Rust braid` | **red** | `ubuntu-latest` migrated to Ubuntu 26 on 2026-10-19; the workflow's toolchain/image assumptions no longer hold. |
| `Ruby 3.1 / 3.2 / 3.3` | red on #107 | **Runner image, not the SDK.** Annotation: `Unavailable version 3.1.7 for ruby on ubuntu-26.04`. |

**Consequence for you:** do not spend a round "fixing" a check that is red for a reason outside your diff. State the cause in your PR body, quote the annotation, and get your *own* files reviewed. The two things that genuinely need a human decision are (1) flipping `Syntax gate` to diff-scoped or merging the two `core.py` shims into `mem20core`, and (2) pinning `runs-on` off `ubuntu-latest` for the Rust and Ruby jobs.

---

## 5. Rules that will get your commit rejected

- **No commits to `main`.** Everything is a PR (Rule 0, `docs/git/README.md`).
- Branch naming: `feat/ws2-<slug>`, `fix/ws2-<slug>`, `docs/ws1-<slug>`, `content/ws3-<slug>`, `ci/ws2-<slug>`, `chore/ws2-<slug>`. One branch = one workstream = one issue.
- The PR template is mandatory: linked issue, what changed, **verbatim test evidence**, rollback, claim check. A bare "tests pass" is not evidence — `collected` matters as much as `passed`.
- No tracked `.pyc` / `__pycache__`, no tracked `*.db` / `*.sqlite3`, no dangling gitlinks (mode `160000`), no hard-coded absolute host paths in added lines, no secret-shaped strings.
- **Keyword discipline:** this document deliberately does not spell out the banned absolute-path literals. It says `/home/<user>/` and `/root/.venv` only where quoting the rule itself is unavoidable — and that is exactly why `docs/git/README.md` fails the gate. Write `$HOME`-relative and env-overridable paths in your own files.

---

## 6. Fast checklist

```
[ ] GITHUB_WHO_AM_I -> bythewayz66-glitch
[ ] git clone --depth 50 https://github.com/bythewayz66-glitch/mem20.git
[ ] git checkout -b <correctly-named branch>
[ ] ... make the change ... run the tests, capture collected/passed/failed verbatim
[ ] commit, then land it with GITHUB_COMMIT_MULTIPLE_FILES (branch, base_branch=main)
[ ] GITHUB_GET_A_BRANCH -> record commit.sha
[ ] GITHUB_LIST_CHECK_RUNS_FOR_A_REF(ref=sha) -> record green/red by name
[ ] report with branch + SHA + check names. No SHA, no delivery.
```

---

*Owner: mem20 Orchestrator. Correct this file in place if a fact above changes — do not add a second access document.*
