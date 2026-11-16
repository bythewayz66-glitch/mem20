# mem20 — Sales Motion for the 487-Tool / 129-Domain Surface (v8, 2026-11-16)

**Seat:** VP of Sales
**Artifact type:** sales motion — ICP, discovery, technical demo, pilot-to-paid, pricing/packaging, forecast
**Repo:** https://github.com/bythewayz66-glitch/mem20 · **Branch read:** `main`
**HEAD at capture:** `0224a64946a2c00313a9872515893157adcbc47e` (2026-11-16 06:55:07 +0000)
**Version:** **4.0.0** · **License:** **Apache-2.0** · **Surface:** **487 tools across 129 domains** · **Transport:** MCP JSON-RPC 2.0 over stdio
**Numbers:** house numbers per `docs/gtm/claim-ledger-v8-2026-11-16.md` §6 — carried, not re-derived
**Supersedes:** `docs/gtm/mem20-sales-one-pager.md` (v3), which states 270/27 and MIT. Both are wrong at this HEAD.

---

## 1. The 30-second pitch

> Every agent-memory vendor sells you relevance. mem20 sells you **proof**.
>
> Grounded facts and simulated hypotheses live in **separate stores** — not one store with a flag. Try to write invented content through the grounded path and the server raises `PermissionError`. Try to write a fact without declaring how it was learned and it raises `ValueError`. Every entry carries its origin and store in an append-only ledger, and `audit_contamination()` reports a contamination rate plus six violation classes for your store.
>
> **Apache-2.0**, Python 3.10+, self-hosted, **487 tools across 129 domains**, over MCP. You can read the code that holds your audit trail, because you cannot audit a black box.

**Email subject line:** `The memory layer you can prove — grounded vs simulated, enforced in code.`

**The one line that must survive every edit:** *"Grounded vs simulated is a hard, audited boundary, not a prompt convention."*

---

## 2. ICP — who we sell to, and who we walk away from

| Tier | Segment | Trigger event | Where they live | Entry ACV |
|---|---|---|---|---|
| **A** | **Regulated AI teams** — fintech, healthcare, legal, gov | A model-risk or audit function asked *"where did the agent learn this?"* and the answer was *"the vector store"* | LinkedIn, industry conferences, direct outbound | Business $18,000 |
| **B** | **AI platform / infra engineers** building production agents | Their agent confabulated in staging and polluted the memory store | GitHub, HN, LangChain & MCP Discord, r/LocalLLaMA | Team $6,000 → Business |
| **C** | **Self-host-first / OSS teams** and MCP-ecosystem builders | Cannot send memory to a vendor cloud | MCP directories, GitHub | Team $6,000 |

**Qualification — the four questions that decide the deal in the first call:**

1. *"Does anyone outside your team ever ask you to prove where the agent learned something?"* — **No → Tier B/C at best.** Yes → Tier A, and the whole motion applies.
2. *"Can you run a Python service, or do you need a managed endpoint?"* — **Managed → disqualify.** There is no hosted offering and no PyPI package; install is source-only. Say so in the first call, not the third.
3. *"Do you need a benchmark comparable to Mem0 or Zep?"* — **Yes → disqualify.** We do not have one and will not claim one.
4. *"What happens today when the agent invents something and stores it?"* — **"Nothing, it just sits there" → this is the deal.** That is the pain mem20 removes.

**Not a fit — say so early and save both sides the cycle:**
- Teams that only need retrieval relevance and have no audit obligation. Mem0 or a plain vector DB is cheaper.
- Teams that want a **managed SaaS with no operational surface**. If they cannot run a Python service, the install is a blocker, not a feature.
- Teams needing a **published benchmark comparable to Mem0 or Zep**.

---

## 3. The three objections and the honest answers

| Objection | Answer |
|---|---|
| *"Where are your LoCoMo / LongMemEval numbers?"* | **We don't have them.** What ships is a seven-mode benchmark on our own 250-query corpus: direct 1.000 (`bm25`), multi-hop 0.800 (`bm25`) / 1.000 (`vector`), and on hard adversarial queries **sparse 0.025, dense 0.750**. The weak rows are in the table, not buried. Any figure set against Mem0's 92.5 or Zep's 94.8% is a category error — different corpora, different metrics, vendor self-reported. **Lead with this; it is why they trust the rest.** |
| *"How do I install it? Pip?"* | **Source only.** `git clone` + `pip install -r requirements.txt`. There is **no PyPI package** — `mem20`, `mem20-ai` and `mem20oreo` all 404. One caveat worth stating up front: the install pins `mcp>=2.1.1`; installing `mcp<2` produces a misleading "mcp package not installed" error. |
| *"Is the promotion gate airtight?"* | **No — narrowed, not closed.** Bare calls are refused; the prediction-error path demands structured evidence tied to a *recorded* prior prediction. But a free-text `confirmation` argument still promotes. We publish the six-path test result rather than describing the gate as airtight. Say this before they find it. |

**Never say:** tamper-proof, unfakeable, provably secure, matches Mem0, beats Zep, industry-leading retrieval, MIT. One of those in a deal and the whole trust position collapses.

---

## 4. The technical demo — 12 minutes, four commands, no slides

The demo is the product. Run it live against a throwaway store. Every step below is reproducible from a clean clone at `0224a64`.

| # | Step | Command | What the buyer sees |
|---|---|---|---|
| 1 | **The partition holds** | `python3 docs/gtm/verify/partition.py` | A grounded write succeeds; a simulated write through the grounded path is **refused** with `PermissionError`; `recall()` returns grounded only; `recall(include_simulated=True)` returns both |
| 2 | **The audit is real** | same run → A6 | `contamination_rate=0.0 status=CLEAN violation_classes=6`, all six empty |
| 3 | **The gate is honest** | same run → PG1–PG6 | Bare promotion refused; unrecorded prediction ref refused; **free-text confirmation still promotes** — we show the hole |
| 4 | **The benchmark is honest** | `python3 docs/gtm/verify/bench_rows.py` | Seven modes, including `bm25` 0.025 on hard adversarial and `graph` 0.033 on multi-hop |

**The line to deliver at step 3:** *"That's the hole in our own gate. We publish it. Now ask yourself which of your vendors publishes theirs."*

**The line to deliver at step 4:** *"We publish every row, including the ones that make us look bad. What we sell is provable separation, not the best retrieval score."*

**What the demo must NOT do:** quote a LoCoMo number, present `graph` as a strength, average the adversarial modes into one score, or claim the gate is airtight.

---

## 5. Pricing and packaging

**House numbers — carried from the owner directive, not re-derived** (`docs/finance/inputs.json` → `house_numbers.provenance`).

| Tier | ACV | Share of book | Gross margin | CAC payback | Role in the motion |
|---|---:|---:|---:|---:|---|
| **Team** | $6,000 | 72% | **28.7%** | **9.77 yr** | **Land.** Entry point only. |
| **Business** | $18,000 | 12% | 76.2% | 1.22 yr | **Expand.** The real business. |
| **Scale** | $36,000 | 12% | 88.1% | 0.53 yr | **Expand.** |
| **Enterprise** | $80,000 | 4% | 94.7% | 0.22 yr | **Expand.** |
| **Blended** | **$14,000** | 100% | 69.4% | 1.73 yr | — |

**The Team tier is the problem in this table, and the motion is built around it.** At 28.7% gross margin and a 9.77-year CAC payback, a Team deal does not pay for itself. It is a **land** motion whose only justification is conversion upward. Two consequences the rep must internalise:

1. **Never sell Team as the destination.** Sell it as a 90-day proof, with the Business conversation scheduled at signature.
2. **A Team deal with no expansion path is a loss, not a small win.** If qualification question 1 answers "no", the deal is Tier C and should be routed to self-serve, not to a rep's quota.

**Packaging rules:**
- **No per-seat pricing.** mem20 is a substrate, not a seat-based tool. Price on the store and the audit surface, not headcount.
- **No usage metering on recall.** Metering retrieval calls punishes exactly the behaviour the product is for.
- **The audit surface is the paid surface.** The partition and the ledger are the value; the 487-tool surface is the delivery vehicle.

**Never say:** a TAM/SAM/SOM figure other than TAM **$1.28B** / SAM **$282M** / SOM **$1.68M** / 120 accounts; a blended ACV other than **$14,000**; "we re-derived TAM".

---

## 6. The 6-week pilot-to-paid motion

| Week | Stage | Owner | Exit criterion |
|---|---|---|---|
| **0** | **Qualify** | AE | The four questions in §2 answered; Tier A or B confirmed; a named audit stakeholder identified |
| **1** | **Install + first grounded recall** | AE + buyer's engineer | `git clone` → `pip install -r requirements.txt` → a grounded write and a grounded `recall()` succeed in *their* environment |
| **2** | **The partition test on their data** | Buyer's engineer | `partition.py` run against a store seeded with *their* content; the simulated write is refused; `audit_contamination()` returns `CLEAN` |
| **3** | **The audit walkthrough** | AE + audit stakeholder | The six violation classes explained against their compliance framework; the append-only ledger demonstrated |
| **4** | **The honest-limits session** | AE | §3's three objections delivered *unprompted*; the PG4 hole shown; the benchmark's weak rows shown |
| **5** | **Expansion case** | AE + buyer's platform lead | A written Business-tier proposal tied to the audit obligation, not to tool count |
| **6** | **Close or disqualify** | AE | Signed Business/Scale, or a documented disqualification with the reason |

**Why week 4 exists.** The honest-limits session is the close. A buyer who has been shown the PG4 hole and the 0.025 adversarial row, and still wants the product, has bought the *position* — and that buyer does not churn on a benchmark comparison six months later. Skipping week 4 wins the pilot and loses the renewal.

**Pilot pricing:** the pilot is **free for 6 weeks**, capped at one store and one environment. It is not a discount — it is the qualification instrument. A pilot that has not produced a named audit stakeholder by week 3 is disqualified, not extended.

---

## 7. Forecast — the shape of the number

**Assumptions (all ESTIMATE, stated so they can be challenged):**

| Assumption | Value | Basis |
|---|---|---|
| SOM account count | **120** | house number, `docs/finance/inputs.json` |
| Blended ACV | **$14,000** | house number |
| SOM ARR | **$1.68M** | 120 × $14,000 = $1,680,000 (identity gate PASS, `docs/pricing/tier-price-derivation.csv`) |
| Tier mix | Team 72% / Business 12% / Scale 12% / Enterprise 4% | house tier ladder |
| Pilot → paid conversion | **ESTIMATE 25%** | no measured funnel exists yet; this is the number to instrument first |
| Sales cycle | **ESTIMATE 6 weeks** | the pilot length in §6 |

**The forecast pack is deliberately thin, and that is the finding.** There is no measured funnel — no pilot-to-paid conversion rate, no stage-duration data, no win/loss record. The first job of the Data & Revenue Analytics Lead is to instrument §6's six weeks so the 25% and 6-week figures stop being estimates. **Do not present a forecast built on these two estimates as if it were measured.**

**What can be stated as fact:** SOM ARR **$1.68M** at 120 accounts × $14,000 blended ACV, and the tier mix above. Everything downstream of conversion is an estimate.

---

## 8. Guardrails for the sales room

| # | Rule |
|---|---|
| S1 | The surface is **487 tools across 129 domains**. Never 270, 27, 268, 26, 258, 257, 311 or 39 as current. |
| S2 | The license is **Apache-2.0**. Never "MIT" for the root repo. |
| S3 | The version is **4.0.0**. |
| S4 | **No LoCoMo / LongMemEval figure**, ever. |
| S5 | The **adversarial weak rows stay visible** in any asset that quotes a retrieval number. |
| S6 | The promotion gate is **"narrowed, not closed"**. Never "airtight", "tamper-proof", "unfakeable", "provably secure". |
| S7 | Install is **source-only**. Never any `pip install mem20` form. |
| S8 | Never publish or link a `/sites/` or `/files/` URL as a destination. |
| S9 | House numbers are **carried, not re-derived**. Say so. |
| S10 | The **19 unwired tools** are named as unwired whenever the 487 count is broken down. |

---

## 9. Hand-off

**Next seat: Head of Marketing & Demand Generation.** Input: this motion's §2 (ICP and the four qualification questions) and §3 (the three objections) — the launch copy must be re-cut so that the inbound lead arrives already knowing the honest limits, which is what makes the week-4 session a close rather than a surprise.

**Then: Data & Revenue Analytics Lead**, to instrument §6's six weeks and replace the two ESTIMATE figures in §7 with measured ones.

**Verification:** `python3 docs/gtm/verify/check_gtm_v8.py` — exit 0 = PASS.
