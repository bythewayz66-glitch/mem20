# Branch disposition — 2026-10-31

**Measured at:** 2026-10-31, America/Denver
**Repository:** `github.com/bythewayz66-glitch/mem20`
**Baseline `main` at measurement:** `66d4e5a09d3919f0b0d477777ceb653305c61967`
**`main` at final verification:** `5bcc4fc08a671a7f5f806a8c2a1303632e9321c9`
**Measured by:** Mem20-admin (H5, merge order 5 of 5)
**Method:** fresh `git clone` + `git fetch --all --prune`, then per branch
`git rev-list --left-right --count main...<head>`, `git merge-base --is-ancestor`,
`git cherry main <head>` (patch-equivalence), and `git diff --stat main...<head>`.
Every row below is a real command result from this run, not a report from another agent.

> **Note on a moving baseline.** `main` advanced three times during this run
> (`f1672473` → `ca2a72b` → `66d4e5a0` → `10c9b95b` → `5bcc4fc0`) as other agents landed
> their own lanes. §1 records the state at measurement; §12 records the final re-verification
> and the two rows that changed underneath this document.

---

## 1. Disposition table (state at measurement, `main` = `66d4e5a0`)

| # | Branch | Head measured | Ahead / Behind | Ancestor of `main`? | Disposition |
|---|---|---|---:|---|---|
| 1 | `chore/ws1-purge-retired-infra-refs` | `de37968ac72cb89e9dd555bb67923220e959a260` | 0 / 11 | **YES** | **MERGED (H1)** via #145 → `f1672473`. Delete branch. |
| 2 | `docs/ws1-retire-jaysonai-hostname` | `080fdda1df70920993d272ed43d8848fe7830875` | 0 / 4 | **YES** | **MERGED (H2)** via `ca2a72b`. Delete branch. |
| 3 | `chore/ws1-rebuild-app-bundle-purge-jaysonai` | `faf9cef3727950c40e1e7db2f4252baa92a958d9` | 2 / 15 | **no** | **NOT MERGED.** PR **#146 is open**. Keep — do not delete. |
| 4 | `chore/ruby-sdk-surface-guard` | `c56ccb092eef6858edddd284dddd57828e89ed2f` | 1 / 12 | **no** | **NOT MERGED at measurement** — landed later in this run as `10c9b95b` (see §12). |
| 5 | `docs/ws1-daily-reports-2026-10-31` | `4f20ecfb848f80e2fe4490050ecfb1e178cea401` | 0 / 15 | **YES** | **MERGED (H5)** via #147 → `66d4e5a0`. Delete branch. |
| 6 | `chore/retire-jaysonai-sidney-gabe` | `d0ac17b065405446ed0bf9a42b4d07330bb2cc7f` | 1 / 15 | **no** | **SUPERSEDED by H1.** Close, do not merge. |
| 7 | `dependabot/pip/aiohttp-gte-3.14.5` | `6a087a231c9066694208048a69deb780a330e433` | 1 / 89 | **no** | **SUPERSEDED** — #142 merged as `6b3bdca2`. **DELETED this run.** |
| 8 | `chore/ws1-release-tag-3.1.0` | `73343f6853ec4b3577198e783c89bbb1a5526bf2` | 0 / 11 | **YES** | **Already merged** via `27c1e5f` (#144). **DELETED this run.** |
| 9 | `main` (baseline) | `66d4e5a09d3919f0b0d477777ceb653305c61967` | — | — | Reference point. |

`Ahead` = commits on the branch not on `main`. `Behind` = commits on `main` not on the branch.

---

## 2. Corrections to the SHAs supplied in the H5 task card

Two of the eight SHAs in the task card **do not exist in this repository**, and one other is
not the branch head. Recorded here so the record is not silently wrong:

| Branch | SHA given in task | Reality |
|---|---|---|
| `chore/ws1-purge-retired-infra-refs` | `1df637d6` | **No such object.** `git cat-file -e 1df637d6^{commit}` fails. Actual head is `de37968ac7`. |
| `docs/ws1-retire-jaysonai-hostname` | `d010fdb3` | **No such object.** Actual head is `080fdda1df`. |
| `chore/ws1-rebuild-app-bundle-purge-jaysonai` | `67f7e185` | Exists, but it is the **first of two** commits on the branch, not the head. Head is `faf9cef372`. |
| `chore/ruby-sdk-surface-guard` | `c56ccb09` | Correct — matches head. |
| `docs/ws1-daily-reports-2026-10-31` | `4f20ecfb` | Correct — matches head. |
| `chore/retire-jaysonai-sidney-gabe` | `d0ac17b0` | Correct — matches head. |
| `dependabot/pip/aiohttp-gte-3.14.5` | `6a087a23` | Correct — matches head. |
| `chore/ws1-release-tag-3.1.0` | `73343f68` | Correct — matches head. |

---

## 3. Correction to the merge premise: H3 was NOT merged

The task card described H3 and H4 as "merged". At measurement, **neither was on `main`.**
Evidence:

```
$ git merge-base --is-ancestor faf9cef3727950c40e1e7db2f4252baa92a958d9 main   # H3
(exit 1 — not an ancestor)

$ git merge-base --is-ancestor c56ccb092eef6858edddd284dddd57828e89ed2f main   # H4
(exit 1 — not an ancestor)

$ git cherry main chore/ws1-rebuild-app-bundle-purge-jaysonai
+ 67f7e18516c9e0db46edf360f8334bdb67dc34f1
+ faf9cef3727950c40e1e7db2f4252baa92a958d9

$ git cherry main chore/ruby-sdk-surface-guard
+ c56ccb092eef6858edddd284dddd57828e89ed2f
```

`+` means the patch is **not** in `main`. Neither branch was squash-merged either —
`git cherry` would have printed `-` for a patch-equivalent commit.

**H4 has since landed** — merged into `main` as `10c9b95b` during this run (§12).

**H3 is still not merged.** It remains open PR #146 (opened 2026-10-31T22:59:45Z). Its content
is genuinely absent from `main`: `docs/app/index.html` on `main` still points at
`index-BmhMl8hv.js`, and that bundle still contains a `jaysonai` string
(`git grep -c -iE 'jaysonai' main -- 'docs/app/assets/*'` → 1 match). The branch replaces it
with `index-BS9Fg-qc.js`.

**Consequence:** the "5 of 5" merge order is complete for H1, H2, H4 and H5. **H3 remains open
work and must not be counted as landed.**

---

## 4. H5a — merge performed this run

| Item | Value |
|---|---|
| Branch | `docs/ws1-daily-reports-2026-10-31` |
| Branch head | `4f20ecfb848f80e2fe4490050ecfb1e178cea401` |
| PR | **#147** — `docs(ops): attest daily-reports push under owner token mandate (H5)` |
| Merge method | merge commit |
| **Merge SHA** | **`66d4e5a09d3919f0b0d477777ceb653305c61967`** |
| Parents | `d709d1b1796c325c4acb8f6121a8e45adf9fce88` + `4f20ecfb848f80e2fe4490050ecfb1e178cea401` |
| Diff | 1 file, +10 / −0 |

The five daily-report records for 2026-10-27 → 10-31 were **already on `main`** via
`f25b57d776149985676bfd14e8968c320e3af661` (#143). The only outstanding delta on the branch
was the credential-attestation block appended to `published/daily-reports/2026-10-31.md`,
which is what #147 landed. Verified after merge:

```
$ git merge-base --is-ancestor 4f20ecfb848f80e2fe4490050ecfb1e178cea401 main
(exit 0 — H5a verified)
```

`published/daily-reports/` on `main` now carries 2026-10-24 … 2026-10-31 (8 files).

---

## 5. H5b — this document

| Item | Value |
|---|---|
| Path | `docs/ops/branch-disposition-2026-10-31.md` |
| **Commit SHA** | **`5bcc4fc08a671a7f5f806a8c2a1303632e9321c9`** |
| Parent | `10c9b95bbab30c042756a529a7f3a16383eedec0` |
| Size | 11,118 B (first revision) |

---

## 6. Ref deletions performed this run

Both were proven fully contained in `main` before deletion.

| Branch | Proof of containment | Result |
|---|---|---|
| `dependabot/pip/aiohttp-gte-3.14.5` | `git cherry main` → `- 6a087a23` (patch already in `main`); `requirements.txt` on `main` reads `aiohttp>=3.14.5` | **deleted** (HTTP 204) |
| `chore/ws1-release-tag-3.1.0` | `git merge-base --is-ancestor 73343f68 main` → exit 0; 0 ahead / 11 behind; tag `v3.1.0` → `97add7fdf43cc55925a3078e56b410cb9bb67233`, also an ancestor of `main`; `VERSION` on `main` = `3.1.0` | **deleted** (HTTP 204) |

Deleting a branch does not delete its commits — both remain reachable from `main`, and the
`v3.1.0` tag is untouched. Confirmed gone:
`git ls-remote --heads origin 'dependabot/pip/aiohttp-gte-3.14.5' 'chore/ws1-release-tag-3.1.0'` → 0 lines.

---

## 7. Branches recommended for deletion (not deleted — outside this task's authority)

Fully merged, carrying nothing `main` lacks. Deletion is safe but was **not** performed here
because the task card only authorised the two deletions in §6.

| Branch | Head | Why safe |
|---|---|---|
| `docs/ws1-retire-jaysonai-hostname` | `080fdda1df` | 0 ahead; ancestor of `main` |
| `docs/ws1-daily-reports-2026-10-31` | `4f20ecfb84` | 0 ahead; ancestor of `main` (merged as #147) |
| `chore/ruby-sdk-surface-guard` | `c56ccb092e` | ancestor of `main` (merged as `10c9b95b`) |

`chore/ws1-purge-retired-infra-refs` was on this list at measurement; it has since been
deleted by another agent (§12).

---

## 8. `chore/retire-jaysonai-sidney-gabe` — why "superseded" is the right call

Head `d0ac17b065405446ed0bf9a42b4d07330bb2cc7f`, 1 ahead / 15 behind, **not** an ancestor of
`main`, and `git cherry` reports `+` — so it is **not** patch-identical to H1. That is expected:
it is an earlier, narrower attempt at the same purge. Its five files are
`CANONICAL.md`, `docs/README.md`, `docs/gtm/README.md`, `docs/webdev-deployment-targets.md`
(−114 lines) and `docs/webdev/ionos-dns-mem20.md`.

H1 (`f1672473`, #145) and H2 (`ca2a72b`) already rewrote those same surfaces, and `main` now
carries the retirement statement in `CANONICAL.md:62` ("The former server channel is
**retired**: the Sidney host (`216.198.115.91`) no longer…"). Merging this branch on top would
re-apply an older edit over newer text and risk reverting H1/H2 wording.

**Disposition: close without merging.** If any specific line from it is still wanted, it should
be re-cut as a fresh branch against current `main`, not merged as-is.

---

## 9. Token mandate — verified, not asserted

The mandate: owner token via remote URL or `GITHUB_TOKEN`/`GH_TOKEN` env only; never in a
tracked file, workflow YAML, committed `.git/config`, or commit message.

Checks run against `main` this run:

```
$ git grep -n -I -E 'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}' main -- .
main:mem20botz/tests/test_mem20botz.py:323:  out = mask_secrets("ghp_0123456789abcdefghijABCDEFGHIJ")
```

The single match is a **test fixture** for the secret-masking helper, not a live credential.
`.github/workflows/ci.yml` carries a "Guard against added secrets" step that assembles its
patterns from fragments and fails the build on any secret-shaped added line. The H5 branch
commit message contains no credential (`grep -iE 'ghp_|github_pat_|token='` → no match).

No token was written by this run. All GitHub operations in this run went through the
authenticated GitHub connection; no credential was placed in the working tree, `.git/config`,
a workflow file, or a commit message.

---

## 10. Retired infrastructure

Sidney (`216.198.115.91`) and `gabe` are **retired**. This document records no live dependency
on either. The only remaining mention of the Sidney IP on `main` is the dated retirement
statement in `CANONICAL.md:62`, which is intentional historical record, not a live reference.

---

## 11. Follow-ups with owners

| # | Action | Owner | Evidence required |
|---|---|---|---|
| 1 | Land **H3** — review and merge PR #146 (`chore/ws1-rebuild-app-bundle-purge-jaysonai`). `main` still serves a bundle containing a `jaysonai` string. | Webpage Developer / GitHub Repo Assistant | merge SHA on `main`; `git grep -c -iE 'jaysonai' main -- 'docs/app/assets/*'` → 0 |
| 2 | Close `chore/retire-jaysonai-sidney-gabe` without merging (superseded by H1/H2). | GitHub Repo Assistant | closed PR/ref state |
| 3 | Delete the three fully-merged branches in §7. | GitHub Repo Assistant | 204 on each ref delete |
| 4 | Re-cut any still-wanted line from `chore/retire-jaysonai-sidney-gabe` against current `main` as a fresh branch. | GitHub Repo Assistant | new branch + PR |

---

## 12. Final re-verification (`main` = `5bcc4fc0`)

Re-run after this document was first committed, because `main` moved during the run.

```
$ git log --oneline -4 origin/main
5bcc4fc docs(ops): record branch disposition for all 9 refs measured 2026-10-31 (H5b)
10c9b95 Merge branch 'chore/ruby-sdk-surface-guard' into main (ruby SDK surface guard, H4)
66d4e5a Merge pull request #147 from bythewayz66-glitch/docs/ws1-daily-reports-2026-10-31
d709d1b docs(tools): correct docs/02-tools-reference.md to 270 tools / 27 domains
```

Two rows in §1 changed underneath this document:

| Branch | Change | Final state |
|---|---|---|
| `chore/ruby-sdk-surface-guard` | **H4 landed** as `10c9b95b` (merged by another agent mid-run) | ancestor of `main` = **YES** |
| `chore/ws1-purge-retired-infra-refs` | **ref deleted** by another agent | branch **GONE**; commits still reachable via `f1672473` |

Final ancestry re-check:

```
docs/ws1-retire-jaysonai-hostname              080fdda1df   ancestor=YES
chore/ws1-rebuild-app-bundle-purge-jaysonai    faf9cef372   ancestor=no
chore/ruby-sdk-surface-guard                   c56ccb092e   ancestor=YES
docs/ws1-daily-reports-2026-10-31              4f20ecfb84   ancestor=YES
chore/retire-jaysonai-sidney-gabe              d0ac17b065   ancestor=no
```

**Net result: of the 9 refs measured, 5 are fully contained in `main` (H1, H2, H4, H5,
release-tag), 2 were deleted as superseded, 1 is superseded and should be closed
(`chore/retire-jaysonai-sidney-gabe`), and 1 is genuinely unlanded work
(`chore/ws1-rebuild-app-bundle-purge-jaysonai`, PR #146).**

Branches that appeared during the run and are **out of scope** for this document (other
agents' lanes, not part of the 9): `chore/benchmarks-accuracy-2026-10-31`,
`chore/deck-assets-accuracy`, `chore/launch-copy-accuracy`, `chore/perl-sdk-surface-guard`,
`chore/ux-docs-accuracy`, `chore/web-src-purge-retired-infra`.

---

## 13. House numbers (unchanged, carried for consistency)

- **257 tools across 26 domains** — legacy house number.
- Directly counted surface: **270 tools / 27 domains** (`docs/02-tools-reference.md` corrected
  to this in `d709d1b`).
- TAM **$1.28B** / SAM **$282M** / SOM **$1.68M**; blended ACV **$14,000**.

---

*As an AI Agent, I cannot provide legally protected, personalized investment advice. This
analysis is for informational purposes only and does not constitute investment advice or
recommendations. Consult a licensed financial advisor before making investment decisions.*
