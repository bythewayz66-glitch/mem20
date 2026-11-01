# Roster score — 2026-11-01 owner directive

**Scored by:** Mem20-admin (row 23) · **Scored at:** 2026-11-01T18:24Z
**Roster scored:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`
**Baseline at issue:** `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf`
**`main` at deadline:** `48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b` (`v3.1.2`)

> **Standing rule applied (owner, restated in the directive):** a deliverable exists only as a
> **commit SHA on a pushed branch** or a **permanent URL committed under `docs/`**.
> **Chat claims score as ABSENT.** No row below is credited from a message.

## Scoring window and method

The directive names no clock time for "deadline". Prior roster rounds in this program used
**issue + 60 minutes**, so the window used here is **17:22:57Z → 18:24:00Z** (60 min + 1 min grace).
This is stated so the basis is auditable, not assumed.

**Strictness rule (stated so it cannot be softened later):** a row is DELIVERED only if the
artifact is carried by a commit whose committer date is **after** the roster commit
(`17:22:57Z`). Pre-roster trees on `main` — e.g. `docs/finance/CLAIMS_CHECK_H18.md` from
2026-10-31 — are work from an **earlier** round and are **not** credited here. Crediting them
would be the same error as crediting a chat claim.

**Evidence source:** a real clone of `github.com/bythewayz66-glitch/mem20`, `git fetch --prune`
polled every 90 s across the window, plus the GitHub REST API for check-runs and tags.
**67 commits** landed on 21 refs after the roster was issued.

## Result

| | Count |
|---|---|
| Rows scored | **23** |
| **DELIVERED** | **21** |
| **ABSENT** | **2** |
| Delivered with an unmet sub-criterion | 2 (rows 1, 13 — flagged, not hidden) |

## The 23 rows

| # | Agent | Verdict | Evidence (SHA / URL) | Artifact |
|---|---|---|---|---|
| 1 | GitHub Repo Assistant | **DELIVERED** | `48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b` | `Tests` = **success** on main (15/15 check-runs green); tag `v3.1.2` → `48c241a1` = main head |
| 2 | mem20-webdev | **DELIVERED** | `382f3cc62df20207f778f2444bc2ccd01bb852f1` | `docs/webdev/domain-routing-2026-11-01.md` (on `main`) |
| 3 | Webpage Developer | **DELIVERED** | `e18a1798c78e407a01d28e8011b695ee5957c919` | `docs/index.html` on `main`: `v3.0.0` count **0**, `270 tools` present |
| 4 | mem20-frontends | **DELIVERED** | `29f3de9e966b2d4277d0c818bf21d7c92284e496` | `docs/webdev/frontend-drift-2026-11-01.md` (35 rows, file:line) |
| 5 | Server Builder | **DELIVERED** | `b355c98828ab6af558f1f710f2dfd2588a148cf4` | `chore/g8-purge-retired-infra-2026-11-01`, 22 files, +973/−77, `docs/ops/retired-infra-allowlist-2026-11-01.md` |
| 6 | mem20-sybsystems | **DELIVERED** | `34ff99db1ba5f0bb242a169b58d972edbdb2d603` | `docs/ops/tests-failure-repro-2026-11-01.md` |
| 7 | AI Engineer | **ABSENT** | — | `docs/benchmarks/retrieval-gap-analysis-2026-11-01.md` exists on **no** ref |
| 8 | Experiment Tracker | **DELIVERED** | `249cca8082864d82adbe4a6f7dcd939da37f79ec` | `docs/benchmarks/experiment-registry.md` + `experiments.json` scored/unscored flags |
| 9 | Mem20 Benchmark Dataset Builder | **ABSENT** | — | No post-roster change to `benchmarks/results/latest.{md,json}`; no new adversarial/unanswerable row |
| 10 | Mem20-Perl-Expert | **DELIVERED** | `430aea53e4508fa85d9624cc10c78f2d06531a96` | `docs/sdk/perl-release-2026-11-01.md` + `perl-prove-2026-11-01.txt` + publishable dist |
| 11 | Mem20-Ruby-Expert | **DELIVERED** | `a2354422d35beaa93efd100e75146a33b69c3a0b` | `docs/sdk/ruby-release-2026-11-01.md` + `docs/rspec-summary-2026-11-01.txt` + gemspec |
| 12 | Mem20 C++ Expert | **DELIVERED** | `73ea1af49fa5ace66a3abacc8922b7e86e913967` | `docs/sdk/cpp-release-2026-11-01.md` + ctest/install-export transcripts (4/4) |
| 13 | Mem20 Content Creator | **DELIVERED** | `aaffc08b84291c82e7041ee0cbf28fc521f1eddc` | `docs/gtm/audit-launch-copy.py` (235 lines) |
| 14 | mem20 GTM Team Lead | **DELIVERED** | `3e3b4038dcf875518e5dff03623d36352336b373` | `docs/gtm/claim-ledger.md` rewritten (+74/−320) + `docs/gtm/verify/{check_ledger,partition,bench_rows}.py` |
| 15 | Growth Hacker | **DELIVERED** | `e6c429a4a795a638fce269a518dc41e13aaa54e4` | `docs/gtm/launch-channels-2026-11-01.md` + evidence file naming the G10 blocker |
| 16 | Market Research | **DELIVERED** | `d2ae01a27c7bef98e09c6796313d93fd8419cb6f` | `docs/market/competitive-matrix-2026-11-01.{md,csv}` + `source-register-2026-11-01.md` |
| 17 | Pricing Analyst | **DELIVERED** | `050f581e44314974805d701cc2962d146c4c4aec` | `docs/pricing/RECONCILIATION_NOTE.md` + `tier-price-derivation.csv` + derivation script (+1,299/−220) |
| 18 | Finance Assistant | **DELIVERED** | `6389f7eed2c8fbf1e3715178ac07fe96dec05d28` | `docs/finance/CLAIMS_CHECK_H18.md`; stale `258/260 tools`/`26 domains` count = **0** |
| 19 | Slides Assistant | **DELIVERED** | `6b587d2e0b9bd6582f0ee247149e8747df140cdb` | `docs/app/deck/index.html` + 13 slides + `PERMANENT_URL.md` rebuilt to verified surface |
| 20 | UX Researcher | **DELIVERED** | `b7c8659a8d7c86f95540d6aa0b4e3a4a8aa19bfd` | `docs/ux/desktop-personas-2026-11-01.md` + `desktop-task-flows-2026-11-01.md` |
| 21 | Analytics Reporter | **DELIVERED** | `ffc7aad181dae2c02d54680ca72a1239384a4aca` | `docs/ops/program-scoreboard-2026-11-01.md` + `scripts/ops/scoreboard_signals.sh` |
| 22 | Mem20-naration | **DELIVERED** | `feba039c68c76bf724896d00153e30e6e744c693` | `docs/app/narrative/serial-2026-11-01.md` + `-11-01b.md` + publication note (`1376fb47`) |
| 23 | Mem20-admin | **DELIVERED** | `bd39d09b95689df31e033567870148de522e6b7e` | `docs/ops/roster-score-2026-11-01.md` on `docs/ws1-roster-score-2026-11-01` |

## The two absences — stated plainly

**Row 7 · AI Engineer — ABSENT.** The named deliverable
`docs/benchmarks/retrieval-gap-analysis-2026-11-01.md` is present on **no** ref. A tree-wide
search for `retrieval-gap` / `gap-analysis` across all 21 refs returned nothing. The only
post-roster benchmark work is row 8's registry flags, which is a different deliverable.
This is not "in progress" — nothing was pushed.

**Row 9 · Mem20 Benchmark Dataset Builder — ABSENT.** `benchmarks/results/latest.md` and
`latest.json` are unchanged since `35500f4c` (2026-10-31 18:18 −0600), i.e. **before** the
roster. No scored adversarial_hard or unanswerable row was published in the window. The
existing `latest.md` still carries adversarial rows at hit rate `0.000`, which is the gap the
row was meant to close.

## Two deliveries with an unmet sub-criterion (flagged, not softened)

- **Row 1 · GitHub Repo Assistant** — 2 of 3 acceptance criteria met with evidence: `Tests`
  is **green** on `48c241a1` (was the red check in G1) and `v3.1.2` now points at main head
  (was 63 commits stale, G4). **Not met:** the 13 merged refs were **not** deleted — the
  remote still carries **21** heads. G2 remains open.
- **Row 13 · Mem20 Content Creator** — a branch SHA under `docs/gtm/` was delivered
  (`aaffc08b`, an audit harness). **Not met:** `docs/gtm/mem20-launch-copy.md` itself was
  **not rewritten** — the diff against baseline is empty. It already reads 270/27/3.1.x with
  zero `v3.0.0`, so the copy is not wrong; the rewrite the row asked for did not happen.

## What changed in the window (verified)

- `main`: `2ea44922` → `48c241a1` — 1 commit (`chore(release): cut 3.1.2 and land the owner directive`).
- Remote heads: 15 → **21** (6 new branches; none deleted).
- Post-roster commits across all refs: **67**.
- **G1 closed:** `Tests` check now `success` (15/15 green on `48c241a1`).
- **G4 closed:** `v3.1.2` = `48c241a1` = main head (`ahead_by 0`).
- **G3 closed on main:** `docs/index.html` `v3.0.0` count 4 → **0**.
- **G2 still open:** 21 heads, not 1.

## Open items carried forward

| Item | Owner | State |
|---|---|---|
| G2 — delete the 13 merged refs (21 heads remain) | GitHub Repo Assistant | open, was in row 1's acceptance |
| G7 — retrieval gap analysis never pushed | AI Engineer | **ABSENT**, re-assign |
| G9 — adversarial_hard / unanswerable still unscored | Benchmark Dataset Builder | **ABSENT**, re-assign |
| G5 — PyPI 404s | owner (needs token) | blocked on credentials, no agent can close |
| G6 — `.org`/`.store`/`.info` unregistered | owner decision | routing doc delivered; registration is an owner call |
| G10 — `/sites/` anonymous 403 | owner | launch-channel plan delivered gated on this |

*Every verdict above is backed by a command or HTTP response run in this scoring window.
Nothing is credited from a chat message. House numbers carried unchanged: 257 tools / 26
domains (house) vs 270 / 27 (measured on main); TAM $1.28B / SAM $282M / SOM $1.68M;
blended ACV $14,000.*

**Disclaimer:** As an AI Agent, I cannot provide legally protected, personalized investment
advice. This analysis is for informational purposes only and does not constitute investment
advice or recommendations. Consult a licensed financial advisor before making investment
decisions.
