# mem20 — GTM Claim Verification Ledger (v6)

**Owner:** mem20 GTM Team Lead · **Seat:** Brand & Positioning Strategist / Opportunity & Market Analyst
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **Branch read:** `main`
**HEAD at capture:** `f1672473cd19d5926e1df0c80042259d3b4b17ca` (2026-10-31 16:59:08 -0600)
**Captured:** 2026-10-31 · **Method:** every row traced to a file, a command, or a captured run against a full clone of the canonical remote at this HEAD.
**Surface of record:** **270 tools / 27 domains.** The values 257, 258 and 268 are **RETIRED** and survive only in §7.
**Supersedes:** claim ledger v5 (HEAD `e7758bd178d38da63c5359dded0aada8bfc0eea5`, captured 2026-10-27).

> **Why v6 exists.** v6 is not a cosmetic refresh. Four things the v5 ledger asserted as current are **no longer true at this HEAD**, and three of them are load-bearing for launch copy:
>
> 1. **The benchmark was re-run on a different, 20× larger corpus, and the headline adversarial result inverted.** v5's §0 opened with *"adversarial 0.000 across hybrid, keyword and semantic, n=3"*. The shipped file at this HEAD is `mem20-scale-corpus-v2` — **700 grounded / 1,300 simulated / 250 queries** — and `semantic` scores **0.950** on adversarial. The weakness moved: it is now **`keyword` on `adversarial_hard` at 0.000 (n=40)** and **`keyword` on `contradiction` at 0.050 (n=40)**, and **`hybrid` and `graph` have no rows at all in the shipped file**. Any asset still saying "0.000 in all three modes, 13 queries" is quoting a retired benchmark.
> 2. **The `aiohttp` install defect is closed.** v5's D2b said `grep -c aiohttp requirements.txt` → **0** and forbade a clean install claim. At this HEAD `requirements.txt` pins **eight** packages including `aiohttp>=3.14.5` and `mcp-types>=2.3.0`, and the server boots. D2b is **CLOSED**.
> 3. **The version row is a contradiction inside the repo, not a single value.** `VERSION` = **3.1.0**, `pyproject.toml` = **3.0.0**, highest tag = **v3.1.1**. v5 said "3.0.0" flatly. See V4 — this is a packaging defect, and assets quote **3.1.0** (the name `main` carries) while naming the defect.
> 4. **The public page was fixed.** v5/README reported `docs/index.html` still printing the retired tool/domain pair. At this HEAD it prints **270 × 10** and **27 domains × 8**, zero occurrences of the retired pair. That drift row is retired; `docs/02` and `docs/05` still carry it.

### What changed since v5

| # | Change | Detail |
|---|---|---|
| C1 | **§0 rewritten — the adversarial finding inverted** | `semantic` adversarial 0.950 / adversarial_hard 0.900 at n=60/40. The hole is now mode-specific (`keyword`), not product-wide. |
| C2 | **Benchmark corpus and scope replaced** | `mem20-agent-kb-v1` (14/3/13) → **`mem20-scale-corpus-v2` (700/1,300/250)**. Two new query kinds: `adversarial_hard`, `contradiction`. `hybrid` and `graph` produce no rows. |
| C3 | **D2b (aiohttp) CLOSED** | Eight pins, `aiohttp>=3.14.5` and `mcp-types>=2.3.0` present; handshake passes from a clean install. |
| C4 | **Version is self-contradictory in the repo** | `VERSION` 3.1.0 · `pyproject.toml` 3.0.0 · tags v3.1.0 + v3.1.1. Highest tag `v3.1.1` is an ancestor of `main` but `main`'s `VERSION` was rolled back to 3.1.0 by the release commit `73343f6`. |
| C5 | **`docs/index.html` drift FIXED** | 270 × 10, 27 domains × 8, retired pair 0. The remaining in-tree drift is `docs/02` and `docs/05` only. |
| C6 | **Repo grew to 8,516 tracked files** | From 7,991 at `e7758bd1`. |
| C7 | **`toolchest/inventory.json` no longer counts MCP tools at all** | `counts.mcp = 0`, regenerated `2026-10-29T05:54:53Z`. The superseded inventory figure is retired (§7 R3), and so is the README's claim that the file still carries it. |
| C8 | **Retired-infrastructure hosts removed from this document** | No retired hostname appears as a **live reference** anywhere in v6, including §7. The only occurrences are a quoted commit subject (V2) and a branch name (H2 coordination note) — neither is a citation of the host as a surface. The register records the retirement without reproducing the string. |

---

## 0. The weakest measured row — read this before the strengths

This is the first thing in the document because it is the first thing a hostile reviewer will find. It is stated in full, in the same units the benchmark file uses, with no softening.

**Source:** `benchmarks/results/latest.md` / `latest.json` at this HEAD. Corpus **`mem20-scale-corpus-v2`**: 700 grounded facts, 1,300 simulated facts, 250 queries. Reproduce: see §5.

| Mode | Query class | n | Hit rate | MRR | Leak rate |
|---|---|---:|---:|---:|---:|
| `keyword` | **adversarial_hard** | 40 | **0.000** | 0.000 | 0.000 |
| `keyword` | **contradiction** | 40 | **0.050** | 0.030 | 0.000 |
| `keyword` | unanswerable | 20 | 0.000 | 0.000 | 0.000 |
| `semantic` | adversarial_hard | 40 | 0.900 | 0.810 | 0.000 |
| `semantic` | contradiction | 40 | 1.000 | 1.000 | 0.000 |
| `semantic` | unanswerable | 20 | 0.000 | 0.000 | 0.000 |
| **`hybrid`** | **any** | — | **not scored** | — | — |
| **`graph`** | **any** | — | **not scored** | — | — |

Six things must be said about that block, in this order, every time it is presented:

1. **`keyword` mode collapses on hard adversarial and contradiction queries: 0.000 (n=40) and 0.050 (n=40).** That is the weakest measured row in the product and it is mode-specific, not universal.
2. **`semantic` mode is materially better on the same classes: 0.950 / 0.900 / 1.000.** Do not average the two modes into one "adversarial score" — the split *is* the finding. A reader who picks the flattering mode and quotes 0.950 is misrepresenting the product exactly as badly as one who quotes 0.000 and calls it a product-wide failure.
3. **`hybrid` and `graph` are not scored in the shipped file.** The harness supports both (`mem20benchmarkz/mem20benchmarkz/bench.py:139` hybrid, `:143` graph), but the committed run used `--modes keyword,semantic`. **This is `unmeasured`, which is neither a zero nor a pass.** Any asset that quotes a hybrid or graph retrieval number is quoting a benchmark that no longer ships — see §7 R17.
4. **Unanswerable 0.000 is correct behaviour, not a defect.** The system abstains when there is no grounded answer. It is listed above only so that nobody mistakes it for a failure later.
5. **It does not contradict the leak rate.** Leak rate **0.000** across every scored row means *no simulated record surfaced in a grounded result*. Hit rate measures whether the correct grounded record was returned. A system can score 0.000 on both at once: it abstains. **Abstaining is the safe failure, and it is still a failure.** Never present 0.000 leak as if it cancels a weak hit rate.
6. **The row is carried as a column, not as a footnote.** See §0.5.

**What this bounds.** mem20's claim is auditable separation, not retrieval leadership. The `keyword` block is the price of that claim stated openly: the partition holds, and one of the two scored retrieval modes has not learned to resolve deliberately deceptive queries. Any sales asset that claims retrieval superiority is contradicted by this table and must not ship.

**The one-line version for a sales room:** *"In keyword mode our hard-adversarial hit rate is zero and contradiction is 0.05; semantic mode is 0.90 and 1.00 on the same classes. We publish both rows. What we sell is provable separation, not the best retrieval score."*

### 0.5 The `Adversarial` column — controlled vocabulary

Every claim table in this ledger (§1, §3, §4, §6) carries an **Adversarial** column. It is not decorative. It answers one question per row: **does the measured adversarial result bound this claim, and how?**

| Value | Meaning | What the writer must do |
|---|---|---|
| **`0.000`** | The claim touches retrieval quality and is bounded by the weakest measured row. | Reproduce the §0 block in the same asset. A bare `0.000` cell without §0 is a defect. |
| **`unmeasured`** | `hybrid` / `graph` have no row in the shipped file. | Never present them as a pass. Name them as unmeasured whenever either appears. |
| **`n/a: <reason>`** | Not a retrieval claim; the measured rows do not bound it. The reason is mandatory. | Still carry §0 if the *same asset* quotes any retrieval number elsewhere. |

**Three rules bind this column, and they are machine-checkable:**

1. **No cell may be blank, `—`, or `TBD`.** An absent value is how a caveat gets lost in transcription. A blank cell fails review.
2. **A `0.000` cell is a citation, not a label.** It obliges the §0 block to appear in the destination asset, not merely this ledger.
3. **`n/a` is never a claim of strength.** It says the retrieval rows do not *speak to* this claim — not that this claim is unaffected by retrieval weakness. A pricing claim is `n/a: not a retrieval claim`; that does not make the product good at retrieval.

---

## 1. Verified product facts

| # | Claim | Verified value | Evidence (captured 2026-10-31) | Adversarial |
|---|-------|---------------|--------------------------------|-------------|
| V1 | Canonical repo | `github.com/bythewayz66-glitch/mem20` | GitHub API: `private=false`, `default_branch=main`, `license.spdx_id=MIT`, `pushed_at=2026-10-31T22:59:08Z`, `stargazers_count=1`, `forks_count=0`, `open_issues_count=1` | `n/a: repo identity` |
| V2 | HEAD commit | `f1672473cd19d5926e1df0c80042259d3b4b17ca` | `git log -1` — *"chore(infra): purge retired jaysonai.online / Sidney / gabe references (#145)"*. `git describe` → `v3.1.0-3-gf167247` (three commits past the `v3.1.0` tag). | `n/a: commit identity` |
| V3 | Tracked files | **8,516** | `git ls-tree -r --name-only HEAD \| wc -l`. Was 7,991 at `e7758bd1`; 8,516 at `27c1e5fb`. The delta is docs, `published/` records and release files — **not** lost capability. | `n/a: repo size` |
| V4 | Version | **3.1.0** — and the repo **contradicts itself** | `VERSION` = `3.1.0`. `pyproject.toml` `version = "3.0.0"` — **never bumped at either release cut**. Tags: `v3.1.0` → `73343f6`, `v3.1.1` → `52ffe13`. `main`'s `VERSION` was rolled **back** from 3.1.1 to 3.1.0 by release commit `73343f6` while the `v3.1.1` tag sits at an ancestor. See §1.1. | `n/a: version string` |
| V5 | License | **MIT** | `LICENSE` line 1 = `MIT License`; GitHub API `license.spdx_id = "MIT"`; `pyproject.toml` `license = { text = "MIT" }` | `n/a: licensing` |
| V6 | Python floor | **>=3.10** | `pyproject.toml` `requires-python = ">=3.10"` | `n/a: runtime requirement` |
| **V7** | **MCP tool surface** | **270 tools** | **Live handshake.** `python3 verify_mcp.py` → `TOOL_COUNT: 270`, `RESULT: PASS`, `protocolVersion 2025-06-18`. Independently: `grep -rhoE 'self\.tools\[' mcp/ --include="*.py" \| wc -l` = **272** raw literal hits, **270** unique quoted names. Third source: `docs/finance/inputs.json` → `tool_surface.tools = 270`. Fourth: CI `.github/workflows/mcp-verify.yml` pins `MEM20_EXPECTED_TOOLS: "270"`. | `n/a: counts tools, not retrieval quality` |
| **V8** | **Tool domains** | **27** | `sed -n '/def _setup_tools/,/^    def /p' mcp/server.py \| grep -cE 'self\.register_[a-z_]+_tools\(\)'` = **27**. Confirmed against `docs/finance/inputs.json` → `tool_surface.domains = 27`. | `n/a: counts domains, not retrieval quality` |
| V9 | Transport | JSON-RPC 2.0 over **stdio** (default); Streamable HTTP via `MEM20_TRANSPORT=http` on `MEM20_MCP_PORT` (8082) | `verify_mcp.py` handshake over stdio | `n/a: transport mechanism` |
| V10 | Health surface | `/health`, `/ready`, `/metrics` | `mcp/health.py`; a bind conflict on :8080 degrades to a warning, not a failure — observed again this run: `WARNING mem20.mcp health endpoint disabled (could not bind :8080): [Errno 98] Address already in use`, and the run still returned `RESULT: PASS` | `n/a: operational surface` |
| V11 | Embedder | `sentence-transformers/all-MiniLM-L6-v2`, 384-dim | `memory_engine/memory.py`; `benchmarks/results/latest.json` → `environment.embedding_model` / `embedding_dim: 384` | `0.000` — this is the embedder behind the `keyword` weak rows and the `semantic` strong ones |
| V12 | Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2`, on by default, `MEM20_RERANK=0` opt-out | `memory_engine/memory.py`; benchmark `environment.cross_encoder: true` | `unmeasured` — **`trust.rerank_off_comparison` is `null` in the shipped JSON**, so the rerank on/off comparison v5 quoted is no longer shipped |
| V13 | Hybrid retrieval | vector (`IndexFlatIP`) + BM25 (`BM25Okapi`), RRF fusion | `memory_engine/memory.py` `recall_hybrid()`; harness `bench.py:139` | `unmeasured` — **the shipped results file has no `hybrid` row.** The capability exists; the number does not ship. |
| V14 | `epistemic_status` is **required** on write | Captured refusal this run: `ValueError: remember() requires an explicit epistemic_status. Declare how this claim was learned; one of ['observed', 'inferred', 'imagined', 'user_stated', 'hypothesis', 'agent_generated', 'unlabeled']` | `inspect.signature(M.remember)` returns `epistemic_status: 'str \| None' = None` — optional in *signature*, mandatory in *behaviour*. Do not describe it as a required parameter; describe it as a required value. | `n/a: write-path guard` |
| V15 | Issues enabled / Discussions disabled | `has_issues=true`, `has_discussions=false`, `has_wiki=true`, `has_projects=true`, `has_pages=true` | GitHub API, this run | `n/a: repo configuration` |
| V16 | Repository description | *"Memory substrate and agent runtime for AI systems that have to be trusted — grounded facts and simulated hypotheses never mix, and every retrieval call reports index drift instead of hiding it."* | GitHub API `description` — the owner's own framing, safe to quote as positioning | `0.000` — it makes an implicit retrieval claim; the asset must still carry §0 |

### 1.1 The version row is a defect, not an ambiguity

This is the one row a reviewer can use to embarrass the release if it is quoted sloppily, so it is spelled out.

| Ref | `VERSION` | `pyproject.toml` | Note |
|---|---|---|---|
| `v3.0.0` (`a366ff74` era) | 3.0.0 | 3.0.0 | Consistent. |
| `52ffe13` (tag **v3.1.1**) | **3.1.1** | 3.0.0 | `VERSION` bumped; `pyproject.toml` missed. |
| `73343f6` (tag **v3.1.0**) | **3.1.0** | 3.0.0 | Release commit **reverted** `VERSION` 3.1.1 → 3.1.0. |
| `main` @ `f1672473` | **3.1.0** | **3.0.0** | Both stale relative to the highest tag. |

**What GTM says:** *"Version 3.1.0 — `VERSION` on `main` at `f1672473`."* That is true and checkable with one command.

**What GTM does not say:** "version 3.1.1", "version 3.0.0", or "the PyPI release is 3.1.0" (there is no PyPI release — D1). If asked about `pyproject.toml`, the honest answer is: *"it still reads 3.0.0; the tag and the `VERSION` file are ahead of it. That is a packaging defect, filed, not a capability difference."*

**Consequence for any install-from-source claim:** `pip install .` builds an artifact labelled **3.0.0** regardless of the tag. Do not ship an install path that implies a 3.1.0 wheel.

### Note on the 270 / 27 figure

At this HEAD the live handshake is the authority and it says **270**, with **27** registered mixins agreeing, `docs/finance/inputs.json` recording the same pair plus the retired prior as `previous_tools` / `previous_domains`, and CI pinning the same value. Four independent measures agree — that agreement is the defence, not any single number.

**How to answer a challenge:** run the command, not a different number. `python3 verify_mcp.py` → `TOOL_COUNT: 270`. The verifier needs `mcp>=2.1.1`, `mcp-types`, `aiohttp`, `pydantic`, `numpy` and `pip install -e ./mem20api`; with those present it passes from a full clone at this HEAD.

**Residual documentation drift, measured this run.**

| File | What it still prints | Status |
|---|---|---|
| `docs/02-tools-reference.md:3-4` | the retired tool count across the retired domain count (see §7 R2) | **Live drift — P1 documentation defect.** Contradicts its own stated method: instantiating the server returns 270. |
| `docs/05-complete-tools-reference.md` | the retired tool count in the header (`:3`) and in the totals row (`:4679`) (see §7 R2) | **Live drift — same P1 item.** |

**Correct at this HEAD:** `README.md` (270 × 6, 27 domains × 5, retired pair × 0), `docs/README.md` (270 × 2, 27 domains × 1), **`docs/index.html` (270 × 10, 27 domains × 8, retired pair × 0 — fixed since v5)**, `CHANGELOG.md` `[Unreleased]`, and `docs/finance/inputs.json`.

**`toolchest/inventory.json` no longer reports an MCP tool count at all:** `counts = {mcp: 0, cli: 2, subsystem: 310, total: 312}`, `generated_at = 2026-10-29T05:54:53Z`. It is a *subsystem* inventory now, not a tool-surface source. Do not cite it for or against 270 (§7 R3).

**This is a documentation defect, not a product ambiguity** — quote the verifier, and name the drift rather than matching it.

---

## 2. The surface of record

| Field | Value | Status |
|---|---|---|
| Tools | **270** | Current — live handshake |
| Domains | **27** | Current — mixin count |
| Retired tool values | three superseded counts | **RETIRED** — enumerated only in §7 |
| Retired domain value | one superseded count | **RETIRED** — enumerated only in §7 |

**Binding rule:** any sentence in any asset in this directory that names the tool surface names it as **"270 tools across 27 domains."** No exceptions, no abbreviations, no "~270", no "over 250". If a number is challenged, the answer is §1/V7's command.

---

## 3. Distribution state (re-measured at `f1672473`; two items changed since v5)

| # | Question | Measured result | Consequence for GTM | Adversarial |
|---|---|---|---|---|
| **D1** | Is there a PyPI package? | **No.** `pypi.org/pypi/mem20/json` → **404**; `mem20-ai/json` → **404**; `mem20oreo/json` → **404** (all three, this run) | **Never print `pip install mem20`, `pip install mem20-ai`, or a PyPI badge.** Install is source-only. | `n/a: packaging` |
| **D2** | What is the documented install path? | `git clone https://github.com/bythewayz66-glitch/mem20.git` → `pip install -r requirements.txt`. `requirements.txt` on `main` now pins **eight**: `mcp>=2.1.1`, `mcp-types>=2.3.0`, `aiohttp>=3.14.5`, `pydantic>=2.13.4`, `anyio>=4.14.2`, `numpy>=1.24`, `faiss-cpu>=1.7.4`, `sentence-transformers>=2.2.0`. | State the two-command source install. It is now complete — see D2b. | `n/a: install path` |
| **D2b** | **Is that install path complete?** | **Yes — CLOSED since v5.** `aiohttp` is pinned (`>=3.14.5`, bumped from `>=3.9` by #142) and `mcp-types>=2.3.0` is pinned, with an in-file comment naming exactly the module-scope imports that made them mandatory (`a2a_tools.py:19`, `server.py:48`). A clean `pip install -r requirements.txt` boots the server: `verify_mcp.py` → `TOOL_COUNT: 270`, `RESULT: PASS`. | **v5's prohibition ("no asset may print an install line that claims to work end to end") is LIFTED.** The install line may be printed as-is. | `n/a: install path` |
| **D3** | Are `/sites/` CDN URLs publicly reachable? | **No — 403 to anonymous requests.** Verified token-free this run on the repo's own `homepage` target: `HTTPError 403: Forbidden`. A token-carrying `curl` in our shell returns 200 and **lies**. | **Never publish, promote, or link a `/sites/` URL in a public asset.** | `n/a: hosting` |
| **D4** | What is the canonical public URL? | **`https://mem20.com`** → **HTTP 200, 33,429 bytes, md5 `37246f8d13b0f6870faa913c0a44c68d`**. **`https://bythewayz66-glitch.github.io/mem20/`** → **HTTP 200, 33,429 bytes, same md5 `37246f8d13b0f6870faa913c0a44c68d`**. Both are **byte-identical to the committed `docs/index.html`** (`33,429` bytes, md5 `37246f8d13b0f6870faa913c0a44c68d`). | **Both hosts are md5-proven to serve the committed page.** Prefer **`mem20.com`** in customer-facing copy; use `github.io` where a `github.com` link is expected. **v5's 36,627 bytes / md5 `f82e7f31…` are RETIRED (§7 R16).** | `n/a: hosting` |
| **D5** | Does the CNAME host resolve? | **Yes.** `docs/CNAME` contains exactly **`mem20.com`**. `getent hosts mem20.com` → four GitHub Pages A-records (`185.199.108.153`, `.109.153`, `.110.153`, `.111.153`); `https://mem20.com` → **200**, md5-identical per D4. | **The retired host is retired and is not named anywhere in this document.** `mem20.com` is the preferred customer-facing URL. | `n/a: DNS` |
| **D6** | Any stale public pointer? | **Yes, unchanged since v5.** The repo **`homepage` field** is `https://static.teamily.ai/sites/ca954f26-cfef-49bf-92b4-55c652e71f8f/webpages/mem20-site/index.html` — verified **403** to anonymous requests this run. | **Owner action, not GTM:** repoint `homepage` to `https://mem20.com`. Every visitor who clicks it from the repo hits a 403 — the worst first impression for a trust-positioned product. | `n/a: link hygiene` |

---

## 4. Live partition + audit evidence (captured 2026-10-31 at `f1672473`)

Harness run against a full clone, throwaway store (`MEM20_STORE_PATH=/tmp/mem20-gtm-<ts>`), engine imported from the repo root (`sys.path.insert(0, ".")`).

| # | Check | Captured result | Verdict | Adversarial |
|---|-------|----------------|---------|-------------|
| A1 | Grounded write | accepted; `origin=grounded`, `store=grounded`, `action=remember` | ✅ verified | `n/a: write path` |
| **A2** | `remember(..., _allow_simulated=True)` | `PermissionError: remember() is grounded-only. Simulated content must use remember_simulated(); this call is refused to protect Step 7.4 separation.` | ✅ verified — **quote verbatim; strongest asset in the repo** | `n/a: write path` |
| A3 | `remember_simulated(...)` | accepted; `origin=simulated`, `store=simulated`, `epistemic_status=imagined` | ✅ verified | `n/a: write path` |
| A4 | `recall(topic=…)` default | returned `list[dict]`, n=1; origins `['grounded']` only; stores `['grounded']` | ✅ verified | `0.000` — the scored retrieval paths carry the weak rows in §0 |
| A5 | `recall(include_simulated=True)` | returned `list[dict]`, n=2; origins `['grounded', 'simulated']`; stores `['grounded', 'simulated']` | ✅ verified | `0.000` — same |
| **A6** | `audit_contamination(actor=…)` | `contamination_rate: 0.0`, `status: "CLEAN"`; **6** violation classes, **all empty**: `violations_origin_not_grounded`, `violations_pinned_origin_not_grounded`, `violations_pinned_simulated_content`, `violations_simulated_in_bm25_corpus`, `violations_simulated_in_graph`, `violations_simulated_in_grounded_index` | ✅ verified — **6 classes, not 3.** Read the audit's own keys and count them; never assert a count from memory. | `n/a: separation audit` |
| A7 | `epistemic_status` omitted | `ValueError` refusing an unlabeled write (V14) | ✅ verified hardening | `n/a: write guard` |
| A8 | Audit after promotion attempts | still `contamination_rate: 0.0`, `status: "CLEAN"` | ✅ verified — the gate does not corrupt the store, even when it admits content | `n/a: separation audit` |

> **Measurement note (worth carrying, because it caught a false negative this run).** `recall(tags=["gtm"], k=10)` returned **n=0** on a store that demonstrably contained two records written with `tags=None`. That is a filter shape issue in the harness, **not** a product finding — the same store returned n=1 / n=2 when queried by `topic=`. Any harness that reports "0 results" from a tag-filtered call must re-query by topic before recording a defect.

### Promotion gate — six paths, all re-captured this run at `f1672473`

The gate is **narrowed, not closed.** Report these as six distinct behaviours, never as one claim.

| # | Path | Captured behaviour | Adversarial |
|---|---|---|---|
| PG1 | Bare call, `sim_id` only | **REFUSED** — *"Promotion blocked: requires explicit external confirmation OR real-world prediction-error resolution (resolution_note + attestation)."* | `n/a: promotion gate` |
| PG2 | `resolved_via_prediction_error=True` + free-text note | **REFUSED** — *"Promotion via prediction-error resolution requires structured evidence linking to a recorded prior prediction (keys ('prediction_ref', 'observed_outcome'))."* | `n/a: promotion gate` |
| PG3 | Structured `prediction_error_evidence` naming an unrecorded `prediction_ref` | **REFUSED** — *"Promotion blocked: prediction_ref pred-does-not-exist is not a recorded prior prediction. The prediction-error gate requires a real, previously recorded prediction that resolved in favor (or a registered PREDICTION_ERROR_VERIFIER for external signed attestation)."* **Pass `resolved_via_prediction_error=True` and `resolution_note` too** — without them the call returns the earlier PG1 message instead of this one. | `n/a: promotion gate` |
| **PG4** | **Free-text `confirmation` alone** | **PROMOTES.** Returned `{"promoted": true, "epistemic_status": "hypothesis", "evidence_hash": None}`. **This is the residual open path.** | `n/a: promotion gate` |
| PG5 | Whitespace-only `confirmation` | **REFUSED** — falls through to the PG1 message. Confirmation is length-checked, not evidence-checked. | `n/a: promotion gate` |
| PG6 | `resolution_note` alone, no evidence | **REFUSED** — PG1 message. | `n/a: promotion gate` |

**Why PG4 matters and how to describe it.** A promotion can be obtained by typing a sentence. The resulting grounded record is tagged `epistemic_status: hypothesis` and carries `evidence_hash: null` — so the promotion is **recorded as unevidenced** in the ledger, which is the real control: the audit trail preserves the fact that no evidence was attached. That is the honest framing, and it is a good one: **"evidence-based with an append-only audit trail that records when evidence was absent."** It is not a claim that the gate cannot be passed by typing.

**Never** describe the gate as airtight, tamper-proof, unfakeable, provably secure, or as refusing self-attestation. A reader who runs PG4 in thirty seconds will find the free-text path, and this product's entire positioning is that its numbers hold up under scrutiny.

---

## 5. The benchmark — every row the file actually ships

Source: `benchmarks/results/latest.md` and `latest.json` at this HEAD. Corpus **`mem20-scale-corpus-v2`**: **700 grounded facts, 1,300 simulated facts, 250 queries.** Two modes scored: `keyword`, `semantic`. Six query kinds: `adversarial`, `adversarial_hard`, `contradiction`, `direct`, `multi_hop`, `unanswerable`.

| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| `keyword` | adversarial | 60 | 1.000 | 1.000 | 0.000 | 110.2 |
| `keyword` | adversarial_hard | 40 | **0.000** | 0.000 | 0.000 | 192.1 |
| `keyword` | contradiction | 40 | **0.050** | 0.030 | 0.000 | 184.5 |
| `keyword` | direct | 60 | 1.000 | 1.000 | 0.000 | 146.8 |
| `keyword` | multi_hop | 30 | 0.800 | 0.800 | 0.000 | 184.9 |
| `keyword` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 108.8 |
| `semantic` | adversarial | 60 | 0.950 | 0.884 | 0.000 | 102.3 |
| `semantic` | adversarial_hard | 40 | 0.900 | 0.810 | 0.000 | 102.1 |
| `semantic` | contradiction | 40 | 1.000 | 1.000 | 0.000 | 104.3 |
| `semantic` | direct | 60 | 0.900 | 0.864 | 0.000 | 103.0 |
| `semantic` | multi_hop | 30 | 1.000 | 0.950 | 0.000 | 105.3 |
| `semantic` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 105.8 |

Aggregate latency: `keyword` n=250, p50 **112.0** / p95 **203.4** / p99 **289.8** / max 419.7 ms; `semantic` n=250, p50 **103.5** / p95 **195.4** / p99 **291.6** / max 438.8 ms.

Trust block (`latest.json` → `trust`): contamination rate **0.0**, contamination violations **0**, simulated records in BM25 **[]**, stale pointer rate **0.000000**, stale pointers **0**, indexed entries **1,400**, index healthy **True**, graph **654 entities / 3,601 edges**, degraded queries **0**, queries with drift diagnostic **500**, all reported healthy **True**, ledger records **700**, **`rerank_off_comparison: null`**.

**Four rules bind this table, all non-negotiable:**

1. **Carry the file's own warning, verbatim:** *"These numbers are not comparable to competitor benchmarks. Mem0's LoCoMo (92.5) and LongMemEval (94.4) figures and Zep's DMR (94.8%) come from different corpora — two of the three are private or vendor-defined — and different metrics. Nothing here refutes or reproduces them. These results describe this corpus only."*
2. **The `keyword` 0.000 / 0.050 rows stay visible, and `hybrid` / `graph` stay named as `unmeasured`** (§0).
3. **Never set this against Mem0's LoCoMo 92.5 / LongMemEval 94.4 or Zep's DMR 94.8%.** Vendor self-reported, different corpora, different metrics.
4. **Never present 0.0 leak rate as a retrieval result.** It is a separation result, measured on this corpus, and §0 rule 5 governs how the two interact.

**Reproduce (the file's own commands):**

```bash
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes keyword,semantic --out benchmarks/results
```

**Scope disclosure, mandatory whenever this table is quoted:** the committed run scored **two** modes. The harness supports four (`bench.py:139` hybrid, `:143` graph), so *"we only scored two"* is a reporting choice, not a harness limit. Say so plainly rather than letting a reader assume hybrid was measured and passed.

---

## 6. House numbers (commercial)

| # | Metric | Value | Status / source | Adversarial |
|---|---|---|---|---|
| H1 | TAM | **$1.28B** | House number, carried verbatim in `docs/finance/inputs.json` → `house_numbers.tam_usd: 1280000000`, `provenance: "carried verbatim from the owner directive; NOT re-derived in this file"` | `n/a: commercial sizing` |
| H2 | SAM | **$282M** | `house_numbers.sam_usd: 282000000` | `n/a: commercial sizing` |
| H3 | SOM (ARR) | **$1.68M** | `house_numbers.som_arr_usd: 1680000` | `n/a: commercial sizing` |
| H4 | Blended ACV | **$14,000** | `house_numbers.blended_acv_usd: 14000` | `n/a: pricing` |
| H5 | Accounts to realise SOM | **120** | `house_numbers.som_accounts: 120`, arithmetically consistent: 120 × $14,000 = $1,680,000 exactly | `n/a: arithmetic on house numbers` |

**These are house numbers, not fresh measurements.** `CHANGELOG.md` states the commercial figures are *"deliberately not restated as new measurements."* Every asset quoting them carries the same qualifier. The `inputs.json` rule is explicit and binding: **an account count is never multiplied back into a TAM or SAM figure.**

**Derived ratios (arithmetic on the house numbers — label as estimates, show the division):**
- SOM ÷ ACV = 1,680,000 ÷ 14,000 = **120 accounts** (exact).
- SOM ÷ SAM = **0.60%** of SAM.
- SAM ÷ TAM = **22.03%** of TAM.

Do not present 120 accounts as a forecast. It is the arithmetic consequence of three carried constants. **Note the `n/a` cells above:** a commercial row is not a retrieval claim, so §0 does not bound it — but that is not permission to imply the product retrieves well. If an asset quotes H1–H5 *and* any retrieval number, it carries §0 regardless.

---

## 7. Retired values — the only place these numbers may appear

**This is the sole register of superseded values. Every occurrence of a retired number outside this table is a defect.** In a sales room, quote from §1/§2 and ignore this section entirely; it exists so a reviewer can see what changed and why, without those strings contaminating live claims.

| # | Retired value | Status | Superseded by / correction |
|---|---|---|---|
| **R1** | 257 tools / 26 domains | **RETIRED** | **270 tools / 27 domains** (§1/V7, V8). Retained in `docs/finance/inputs.json` only as `previous_tools` / `previous_domains`, i.e. as a stated prior. `CHANGELOG.md` `[Unreleased]` names it as wrong in two ways. |
| **R2** | 268 tools / 26 domains | **RETIRED** | 270 / 27. Still printed in `docs/02-tools-reference.md:3-4` and `docs/05-complete-tools-reference.md` (header `:3`, totals row `:4679`) — **P1 documentation defect, not a product ambiguity.** |
| **R3** | 258 tools (`toolchest/inventory.json`) | **RETIRED — and the file no longer says it** | The inventory was regenerated `2026-10-29T05:54:53Z` and now reports `counts.mcp = 0` with `subsystem: 310`, `cli: 2`, `total: 312`. It measures **subsystems, not MCP tools**. Retire both the 258 figure *and* any asset that says "the inventory says 258". |
| **R4** | "three violation classes" | **CORRECTED** | **Six** classes at this HEAD (§4/A6). The key set is not stable across pulls — count the audit's own keys. |
| **R5** | Launch page URL = a `static.teamily.ai/sites/…` link | **RETIRED — 403 anonymous** | Canonical public URL is `https://mem20.com` (md5-proven) or `https://bythewayz66-glitch.github.io/mem20/` (§3/D3, D4). |
| **R6** | `pip install .` as the install line | **TIGHTENED** | `git clone` + `pip install -r requirements.txt` (now complete per §3/D2b). `pip install .` is optional **and** builds a wheel labelled 3.0.0 (§1.1). |
| **R7** | "no benchmark of any kind in the repo" | **RETIRED — benchmarks still ship** | `benchmarks/results/latest.{md,json}` ship on `main` at this HEAD. **The statement holds; every number previously attached to it does not** — see R17. |
| **R8** | "the CNAME host has no DNS record" | **RETIRED for that host, and the host itself is retired** | `docs/CNAME` names **`mem20.com`**, which resolves and returns 200 (§3/D5). The v5 register and the v5 D5 row both printed the retired hostname; v6 does not, anywhere. |
| **R9** | Version `2.1.0rc2` | **RETIRED** | **3.1.0** — `VERSION` on `main` at `f1672473` (§1/V4). Highest tag is `v3.1.1`; `pyproject.toml` still reads 3.0.0 (§1.1). |
| **R10** | HEAD `c274404` / 9,874 files · `7c0b3e8` / 7,915 · `1264076` / 7,974 · `45445f48` / 7,975 · `e7758bd1` / 7,991 | **RETIRED** | **`f1672473cd19d5926e1df0c80042259d3b4b17ca` / 8,516 tracked files** (§1/V2, V3). The task brief also named `27c1e5fb…` — `main` advanced **2 commits** past it during this run; the newer SHA is the one of record. |
| **R11** | Clone-audit "65 distinct implementations / 228 clones" | **STILL WITHDRAWN** | The audit artifacts are not in the tree. Do not use. Cite `proof/audit_response.md` instead: an AST-restricted evaluator replacing a dynamic `eval()`; a 4,848-line MCP monolith split per domain; structured logging still open. |
| **R12** | `JaysonAIOnline/mem20` (retired org) | **STILL 404 — never cite** | Canonical is `bythewayz66-glitch/mem20`. |
| **R13** | "README clone-URL defect (17 stale refs)" | **RESOLVED in the repo** | Do not keep reporting it as a blocker. Re-grep before asserting. |
| **R14** | "`CHANGELOG.md` states 268/26 as its reconciliation target" | **WITHDRAWN — v4 was wrong** | `CHANGELOG.md` `[Unreleased]` states **270/27** and names 257/26 as the wrong prior. Do not report historical changelog entries as live drift. |
| **R15** | "`mem20.com` is a byte-count match only, md5 unproven" | **RETIRED — proven** | Both hosts return md5 `37246f8d13b0f6870faa913c0a44c68d` this run (§3/D4). |
| **R16** | **`mem20.com` = 36,627 bytes, md5 `f82e7f31acf861810b5ea0bb40ea197e`** | **RETIRED — the page changed** | **33,429 bytes, md5 `37246f8d13b0f6870faa913c0a44c68d`**, both hosts, identical to `docs/index.html` (§3/D4). Any asset quoting the old size or hash is quoting the pre-fix page. |
| **R17** | **Benchmark `mem20-agent-kb-v1`: 14 grounded / 3 simulated / 13 queries; "adversarial 0.000 in hybrid, keyword AND semantic, n=3"; "direct 1.000 / multi-hop 0.800"; "rerank on/off: p50 101.4 ms vs 15.7 ms"** | **RETIRED — the shipped benchmark was replaced** | **`mem20-scale-corpus-v2`: 700 / 1,300 / 250.** Scored modes are `keyword` and `semantic` **only**; `hybrid` and `graph` have **no rows**; the adversarial class splits into `adversarial` + `adversarial_hard`; `contradiction` is new; `trust.rerank_off_comparison` is **null**. Every figure in this row is unsupported by the file that ships today (§5). |
| **R18** | **"adversarial 0.000 is a product-wide result"** | **CORRECTED — it is mode-specific** | `semantic` scores **0.950** (`adversarial`) and **0.900** (`adversarial_hard`); `keyword` scores **0.000** on `adversarial_hard` and **0.050** on `contradiction`. Quote the mode with the number, always (§0). |
| **R19** | **"`aiohttp` is missing from `requirements.txt`; install is incomplete; PR #118 is the pending fix"** | **RETIRED — CLOSED** | `requirements.txt` pins eight packages including `aiohttp>=3.14.5` and `mcp-types>=2.3.0`; a clean install boots the server (`TOOL_COUNT: 270`, `RESULT: PASS`). See §3/D2b. |
| **R20** | **"`docs/index.html` still says 268 / 26 domains"** | **RETIRED — FIXED** | Measured this run: **270 × 10**, **27 domains × 8**, retired pair **× 0**. The `docs/index.html` drift row in `docs/gtm/README.md` and `docs/gtm/mem20-campaign-plan.md` §8 must be closed, not re-reported. |
| **R21** | **"`open_issues_count = 16`, `open_issues = 9`"** | **RETIRED** | **`open_issues_count = 1`** at this HEAD (§1/V1). |
| **R22** | **"Version 3.0.0" as the current version** | **RETIRED** | **3.1.0** on `main` (§1/V4). 3.0.0 survives only as the `pyproject.toml` value and as the previous tag — both named as defects, not quoted as current. |

---

## 8. Guardrails (binding on every public asset in this directory)

1. **270 tools across 27 domains.** No 257, 258 or 268 in a live claim — those exist only in §7.
2. **No PyPI implication of any kind.** No `pip install mem20`, no PyPI badge, no "coming soon on PyPI". Install is `git clone` + `pip install -r requirements.txt`, which is now complete (§3/D2b) **but builds a wheel labelled 3.0.0** — do not imply a 3.1.0 artifact.
3. **No `/sites/` URL in any public asset.** The public web surfaces are `https://mem20.com` and `https://bythewayz66-glitch.github.io/mem20/` — both md5-proven identical to the committed `docs/index.html`.
4. **The `Adversarial` column is mandatory and may not be blank** (§0.5). Any claim table shipped in an asset carries it. A row with an empty caveat cell is not shippable.
5. **Retrieval weakness is disclosed in every asset that cites any retrieval number** — `keyword` 0.000 on `adversarial_hard` and 0.050 on `contradiction`, `semantic` materially stronger on the same classes, `hybrid`/`graph` unmeasured. §0 is the wording of record.
6. **No LoCoMo / LongMemEval / DMR claim, and no cross-vendor benchmark comparison.**
7. **Promotion gate described with its residual free-text path** (PG4) as *"evidence-based with an append-only audit trail that records when evidence was absent."* Never *tamper-proof*, *unfakeable*, *airtight*, *provably secure*.
8. **House numbers carry the "house number, not a new measurement" qualifier** (§6).
9. **Banned phrases:** *provably secure · tamper-proof memory · unfakeable · industry-leading retrieval · best-in-class retrieval · matches Mem0 · beats Zep · 0.0 leak rate (as a retrieval or security claim) · 65 distinct implementations · 257 tools · 268 tools · 258 tools · 13-query corpus · 14-fact corpus · "0.000 in all three modes"*.
10. **Every number in a published asset appears in this ledger.** If it is not here, it does not ship.
11. **Never quote a benchmark row without its mode and its `n`.** "0.000 adversarial" alone is a false statement in both directions: it is wrong for `semantic` and it hides that `keyword`'s 0.000 is on `adversarial_hard` (n=40), not `adversarial` (n=60, where keyword scores 1.000).

---

## 9. Say / never say

A sales room compresses the ledger into sentences. These are the sentences.

| Say | Never say | Adversarial |
|---|---|---|
| "270 tools across 27 domains, over MCP." | "Over 250 tools." / "257 tools." / "268 tools." | `n/a: surface claim` |
| "Grounded and simulated memory are separate stores, enforced at the write path — the grounded write function refuses simulated content outright." | "The model is prompted not to mix them." | `n/a: write-path claim` |
| "Contamination rate 0.0 on a clean store, across six violation classes, and the audit is append-only." | "Provably secure." / "Tamper-proof." | `n/a: separation claim` |
| "Our weakest retrieval row is keyword mode on hard adversarial queries: 0.000 at n=40, and 0.05 on contradictions. Semantic mode scores 0.90 and 1.00 on the same classes. We publish both." | "Strong retrieval across all query types." / "Adversarial is 0.000 in every mode." | `0.000` |
| "On a 700-fact corpus: keyword direct 1.000 / multi-hop 0.800; semantic direct 0.900 / multi-hop 1.000. Not comparable to vendor benchmarks." | "Beats Mem0 on LoCoMo." / quoting a hybrid or graph score | `0.000` |
| "Hybrid and graph retrieval exist in the harness; our committed benchmark did not score them. We don't have a number for those, and we won't quote one." | Presenting a hybrid or graph number, or omitting that they were unscored | `unmeasured` |
| "Promotion requires evidence, and the ledger records when evidence was absent (`evidence_hash: null`)." | "The promotion gate cannot be bypassed." | `n/a: promotion claim` |
| "MIT-licensed, self-hostable, source install, no lock-in. Version 3.1.0." | "Enterprise-ready." / "installable from PyPI" | `n/a: licensing claim` |
| "TAM $1.28B / SAM $282M / SOM $1.68M — house numbers, carried, not re-derived." | Presenting them as fresh market measurement. | `n/a: commercial claim` |

---

## 10. Hand-off

**Next seat: Data & Revenue Analytics Lead.** Input they need: §6 (H1–H5) plus §3/D4. With SOM fixed at $1.68M, blended ACV at $14,000, and **two** md5-proven public surfaces (`mem20.com` and `github.io` Pages, byte-identical at md5 `37246f8d13b0f6870faa913c0a44c68d`), they can instrument the funnel that actually exists — repo clone and star delta, Pages sessions on either host — rather than a page anonymous readers cannot load. Any `/sites/`-based analytics spec is retired with §7/R5.

**Second hand-off, blocking every launch asset: the benchmark rewrite.** §7/R17 and §7/R18 are the largest blast radius in this document. `docs/gtm/mem20-launch-copy.md` and `docs/gtm/mem20-sales-one-pager.md` still carry the retired 13-query / 14-fact / "0.000 in every mode" figures in their benchmark blocks. **Owner: Brand & Positioning Strategist** — those are copy surgery against §5, and they must land before any asset quoting a retrieval number ships.

**Third hand-off, P1 documentation:** §1's drift table names two files (`docs/02-tools-reference.md`, `docs/05-complete-tools-reference.md`) that still print the retired tool/domain pair while their own stated method returns 270. Owner: GitHub Repo Assistant (roster item #10 lane).

**Fourth hand-off, packaging defect:** §1.1. `pyproject.toml` says 3.0.0 on a 3.1.0 trunk, and `VERSION` was rolled back to 3.1.0 by the `v3.1.0` release commit while a `v3.1.1` tag exists. Any `pip install .` today produces a mislabelled artifact. Owner: release engineering, not GTM.

**Coordination note (H2):** `docs/ws1-retire-jaysonai-hostname` touches three lines in this directory (`docs/gtm/README.md`, `docs/gtm/claim-ledger.md` D5/R8, `docs/gtm/mem20-campaign-plan.md` §8 item 2). This branch rebases on `main` at `f1672473` and **does not duplicate** H2's retire-the-hostname edit in `README.md` or in the campaign plan. In this ledger the retired hostname simply does not appear — v6 was authored without it, so H2's ledger hunk will be a no-op here rather than a conflict.

**Standing rule for whoever edits this file next:** re-measure, do not inherit. The tool surface, the benchmark corpus, the violation-class count, the CNAME host, the `homepage` field, the `aiohttp` fix state, the `docs/index.html` count and now the **version string** have all changed at least once between pulls. Every number above carries the command that produced it; run the command.
