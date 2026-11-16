# mem20 — Repository Analytics Report

**Generated:** 2026-11-16T13:06:05.378530+00:00  
**Repo:** `bythewayz66-glitch/mem20`  
**HEAD:** `0224a64946a2c00313a9872515893157adcbc47e`  
**Analyzed ref:** `origin/main` — every figure below describes this commit, not the working tree  
**HEAD date:** 2026-11-16T06:55:07+00:00  
**VERSION:** 4.0.0  
**Dataset:** [`data/repo-analytics.json`](data/repo-analytics.json) — regenerate with `python3 scripts/analytics/extract_repo_analytics.py`

> Every figure below is computed from this repository's own git history and in-tree artifacts. No external data, no estimates. The JSON is the artifact of record; this report and `dashboard.html` are rendered from it.

---

## 1. Executive summary

- **1,158 commits** over **70 days** (2026-09-06 → 2026-11-16), averaging **16.5 commits/day**.
- **11,439 tracked files** across **25 top-level directories**; `mem20orcaz/` alone holds 2,798 files (24.5% of the tree).
- **Tool surface grew +176 tools (+56.6%) and +90 domains (+230.8%)** between the first and last `docs/surface.json` snapshot (2026-11-04 → 2026-11-10).
- **50 commits sit on 12 branches ahead of `main`** out of 102 remote branches — unmerged work is the largest single delivery risk in the repo.
- Retrieval quality is **mode-dependent, not uniformly good**: best aggregate hit rate is `vector` at **0.776** (MRR 0.721), while the fastest mode at scale is `hybrid-rerank-off` at **51.6 ms p50**.

### Immediate actions

1. **Triage the 50-commit backlog.** `gtm/claim-ledger-v7-rebase` alone is 14 commits ahead. Either land or close each branch; the count only grows.
2. **Fix the `hybrid` latency regression.** `hybrid` costs **1831 ms p50** for a 0.512 hit rate, while `hybrid-rerank-off` delivers the same 0.776 hit rate in 52 ms. The cross-encoder is buying nothing at this corpus size.
3. **Tag `v4.0.0`.** `VERSION` says 4.0.0 but the latest semver tag is behind `main`; releases are not traceable to a commit.

---

## 2. Commit velocity

### Monthly

| Month | Commits | Cumulative | Share of total |
|---|---:|---:|---:|
| 2026-09 | 24 | 24 | 2.1% |
| 2026-10 | 434 | 458 | 37.5% |
| 2026-11 | 700 | 1,158 | 60.4% |

Peak month: **2026-11** with **700 commits** (60.4% of all history).

### Weekly (ISO week)

| Week | Commits | Cumulative |
|---|---:|---:|
| 2026-W36 | 1 | 1 |
| 2026-W38 | 1 | 2 |
| 2026-W39 | 16 | 18 |
| 2026-W40 | 6 | 24 |
| 2026-W41 | 9 | 33 |
| 2026-W42 | 101 | 134 |
| 2026-W43 | 99 | 233 |
| 2026-W44 | 533 | 766 |
| 2026-W45 | 310 | 1,076 |
| 2026-W46 | 62 | 1,138 |
| 2026-W47 | 20 | 1,158 |

Peak week: **2026-W44** with **533 commits**. The last two weeks (2026-W46: 62, 2026-W47: 20) show a sharp cool-down from the 533-commit peak — worth confirming that is intentional consolidation rather than a stalled pipeline.

### Commit type mix

| Type | Count | Share |
|---|---:|---:|
| `(untyped)` | 256 | 22.1% |
| `fix(conformance)` | 130 | 11.2% |
| `merge` | 44 | 3.8% |
| `docs(ops)` | 39 | 3.4% |
| `fix` | 37 | 3.2% |
| `docs` | 35 | 3.0% |
| `feat` | 33 | 2.8% |
| `fix(mcp)` | 28 | 2.4% |
| `docs(gtm)` | 24 | 2.1% |
| `chore` | 21 | 1.8% |
| `chore(adapz)` | 13 | 1.1% |
| `build(web)` | 12 | 1.0% |

`(untyped)` at 256 commits (22.1%) is the single largest bucket — conventional-commit discipline is not enforced repo-wide, which is why automated changelog generation is unreliable here.

### Authorship

| Author | Commits | Share |
|---|---:|---:|
| bythewayz66-glitch | 801 | 69.2% |
| jayson | 35 | 3.0% |
| JaysonAIOnline | 31 | 2.7% |
| Mem20 C++ Expert | 30 | 2.6% |
| Mem20 Content | 30 | 2.6% |
| spacebunny | 29 | 2.5% |
| Server Builder | 28 | 2.4% |
| mem20 Orchestrator | 21 | 1.8% |
| dependabot[bot] | 15 | 1.3% |
| mem20-web-bot | 12 | 1.0% |
| Super Agent | 12 | 1.0% |
| AI Engineer Agent | 10 | 0.9% |

**bythewayz66-glitch** accounts for **69.2%** of all commits. Agent identities (matched on agent/bot/expert/builder/orchestrator/content/assistant/reporter naming) account for **337 commits (29.1%)** across 39 distinct identities. Bus factor on commit authorship is effectively 1 — a real continuity risk.

---

## 3. Branch and delivery risk

- Remote branches: **102**
- Branches ahead of `main`: **12**
- Total unmerged commits: **50**
- Tags: **132**

| Branch | Commits ahead of `main` |
|---|---:|
| `gtm/claim-ledger-v7-rebase` | 14 |
| `fix/post20-defects` | 9 |
| `feat/4.0-mem20-cpp-expert-braid` | 6 |
| `ruby-sdk-release-2026-11-01` | 6 |
| `feat/4.0-server-builder-mem20meshz` | 4 |
| `feat/4.0-server-builder-gateway` | 3 |
| `docs/ws1-narrative-serial-2026-11-01` | 2 |
| `feat/4.0-mem20-cpp-expert-mem20wasmz` | 2 |
| `feat/4.0-conformance-gate-language-aware-discovery` | 1 |
| `feat/4.0-super-agent-memory-engine` | 1 |
| `fix/open-issues-5` | 1 |
| `fix/perl-sdk-surface-272` | 1 |

The top three branches hold **29 of 50** unmerged commits (58%). With 102 remote branches and 132 tags against 1,158 commits, branch and tag hygiene — not throughput — is the binding constraint on release confidence.

---

## 4. Codebase composition

**11,439 tracked files.**

### By top-level directory (top 15)

| Directory | Files | Share |
|---|---:|---:|
| `mem20orcaz/` | 2,798 | 24.5% |
| `mem20fabricz/` | 701 | 6.1% |
| `mem20officez/` | 617 | 5.4% |
| `mem20owebz/` | 596 | 5.2% |
| `mem20famz/` | 512 | 4.5% |
| `mem20selfz/` | 462 | 4.0% |
| `mem20enginez/` | 452 | 4.0% |
| `mem20simz/` | 360 | 3.1% |
| `mem20mktz/` | 343 | 3.0% |
| `mem20pipez/` | 341 | 3.0% |
| `mem20facez/` | 334 | 2.9% |
| `docs/` | 331 | 2.9% |
| `mem20twinz/` | 281 | 2.5% |
| `mem20labz/` | 217 | 1.9% |
| `mem20gamez/` | 185 | 1.6% |

### By extension (top 12)

| Extension | Files | Share |
|---|---:|---:|
| `.json` | 3,803 | 33.2% |
| `.py` | 3,743 | 32.7% |
| `.md` | 1,276 | 11.2% |
| `.ts` | 472 | 4.1% |
| `.html` | 365 | 3.2% |
| `.toml` | 350 | 3.1% |
| `.js` | 200 | 1.7% |
| `.css` | 174 | 1.5% |
| `.meta` | 140 | 1.2% |
| `.glb` | 116 | 1.0% |
| `.tsx` | 112 | 1.0% |
| `.yml` | 105 | 0.9% |

JSON (3,803) and Python (3,743) together are 66.0% of the tree. The JSON weight is largely generated manifests and evidence artifacts — it is the repo's audit trail, and it is also the main driver of clone size.

---

## 5. Tool / domain surface growth

`docs/surface.json` is regenerated from the live JSON-RPC `tools/list` response, so each snapshot is a measured surface, not a claim.

| Snapshot (commit date) | Tools | Domains | Unwired |
|---|---:|---:|---:|
| 2026-11-04 `a65869cf` | 311 | 39 | 19 |
| 2026-11-09 `5d19a1dc` | 487 | 129 | 19 |
| 2026-11-09 `d47c75ac` | 487 | 129 | 19 |
| 2026-11-09 `f61da552` | 487 | 129 | 19 |
| 2026-11-09 `68721736` | 487 | 129 | 19 |
| 2026-11-09 `3d73e516` | 487 | 129 | 19 |
| 2026-11-09 `642a175c` | 487 | 129 | 19 |
| 2026-11-09 `f7cac4a4` | 487 | 129 | 19 |
| 2026-11-09 `cdf11ab9` | 487 | 129 | 19 |
| 2026-11-10 `8bacb4a4` | 487 | 129 | 19 |

**311 → 487 tools** (+176, +56.6%) and **39 → 129 domains** (+90, +230.8%) in 6 days. Domain count grew faster than tool count, meaning the surface widened into new areas rather than deepening existing ones — 3.8 tools per domain now vs 8.0 before.

**19 tools are unwired** at the current pin — registered but not reachable through the live surface. That is the concrete gap between "built" and "shipped".

### Current domain distribution (top 15)

| Domain | Tools |
|---|---:|
| `memory` | 55 |
| `cognitive` | 19 |
| `world` | 14 |
| `versioncontrol` | 11 |
| `cloudservice` | 10 |
| `database` | 10 |
| `filesystem` | 10 |
| `lie` | 10 |
| `productivity` | 10 |
| `braid` | 9 |
| `communication` | 9 |
| `dev` | 9 |
| `marketing` | 9 |
| `thought_process` | 9 |
| `cloudstorage` | 8 |

---

## 6. Retrieval benchmark results

Corpus **`mem20-scale-corpus-v2`** — 700 grounded facts, 1,300 simulated facts, 250 queries. Embedding model `sentence-transformers/all-MiniLM-L6-v2` (384d), cross-encoder enabled.

> **Comparability caveat.** These numbers describe this corpus only. They are not comparable to Mem0 LoCoMo/LongMemEval or Zep DMR figures, which use different corpora and metrics. No LoCoMo result is claimed.

### Mode aggregates (query-weighted)

| Mode | Queries | Hit rate | MRR | p50 ms |
|---|---:|---:|---:|---:|
| `vector` | 250 | 0.776 | 0.721 | 250.3 |
| `hybrid-rerank-off` | 250 | 0.776 | 0.668 | 51.6 |
| `bm25` | 250 | 0.532 | 0.484 | 125.6 |
| `hybrid` | 250 | 0.512 | 0.505 | 1830.8 |
| `keyword` | 250 | 0.360 | 0.350 | 1629.4 |
| `graph` | 30 | 0.033 | 0.033 | 208.5 |
| `constant` | 250 | 0.000 | 0.000 | 0.0 |

### Best mode per query kind

| Query kind | Best mode | n | Hit rate | MRR | p50 ms |
|---|---|---:|---:|---:|---:|
| `adversarial` | `bm25` | 60 | 0.767 | 0.592 | 102.0 |
| `adversarial_hard` | `vector` | 40 | 0.750 | 0.583 | 203.9 |
| `contradiction` | `vector` | 40 | 1.000 | 1.000 | 296.0 |
| `direct` | `bm25` | 60 | 1.000 | 1.000 | 101.6 |
| `multi_hop` | `vector` | 30 | 1.000 | 0.950 | 299.6 |
| `unanswerable` | `bm25` | 20 | 0.000 | 0.000 | 149.7 |

### Full result matrix

| Mode | Kind | n | Hit rate | MRR | Leak | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| `bm25` | `adversarial` | 60 | 0.767 | 0.592 | 0.000 | 102.0 |
| `bm25` | `adversarial_hard` | 40 | 0.025 | 0.006 | 0.000 | 101.8 |
| `bm25` | `contradiction` | 40 | 0.050 | 0.030 | 0.000 | 195.9 |
| `bm25` | `direct` | 60 | 1.000 | 1.000 | 0.000 | 101.6 |
| `bm25` | `multi_hop` | 30 | 0.800 | 0.800 | 0.000 | 102.7 |
| `bm25` | `unanswerable` | 20 | 0.000 | 0.000 | 0.000 | 149.7 |
| `vector` | `adversarial` | 60 | 0.667 | 0.608 | 0.000 | 203.5 |
| `vector` | `adversarial_hard` | 40 | 0.750 | 0.583 | 0.000 | 203.9 |
| `vector` | `contradiction` | 40 | 1.000 | 1.000 | 0.000 | 296.0 |
| `vector` | `direct` | 60 | 0.900 | 0.864 | 0.000 | 202.0 |
| `vector` | `multi_hop` | 30 | 1.000 | 0.950 | 0.000 | 299.6 |
| `vector` | `unanswerable` | 20 | 0.000 | 0.000 | 0.000 | 297.1 |
| `hybrid` | `adversarial` | 60 | 0.167 | 0.167 | 0.000 | 1694.7 |
| `hybrid` | `adversarial_hard` | 40 | 0.050 | 0.050 | 0.000 | 1897.8 |
| `hybrid` | `contradiction` | 40 | 1.000 | 0.988 | 0.000 | 1899.2 |
| `hybrid` | `direct` | 60 | 1.000 | 0.978 | 0.000 | 1691.0 |
| `hybrid` | `multi_hop` | 30 | 0.533 | 0.533 | 0.000 | 1799.0 |
| `hybrid` | `unanswerable` | 20 | 0.000 | 0.000 | 0.000 | 2003.1 |
| `hybrid-rerank-off` | `adversarial` | 60 | 0.650 | 0.633 | 0.000 | 25.4 |
| `hybrid-rerank-off` | `adversarial_hard` | 40 | 0.625 | 0.515 | 0.000 | 25.5 |
| `hybrid-rerank-off` | `contradiction` | 40 | 1.000 | 0.546 | 0.000 | 25.7 |
| `hybrid-rerank-off` | `direct` | 60 | 1.000 | 0.979 | 0.000 | 77.9 |
| `hybrid-rerank-off` | `multi_hop` | 30 | 1.000 | 0.929 | 0.000 | 76.4 |
| `hybrid-rerank-off` | `unanswerable` | 20 | 0.000 | 0.000 | 0.000 | 78.6 |
| `graph` | `multi_hop` | 30 | 0.033 | 0.033 | 0.000 | 208.5 |
| `keyword` | `adversarial` | 60 | 0.167 | 0.167 | 0.000 | 1800.1 |
| `keyword` | `adversarial_hard` | 40 | 0.025 | 0.006 | 0.000 | 3198.4 |
| `keyword` | `contradiction` | 40 | 0.125 | 0.108 | 0.000 | 2102.3 |
| `keyword` | `direct` | 60 | 1.000 | 0.983 | 0.000 | 1399.1 |
| `keyword` | `multi_hop` | 30 | 0.467 | 0.467 | 0.000 | 380.4 |
| `keyword` | `unanswerable` | 20 | 0.000 | 0.000 | 0.000 | 895.9 |
| `constant` | `adversarial` | 60 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | `adversarial_hard` | 40 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | `contradiction` | 40 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | `direct` | 60 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | `multi_hop` | 30 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | `unanswerable` | 20 | 0.000 | 0.000 | 0.000 | 0.0 |

### What the numbers say

- **`vector` and `hybrid-rerank-off` tie on hit rate (0.776) but differ 4.9× in latency.** The cross-encoder is not paying for itself.
- **`hybrid` is the worst trade in the table**: 1831 ms p50 for a 0.512 hit rate — slower *and* less accurate than `hybrid-rerank-off`.
- **`adversarial_hard` is the real gap.** Best hit rate on that kind is 0.750. Paraphrase-hard probes are where the retrieval stack actually fails.
- **`unanswerable` reads 0.000 across every mode** — the control holds, so the scorer is not inflating hits.

### Benchmark lineage

- v1 measured modes: `graph`, `hybrid`, `keyword`, `semantic`
- v2 supersedes corpus `mem20-agent-kb-v1` (14 facts / 13 queries) → 700 facts / 250 queries (50× facts, 19× queries).

v1 → v2 is a **corpus change, not a regression or an improvement** — the adversarial class was rebuilt and the scorer was fixed, so the two runs are not comparable. Any trend line drawn across them would be false.

---

## 7. Method and limitations

**Sources**

- `git log` / `git rev-list` / `git ls-tree` on a fresh clone of `bythewayz66-glitch/mem20` at `0224a64946a2`.
- `docs/surface.json` read at every commit that touched it (10 snapshots).
- `benchmarks/results/latest.json`, `docs/benchmarks/results-v1.json`, `docs/benchmarks/results-v2.json`, `docs/benchmarks/experiments.json`.

**Limitations — read these before quoting a number**

- Commit counts include merge commits and agent-authored commits; they measure *activity*, not human effort.
- The surface-growth series has only 10 snapshots and 8 of them land on the same day (2026-11-09), so the growth curve is a step function, not a smooth trend. The 2026-11-04 → 2026-11-09 jump is one regeneration, not five days of steady growth.
- Benchmark numbers come from a single run on one machine (`Linux-6.8.0-87-generic-x86_64-with-glibc2.36`); no repeated trials, so no confidence intervals are reported. Treat differences under ~0.05 hit rate as noise.
- `graph` mode was only scored on `multi_hop` (n=30), so its aggregate is not comparable to the 250-query modes.
- Branch-ahead counts are a point-in-time snapshot and move with every push.

---

*Rendered from `data/repo-analytics.json` by `scripts/analytics/render_analytics.py`. Dashboard: [`dashboard.html`](dashboard.html).*
