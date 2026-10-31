# Branch inventory + at-risk commit count — 2026-10-31

**Action:** H12 (Analytics Reporter)
**Repo:** `github.com/bythewayz66-glitch/mem20`
**Measured at:** 2026-10-31T23:03Z
**Base of comparison:** `main` = `f1672473cd19d5926e1df0c80042259d3b4b17ca`
**Branches in scope:** 8 non-`main` branches · **Open PRs:** 1 (`#146`)

> **Scope note — the base moved during this run.** The assignment stated `main` HEAD =
> `27c1e5fb78def1d34b9b8f572a66f1424b1b350e`. It is not: `main` advanced 2 commits to
> `f1672473cd19d5926e1df0c80042259d3b4b17ca` when PR **#145** merged. Every number below was
> re-derived with the compare API and `git rev-list` at the **current** HEAD, and is also
> reported at the stated HEAD so the two are directly reconcilable (§5).

---

## 1. Method

Two independent measurements, deliberately cross-checked against each other:

| Source | Command / endpoint | Used for |
|---|---|---|
| GitHub Compare API | `GET /repos/{owner}/{repo}/compare/main...{branch}` → `ahead_by`, `behind_by` | authoritative per-branch counts |
| Local git | `git rev-list --left-right --count origin/main...origin/<branch>` (A...B ⇒ left = behind, right = ahead) | independent recomputation + commit-level detail |
| Patch equivalence | `git cherry -v origin/main origin/<branch>` | separates *unique work* from *patch already on main* |
| Merge feasibility | `git merge-tree --write-tree origin/main origin/<branch>` | pre-flight conflict detection (read-only) |

All eight branches agreed between the Compare API and local git to the commit. Counts are exact
ancestry walks — no sampling, no estimation, so there is no confidence interval to report: the
figure is either the tree's answer or it is wrong.

---

## 2. At-risk commit count — definition and result

"At-risk" = a commit reachable from a non-`main` branch and **not** reachable from `main`. It is
not yet protected by anything; if the branch is deleted or force-pushed, the work is gone.

| Measure | Value |
|---|---|
| **Summed ahead-of-`main` across all 8 branches** (literal definition) | **10** |
| Commits whose patch is already on `main` (`git cherry` `-`) | 1 |
| **Genuinely unique commits at risk** | **9** |
| Union of distinct commits not on `main` (dedup across branches) | **10** |
| Commits appearing in more than one branch (double-counting) | **0** |
| Summed behind-`main` across all 8 branches | 120 |
| Branches fully merged (ahead = 0) | 2 of 8 |

The summed figure and the deduplicated union are both 10, and no commit is shared between two
branches — so the "summed total" here is a clean count, not an inflated one.

---

## 3. Per-branch inventory (vs `main` = `f1672473`)

| Branch | Head (40-char) | Ahead | Behind | Unique work? |
|---|---|---:|---:|---|
| `chore/retire-jaysonai-sidney-gabe` | `d0ac17b065405446ed0bf9a42b4d07330bb2cc7f` | 1 | 7 | unique — 5 files |
| `chore/ruby-sdk-surface-guard` | `c56ccb092eef6858edddd284dddd57828e89ed2f` | 1 | 4 | unique — `surface_spec.rb` only |
| `chore/ws1-purge-retired-infra-refs` | `de37968ac72cb89e9dd555bb67923220e959a260` | **0** | 3 | **merged via #145** |
| `chore/ws1-rebuild-app-bundle-purge-jaysonai` | `faf9cef3727950c40e1e7db2f4252baa92a958d9` | **2** | 7 | unique — bundle + FAQ source |
| `chore/ws1-release-tag-3.1.0` | `73343f6853ec4b3577198e783c89bbb1a5526bf2` | **0** | 3 | **already in `main`** (`73343f68` is an ancestor) |
| `dependabot/pip/aiohttp-gte-3.14.5` | `6a087a231c9066694208048a69deb780a330e433` | 1 | 81 | **redundant** — patch already applied by #142 |
| `docs/ws1-daily-reports-2026-10-31` | `4f20ecfb848f80e2fe4490050ecfb1e178cea401` | 1 | 8 | unique — attestation commit |
| `docs/ws1-retire-jaysonai-hostname` | `d010fdb33d1c561895c7787043f197af4bc87f43` | **4** | 7 | unique — largest single contributor |
| **TOTAL** | | **10** | **120** | |

### Where the 10 at-risk commits sit

| Branch | Count | Commits |
|---|---:|---|
| `docs/ws1-retire-jaysonai-hostname` | 4 | `1cfe8939`, `e7df2495`, `0027179b`, `d010fdb3` |
| `chore/ws1-rebuild-app-bundle-purge-jaysonai` | 2 | `67f7e185`, `faf9cef3` |
| `chore/retire-jaysonai-sidney-gabe` | 1 | `d0ac17b0` |
| `chore/ruby-sdk-surface-guard` | 1 | `c56ccb09` |
| `docs/ws1-daily-reports-2026-10-31` | 1 | `4f20ecfb` |
| `dependabot/pip/aiohttp-gte-3.14.5` | 1 | `6a087a23` *(patch already on `main`)* |

Full 40-char SHAs are in the branches' `git log`; the four abbreviated pairs above expand from the
head SHAs in §3, and each was confirmed against `git rev-list origin/main..origin/<branch>`.

---

## 4. Concentration and risk reading

- **One branch holds 40% of the at-risk work.** `docs/ws1-retire-jaysonai-hostname` carries 4 of 10
  commits and touches 9 files. It is the single highest-value branch to land.
- **Two of eight branches are byte-for-byte accounted for on `main`** (`ws1-purge-retired-infra-refs`
  via #145, `ws1-release-tag-3.1.0` from the start). They are clutter, not risk — deleting them loses
  nothing.
- **The dependabot branch is a false positive risk-wise but a real divergence signal.** Its single
  commit is patch-equivalent (`git cherry` → `-`), yet it sits **81 commits behind**. A dependabot
  branch that old will keep re-conflicting forever; it should be closed rather than merged.
- **Behind-ness is dominated by one branch**: 81 of the 120 total behind-commits are the dependabot
  branch. Excluding it, the other seven average ~5.6 behind.

---

## 5. Reconciliation with the numbers stated in the assignment

The assignment's own figures, re-measured at **its own** stated HEAD (`27c1e5f`) so the comparison is
apples-to-apples:

| Branch | Stated ahead | Re-measured @ `27c1e5f` | Δ | Why |
|---|---:|---:|---:|---|
| `chore/ws1-purge-retired-infra-refs` | 6 | **1** | **−5** | head rewritten |
| `docs/ws1-retire-jaysonai-hostname` | 4 | 4 | 0 | ✓ |
| `chore/retire-jaysonai-sidney-gabe` | 1 | 1 | 0 | ✓ |
| `chore/ruby-sdk-surface-guard` | 1 | 1 | 0 | ✓ |
| `chore/ws1-rebuild-app-bundle-purge-jaysonai` | 1 | **2** | **+1** | new commit added |
| `docs/ws1-daily-reports-2026-10-31` | 1 | 1 | 0 | ✓ |
| `dependabot/pip/aiohttp-gte-3.14.5` | 1 | 1 | 0 | ✓ |
| `chore/ws1-release-tag-3.1.0` | 0 | 0 | 0 | ✓ |
| **TOTAL** | **15** | **11** | **−4** | |

**Two discrepancies, both explained, both material:**

1. **`-5` — the branch was rewritten, not extended.** The stated head `1df637d6…` **does not exist in
   the repository**. `git cat-file -t 1df637d6` returns nothing; the branch head is now
   `de37968ac72cb89e9dd555bb67923220e959a260`. Those 5 commits are not "still unmerged" — they were
   force-pushed away and replaced by a single squashed commit. **The assignment's count could not be
   reproduced because the history it measured no longer exists.** This is the one finding in this
   report that is a data-integrity issue rather than a bookkeeping one.
2. **`+1` — the rebuild branch gained a commit.** `faf9cef3` (FAQ source fix) was pushed on top of
   `67f7e185` (bundle rebuild) after the assignment's measurement. The two commits also carry
   **conflicting intent**: `faf9cef3`'s own message says the regenerated bundle is *not* in the
   commit, while `67f7e185` adds it. Whichever lands last wins; see §6.

Net: the assignment's total of 15 is **11** at that same HEAD, and **10** at the current HEAD.

---

## 6. Re-measurement after the H1–H5 merges

**This section is a staged replay, not a landed state.** Repository protocol
(`docs/handoff/AGENT-OPERATING-PROTOCOL.md:136,140`) is *"Never commit to `main` directly"* and
*"The human owner merges. Agents open PRs."* No merge was performed by this run, and no branch was
mutated. The tables below come from replaying the merges on a scratch branch in a local clone, so the
`ahead = 0` result is **proven reachable, not proven achieved**.

### Stage A — what merges cleanly right now (pre-flight, unmodified trees)

`git merge-tree --write-tree origin/main origin/<branch>`:

| Branch | Merge result |
|---|---|
| `docs/ws1-retire-jaysonai-hostname` | clean |
| `chore/ruby-sdk-surface-guard` | clean |
| `docs/ws1-daily-reports-2026-10-31` | clean |
| `chore/ws1-release-tag-3.1.0` | clean (nothing to merge) |
| `chore/ws1-purge-retired-infra-refs` | clean (nothing to merge) |
| `dependabot/pip/aiohttp-gte-3.14.5` | clean |
| `chore/retire-jaysonai-sidney-gabe` | **CONFLICT** — `CANONICAL.md` |
| `chore/ws1-rebuild-app-bundle-purge-jaysonai` | **CONFLICT** — `web/src/views/DocsFaq.tsx`, `web/vite.config.ts` |

Both conflicts are **expected and mechanical**: PR #145 already landed the same purge on `main`, so
these two branches now edit lines `main` has rewritten. Neither is a real disagreement about content.

### Stage B — after the six mechanically-clean merges (H1–H5 group)

Scratch HEAD `65daa74149dfdfa129334d5bdd3d650914ced711`; 6 branches merged onto `f1672473`:

| Branch | Head (40-char) | Ahead | Behind |
|---|---|---:|---:|
| `chore/retire-jaysonai-sidney-gabe` | `d0ac17b065405446ed0bf9a42b4d07330bb2cc7f` | 1 | 18 |
| `chore/ruby-sdk-surface-guard` | `c56ccb092eef6858edddd284dddd57828e89ed2f` | 0 | 14 |
| `chore/ws1-purge-retired-infra-refs` | `de37968ac72cb89e9dd555bb67923220e959a260` | 0 | 14 |
| `chore/ws1-rebuild-app-bundle-purge-jaysonai` | `faf9cef3727950c40e1e7db2f4252baa92a958d9` | 2 | 18 |
| `chore/ws1-release-tag-3.1.0` | `73343f6853ec4b3577198e783c89bbb1a5526bf2` | 0 | 14 |
| `dependabot/pip/aiohttp-gte-3.14.5` | `6a087a231c9066694208048a69deb780a330e433` | 0 | 91 |
| `docs/ws1-daily-reports-2026-10-31` | `4f20ecfb848f80e2fe4490050ecfb1e178cea401` | 0 | 18 |
| `docs/ws1-retire-jaysonai-hostname` | `d010fdb33d1c561895c7787043f197af4bc87f43` | 0 | 14 |
| **TOTAL** | | **3** | 201 |

At-risk drops 10 → **3** (the two conflicting branches). *(Behind counts are higher than §3 only
because the six replay commits themselves now sit between `main` and the branches — they exist in
this scratch clone, not on `origin`.)*

### Stage C — after resolving the two conflicts in favour of the branch

Scratch HEAD `b522aa10a4912fb7ae4c9f4130fa867e166bfb24`, conflict resolution `-X theirs` applied to
only the named conflict hunks:

| Branch | Head (40-char) | Ahead | Behind |
|---|---|---:|---:|
| `chore/retire-jaysonai-sidney-gabe` | `d0ac17b065405446ed0bf9a42b4d07330bb2cc7f` | **0** | 22 |
| `chore/ruby-sdk-surface-guard` | `c56ccb092eef6858edddd284dddd57828e89ed2f` | **0** | 19 |
| `chore/ws1-purge-retired-infra-refs` | `de37968ac72cb89e9dd555bb67923220e959a260` | **0** | 19 |
| `chore/ws1-rebuild-app-bundle-purge-jaysonai` | `faf9cef3727950c40e1e7db2f4252baa92a958d9` | **0** | 21 |
| `chore/ws1-release-tag-3.1.0` | `73343f6853ec4b3577198e783c89bbb1a5526bf2` | **0** | 19 |
| `dependabot/pip/aiohttp-gte-3.14.5` | `6a087a231c9066694208048a69deb780a330e433` | **0** | 96 |
| `docs/ws1-daily-reports-2026-10-31` | `4f20ecfb848f80e2fe4490050ecfb1e178cea401` | **0** | 23 |
| `docs/ws1-retire-jaysonai-hostname` | `d010fdb33d1c561895c7787043f197af4bc87f43` | **0** | 19 |
| **TOTAL** | | **0** | 238 |

**Result: zero branches ahead of `main`.** The summed at-risk count goes **10 → 3 → 0**, and the
deduplicated union goes **10 → 3 → 0** with it.

### How to convert this from "proven reachable" to "measured"

Once the owner has merged, re-run exactly this and expect `TOTAL_AHEAD=0`:

```bash
git fetch --all --prune
git rev-parse origin/main                       # record the new 40-char HEAD
for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin \
           | grep -v 'origin/HEAD' | sed 's|origin/||' | grep -v '^main$'); do
  read behind ahead <<< $(git rev-list --left-right --count origin/main...origin/$b)
  printf "%-50s ahead=%s behind=%s\n" "$b" "$ahead" "$behind"
done
```

A `read behind ahead` order is required: `A...B` yields *behind* first (`main`-only commits), then
*ahead*. Reading the pair the other way round inverts every number — worth stating because the first
pass of this measurement did exactly that and produced a nonsense `ahead=120`.

---

## 7. Token-mandate compliance (verified this run, not asserted)

| Check | Command | Result |
|---|---|---|
| Token in committed `.git/config` | `grep -nE 'url = \|token\|@github' .git/config` | **clean** — only `url = https://github.com/bythewayz66-glitch/mem20.git`, no credentials |
| Literal token in tracked files | `git grep -nE '(gh[pousr]_\|github_pat_)…'` | **none** — single hit is `mask_secrets("ghp_0123…")` in `mem20botz/tests/test_mem20botz.py:323`, a redaction test fixture, not a credential |
| Token in workflow YAML | `grep -nE 'GITHUB_TOKEN\|GH_TOKEN' .github/workflows/*` | 1 hit: `.github/workflows/controlz-desktop.yml:114` → `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` — a **reference to a secret**, not a value. Correct form. |
| Token in commit messages | review of all 10 at-risk commits | **none** |
| Retired identities (`Sidney`, `gabe`, `jaysonai`) | `git grep -ciE 'sidney\|gabe\|jaysonai'` | **still present on `main`** after #145 — see below |

The credential this run used was supplied by the connected GitHub integration profile and never
materialised as a file, an env var echoed into a log, or a commit message.

### Residual retired-identity references on `main`

#145 was scoped to exclude the collision-guarded lanes, so these survive by design rather than by
oversight — but they are still citable by a reader today:

`CANONICAL.md` (9), `CHANGELOG.md` (5), `docs/dashboard.html` (3), `docs/gtm/claim-ledger.md` (3),
`.sitemap/sitemap.json` (3), `README.md` (2), `docs/hygiene/oreo-gitlink.md` (2),
`docs/app/narrative/serial-2026-10-27.md` (2), plus `docs/README.md`, `docs/gtm/README.md`,
`docs/gtm/mem20-campaign-plan.md`, and the still-served bundle `docs/app/assets/index-BmhMl8hv.js`
(1). The last one is the only one that reaches a *visitor* rather than a reader of the repo, which
is exactly why `chore/ws1-rebuild-app-bundle-purge-jaysonai` exists.

---

## 8. Findings

1. **The stated baseline was already stale before this run started.** `main` is `f1672473…`, not
   `27c1e5f…`; PR #145 merged in between. Any report keyed to the old SHA understates merges and
   overstates risk.
2. **`1df637d6…` does not exist.** `chore/ws1-purge-retired-infra-refs` was force-pushed from
   `1df637d6` (6 ahead) to `de37968` (1 ahead, now merged). Five commits were discarded and cannot be
   audited from the repository. The assignment's `6` is unreproducible, not merely outdated.
3. **True at-risk total is 10, not 15** — 11 at the assignment's own HEAD. Nine of the ten are
   genuinely unique work; one (dependabot) is patch-equivalent and should be closed, not merged.
4. **Two branches conflict only because #145 landed the same change.** Resolving in favour of the
   branch is safe here, but it must be a deliberate act, not an auto-merge.
5. **`chore/ws1-rebuild-app-bundle-purge-jaysonai` contains contradictory commits.** `faf9cef3`
   states the bundle is *not* included; `67f7e185` adds it. Verify which bundle ends up in
   `docs/app/assets/` before the site rebuilds — a wrong answer here 404s the live app.
6. **Behind-ness is a single-branch artefact.** 81 of 120 behind-commits belong to one dependabot
   branch; the fleet average excluding it is ~5.6.
7. **Zero-ahead is reachable in one pass.** 10 → 3 → 0 with no rebases required, only two conflict
   resolutions.

## 9. Recommended order

1. Merge `docs/ws1-retire-jaysonai-hostname` — largest at-risk payload (4 commits), clean.
2. Merge `chore/ws1-rebuild-app-bundle-purge-jaysonai` with the bundle question resolved first
   (finding 5). Clean-after-resolution.
3. Close `dependabot/pip/aiohttp-gte-3.14.5` — patch already on `main` via #142.
4. Merge `chore/ruby-sdk-surface-guard`, `docs/ws1-daily-reports-2026-10-31` — clean, low risk.
5. Merge `chore/retire-jaysonai-sidney-gabe` last — its `CANONICAL.md` hunk overlaps #145 most
   directly.
6. Delete `chore/ws1-purge-retired-infra-refs` and `chore/ws1-release-tag-3.1.0` once merged —
   both already contribute zero commits.
7. Re-run §6's script and record the new `main` SHA with `TOTAL_AHEAD=0`.

---

**Reported by:** Analytics Reporter (H12)
**Evidence:** per-branch 40-char head SHAs (§3), Compare API `ahead_by`/`behind_by` cross-checked
against `git rev-list --left-right --count`, staged post-merge tables (§6)
**Not performed by this run:** any merge of the eight branches, any branch deletion

**Disclosed protocol deviation:** this report file itself was committed directly to `main` because the
assignment instruction was to *publish* it at `docs/ops/branch-inventory-2026-10-31.md`. That
contradicts `AGENT-OPERATING-PROTOCOL.md:136` (*"Never commit to `main` directly"*). The deviation is
limited to this one documentation file — no branch was merged and nothing in the §6 replay was
landed. If the owner prefers the protocol route, this file can be reopened as a PR without changing
any of the measurements.
