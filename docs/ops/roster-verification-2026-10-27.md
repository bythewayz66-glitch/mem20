# Roster verification — 2026-10-27

**Auditor:** Mem20-admin · **Owner:** bythewayz66
**Check window:** 2026-10-27T15:14Z – 15:20Z (09:14 – 09:20 MDT)
**Deadline this satisfies:** 2026-10-27 12:00 MDT

**Subject:** the 21 roster rows in [`workload-roster-2026-10-27.md`](workload-roster-2026-10-27.md) §2, rows 1–21.
Row 22 (Mem20-admin) took no assignment; its slice is this report.

**Scoreboard:** **21 rows produced a real branch with a real head SHA. 1 of 21 is merged to `main`.**
Delivered work, unlanded work — the gap is merge, not authorship.

**`main` moved during this audit.** Row 11, `content/ws3-investor-deck`, was merged at 09:19:42 MDT as
`e7758bd178d38da63c5359dded0aada8bfc0eea5` ("Merge content/ws3-investor-deck into main"), taking `main`
from `45445f48` and 7,975 tracked files to `e7758bd1` and **7,991**. Everything else below is scored
against the state each branch was in at the check window; the per-row verdicts do not change, because a
row is scored on its branch and its deliverable, not on merge state. Merge status is re-asserted against
the new head in §3.

---

## 1. Baseline re-verified in this run

| Fact | Value | How checked |
|---|---|---|
| Canonical repo | `github.com/bythewayz66-glitch/mem20` (public, MIT) | `git clone` over HTTPS, no credentials needed |
| `main` HEAD | `45445f4850377814cd95b7fa50c0a9153f76c163` | `git log -1 --format=%H` |
| HEAD commit | 2026-10-27 09:13:27 -0600 — `docs(ops): dispatch the 2026-10-27 workload roster — 22 agents, 1-hour round (#116)` | `git log -1 --format='%H %ci %s'` |
| Tracked files | 7,975 | `git ls-files \| wc -l` |
| VERSION | 3.0.0 | `cat VERSION` |
| Remote heads | 53 (main + **52** side branches) | `git ls-remote --heads origin \| wc -l` |
| At-risk commits | **177** (sum of `main..branch` per branch, 12-char SHAs above) | `git rev-list --count origin/main..origin/<b>` summed over all 52 |
| At-risk commits, de-duplicated | 168 | `git rev-list --count origin/main..<all side heads>` |
| Open PRs | **11** (#103–#111, #113, #118) | `GITHUB_LIST_PULL_REQUESTS(state=open)` |

The 177 in the task brief is the **double-counted** figure — the same commit reachable from two branches is
counted twice. Both numbers are recorded so neither reads as a correction of the other.

### Roster squash confirmed content-identical

`docs/ws1-workload-roster-2026-10-27` @ `05da8465c607ee0fa12982d50268bdbf35f88067` → `main` `45445f48`
(PR #116, merged 2026-10-27T09:13:27-06:00). Re-checked this run:

```
git diff origin/main origin/docs/ws1-workload-roster-2026-10-27 -- docs/ops/workload-roster-2026-10-27.md
# (no output — empty)
```

No diff, so the roster text on `main` is the text that was dispatched. The branch is now fully merged and
deletable; it is the one row of the 22 that landed.

---

## 2. Method — what "DELIVERED" required

A row scores **DELIVERED** only when all four hold, each from a check in this run:

1. **Branch exists** at `refs/heads/<branch>` on `origin` — `git ls-remote --heads origin`.
2. **A 40-character head SHA** — `git rev-parse origin/<branch>`, full SHA printed per row below.
3. **The tip is after the 08:44Z dispatch baseline** — `git log -1 --format=%ci`. A pre-dispatch tip is
   not new work, however green the branch looks.
4. **The row's named deliverable is actually in that tree** — `git cat-file -e origin/<branch>:<path>`
   plus `git diff --stat origin/main...origin/<branch>`. A SHA with no deliverable behind it is an
   empty claim.

Merged status is scored separately, because it is a different question: **is this work on `main`?**
`git merge-base --is-ancestor` returns false for all 21.

Everything below is a check from this run. Where a claim could not be checked, the row says so instead of
scoring it — no row is credited on an agent's message alone.

---

## 3. Verification table — 21 rows

`AHEAD/BEHIND` are `main..branch` / `branch..main`. `TIP (MDT)` is the branch head commit time.

| # | Agent | Branch | Head SHA (40) | Tip (MDT) | Ahead/Behind | Named deliverable | Merged | Score |
|---|---|---|---|---|---|---|---|---|
| 1 | mem20-webdev | `feat/ws2-desktop-packaging-40` | `9bf6bdade5db2b4f21382e9d338921860e517c11` | 02:56:55 | 1 / 1 | `docs/app/desktop-packaging.md` (10,971 B) | no | DELIVERED |
| 2 | Experiment Tracker | `docs/ws1-experiment-registry` | `d48d89d73090fe8770386661a314c93d6ac94b2e` | 02:57:12 | 2 / 1 | `docs/benchmarks/experiment-registry.md` (11,582 B) + `experiments.json` (27,666 B) | no | DELIVERED |
| 3 | Webpage Developer | `feat/ws2-launch-page-270` | `78878699b599cbb017133a06f32bd2109b351146` | 03:10:33 | 8 / 1 | `docs/index.html` rebuilt, `docs/ops/launch-page-270-urls.md` URL record | no | DELIVERED — unpublished |
| 4 | mem20 GTM Team Lead | `docs/ws1-gtm-claim-ledger-refresh` | `09d0cbdc428bb1034101501ff9267a368a42b315` | 02:55:16 | 1 / 1 | `docs/gtm/claim-ledger.md` (26,021 B) | no | DELIVERED |
| 5 | mem20 Orchestrator | `docs/ws1-merge-order` | `c79c8d6ad6d0df15a96ec5088a7053dca6d20633` | 02:55:10 | 1 / 1 | `docs/ops/merge-order-2026-10-27.md` (17,939 B) | no | DELIVERED |
| 6 | Finance Assistant | `fix/ws2-finance-270` | `619cccbe9b3b9e202365e36c350dde7a11fff6fb` | 02:53:30 | 1 / 1 | `docs/finance/` model re-run against 270/27 | no | DELIVERED |
| 7 | Server Builder | `fix/ws2-sidecar-compiles-36` | `0bce325ade0820f064d9e1a4d0bace1ddbd2452d` | 03:06:16 | 3 / 1 | `mem20desktop` crate: `health.rs`, `http/mod.rs`, `http/tests.rs`, `sidecar.rs`, `Cargo.toml` | no | DELIVERED — see §4(a) |
| 8 | Market Research | `docs/ws1-benchmark-comparability` | `0c6829f201d0bad80ea4e4145fd58255b2ba6bf5` | 02:56:12 | 2 / 1 | `docs/benchmarks/comparability-matrix.md` (18,567 B) | no | DELIVERED |
| 9 | Pricing Analyst | `fix/ws2-pricing-tier-sensitivity` | `3f0c468fedcfd6ed471b2d985b15b51dd41e241f` | 03:01:45 | 3 / 1 | `docs/pricing/tier-sensitivity.md` (16,815 B) | no | DELIVERED |
| 10 | GitHub Repo Assistant | `fix/ws2-suite-collection-unblock` | `a47e7d70d87dcbd42a10aa56fe72fc64d17d1049` | 03:04:07 | 7 / 1 | `aiohttp`/`mcp-types` declared, 14 import-time `sys.exit` guards removed, `conftest.py` hookwrapper | no | DELIVERED (PR **#118**) |
| 11 | Slides Assistant | `content/ws3-investor-deck` | `75243c4c6dd53998af2f45b17333a7aa8997c984` | 02:59:23 | 4 / 1 | `docs/app/deck/slides/slide_01..13` + `PERMANENT_URL.md` | no | DELIVERED — unpublished |
| 12 | Mem20-Perl-Expert | `fix/ws2-perl-jobs-coverage` | `23c75a75749ee4831ed651c4ab5db21379042e5f` | 02:57:51 | 8 / **40** | `sdk/perl/t/95-jobs.t` (11,448 B) | no | DELIVERED |
| 13 | Mem20-naration | `content/ws3-narrative-serial` | `c5b54596ddfc123d2d91fd61ead7daf0803bc0cb` | 02:57:48 | 1 / 1 | `docs/app/narrative/serial-2026-10-27.md` (65,137 B) | no | DELIVERED |
| 14 | Analytics Reporter | `fix/ws2-metrics-collector` | `544b8b316d7de2b360874138c719f8665980820f` | 02:55:38 | 3 / 1 | `docs/ops/metrics.json` (23,611 B) + `metrics_collector.py --since` | no | DELIVERED |
| 15 | Mem20 Content Creator | `content/ws3-launch-copy-270` | `e95b7ea00f4c73af15f93625e298e0f7e77e7041` | 02:57:17 | 1 / 1 | `docs/gtm/mem20-launch-copy.md` (30,615 B) | no | DELIVERED |
| 16 | Mem20-Ruby-Expert | `fix/ws2-ruby-job-spec` | `af16ecb339a302d8e631ab84168236bed35e6ae2` | 03:03:34 | 3 / 1 | `mem20-sdk-ruby/spec/mem20/job_spec.rb` (296 lines) + `lib/mem20/job.rb` | no | DELIVERED |
| 17 | Mem20 C++ Expert | `feat/ws2-cpp-live-surface-test` | `9605415431fba5868469cbaef53c177017721dc1` | 02:59:46 | 1 / 1 | `sdk/cpp/tests/test_live_surface.cpp` (9,185 B) | no | DELIVERED |
| 18 | UX Researcher | `docs/ws1-issue-40-update-ux` | `3a25920f2999845325cda906ed7b68fcc940fd47` | 02:53:12 | 1 / 1 | `docs/ux/issue-40-install-update-ux.md` (35,527 B) | no | DELIVERED |
| 19 | Benchmark Dataset Builder | `feat/ws2-bench-scale-2000` | `6687c6faa401e5afff14f1c12ba0dc8bba26b96b` | 03:22:25 | 5 / 1 | `benchmarks/results/latest.json`, `docs/benchmarks/results-v2.json`, 2,000-record corpus | no | DELIVERED |
| 20 | mem20-frontends | `fix/ws2-controlz-a11y` | `f1596841244f4bb42286aa426dd92fcd7c715139` | 03:03:25 | 4 / 1 | `mem20controlz/.../web/src/a11y.js`, `FocusTrap.jsx`, `docs/ux/frontend-a11y-audit.md` | no | DELIVERED |
| 21 | Super Agent | `docs/ws1-verification-transcript` | `66f636424a3566f4b9841dd4e4b6d57568f4bf1f` | 02:54:56 | 1 / 1 | `docs/ops/verification-2026-10-27.md` (16,591 B) | no | DELIVERED |
| 22 | Mem20-admin | `docs/ws1-workload-roster-2026-10-27` | `05da8465c607ee0fa12982d50268bdbf35f88067` | 02:47 | 1 / 2 | the roster itself | **YES** — squashed `45445f48` | LANDED (1 of 22) |

**Counts:** 21 branches / 21 distinct 40-char SHAs / 21 named deliverables present / **1 merged** (row 22)
/ **1 of 21 assignments merged** (row 11, `e7758bd1`, observed mid-audit).

Merge status re-checked against the new head `e7758bd1`: `git merge-base --is-ancestor origin/<branch>
origin/main` returns true for **1 of 21** — `content/ws3-investor-deck`, row 11. The other 20 remain
branch-only. The table's `Merged` column records the state at the per-row check; this line is the
post-merge recount, and the two differ only on row 11.

All 21 tips are after the 08:44Z (02:44 MDT) dispatch baseline; the earliest is row 6 at 02:53:30 MDT.
That check matters: a stale branch would satisfy items 1–2 and still be no work at all.

### Rows where the agent's own reported SHA has moved

Two rows were reported in the room at an earlier SHA and have since advanced. The table scores the
**current** tip, not the reported one — a row is only as good as what is on the branch now.

| Row | Reported | Current tip | Reading |
|---|---|---|---|
| 2 | bench branch `40b022f1…` (room, 09:21Z) | `6687c6faa401…` on `feat/ws2-bench-scale-2000` | `40b022f1` **is** an ancestor of the current tip (`git merge-base --is-ancestor` → true). Three commits added on top, including the corpus generator the agent had flagged as still-uncommitted. The reproducibility gap it disclosed is now closed on the branch. |
| 3 | `acb3662496…` (room, 09:08Z) | `78878699b599…` | Superseded. The later head carries the final 61,488-byte dashboard; the agent stated two intermediate placeholder commits were reverted. Current tip is the one scored. |

Row 2's `AHEAD 5 / BEHIND 1` and row 19's branching off `b9de9aa` mean the branch is one commit behind
`main` (`45445f48` is the roster-only commit). Behind-by-one on a docs-only commit is not a conflict risk;
it is recorded because a reviewer will see it and should not have to rediscover why.

---

## 4. Two corrections recorded

### (a) `feat/ws2-tauri-sidecar-36` is superseded by `fix/ws2-sidecar-compiles-36` @ `0bce325ade08`

**Finding:** the sidecar branch declares two modules it never committed.

```
# lib.rs on feat/ws2-tauri-sidecar-36, lines 13-14
pub mod health;
pub mod http;
```

```
# what that branch actually commits (git diff --stat main...feat/ws2-tauri-sidecar-36)
mem20controlz/src-tauri/mem20desktop/src/lib.rs      |  51 ++
mem20controlz/src-tauri/mem20desktop/src/sidecar.rs  | 407 ++
mem20controlz/src-tauri/src/lib.rs                   | 176 ++-
3 files changed, 633 insertions(+), 1 deletion(-)
```

`src/health.rs` and `src/http/` are **not on the branch** — `git ls-tree` over
`mem20controlz/src-tauri/mem20desktop/` on that head returns exactly `lib.rs` and `sidecar.rs`, and the
crate's `Cargo.toml` is absent too. A `lib.rs` that declares a module with no file behind it does not
compile. `feat/ws2-tauri-sidecar-36` @ `b7163284d6f8` (2 ahead) is therefore **superseded, not a merge
candidate**.

**Superseding branch:** `fix/ws2-sidecar-compiles-36` @ `0bce325ade0820f064d9e1a4d0bace1ddbd2452d`.
It commits the crate that the declaration needed:

```
mem20controlz/src-tauri/mem20desktop/Cargo.toml
mem20controlz/src-tauri/mem20desktop/src/lib.rs
mem20controlz/src-tauri/mem20desktop/src/health.rs
mem20controlz/src-tauri/mem20desktop/src/http/mod.rs
mem20controlz/src-tauri/mem20desktop/src/http/tests.rs
mem20controlz/src-tauri/mem20desktop/src/sidecar.rs
```

Every `mod` declared in that crate's `lib.rs` resolves to a file: `health` → `health.rs`,
`http` → `http/mod.rs`, `sidecar` → `sidecar.rs`. (`tests` is the inline `mod tests { }` test module at
line 40, not a file — that is correct Rust, not a gap.)

**What is verified and what is not.** Module resolution is verified statically, above. The row's stated
acceptance — `cargo check` exit 0 from a clean clone — is **NOT verified here**: no Rust toolchain exists
in this sandbox (`command -v cargo` returns nothing). The row is scored DELIVERED on the deliverable being
present and internally resolvable; it is **not** scored as compiling. That check needs a runner with cargo,
and should gate the merge rather than be assumed.

### (b) `fix/issues-5-18-complete` @ `d25015a149ae` — 26 conflicts, reverts main, close unmerged

**PR #104 already says so.** Title: *"Triage: fix/issues-5-18-complete (21 commits) — superseded by main,
do not merge as-is"*. The body's recommendation 1 is verbatim: **"Close this PR unmerged — merging reverts
`main`."** The branch tip has not moved since: `d25015a149ae7cc00138af3887f0df3e278579c6` is still the head
of PR #104, and PR #104 is still **open** — the recommendation was written on 2026-10-27T01:56Z and is
outstanding ~13 hours later.

**Conflicts: 26, reproduced this run.**

```
git merge-tree --write-tree --name-only origin/main origin/fix/issues-5-18-complete
# exit 1, conflicted tree 7806f5eb
```

The 26 conflicted paths are `.github/workflows/ci.yml`, `cog/cognitive_engine.py`,
`docs/INDEX.md`, `llm.py`, `mcp/tests/test_search_rate_limit.py`,
`mem20AIonbordz/src/mem20AIonbordz/discover.py`, `mem20agentz/mem20agentz/production.py`,
`mem20gamez/mem20gamez/build_harness/runner.py`, `mem20owebz/run_pipeline.py`,
`mem20owebz/run_pipeline_ai.py`, `mem20owebz/run_pipeline_queued.py`, eight files under
`mem20owebz/tools/{blender,release,unity}/`, `specs/README.md`, `specs/prod.md`,
`specs/game-maker/20_Essential_Game_Maker_Pipelines.md`, `tests/test_memory_api.py`,
`tests/test_retrieval_graph.py`, `tools/gen_completion_audit.py`, `tools/gen_systems_value.py`,
`verification/verify_refactor.py`.

**The revert is a collision-set property, and the counts land exactly.** Branch and `main` both changed
**42** files since merge base `81b0b9ca6429` (2026-10-21), and the collision set is the full 42. On
**24 of those 42**, `main` holds inserted lines the branch does not have — 262 lines of `main` content
would be dropped. Those 24 are the "~20 of 42" in the claim; the 42 is the same 42 in both figures, which
is why the claim checks out rather than needing to be softened.

Why no file is a *pure* revert (branch byte-identical to merge base): the branch's own edits are real. The
revert is in the overlap — where the branch modified a file from the old base and `main` has since
superseded that work, the branch's line is the older decision. PR #104's Finding 2 already names five of
them (`llm.py` path form, `production.py` `MEM20_SPEC_SOURCES` vs `_SOURCE`, `cognitive_engine.py` inline
`__import__`, `ci.yml` 229→114 lines, `docs/INDEX.md` Claims link dropped).

**Disposition: close #104 unmerged; do not merge this branch.** Preserve nothing by merging — preserve it
by tag. A tag `archive-fix-issues-5-18-complete-2026-10-26` pinning `d25015a` is what PR #104 proposes and
what the "nothing is lost" rule requires before the ref is deleted. PR #104's Finding 4 already isolates
the two hunks worth re-landing fresh on `main` (`local_build.py` `UNITY_EDITOR` candidate,
`test_retrieval_graph.py` hardcoded-path removal); that is a 2-file PR, not this branch.

---

## 5. NOT DELIVERED list

**No assignment row is NOT DELIVERED.** All 21 produced a branch, a 40-char head SHA after the dispatch
baseline, and the row's named deliverable in that tree. There is no row to name in this section, and it is
left explicit rather than deleted so the next auditor can see the check was made and what it returned.

*(A prior reading of this run scored rows 7 and 16 as NOT DELIVERED on an absent-path check. That was an
auditor path error, corrected before scoring: the Ruby spec lives at
`mem20-sdk-ruby/spec/mem20/job_spec.rb`, not `spec/mem20/job_spec.rb`, and the sidecar modules live under
`mem20controlz/src-tauri/mem20desktop/src/`. Both files exist. The check is recorded here because a
"NOT DELIVERED" produced by a wrong path is exactly the false negative this table exists to prevent.)*

### Delivered but at risk — these belong in the next decision, not this scoreboard

The scoreboard says DELIVERED. That is not the same as preserved. Work is at risk when it exists only on a
side branch, because a branch is a ref, not a backup.

| Risk | Evidence | Owner |
|---|---|---|
| **20 of 21 delivered branches are unmerged.** Merging `main` forward does not carry them; each needs a PR or a deliberate close. Row 11 has since landed (§3). | `git merge-base --is-ancestor origin/<b> origin/main` true for 1 of 21 only | mem20 Orchestrator |
| **Rows 1–21 are branch-only except row 10 (#118) and row 11 (merged).** The open PRs are #103–#111, #113, #118, and only #118 is a roster row. So 19 delivered rows have neither a PR nor a merge. | `GITHUB_LIST_PULL_REQUESTS(state=open)` vs roster branch names | branch owners |
| **Row 3 produces an artefact with no public surface.** Its rebuilt `docs/index.html` is unmerged, so the live page still serves the pre-270 build. Row 11's deck has merged but still carries only a `PERMANENT_URL.md` record — merging source is not publishing it. | `/sites/` returns 403 to token-free requests (see §6) | Webpage Developer / Slides Assistant |
| **177 at-risk commits** across 52 side branches at the baseline; row 11's 5 commits have since landed. | `git rev-list --count` sum | mem20-webdev / Mem20-admin |
| **Row 7 does not compile as inherited.** `feat/ws2-tauri-sidecar-36` is a decoy with 2 ahead; only `fix/ws2-sidecar-compiles-36` has the modules. Any merge order that takes `#36` first breaks the Tauri build. | §4(a) | mem20 Orchestrator (merge-order doc, row 5) |
| **PR #104 still open** with a "close unmerged" recommendation, ~13h old. | §4(b), `GITHUB_GET_A_PULL_REQUEST(104)` → `state: open` | GitHub Repo Assistant |

**The one-line version:** 21 of 22 rows delivered; 2 landed (row 22's roster, row 11's deck); the
program's exposure is not missing work, it is **unmerged** work — 20 branches and 177 commits sitting
outside `main`, 19 of them with no PR at all.

---

## 6. Related facts re-checked while auditing

| Fact | Value | How checked |
|---|---|---|
| PR #104 state | **open**, unchanged tip `d25015a` | `GITHUB_GET_A_PULL_REQUEST(104)` |
| PR #104 verdict | "Close this PR unmerged — merging reverts `main`" | PR body, recommendation 1 |
| PR #118 (row 10) | open, head `a47e7d70d87d`, base `b9de9aa8`, reports collected 2486→2489 | `GITHUB_LIST_PULL_REQUESTS` |
| `/sites/` anonymous access | **403** token-free; 200 only because the shell injects a token | prior room finding, not re-probed here — see note |
| Public host | `mem20.com` (github.io 301-redirects to it via `docs/CNAME`) | prior room finding, not re-probed here |
| Rust toolchain | absent — `cargo` not on PATH | `command -v cargo` |

**Not checked in this run, therefore not asserted:** live HTTP status of `mem20.com` and of any `/sites/`
URL. This run verified repository state only. The public-surface rows above are carried from the room
record and are marked as such — they are not this auditor's measurement, and the next run should probe
them before any public post goes out.

---

## 7. Next actions

| # | Action | Owner | Why now |
|---|---|---|---|
| 1 | Close PR #104 unmerged; tag `d25015a` before any ref deletion | GitHub Repo Assistant | 26 conflicts, reverts 24 files, recommendation 13h old |
| 2 | Merge `fix/ws2-sidecar-compiles-36`, retire `feat/ws2-tauri-sidecar-36` | mem20 Orchestrator | The sidecar decoy will break a Tauri merge if taken first; `docs/ops/merge-order-2026-10-27.md` (row 5) already carries the order |
| 3 | Run `cargo check` on `fix/ws2-sidecar-compiles-36` on a runner with cargo | Server Builder | The row's own acceptance, unverifiable in this sandbox |
| 4 | Open PRs for the 12 branch-only rows; batch the docs-only ones (`ws1-*`) into one | branch owners | Branch-only work has no review path and no merge |
| 5 | Merge row 3 to `main` so the live page carries 270/27 and v3.0.0 | Webpage Developer | Delivered and unpublished — currently the worse of the two states |
| 6 | Re-probe `mem20.com` and `/sites/` anonymously, then decide what may be published | Mem20-admin | §6 carried these forward instead of measuring them |

**Blockers still standing (unchanged, not re-tested this run):** `mem20.jaysonai.online` NXDOMAIN — a
missing record, not propagation; PyPI 404 on `mem20`/`mem20-ai`/`mem20oreo`, so installs stay
source-only; Sidney `216.198.115.91` dark; `gabe` publish not attempted.

---

**House numbers carried, not re-derived:** 270 tools across 27 domains (257/26 retired);
TAM $1.28B / SAM $282M / SOM $1.68M; blended ACV $14,000.

*As an AI agent I cannot provide legally protected, personalized investment advice. This report is for
informational purposes only and does not constitute investment advice or a recommendation. Consult a
licensed financial advisor before making investment decisions.*
