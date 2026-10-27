# mem20 — GTM Claim Verification Ledger (v3)

**Owner:** mem20 GTM Team Lead · **Seat:** Brand & Positioning Strategist / Opportunity & Market Analyst
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **HEAD at capture:** `7c0b3e8d9525cd8c3a9f8f1825267aed52fac68a` · **Branch:** `main`
**Captured:** 2026-10-26 · **Method:** every claim below traced to a file, a command, or a captured run against the canonical clone.
**Supersedes:** claim ledger v2 (`published/sites/66161135-…/documents/mem20-gtm-v2/claim-ledger.md`, verified 2026-10-14 at HEAD `c274404`).

> **Why v3 exists.** Three things changed since v2 that invalidate parts of it: the tool surface moved (the repo now registers **270 tools across 27 domains**, not 268/26), the shipping/distribution state was re-measured (no package on PyPI, no public reachability on the `/sites/` CDN), and the canonical public URL changed to GitHub Pages. v3 is the source of truth for every asset in this directory.

---

## 1. Verified product facts

| # | Claim | Verified value | Evidence (run 2026-10-26) |
|---|-------|---------------|---------------------------|
| V1 | Canonical repo | `github.com/bythewayz66-glitch/mem20` | `git ls-remote …HEAD` resolves; GitHub API: `private=false`, `default_branch=main`, `license.spdx_id=MIT`, `pushed_at=2026-10-27T01:50:06Z`, `stargazers_count=1`, `forks_count=0` |
| V2 | HEAD commit | `7c0b3e8d9525cd8c3a9f8f1825267aed52fac68a` | `git log -1` — "chore(ops): record 2026-10-26 daily ops sweep findings + owner assignment roster" |
| V3 | Tracked files | **7,915** | `git ls-files \| wc -l`. Down from 9,874 at v2's HEAD `c274404` because 3.0.0 untracked generated output (`build/`, `__pycache__/`, `node_modules/`, `dashboard/dist/`, `*.egg-info`, `*.pyc`). **Not a capability loss** — see CHANGELOG 3.0.0. |
| V4 | Version | **3.0.0** | `pyproject.toml` `version = "3.0.0"`; `VERSION` file equals `3.0.0` |
| V5 | License | **MIT** | `LICENSE` line 1; GitHub API `license.spdx_id = "MIT"` |
| V6 | Python floor | **>=3.10** | `pyproject.toml` `requires-python = ">=3.10"` |
| **V7** | **MCP tool surface** | **270 tools** | **Three independent measures agree at this HEAD:** live handshake `verify_mcp.py` → `TOOL_COUNT: 270`; `grep -rhoE 'self\.tools\[' mcp/ --include="*.py" \| wc -l` = 272 raw literal hits / `270` unique quoted names; `docs/README.md` §"270 Tools Across 27 Domains" |
| **V8** | **Tool domains** | **27** | `sed -n '/def _setup_tools/,…/p' mcp/server.py \| grep -cE 'self\.register_[a-z_]+_tools\(\)'` = **27** (matches the 27: the mixin count and the doc count now agree — at v2's HEAD they did not) |
| V9 | Transport | JSON-RPC 2.0 over **stdio** (default); Streamable HTTP via `MEM20_TRANSPORT=http` on `MEM20_MCP_PORT` (8082) | `verify_mcp.py` handshake over stdio; `mcp/server.py` |
| V10 | Health surface | `/health`, `/ready`, `/metrics` | `mcp/health.py`; a bind conflict on :8080 degrades to a warning, not a failure (observed in the capture run) |
| V11 | Embedder | `sentence-transformers/all-MiniLM-L6-v2`, 384-dim | `memory_engine/memory.py` |
| V12 | Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2`, on by default, `MEM20_RERANK=0` opt-out | `memory_engine/memory.py`; `benchmarks/results/latest.md` |
| V13 | Hybrid retrieval | vector (`IndexFlatIP`) + BM25 (`BM25Okapi`), RRF fusion | `memory_engine/memory.py` `recall_hybrid()` |
| V14 | Epistemic status is **required** on write | `remember()` raises `ValueError` unless `epistemic_status` is one of `observed / inferred / imagined / user_stated / hypothesis / agent_generated / unlabeled` | `inspect.signature(M.remember)` + the refusal text; confirmed live at this HEAD |
| V15 | Issues enabled / Discussions disabled | `has_issues=true`, `has_discussions=false`, `has_wiki=true`, 9 open issues | GitHub API |

### Note on the 270 / 27 figure — what changed and who owns the number

The repo has carried **four different tool counts** across recent history: `257 / 26` (README + CHANGELOG 3.0.0), `258` (`toolchest/inventory.json`, generated 2026-10-07 — stale), `268 / 26` (README at v2's HEAD) and now **270 / 27**.

At this HEAD the live handshake is the authority and it says **270**, with **27** registered mixins agreeing. The deltas visible in `CHANGELOG.md [Unreleased]` explain two of them: the `memory_*` row was undercounted by 3 (listed 49 against 52 registered) and the **10 `lie_*` tools were missing from every table**. `docs/02-tools-reference.md` still says 268/26 and `toolchest/inventory.json` still says 258 — both are stale and the P1 owner (Webpage Developer) is retiring them.

**GTM rule: publish 270 / 27. Do not publish 257, 258 or 268.** If a reader challenges it, the answer is the command, not a different number: `python3 verify_mcp.py` → `TOOL_COUNT: 270`.

---

## 2. Distribution state (re-measured — this is what v2 got wrong)

| # | Question | Measured result | Consequence for GTM |
|---|---|---|---|
| **D1** | Is there a PyPI package? | **No.** `https://pypi.org/pypi/mem20/json` → **404**; `…/mem20-ai/json` → **404**; `…/mem20oreo/json` → **404** (all three checked 2026-10-26) | **Never print `pip install mem20`, `pip install mem20-ai`, or a PyPI badge.** Install is source-only. |
| **D2** | What *is* the install path? | `git clone https://github.com/bythewayz66-glitch/mem20.git` → `pip install -r requirements.txt`. `requirements.txt` ships at repo root (234 bytes, pins `mcp>=2.1.1`, `pydantic>=2.13.4`, `anyio>=4.14.2`, …). `pip install .` + `mem20-mcp` also works but is optional. | State the two-command source install. The `mcp>=2.1.1` pin matters — `mcp<2` boots to a misleading *"mcp package not installed"* error. |
| **D3** | Are `/sites/` CDN URLs publicly reachable? | **No — 403 to anonymous requests.** Verified with a token stripped, both on `static.teamily.ai/sites/f7c01331-…/mem20-launch-copy.md` and `…/202c2d28-…/mem20-orchestrator-status/index.html`. Same for the repo's own homepage field target `…/ca954f26-…/mem20-site/index.html` → **403**. | **Never publish, promote, or link a `/sites/` URL in public GTM.** They resolve only with a signed token. |
| **D4** | What is the canonical public URL? | **`https://bythewayz66-glitch.github.io/mem20/`** → **HTTP 200**, 40,727 bytes, **md5 `8a61d84d71030f8c10bacf8bcf262935` = byte-identical to `docs/index.html` at HEAD**. Served by `.github/workflows/pages.yml` (Actions source, `paths: docs/**`). | This is the only public web surface. Cite it. |
| **D5** | Does `mem20.jaysonai.online` resolve? | **No DNS record** (`getent hosts` empty; `curl` → `000`). `docs/CNAME` still names it. | Do not cite it. Flag as an ops item: with CNAME present and no DNS, Pages serves on `github.io` only — and `docs/CNAME` is a live misconfiguration for anyone who reads it. |
| **D6** | Any other stale public pointer? | Yes — the **GitHub repo `homepage` field** is set to a `/sites/` URL (`…/ca954f26-…/mem20-site/index.html`), i.e. a 403. | **Owner action, not GTM:** repoint `homepage` to the Pages URL. Every visitor who clicks it hits a 403 — the worst possible first impression for a trust-positioned product. |

---

## 3. Live partition + audit evidence (captured 2026-10-26, HEAD `7c0b3e8`)

Harness run against the canonical clone, throwaway store (`MEM20_STORE_PATH=/tmp/mem20-gtm-<ts>`), engine imported from the repo root.

| # | Check | Captured result | Verdict |
|---|-------|----------------|---------|
| A1 | Grounded write | accepted; `origin=grounded` | ✅ verified |
| **A2** | `remember(..., _allow_simulated=True)` | `PermissionError: remember() is grounded-only. Simulated content must use remember_simulated(); this call is refused to protect Step 7.4 separation.` | ✅ verified — **quote verbatim; strongest asset in the repo** |
| A3 | `remember_simulated(...)` | accepted; `origin=simulated` | ✅ verified |
| A4 | `recall()` default | origins `['grounded']` only | ✅ verified |
| A5 | `recall(include_simulated=True)` | origins `['simulated', 'grounded']` | ✅ verified |
| **A6** | `audit_contamination(actor=…)` | `contamination_rate: 0.0`, `status: "CLEAN"`; **6** violation classes returned, all empty: `violations_origin_not_grounded`, `violations_simulated_in_grounded_index`, `violations_simulated_in_bm25_corpus`, `violations_simulated_in_graph`, `violations_pinned_origin_not_grounded`, `violations_pinned_simulated_content` | ✅ verified — **6 classes, not 3.** v2 said 3 (true at `c274404`); the count moved. Read the audit's own keys, never assert a count from memory. |
| A7 | `epistemic_status` omitted | `ValueError` refusing an unlabeled write | ✅ verified hardening |

**Promotion gate — report the paths separately, never as one claim.** The gate is *narrowed, not closed*:

| Path | Behavior |
|---|---|
| Bare call (no evidence) | **refused** |
| Boolean `resolved_via_prediction_error=True` + free-text note | **refused** — demands structured evidence linking to a recorded prior prediction |
| Structured but unrecorded `prediction_ref` | **refused** — "not a recorded prior prediction" |
| **Free-text `confirmation` alone** | **PROMOTES** — residual path, still open |

**Do not** describe the gate as airtight, tamper-proof, unfakeable, or as refusing self-attestation. A reader who tests it will find the free-text path, and this product's entire positioning is that its numbers hold up under scrutiny.

---

## 4. House numbers (commercial)

| # | Metric | Value | Status / source |
|---|---|---|---|
| H1 | TAM | **$1.28B** | House number, restated in `CHANGELOG.md [Unreleased]` §"Note on house numbers" |
| H2 | SAM | **$282M** | Same |
| H3 | SOM | **$1.68M** | Same |
| H4 | Blended ACV | **$14,000** | Same |

**These are house numbers, not fresh measurements, and must be labelled as such.** `CHANGELOG.md` is explicit: *"The commercial figures are unchanged by this release and are deliberately not restated as new measurements."* Any asset quoting them carries the same qualifier. A derived sales target is arithmetic on top of them — show the division and label it an estimate, e.g. SOM ÷ ACV = 1.68M ÷ 14,000 = **120 accounts** to fully realise SOM.

---

## 5. What was withdrawn from v2, and the one thing it got wrong

| # | v2 said | v3 status | Correction |
|---|---|---|---|
| **C1** | 268 tools / 26 domains | **RETIRED** | **270 tools / 27 domains** (V7, V8). 268 survives only as a historical count. |
| **C2** | "three violation classes at this HEAD" | **CORRECTED** | **six** classes at `7c0b3e8` (A6). The key set is not stable across pulls. |
| **C3** | Launch page URL = a `static.teamily.ai/sites/…` link | **RETIRED — 403 anonymous** | Canonical public URL is `https://bythewayz66-glitch.github.io/mem20/` (D3, D4) |
| **C4** | "`pip install .`" as the install line | **TIGHTENED** | Primary install is `git clone` + `pip install -r requirements.txt` (D2). `pip install .` is optional. |
| **C5** | "no benchmark of any kind in the repo" | **RETIRED** | `benchmarks/results/latest.{md,json}` now ship on `main` (they did not at `c274404`). See §6 — quote them with their own warning attached. |
| C6 | Version 2.1.0rc2 | **RETIRED** | 3.0.0 (V4) |
| C7 | HEAD `c274404`, 9,874 files | **RETIRED** | `7c0b3e8`, 7,915 files (V2, V3) |
| C8 | Clone-audit "65 distinct implementations / 228 clones" | **STILL WITHDRAWN** | Do not use. Cite `proof/audit_response.md` (AST-restricted evaluator replacing a dynamic `eval()`; monolith split per-domain; structured logging still open) instead. |
| C9 | `JaysonAIOnline/mem20` | **STILL 404 — never cite** | Canonical is `bythewayz66-glitch/mem20` |
| C10 | README clone-URL defect (17 stale refs) | **RESOLVED in the repo** | Do not keep reporting it as a blocker. Re-grep before asserting. |

---

## 6. The benchmark table — publishable now, with its caveat welded on

The repo ships `benchmarks/results/latest.md` at this HEAD. Corpus `mem20-agent-kb-v1`: **14 grounded facts, 3 simulated facts, 13 queries.**

| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| `hybrid` | direct | 5 | 1.000 | 1.000 | 0.000 | 108.0 |
| `hybrid` | multi_hop | 5 | 0.800 | 0.640 | 0.000 | 105.1 |
| `hybrid` | **adversarial** | 3 | **0.000** | 0.000 | 0.000 | 102.0 |
| `semantic` | direct | 5 | 1.000 | 0.900 | 0.000 | 12.2 |
| `keyword` | direct | 5 | 1.000 | 1.000 | 0.000 | 103.3 |
| `graph` | multi_hop | 2 | 1.000 | 1.000 | 0.000 | 0.6 |

Trust block: contamination rate **0.0**, simulated records in BM25 corpus **[]**, stale pointer rate **0.000000**.

**Three rules bind this table, and all three are non-negotiable:**

1. **Carry the file's own warning.** Verbatim: *"These numbers are not comparable to competitor benchmarks… Nothing here refutes or reproduces them. These results describe this corpus only."*
2. **The adversarial 0.000 row stays visible.** It is a real weakness on a 3-query slice, and hiding it is exactly the move that gets a launch torn apart on HN. Lead with it.
3. **Never set it against Mem0's LoCoMo 92.5 / LongMemEval 94.4 or Zep's DMR 94.8%.** Those are vendor self-reported, on different corpora, under different metrics.

---

## 7. Guardrails (binding on every public asset in this directory)

1. **270 tools / 27 domains.** No 257, 258 or 268 in any public asset.
2. **No PyPI implication of any kind.** No `pip install mem20`, no PyPI badge, no "coming soon on PyPI". Install is `git clone` + `pip install -r requirements.txt`.
3. **No `/sites/` URL in any public asset.** The only public web surface is `https://bythewayz66-glitch.github.io/mem20/`.
4. **No LoCoMo / LongMemEval / DMR claim, and no cross-vendor benchmark comparison** (§6 rules 1–3).
5. **Promotion gate described with its residual free-text path**, as "evidence-based with an append-only audit trail". Never *tamper-proof*, *unfakeable*, *airtight*, *provably secure*.
6. **House numbers carry the "house number, not a new measurement" qualifier** (§4).
7. **Banned phrases:** *provably secure · tamper-proof memory · matches Mem0 · beats Zep · industry-leading retrieval · 0.0 leak rate (as a benchmark) · 65 distinct implementations · 257 tools · 268 tools*.
8. **Every number in a published asset appears in this ledger.** If it is not here, it does not ship.

---

## 8. Hand-off

The next seat to pick this up is the **Data & Revenue Analytics Lead**, and the input they need is §4 plus §2/D4: with SOM fixed at $1.68M, blended ACV at $14,000 and exactly one measurable public surface (Pages + the GitHub repo), they can instrument the funnel that actually exists — repo clone/star delta and Pages sessions by `utm_content` — instead of a page that anonymous readers cannot load. The `/sites/` analytics spec in campaign plan v2 must be retired with it.
