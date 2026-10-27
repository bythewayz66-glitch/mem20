# Workload roster — 2026-10-27 (owner directive, 1-hour round)

**Dispatched by:** Mem20-admin · **Authority:** mem20 Orchestrator · **Owner:** bythewayz66
**Dispatched at:** 2026-10-27 08:44 UTC / 02:44 MDT
**Hard deadline:** **2026-10-27 09:44 UTC / 03:44 MDT** (one hour)
**Auditor at checkpoint:** Mem20-admin

A row is `DELIVERED` only when a live branch head SHA or a committed URL is recorded.
Chat does not count. This file is the scoreboard.

---

## 1. Baseline verified in this run (08:44 UTC)

| Fact | Value | How checked |
|---|---|---|
| Canonical repo | `github.com/bythewayz66-glitch/mem20` (public, MIT) | `GITHUB_GET_A_PULL_REQUEST` base repo payload |
| `main` HEAD | `1264076698a00878acc3adacf7bf1d51eea315cc` | `git log -1` after clone |
| HEAD commit date | 2026-10-27 02:39:10 -0600 | `git log -1 --format=%ci` |
| HEAD subject | `fix(tests): stop the unit-marker step failing on an empty selection (#115)` | `git log -1 --format=%s` |
| Tracked files | 7,974 | `git ls-files \| wc -l` |
| VERSION | 3.0.0 | `cat VERSION` |
| Side branches | 29 (excluding `main`) | `git for-each-ref refs/remotes/origin` |
| Last push | 2026-10-27T08:42:09Z | repo API `pushed_at` |
| Open PRs | 10 (#103–#111, #113) | `GITHUB_LIST_PULL_REQUESTS(state=open)` |
| Open issues | 5 (#30, #35, #36, #37, #40) | `GITHUB_LIST_REPOSITORY_ISSUES(state=open)` |
| Authoritative surface | **270 tools / 27 domains** (257/26 retired) | `docs/finance/inputs.json` `tool_surface`, README, `docs/index.html` all agree |

### Corrections to the directive's in-flight list

The directive names seven in-flight items. Two are no longer in flight — verified this run:

| Directive said | Reality at 08:44 UTC |
|---|---|
| "PR #112 (Syntax gate)" in flight | **Already MERGED** 2026-10-27T08:28:34Z at `d3ec87699242e89830c66914e49763a352f4f25e`. Do not re-open or duplicate. |
| "270/27 tool count" still to be landed | **Already on `main`**: README, `docs/index.html`, and `docs/finance/inputs.json` all carry 270/27 with `previous_tools: 257` recorded as retired. Assigning it again would be duplicate work. |

Still genuinely in flight and therefore **excluded from this roster**:
`#103` (#30 OREO), `#104` (triage), `#105` (#43 Telegram), `#106` (C++ docs),
`#107` (Ruby surface), `#108` (#39 offline UX), `#109` (#38 palette),
`#110` (Perl surface), `#111` (access path), `#113` (#37 tray),
branch `docs/ionos-dns-mem20` @ `a114762f8dda6b99e9e9a30bd6a9504850c8a557`.

### Two real defects found while baselining (assigned below)

1. **`aiohttp` is missing from `requirements.txt`** — `grep -n aiohttp requirements.txt mcp/requirements.txt` returns nothing (exit 2), while `mcp/tools/a2a_tools.py` imports it at module scope. The server cannot boot from a clean `pip install -r requirements.txt`. → GitHub Repo Assistant, because it also breaks `pytest --collect-only`.
2. **`feat/ws2-tauri-sidecar-36` declares modules it never committed.** `git diff --stat main...feat/ws2-tauri-sidecar-36` shows only 3 files (`lib.rs`, `sidecar.rs`); the `health`/`http` modules it references live on `feat/ws2-tauri-shell-35` (13 files, 1340 insertions). #36 does not compile standalone. → Server Builder.

---

## 2. The 22 assignments

Naming follows `docs/git/README.md`: `feat/ws2-`, `fix/ws2-`, `docs/ws1-`, `content/ws3-`, `ci/ws2-`, `chore/ws2-`.
Evidence is always the same: a **40-character commit SHA** returned by
`GITHUB_GET_A_BRANCH(owner="bythewayz66-glitch", repo="mem20", branch="<branch>")`
after the commit lands, or a permanent URL committed under `docs/` / `published/`.

| # | Agent | Deliverable (why only they) | Branch | Evidence |
|---|---|---|---|---|
| 1 | mem20-webdev | #40 has no branch at all: desktop packaging, code-signing, auto-update. Add bundle targets + updater config in `mem20controlz/src-tauri/`, plus `docs/app/desktop-packaging.md` stating exactly which artefacts are reproducible in CI and which need signing credentials. | `feat/ws2-desktop-packaging-40` | branch SHA |
| 2 | Experiment Tracker | An experiment registry that records, per retrieval mode, whether it is *scored* or merely *present*. `benchmarks/results/latest.md` scores 4 modes and the adversarial class sits at 0.000 — the registry must name the unscored methods. `docs/benchmarks/experiment-registry.md` + `docs/benchmarks/experiments.json`. | `docs/ws1-experiment-registry` | branch SHA |
| 3 | Webpage Developer | The published `/sites/` launch page is stale. Rebuild the launch page and dashboard against the **270/27** surface actually served by `main`, commit the source and the permanent URL record. | `feat/ws2-launch-page-270` | branch SHA + URL |
| 4 | mem20 GTM Team Lead | Refresh `docs/gtm/claim-ledger.md` so every claim carries the 270/27 surface **and** the honest adversarial limitation (hit rate 0.000). A claim ledger that omits the weakest row is a liability in a sales room. | `docs/ws1-gtm-claim-ledger-refresh` | branch SHA |
| 5 | mem20 Orchestrator | The single ordering that lands the open PRs without a `lib.rs` collision. `#35`, `#36` and `#37` all edit `mem20controlz/src-tauri/src/lib.rs`; `#36` cannot compile alone. Write the stack order and the exact three-line union into `docs/ops/merge-order-2026-10-27.md`. | `docs/ws1-merge-order` | branch SHA |
| 6 | Finance Assistant | `docs/finance/` still models the retired 257/26 surface. Re-run `compute_model.py` against 270/27, prove SOM $1.68M = 120 accounts × $14,000, append the reconciliation row. Numbers are carried, not re-derived. | `fix/ws2-finance-270` | branch SHA |
| 7 | Server Builder | Make `#36` compile: rebase `sidecar.rs` onto `#35`'s committed `health`/`http` modules, union the module list in `lib.rs`. Acceptance is `cargo check` exit 0 from a clean clone of the branch — not a working tree. | `fix/ws2-sidecar-compiles-36` | branch SHA |
| 8 | Market Research | The benchmark file itself says its numbers are **not comparable** to Mem0 LoCoMo 92.5 / LongMemEval 94.4 / Zep DMR 94.8. Turn that caveat into a sourced comparability matrix: corpus, metric, and why each is or is not comparable. `docs/benchmarks/comparability-matrix.md`. | `docs/ws1-benchmark-comparability` | branch SHA |
| 9 | Pricing Analyst | ACV is already reconciled 44/44 at $14,000 — do **not** redo that. New work: the tier ladder (`Team $6,000 / 0.72`, `Business $18,000 / 0.12`) is unvalidated against the $14,000 blend. `docs/pricing/tier-sensitivity.md` with the arithmetic, plus extend `audit_acv_consistency.py` to catch 257/26 drift. | `fix/ws2-pricing-tier-sensitivity` | branch SHA |
| 10 | GitHub Repo Assistant | Unblock suite collection for everyone: `mcp/server.py` raises a bare `SystemExit` at import, and `aiohttp` is absent from `requirements.txt` while `mcp/tools/a2a_tools.py` imports it at module scope. Prove `pytest --collect-only` reports a `collected` count. | `fix/ws2-suite-collection-unblock` | branch SHA |
| 11 | Slides Assistant | An investor/board deck built **only** from numbers verified in this roster's baseline, with the adversarial row shown rather than hidden. Commit deck source under `docs/app/deck/` and the permanent URL record. | `content/ws3-investor-deck` | branch SHA + URL |
| 12 | Mem20-Perl-Expert | `#110` is open — do not duplicate. New: the 25 long-running tools answer with a `{job_id,status:running}` envelope; the Perl SDK has `wait_for_job` but no test drives it to a terminal state. Add `sdk/perl/t/95-jobs.t` with a hermetic child process. | `fix/ws2-perl-jobs-coverage` | branch SHA |
| 13 | Mem20-naration | The narrative serial: this round's story told from SHAs and URLs, not from chat. Every claim carries its commit. `docs/app/narrative/serial-2026-10-27.md`. | `content/ws3-narrative-serial` | branch SHA |
| 14 | Analytics Reporter | No visitor telemetry exists, so measure what is real: commit velocity, PR cycle time, test counts, branch divergence — from `git log`. Extend `metrics_collector.py` with a `--since` window and emit `docs/ops/metrics.json`. | `fix/ws2-metrics-collector` | branch SHA |
| 15 | Mem20 Content Creator | `docs/gtm/mem20-launch-copy.md` is written against the retired surface. Rewrite to 270/27 and replace any performance claim with the measured row plus its caveat. | `content/ws3-launch-copy-270` | branch SHA |
| 16 | Mem20-Ruby-Expert | `#107` is open — do not duplicate. New: no spec covers the job envelope. Add `spec/mem20/job_spec.rb` driving `job_from` / `wait_for_job` against the existing `RecordingTransport` double, no Python required. | `fix/ws2-ruby-job-spec` | branch SHA |
| 17 | Mem20 C++ Expert | `#106` is open (docs only) — do not duplicate. New: `sdk/cpp/tests/` has no test that performs a real `tools/call`. Add a live-stdio test asserting 270 unique names and one `memory_store` → `memory_recall` round trip, wired into CMake. | `feat/ws2-cpp-live-surface-test` | branch SHA |
| 18 | UX Researcher | `#37`, `#38`, `#39` all have PRs — do not duplicate. New: `#40` packaging has no UX at all. `docs/ux/issue-40-install-update-ux.md` covering first run, unsigned-binary warning, update prompt, and failure states. | `docs/ws1-issue-40-update-ux` | branch SHA |
| 19 | Mem20 Benchmark Dataset Builder | `feat/scale-corpus-2000` is stale (2 ahead, last commit 2026-10-20). Corpus is 14 facts / 13 queries and adversarial scores 0.000. Rebuild the corpus at scale with an adversarial class that is *answerable*, re-run, commit `benchmarks/results/latest.json` + `docs/benchmarks/results-v2.json`. | `feat/ws2-bench-scale-2000` | branch SHA |
| 20 | mem20-frontends | `#38`/`#39` are in PRs — do not duplicate. New: `mem20controlz/mem20controlz/web/src/` has no accessibility or reduced-motion pass, and the palette is keyboard-only in ways a screen reader cannot follow. `docs/ux/frontend-a11y-audit.md` plus the actual fixes. | `fix/ws2-controlz-a11y` | branch SHA |
| 21 | Super Agent | Run the repo's own verifier and the hygiene gate locally, commit the raw transcript: `docs/ops/verification-2026-10-27.md`. Evidence, not summary — the point is that a reviewer can diff it against their own run. | `docs/ws1-verification-transcript` | branch SHA |
| 22 | Mem20-admin | This roster, the checkpoint trigger, and the post-deadline verification report. Verification is my slice; I do not take an assignment. | `docs/ws1-workload-roster-2026-10-27` | this file |

**Count: 22 assignments to 22 agents.** 21 of them produce a new branch; Mem20-admin's slice is verification.

---

## 3. How work is landed (same for every agent)

```python
GITHUB_COMMIT_MULTIPLE_FILES(
    owner="bythewayz66-glitch", repo="mem20",
    base_branch="main",              # branch is created from main
    branch="<your branch from the table>",
    message="<type>(<scope>): <what changed>",
    upserts=[{"path": "...", "content": "..."}],
)
```

* Access path: `docs/ops/GITHUB_ACCESS.md`, on branch `docs/ws1-github-access-path`
  (PR #111, head `bef79279c2b99f44b14f3d60b11bacd865f537d0`).
* No `gh` CLI and no `GH_TOKEN` in the sandbox. The integration above is the only write path.
* Verify your own push before reporting:
  `GITHUB_GET_A_BRANCH(owner="bythewayz66-glitch", repo="mem20", branch="<branch>")`
  and quote `commit.sha` in full (40 characters).
* **Hygiene gate warning:** the gate scans added lines in *every* changed file, markdown included.
  Do not reproduce the banned absolute-path literal in anything you write. Describe paths
  relative to the checkout.

## 4. The chain rule

Every agent does **two** things:

1. Delivers their own row above, pushed, with a SHA.
2. Assigns **one new piece of work** to **one other agent** by `@`-mentioning them.

To @-mention someone you must resolve their real userID:
`get_groups_info(["3388661668"])` and read `members_detail[userID].nickname`.
A nickname in the message text triggers nobody. Never `@` yourself.

The chain ends when the work is in GitHub — not when the messages stop.
If two agents converge on the same file, the second one rebases or takes a different slice;
duplicate commits on one branch will be rejected at verification.

## 5. Checkpoint

At **09:44 UTC / 03:44 MDT** Mem20-admin checks every claim against:

* `GITHUB_GET_A_BRANCH` for the named branch → does the SHA exist, and is its commit date after 08:44 UTC?
* `curl` for any committed URL → HTTP status and byte count.

Every row is scored `DELIVERED` / `NOT DELIVERED` / `UNKNOWN`. A branch that still sits at
its pre-dispatch SHA is `NOT DELIVERED` no matter what was said in the room.
