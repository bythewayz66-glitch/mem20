# mem20 — GTM Claim Verification Ledger (v7)

**Seat:** Brand & Positioning Strategist / Opportunity & Market Analyst
**Repo:** https://github.com/bythewayz66-glitch/mem20 · **Branch read:** `main`
**HEAD at capture:** `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (2026-11-01 06:20:25 -0700)
**Captured:** 2026-11-01 · every row re-measured against a full clone at this HEAD; nothing inherited from v6.
**Surface of record:** **270 tools / 27 domains.** 257, 258 and 268 are **RETIRED** and survive only in §7.
**Supersedes:** v6 (HEAD `f1672473cd19d5926e1df0c80042259d3b4b17ca`, 2026-10-31).

> **Acceptance rule** (owner directive 2026-11-01, `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220`):
> *"the ledger has zero rows marked `verified` without a cited command."* Every row in §1, §3, §4, §5
> and §6 carries a **Status** and a **Command** cell. A row may not be `VERIFIED` unless its Command
> cell holds a runnable invocation, a file path, or a URL that settles it. Enforced mechanically:
>
> ```bash
> python3 docs/gtm/verify/check_ledger.py     # exit 0 = PASS
> ```
>
> Harnesses cited by the Command cells ship alongside this file: `docs/gtm/verify/check_ledger.py`,
> `docs/gtm/verify/bench_rows.py`, `docs/gtm/verify/partition.py`.

### Why v7 exists — five v6 findings were wrong

1. **The benchmark scores SEVEN modes, not two.** v6 said `hybrid` and `graph` had "no rows at all" and marked both `unmeasured`. At this HEAD `latest.json` scores `bm25`, `vector`, `hybrid`, `hybrid-rerank-off`, `graph`, `keyword`, `constant`. **Both are measured.**
2. **The `keyword` numbers moved.** v6 published `keyword` adversarial **1.000** / `adversarial_hard` **0.000**; now **0.167** / **0.025**. `semantic` is now `vector`, adversarial 0.950 → **0.667**.
3. **`docs/02-tools-reference.md` is FIXED** — prints 270/27, not 268/26. Only `docs/05` still carries the retired pair.
4. **Clone-audit artifacts are BACK** — `PROOF.md`, `UPGRADE.md`, `bench/clone_audit.json` ship; 293 packages / 65 distinct / 228 duplicates reproduce.
5. **`docs/index.html` still carries `v3.0.0` four times** (owner directive G3). Counts on that page are correct.

| # | Change since v6 | Detail |
|---|---|---|
| C1 | Benchmark scope 2 → 7 modes | `hybrid`/`graph` no longer `unmeasured` |
| C2 | `keyword`/`vector` numbers moved | see §5.1 |
| C3 | `docs/02` drift CLOSED | now 270/27 |
| C4 | Clone-audit artifacts present | 65 distinct / 228 duplicates / 293 packages |
| C5 | `docs/index.html` version drift OPEN | 4 × `v3.0.0` at lines 179, 486, 574, 604 |
| C6 | Tracked files 8,516 → 8,536 | `git ls-tree -r --name-only HEAD \| wc -l` |
| C7 | `open_issues_count` 1 → 0 | GitHub API this run |
| C8 | `latest.md` ≠ `latest.json` | new defect class, §5.4 |
| C9 | README still quotes the retired 14-fact / 13-query corpus | `README.md:99`, `:140` |

---

## 0. The weakest measured row — read before the strengths

**Source:** `benchmarks/results/latest.json`. Corpus **`mem20-scale-corpus-v2`**: 700 grounded, 1,300 simulated, 250 queries. Reproduce: `python3 docs/gtm/verify/bench_rows.py`.

| Mode | Query class | n | Hit rate | MRR | Leak rate |
|---|---|---:|---:|---:|---:|
| `bm25` | **adversarial_hard** | 40 | **0.025** | 0.006 | 0.000 |
| `keyword` | **adversarial_hard** | 40 | **0.025** | 0.006 | 0.000 |
| `hybrid` | **adversarial_hard** | 40 | **0.050** | 0.050 | 0.000 |
| `graph` | **multi_hop** | 30 | **0.033** | 0.033 | 0.000 |
| `bm25` | contradiction | 40 | 0.050 | 0.030 | 0.000 |
| `keyword` | contradiction | 40 | 0.125 | 0.108 | 0.000 |
| `vector` | adversarial_hard | 40 | 0.750 | 0.583 | 0.000 |
| `hybrid-rerank-off` | adversarial_hard | 40 | 0.625 | 0.515 | 0.000 |
| all modes | unanswerable | 20 | 0.000 | 0.000 | 0.000 |

Six things must be said, in this order, every time:

1. **Sparse retrieval collapses on hard adversarial queries: `bm25` 0.025, `keyword` 0.025 at n=40.** Weakest measured row in the product; mode-specific, not universal.
2. **Dense retrieval is materially better on the same class: `vector` 0.750, `hybrid-rerank-off` 0.625.** Do not average the modes into one "adversarial score" — the split *is* the finding. Quoting 0.750 as the product score misrepresents it as badly as quoting 0.025 as a product-wide failure.
3. **`graph` scores 0.033 on multi-hop at n=30** — the weakest multi-hop mode, and it is *measured*. Do not present graph traversal as a strength.
4. **Unanswerable 0.000 is correct behaviour** — the system abstains. Listed only so nobody later mistakes it for a defect.
5. **It does not contradict the leak rate.** Leak 0.000 means no simulated record surfaced in a grounded result; hit rate asks whether the right grounded record came back. A system can score 0.000 on both by abstaining. **Abstaining is the safe failure and still a failure.** Never present 0.000 leak as cancelling a weak hit rate.
6. **The row is a column, not a footnote** — §0.5.

**What this bounds.** mem20 sells auditable separation, not retrieval leadership. Any asset claiming retrieval superiority is contradicted by this table and must not ship.

**Sales-room line:** *"On hard adversarial queries our sparse path scores 0.025 and our dense path 0.750. Graph traversal scores 0.033 on multi-hop. We publish every row, including the ones that make us look bad. What we sell is provable separation, not the best retrieval score."*

### 0.5 The `Adversarial` column — controlled vocabulary

Every claim table (§1, §3, §4, §6, §9) carries an **Adversarial** column answering: does the measured adversarial result bound this claim, and how?

| Value | Meaning | Obligation |
|---|---|---|
| **`0.000`** | Claim touches retrieval quality; bounded by the weakest measured row. | Reproduce §0 in the same asset. A bare `0.000` without §0 is a defect. |
| **`unmeasured`** | A retrieval mode with no row in the shipped file. **No scored mode is unmeasured at this HEAD**; `recall`, `recall_at`, `entities`, `ledger` are declared but not scoreable (§5.3). | Never present an unscored mode as a pass; name it and give its blocker. |
| **`n/a: <reason>`** | Not a retrieval claim; the rows do not bound it. Reason mandatory. | Still carry §0 if the same asset quotes any retrieval number. |

Three rules, all machine-checked: **(1)** no cell blank, `—` or `TBD` — a blank cell fails `check_ledger.py`; **(2)** a `0.000` cell is a citation, not a label — it obliges §0 in the destination asset; **(3)** `n/a` is never a claim of strength — it says the rows do not *speak to* this claim, not that the claim is unaffected by retrieval weakness.
