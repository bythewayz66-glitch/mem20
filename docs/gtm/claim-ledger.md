# mem20 — GTM Claim Verification Ledger (v5)

**Owner:** mem20 GTM Team Lead · **Seat:** Brand & Positioning Strategist / Opportunity & Market Analyst
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **Branch read:** `main`
**HEAD at capture:** `e7758bd178d38da63c5359dded0aada8bfc0eea5` (2026-10-27 09:19:42 -0600)
**Captured:** 2026-10-27 15:00–15:22 UTC · **Method:** every claim traced to a file, a command, or a captured run against a full clone of the canonical remote at this HEAD.
**Surface of record:** **270 tools / 27 domains.** The values 257, 258 and 268 are **RETIRED** and survive only in §7.
**Supersedes:** claim ledger v4 (HEAD `1264076698a00878acc3adacf7bf1d51eea315cc`, captured 2026-10-27 08:49–08:56 UTC).

> **Why v5 exists.** v4 disclosed the weakest measured row honestly, but it disclosed it as a **section** — a thing a writer could quote past. v5 makes the disclosure **structural**: every claim table in this document carries an **Adversarial** column, and no cell in it may be blank. A row cannot be lifted into a sales asset without the caveat travelling with it, because the caveat is now part of the row. v5 also re-measures at `e7758bd1`, which moved after v4 was written, and corrects four things that changed.

### What changed since v4

| # | Change | Detail |
|---|---|---|
| C1 | **Adversarial caveat is now a required column** | §1, §4 and §6 each gain an `Adversarial` column with a controlled 3-value vocabulary (§0.5). Blank or `—` is a defect. |
| C2 | **Benchmark rows are unchanged** | `benchmarks/results/latest.md` is byte-identical in substance to v4's reading; all nine rows re-verified verbatim at this HEAD. |
| C3 | **`mem20.com` identity is now PROVEN** | v4 recorded a byte-count match only (md5 capture kept failing, curl exit 56). This run both hosts returned **md5 `f82e7f31acf861810b5ea0bb40ea197e`**, identical to `docs/index.html`. |
| C4 | **`CHANGELOG.md` is no longer drift — v4 was wrong about it** | v4 §1 reported `CHANGELOG.md` §3.0.0 "states 268/26 as its reconciliation target" as live drift. At this HEAD `CHANGELOG.md` `[Unreleased]` **correctly** states 270/27 and explicitly names 257/26 as the wrong prior. The 268/26 strings are historical §3.0.0 entries below the Unreleased block. **The drift is in `docs/02-tools-reference.md` and `docs/05-complete-tools-reference.md` only.** |
| C5 | **`aiohttp` fix is in flight, not landed** | Still absent from `requirements.txt` on `main` (verified: `grep -c aiohttp` → **0**). It is declared in **PR #118** (`fix/ws2-suite-collection-unblock`, head `a47e7d70d87dcbd42a10aa56fe72fc64d17d1049`), open and unmerged at capture. |
| C6 | **Repo grew to 7,991 tracked files** | The investor/board deck (`docs/app/deck/`, 16 files) merged as `e7758bd1`. |

---

## 0. The weakest measured row — read this before the strengths

This is the first thing in the document because it is the first thing a hostile reviewer will find. It is stated in full, in the same units the benchmark file uses, with no softening.

**mem20 retrieves nothing on adversarial-class queries.** On the shipped corpus:

| Mode | Query class | n | Hit rate | MRR | Leak rate |
|---|---|---:|---:|---:|---:|
| `hybrid` | **adversarial** | 3 | **0.000** | 0.000 | 0.000 |
| `keyword` | **adversarial** | 3 | **0.000** | 0.000 | 0.000 |
| `semantic` | **adversarial** | 3 | **0.000** | 0.000 | 0.000 |
| `graph` | adversarial | — | **not measured** | — | — |

Five things must be said about that block, in this order, every time it is presented:

1. **Three of the four scored modes score 0.000 on adversarial queries.** `hybrid` — the default retrieval path — scores 0.000. Keyword 0.000. Semantic 0.000.
2. **`graph` has no adversarial row at all.** It is scored on `multi_hop` only (n=2). Its adversarial behaviour is **unmeasured — that is not a zero and not a pass.** Do not let it be counted as a strength by omission.
3. **n = 3.** This is a 3-query slice on a 14-fact / 13-query corpus, not a benchmark. The confidence interval on 0/3 is enormous. It is a real signal that the adversarial class is unsolved, and it is not a precise estimate of the failure rate.
4. **It does not contradict the leak rate.** Leak rate 0.000 across all four modes means *no simulated record surfaced in a grounded result*. Hit rate 0.000 on adversarial means *the correct grounded record was not returned*. A system can score 0.000 on both at once: it abstains. **Abstaining on an adversarial query is the safe failure, and it is still a failure.** Say it that way — never present 0.000 leak as if it cancels 0.000 hit.
5. **The row is carried as a column, not as a footnote.** See §0.5.

**What this bounds.** mem20's claim is auditable separation, not retrieval leadership. The adversarial row is the price of that claim stated openly: the partition holds, and the retrieval layer has not learned to resolve deliberately deceptive queries. Any sales asset that claims retrieval superiority is contradicted by this table and must not ship.

**The one-line version for a sales room:** *"On adversarial queries our hit rate is zero — three of three modes. We publish that row instead of hiding it. What we sell is provable separation, not the best retrieval score."*

### 0.5 The `Adversarial` column — controlled vocabulary

Every claim table in this ledger (§1, §4, §6) carries an **Adversarial** column. It is not decorative. It answers one question per row: **does the 0.000 adversarial result bound this claim, and how?**

| Value | Meaning | What the writer must do |
|---|---|---|
| **`0.000`** | The claim touches retrieval quality and is bounded by the adversarial row. | Reproduce the §0 block in the same asset. A bare `0.000` cell without §0 is a defect. |
| **`unmeasured`** | `graph` has no adversarial row. | Never present it as a pass. Name it as unmeasured whenever `graph` appears. |
| **`n/a: <reason>`** | Not a retrieval claim; the adversarial row does not bound it. The reason is mandatory. | Still carry §0 if the *same asset* quotes any retrieval number elsewhere. |

**Three rules bind this column, and they are machine-checkable:**

1. **No cell may be blank, `—`, or `TBD`.** An absent value is how a caveat gets lost in transcription. A blank cell fails review.
2. **A `0.000` cell is a citation, not a label.** It obliges the §0 block to appear in the destination asset, not merely this ledger.
3. **`n/a` is never a claim of strength.** It says the adversarial row does not *speak to* this row — it does not say this row is unaffected by retrieval weakness. A pricing claim is `n/a: not a retrieval claim`; that does not make the product good at retrieval.

---

## 1. Verified product facts

| # | Claim | Verified value | Evidence (captured 2026-10-27) | Adversarial |
|---|-------|---------------|--------------------------------|-------------|
| V1 | Canonical repo | `github.com/bythewayz66-glitch/mem20` | GitHub API: `private=false`, `default_branch=main`, `license.spdx_id=MIT`, `pushed_at=2026-10-27T15:19:42Z`, `stargazers_count=1`, `forks_count=0`, `open_issues_count=16` | `n/a: repo identity` |
| V2 | HEAD commit | `e7758bd178d38da63c5359dded0aada8bfc0eea5` | `git log -1` — *"Merge content/ws3-investor-deck into main (2026-10-27 convergence)"* | `n/a: commit identity` |
| V3 | Tracked files | **7,991** | `git ls-tree -r --name-only origin/main \| wc -l`. Was 7,975 at `45445f48`; the 16-file deck merge accounts for the whole delta. | `n/a: repo size` |
| V4 | Version | **3.0.0** | `pyproject.toml` `version = "3.0.0"`; `VERSION` file equals `3.0.0` | `n/a: version string` |
| V5 | License | **MIT** | `LICENSE` line 1 = `MIT License`; GitHub API `license.spdx_id = "MIT"` | `n/a: licensing` |
| V6 | Python floor | **>=3.10** | `pyproject.toml` `requires-python = ">=3.10"` | `n/a: runtime requirement` |
| **V7** | **MCP tool surface** | **270 tools** | **Live handshake.** `python3 verify_mcp.py` → `TOOL_COUNT: 270`, `RESULT: PASS`, `protocolVersion 2025-06-18`. Independently: `grep -rhoE 'self\.tools\[' mcp/ --include="*.py" \| wc -l` = **272** raw literal hits, **270** unique quoted names. Third source: `docs/finance/inputs.json` → `tool_surface.tools = 270`. | `n/a: counts tools, not retrieval quality` |
| **V8** | **Tool domains** | **27** | `sed -n '/def _setup_tools/,/^    def /p' mcp/server.py \| grep -cE 'self\.register_[a-z_]+_tools\(\)'` = **27**. Confirmed against `docs/finance/inputs.json` → `tool_surface.domains = 27`. | `n/a: counts domains, not retrieval quality` |
| V9 | Transport | JSON-RPC 2.0 over **stdio** (default); Streamable HTTP via `MEM20_TRANSPORT=http` on `MEM20_MCP_PORT` (8082) | `verify_mcp.py` handshake over stdio | `n/a: transport mechanism` |
| V10 | Health surface | `/health`, `/ready`, `/metrics` | `mcp/health.py`; a bind conflict on :8080 degrades to a warning, not a failure — observed again this run: `WARNING mem20.mcp health endpoint disabled (could not bind :8080): [Errno 98] Address already in use`, and the run still returned `RESULT: PASS` | `n/a: operational surface` |
| V11 | Embedder | `sentence-transformers/all-MiniLM-L6-v2`, 384-dim | `memory_engine/memory.py`; `benchmarks/results/latest.md` environment block | `0.000` — this is the embedder behind the 0.000 hybrid/semantic rows |
| V12 | Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2`, on by default, `MEM20_RERANK=0` opt-out | `memory_engine/memory.py`; benchmark file's "Reranking cost" section | `0.000` — reranking does not rescue the adversarial class (§5) |
| V13 | Hybrid retrieval | vector (`IndexFlatIP`) + BM25 (`BM25Okapi`), RRF fusion | `memory_engine/memory.py` `recall_hybrid()` | `0.000` — the default path scores 0.000 on adversarial |
| V14 | `epistemic_status` is **required** on write | Captured refusal this run: `ValueError: remember() requires an explicit epistemic_status. Declare how this claim was learned; one of ['observed', 'inferred', 'imagined', 'user_stated', 'hypothesis', 'agent_generated', 'unlabeled']` | `inspect.signature(M.remember)` returns `epistemic_status: 'str \| None' = None` — optional in *signature*, mandatory in *behaviour*. Do not describe it as a required parameter; describe it as a required value. | `n/a: write-path guard` |
| V15 | Issues enabled / Discussions disabled | `has_issues=true`, `has_discussions=false`, `has_wiki=true`, `has_projects=true`, `has_pages=true` | GitHub API, this run | `n/a: repo configuration` |
| V16 | Repository description | *"Memory substrate and agent runtime for AI systems that have to be trusted — grounded facts and simulated hypotheses never mix, and every retrieval call reports index drift instead of hiding it."* | GitHub API `description` — the owner's own framing, safe to quote as positioning | `0.000` — it makes an implicit retrieval claim ("never mix" is fine; the drift-reporting clause is not a quality claim, but the asset must still carry §0) |

### Note on the 270 / 27 figure

At this HEAD the live handshake is the authority and it says **270**, with **27** registered mixins agreeing and a third source (`docs/finance/inputs.json`) recording the same pair plus `previous_tools: 257`, `previous_domains: 26` as a stated prior. Three independent measures agree — that agreement is the defence, not any single number.

**How to answer a challenge:** run the command, not a different number. `python3 verify_mcp.py` → `TOOL_COUNT: 270`. The verifier needs `mcp>=2.1.1`, `aiohttp`, `anyio`, `pydantic`, `numpy` and `pip install -e ./mem20api`; with those present it passes from a full clone at this HEAD.

**Residual documentation drift, measured this run — CORRECTED from v4.** v4 reported `CHANGELOG.md` as carrying stale counts. At this HEAD it does **not**: `CHANGELOG.md` `[Unreleased]` states *"Tool counts reconciled to the live surface: 270 tools across 27 domains"* and explicitly records that *"The docs carried 257 / 26, which was wrong in two ways."* The remaining drift is two files:

| File | What it still prints | Status |
|---|---|---|
| `docs/02-tools-reference.md:3-4` | "**268 tools across 26 domains** (verified by instantiating `Mem20MCPServer`…)" | **Live drift — P1 documentation defect.** Contradicts its own stated method: instantiating the server returns 270. |
| `docs/05-complete-tools-reference.md` | 268 in the header (`:3`), a totals row (`:4679` → `\| **TOTAL** \| **268** \| 26 domains \|`), and four issue-body quotes | **Live drift — same P1 item.** |

Correct at this HEAD: `README.md`, `docs/README.md`, `docs/index.html`, and the merged investor deck all state **270 / 27**. `toolchest/inventory.json` still carries `counts.mcp = 258` but its `generated_at` is `2026-10-07T11:13:27Z` — stale generator output, not a live claim (see §7/R3).

**This is a documentation defect, not a product ambiguity** — quote the verifier, and name the drift rather than matching it.

---

## 2. The surface of record

| Field | Value | Status |
|---|---|---|
| Tools | **270** | Current — live handshake |
| Domains | **27** | Current — mixin count |
| Retired tool values | 257 · 258 · 268 | **RETIRED** — historical only, see §7 |
| Retired domain value | 26 | **RETIRED** — historical only, see §7 |

**Binding rule:** any sentence in any asset in this directory that names the tool surface names it as **"270 tools across 27 domains."** No exceptions, no abbreviations, no "~270", no "over 250". If a number is challenged, the answer is §1/V7's command.

---

## 3. Distribution state (re-measured at `e7758bd1`; two items changed since v4)

| # | Question | Measured result | Consequence for GTM | Adversarial |
|---|---|---|---|---|
| **D1** | Is there a PyPI package? | **No.** `pypi.org/pypi/mem20/json` → **404**; `mem20-ai/json` → **404**; `mem20oreo/json` → **404** (all three, this run) | **Never print `pip install mem20`, `pip install mem20-ai`, or a PyPI badge.** Install is source-only. | `n/a: packaging` |
| **D2** | What is the documented install path? | `git clone https://github.com/bythewayz66-glitch/mem20.git` → `pip install -r requirements.txt`. `requirements.txt` on `main` pins exactly six: `mcp>=2.1.1`, `pydantic>=2.13.4`, `anyio>=4.14.2`, `numpy>=1.24`, `faiss-cpu>=1.7.4`, `sentence-transformers>=2.2.0`. | State the two-command source install, and see D2b. | `n/a: install path` |
| **D2b** | **Is that install path complete?** | **No — verified defect, still open on `main`.** `grep -c aiohttp requirements.txt` → **0**. `mcp/tools/a2a_tools.py:19` is a module-scope `import aiohttp`, and `mcp/server.py` imports that module unconditionally. **The fix exists but is not merged:** PR **#118** (`fix/ws2-suite-collection-unblock`, head `a47e7d70d87dcbd42a10aa56fe72fc64d17d1049`) declares `aiohttp>=3.9` and `mcp-types>=2.3.0`. | **Until #118 merges, no asset may print an install line that claims to work end to end.** Add `pip install aiohttp` explicitly, or wait for the merge. Static evidence only — the boot failure itself was not captured this run because `aiohttp` was installed before the handshake. | `n/a: install path` |
| **D3** | Are `/sites/` CDN URLs publicly reachable? | **No — 403 to anonymous requests.** Verified token-free this run on the repo's own `homepage` target: `HTTPError 403: Forbidden`. A token-carrying `curl` in our shell returns 200 and **lies**. | **Never publish, promote, or link a `/sites/` URL in a public asset.** | `n/a: hosting` |
| **D4** | What is the canonical public URL? | **`https://bythewayz66-glitch.github.io/mem20/`** → **HTTP 200, 36,627 bytes, md5 `f82e7f31acf861810b5ea0bb40ea197e` = byte-identical to `docs/index.html` at this HEAD.** **`https://mem20.com`** → **HTTP 200, 36,627 bytes, md5 `f82e7f31acf861810b5ea0bb40ea197e` — IDENTICAL, identity now proven** (v4 could only establish a byte-count match). | Cite either; both are md5-proven to be the committed `docs/index.html`. Prefer `mem20.com` in customer-facing copy, `github.io` where a `github.com` link is expected. | `n/a: hosting` |
| **D5** | Does the CNAME host resolve? | **Yes.** `docs/CNAME` contains **`mem20.com`**. `getent hosts mem20.com` → four GitHub Pages A-records (`185.199.108–111.153`); `https://mem20.com` → **200**, md5-identical per D4. | **v3's "no DNS record" finding is RETIRED.** Do not cite `mem20.jaysonai.online` at all. | `n/a: DNS` |
| **D6** | Any stale public pointer? | **Yes, unchanged since v4.** The repo **`homepage` field** is `https://static.teamily.ai/sites/ca954f26-cfef-49bf-92b4-55c652e71f8f/webpages/mem20-site/index.html` — verified **403** to anonymous requests. | **Owner action, not GTM:** repoint `homepage` to `https://mem20.com`. Every visitor who clicks it from the repo hits a 403 — the worst first impression for a trust-positioned product. | `n/a: link hygiene` |

---

## 4. Live partition + audit evidence (captured 2026-10-27 at `e7758bd1`)

Harness run against a full clone, throwaway store (`MEM20_STORE_PATH=/tmp/mem20-gtm-<ts>`), engine imported from the repo root (`sys.path.insert(0, ".")`).

| # | Check | Captured result | Verdict | Adversarial |
|---|-------|----------------|---------|-------------|
| A1 | Grounded write | accepted; `origin=grounded`, `store=grounded`, `action=remember` | ✅ verified | `n/a: write path` |
| **A2** | `remember(..., _allow_simulated=True)` | `PermissionError: remember() is grounded-only. Simulated content must use remember_simulated(); this call is refused to protect Step 7.4 separation.` | ✅ verified — **quote verbatim; strongest asset in the repo** | `n/a: write path` |
| A3 | `remember_simulated(...)` | accepted; `origin=simulated`, `store=simulated`, `epistemic_status=imagined` | ✅ verified | `n/a: write path` |
| A4 | `recall()` default | returned `list[dict]`, n=1; origins `['grounded']` only; stores `['grounded']` | ✅ verified | `0.000` — this is the path that scores 0.000 on adversarial |
| A5 | `recall(include_simulated=True)` | returned `list[dict]`, n=2; origins `['grounded', 'simulated']`; stores `['grounded', 'simulated']` | ✅ verified | `0.000` — same |
| **A6** | `audit_contamination(actor=…)` | `contamination_rate: 0.0`, `status: "CLEAN"`; **6** violation classes, **all empty**: `violations_origin_not_grounded`, `violations_pinned_origin_not_grounded`, `violations_pinned_simulated_content`, `violations_simulated_in_bm25_corpus`, `violations_simulated_in_graph`, `violations_simulated_in_grounded_index` | ✅ verified — **6 classes, not 3.** Read the audit's own keys and count them; never assert a count from memory. | `n/a: separation audit` |
| A7 | `epistemic_status` omitted | `ValueError` refusing an unlabeled write (V14) | ✅ verified hardening | `n/a: write guard` |
| A8 | Audit after promotion attempts | still `contamination_rate: 0.0`, `status: "CLEAN"` | ✅ verified — the gate does not corrupt the store, even when it admits content | `n/a: separation audit` |

### Promotion gate — six paths, all re-captured this run at `e7758bd1`

The gate is **narrowed, not closed.** Report these as six distinct behaviours, never as one claim.

| # | Path | Captured behaviour | Adversarial |
|---|---|---|---|
| PG1 | Bare call, `sim_id` only | **REFUSED** — *"Promotion blocked: requires explicit external confirmation OR real-world prediction-error resolution (resolution_note + attestation)."* | `n/a: promotion gate` |
| PG2 | `resolved_via_prediction_error=True` + free-text note | **REFUSED** — *"Promotion via prediction-error resolution requires structured evidence linking to a recorded prior prediction (keys ('prediction_ref', 'observed_outcome'))."* | `n/a: promotion gate` |
| PG3 | Structured `prediction_error_evidence` naming an unrecorded `prediction_ref` | **REFUSED** — *"Promotion blocked: prediction_ref pred-does-not-exist is not a recorded prior prediction. The prediction-error gate requires a real, previously recorded prediction that resolved in favor (or a registered PREDICTION_ERROR_VERIFIER for external signed attestation)."* **Pass `resolved_via_prediction_error=True` too** — without it the call returns the earlier PG1 message instead of this one. | `n/a: promotion gate` |
| **PG4** | **Free-text `confirmation` alone** | **PROMOTES.** Returned `{"promoted": true, "epistemic_status": "hypothesis", "evidence_hash": null, "grounded_id": "…"}`. **This is the residual open path.** | `n/a: promotion gate` |
| PG5 | Whitespace-only `confirmation` | **REFUSED** — falls through to the PG1 message. Confirmation is length-checked, not evidence-checked. | `n/a: promotion gate` |
| PG6 | `resolution_note` alone, no evidence | **REFUSED** — PG1 message. | `n/a: promotion gate` |

**Why PG4 matters and how to describe it.** A promotion can be obtained by typing a sentence. The resulting grounded record is tagged `epistemic_status: hypothesis` and carries `evidence_hash: null` — so the promotion is **recorded as unevidenced** in the ledger, which is the real control: the audit trail preserves the fact that no evidence was attached. That is the honest framing, and it is a good one: **"evidence-based with an append-only audit trail that records when evidence was absent."** It is not a claim that the gate cannot be passed by typing.

**Never** describe the gate as airtight, tamper-proof, unfakeable, provably secure, or as refusing self-attestation. A reader who runs PG4 in thirty seconds will find the free-text path, and this product's entire positioning is that its numbers hold up under scrutiny.

---

## 5. The benchmark table — adversarial rows first, then the rest

Source: `benchmarks/results/latest.md` at this HEAD. Corpus `mem20-agent-kb-v1`: **14 grounded facts, 3 simulated facts, 13 queries.** Reproduce: `mem20benchmarkz run --out benchmarks/results`.

| Mode | Query class | n | Hit rate | MRR | Leak rate | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| `hybrid` | adversarial | 3 | 0.000 | 0.000 | 0.000 | 102.0 |
| `keyword` | adversarial | 3 | 0.000 | 0.000 | 0.000 | 110.7 |
| `semantic` | adversarial | 3 | 0.000 | 0.000 | 0.000 | 12.3 |
| `hybrid` | multi_hop | 5 | 0.800 | 0.640 | 0.000 | 105.1 |
| `keyword` | multi_hop | 5 | 0.800 | 0.640 | 0.000 | 104.4 |
| `semantic` | multi_hop | 5 | 0.800 | 0.800 | 0.000 | 11.6 |
| `graph` | multi_hop | 2 | 1.000 | 1.000 | 0.000 | 0.6 |
| `hybrid` | direct | 5 | 1.000 | 1.000 | 0.000 | 108.0 |
| `keyword` | direct | 5 | 1.000 | 1.000 | 0.000 | 103.3 |
| `semantic` | direct | 5 | 1.000 | 0.900 | 0.000 | 12.2 |

Aggregate latency: `hybrid` p50 103.5 / p95 115.6 ms (n=13); `keyword` p50 105.0 / p95 126.3 ms; `semantic` p50 12.2 / p95 15.1 ms; `graph` p50 0.5 ms (n=2).

Trust block: contamination rate **0.0**, simulated records in BM25 corpus **[]**, stale pointer rate **0.000000**, index healthy **True**, ledger records 14, graph 38 entities / 70 edges, 41 queries reporting a diagnostic, all reported healthy **True**.

Reranking cost (the file's own measurement): `MEM20_RERANK=1` → p50 101.4 ms, direct MRR 1.000, multi-hop MRR 0.640. `MEM20_RERANK=0` → p50 15.7 ms, direct MRR 0.900, multi-hop MRR 0.800. **Reranking buys direct-query ranking and costs an order of magnitude in latency** — a genuine engineering trade-off, quotable as such. It buys nothing on adversarial: there is no adversarial row for the rerank-off configuration either.

**Four rules bind this table, all non-negotiable:**

1. **Carry the file's own warning, verbatim:** *"These numbers are not comparable to competitor benchmarks… Nothing here refutes or reproduces them. These results describe this corpus only."*
2. **The three adversarial 0.000 rows stay visible, and `graph`'s missing row stays named as unmeasured** (§0).
3. **Never set this against Mem0's LoCoMo 92.5 / LongMemEval 94.4 or Zep's DMR 94.8%.** Vendor self-reported, different corpora, different metrics.
4. **Never present 0.0 leak rate as a retrieval result.** It is a separation result, measured on this corpus, and §0 rule 4 governs how the two interact.

---

## 6. House numbers (commercial)

| # | Metric | Value | Status / source | Adversarial |
|---|---|---|---|---|
| H1 | TAM | **$1.28B** | House number, carried verbatim in `docs/finance/inputs.json` → `house_numbers.tam_usd: 1280000000`, `provenance: "carried verbatim from the owner directive; NOT re-derived in this file"` | `n/a: commercial sizing` |
| H2 | SAM | **$282M** | `house_numbers.sam_usd: 282000000` | `n/a: commercial sizing` |
| H3 | SOM (ARR) | **$1.68M** | `house_numbers.som_arr_usd: 1680000` | `n/a: commercial sizing` |
| H4 | Blended ACV | **$14,000** | `house_numbers.blended_acv_usd: 14000` | `n/a: pricing` |
| H5 | Accounts to realise SOM | **120** | `house_numbers.som_accounts: 120`, arithmetically consistent: 120 × $14,000 = $1,680,000 exactly | `n/a: arithmetic on house numbers` |

**These are house numbers, not fresh measurements.** `CHANGELOG.md` states the commercial figures are *"deliberately not restated as new measurements."* Every asset quoting them carries the same qualifier.

**Derived ratios (arithmetic on the house numbers — label as estimates, show the division):**
- SOM ÷ ACV = 1,680,000 ÷ 14,000 = **120 accounts** (exact).
- SOM ÷ SAM = **0.60%** of SAM.
- SAM ÷ TAM = **22.03%** of TAM.

Do not present 120 accounts as a forecast. It is the arithmetic consequence of three carried constants. **Note the `n/a` cells above:** a commercial row is not a retrieval claim, so the adversarial row does not bound it — but that is not permission to imply the product retrieves well. If an asset quotes H1–H5 *and* any retrieval number, it carries §0 regardless.

---

## 7. Retired values — the only place these numbers may appear

**This is the sole register of superseded values. Every occurrence of a retired number outside this table is a defect.** In a sales room, quote from §1/§2 and ignore this section entirely; it exists so a reviewer can see what changed and why, without those strings contaminating live claims.

| # | Retired value | Status | Superseded by / correction |
|---|---|---|---|
| **R1** | `257 tools / 26 domains` | **RETIRED** | **270 tools / 27 domains** (§1/V7, V8). Retained in `docs/finance/inputs.json` only as `previous_tools` / `previous_domains`, i.e. as a stated prior. `CHANGELOG.md` `[Unreleased]` names it as wrong in two ways. |
| **R2** | `268 tools / 26 domains` | **RETIRED** | 270 / 27. Still printed in `docs/02-tools-reference.md:3-4` and `docs/05-complete-tools-reference.md` (header, totals row `:4679`, and four issue-body quotes) — **P1 documentation defect, not a product ambiguity.** |
| **R3** | `258 tools` (`toolchest/inventory.json`, generated 2026-10-07T11:13:27Z) | **RETIRED — stale generator output** | 270 / 27. The inventory file's `counts.mcp` predates the surface it describes; its `generated_at` is ten days older than `HEAD`. |
| **R4** | "three violation classes" | **CORRECTED** | **Six** classes at this HEAD (§4/A6). The key set is not stable across pulls — count the audit's own keys. |
| **R5** | Launch page URL = a `static.teamily.ai/sites/…` link | **RETIRED — 403 anonymous** | Canonical public URL is `https://mem20.com` (md5-proven) or `https://bythewayz66-glitch.github.io/mem20/` (§3/D3, D4). |
| **R6** | `pip install .` as the install line | **TIGHTENED** | `git clone` + `pip install -r requirements.txt` (+ `aiohttp`, §3/D2b). `pip install .` is optional. |
| **R7** | "no benchmark of any kind in the repo" | **RETIRED** | `benchmarks/results/latest.{md,json}` ship on `main`. Quote with the caveat welded on (§5). |
| **R8** | "`mem20.jaysonai.online` has no DNS record" | **RETIRED for that host, and the host itself is retired** | `docs/CNAME` names **`mem20.com`**, which resolves and returns 200 (§3/D5). Do not cite the old host at all. |
| **R9** | Version `2.1.0rc2` | **RETIRED** | 3.0.0 (§1/V4). |
| **R10** | HEAD `c274404`, 9,874 files · `7c0b3e8`, 7,915 files · `1264076`, 7,974 files · `45445f48`, 7,975 files | **RETIRED** | `e7758bd1`, 7,991 files (§1/V2, V3). |
| **R11** | Clone-audit "65 distinct implementations / 228 clones" | **STILL WITHDRAWN** | The audit artifacts are not in the tree. Do not use. Cite `proof/audit_response.md` instead: an AST-restricted evaluator replacing a dynamic `eval()`; a 4,848-line MCP monolith split per domain; structured logging still open. |
| **R12** | `JaysonAIOnline/mem20` (retired org) | **STILL 404 — never cite** | Canonical is `bythewayz66-glitch/mem20`. |
| **R13** | "README clone-URL defect (17 stale refs)" | **RESOLVED in the repo** | Do not keep reporting it as a blocker. Re-grep before asserting. |
| **R14** | "`CHANGELOG.md` states 268/26 as its reconciliation target" (v4 §1 claim) | **WITHDRAWN — v4 was wrong** | `CHANGELOG.md` `[Unreleased]` states **270/27** and names 257/26 as the wrong prior. The 268/26 strings are historical §3.0.0 entries *below* the Unreleased block, which is what a changelog is for. Do not report them as live drift. |
| **R15** | "`mem20.com` is a byte-count match only, md5 unproven" (v4 §3/D4) | **RETIRED — now proven** | Both hosts return md5 `f82e7f31acf861810b5ea0bb40ea197e` this run (§3/D4). |

---

## 8. Guardrails (binding on every public asset in this directory)

1. **270 tools across 27 domains.** No 257, 258 or 268 in a live claim — those exist only in §7.
2. **No PyPI implication of any kind.** No `pip install mem20`, no PyPI badge, no "coming soon on PyPI". Install is `git clone` + `pip install -r requirements.txt`, and per §3/D2b that line is currently incomplete without `aiohttp`.
3. **No `/sites/` URL in any public asset.** The public web surfaces are `https://mem20.com` and `https://bythewayz66-glitch.github.io/mem20/` — both md5-proven identical to the committed `docs/index.html`.
4. **The `Adversarial` column is mandatory and may not be blank** (§0.5). Any claim table shipped in an asset carries it. A row with an empty caveat cell is not shippable.
5. **Adversarial 0.000 is disclosed in every asset that cites any retrieval number** — three modes at 0.000, `graph` unmeasured, n=3. §0 is the wording of record.
6. **No LoCoMo / LongMemEval / DMR claim, and no cross-vendor benchmark comparison.**
7. **Promotion gate described with its residual free-text path** (PG4) as *"evidence-based with an append-only audit trail that records when evidence was absent."* Never *tamper-proof*, *unfakeable*, *airtight*, *provably secure*.
8. **House numbers carry the "house number, not a new measurement" qualifier** (§6).
9. **Banned phrases:** *provably secure · tamper-proof memory · unfakeable · industry-leading retrieval · best-in-class retrieval · matches Mem0 · beats Zep · 0.0 leak rate (as a retrieval or security claim) · 65 distinct implementations · 257 tools · 268 tools · 258 tools*.
10. **Every number in a published asset appears in this ledger.** If it is not here, it does not ship.

---

## 9. Say / never say

A sales room compresses the ledger into sentences. These are the sentences.

| Say | Never say | Adversarial |
|---|---|---|
| "270 tools across 27 domains, over MCP." | "Over 250 tools." / "257 tools." / "268 tools." | `n/a: surface claim` |
| "Grounded and simulated memory are separate stores, enforced at the write path — the grounded write function refuses simulated content outright." | "The model is prompted not to mix them." | `n/a: write-path claim` |
| "Contamination rate 0.0 on a clean store, across six violation classes, and the audit is append-only." | "Provably secure." / "Tamper-proof." | `n/a: separation claim` |
| "Our adversarial hit rate is 0.000 on three of three scored modes — we publish that row." | "Strong retrieval across all query types." | `0.000` |
| "Direct-query hit rate 1.000 and multi-hop 0.800 on a 14-fact corpus; not comparable to vendor benchmarks." | "Beats Mem0 on LoCoMo." | `0.000` |
| "Promotion requires evidence, and the ledger records when evidence was absent (`evidence_hash: null`)." | "The promotion gate cannot be bypassed." | `n/a: promotion claim` |
| "MIT-licensed, self-hostable, source install, no lock-in." | "Enterprise-ready." | `n/a: licensing claim` |
| "TAM $1.28B / SAM $282M / SOM $1.68M — house numbers, carried, not re-derived." | Presenting them as fresh market measurement. | `n/a: commercial claim` |
| "On adversarial queries, `graph` is unmeasured — we do not count that as a pass." | Anything that presents `graph`'s multi-hop 1.000 as an overall result. | `unmeasured` |

---

## 10. Hand-off

**Next seat: Data & Revenue Analytics Lead.** Input they need: §6 (H1–H5) plus §3/D4. With SOM fixed at $1.68M, blended ACV at $14,000, and now **two** md5-proven public surfaces (`mem20.com` and `github.io` Pages, byte-identical), they can instrument the funnel that actually exists — repo clone and star delta, Pages sessions on either host — rather than a page anonymous readers cannot load. Any `/sites/`-based analytics spec is retired with §7/R5.

**Second hand-off, blocking a public claim:** §3/D2b is an install-path defect, not a messaging one. It is *partly* addressed by PR #118 but not merged. **Owner: whoever merges #118.** Until it lands, no asset may print an install line that claims to work end to end.

**Third hand-off, P1 documentation:** §1's drift table names two files (`docs/02-tools-reference.md`, `docs/05-complete-tools-reference.md`) that still print 268/26 while their own stated method returns 270. Owner: GitHub Repo Assistant (roster item #10 lane).

**Standing rule for whoever edits this file next:** re-measure, do not inherit. The tool surface, the violation-class count, the CNAME host, the `homepage` field, the `aiohttp` fix state and now the `CHANGELOG.md` drift status have all changed at least once between pulls. Every number above carries the command that produced it; run the command.
