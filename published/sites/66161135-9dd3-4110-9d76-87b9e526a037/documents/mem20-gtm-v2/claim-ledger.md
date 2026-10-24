# mem20 — GTM Claim Verification Ledger (v2)

**Owner:** mem20 GTM Team Lead · **Seat:** Brand & Positioning Strategist / Opportunity & Market Analyst
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **HEAD:** `c274404` · **Branch:** `main`
**Verified:** 2026-10-14 · **Method:** every claim traced to a file, a command, or a captured run in the canonical clone (`/workspace/mem20`, 9,874 tracked files).

> **Why this exists.** The v1 GTM assets were written against the *old* repo pointer (`JaysonAIOnline/mem20`, which is a 404) and carried a benchmark table that **has no source in the shipped repository at this HEAD**. This ledger records what is verifiable, what was reworded, and what was withdrawn — so no public asset repeats an unbacked number.

---

## 1. Verified product facts (carry these into every asset)

| # | Claim | Verified value | Evidence |
|---|-------|---------------|----------|
| V1 | Repository | `github.com/bythewayz66-glitch/mem20` | GitHub API: public, `default_branch=main`, `license=MIT`, `pushed_at=2026-10-14T16:39:03Z` |
| V2 | HEAD commit | `c274404` | `git log -1` in clone |
| V3 | Tracked files | **9,874** | `git ls-files | wc -l` |
| V4 | Version | **2.1.0rc2** | `pyproject.toml` |
| V5 | License | **MIT** | `LICENSE` + GitHub API SPDX `MIT` |
| V6 | Python floor | **>=3.10** | `pyproject.toml` `requires-python` |
| V7 | MCP tool surface | **268 tools** | three independent counts agree: README §"Tool domains" ("verified by instantiating the server and counting `server.tools`"); `grep -rhoE 'self\.tools\[' mcp/ | wc -l` = 268; `toolchest/inventory.json` `counts.mcp` = 268 |
| V8 | Tool domains | **26** | 26 distinct `register_*_tools` mixins under `mcp/`; README domain table has 26 rows |
| V9 | Native subsystem packages | **293** `mem20*z` packages | `ls -d mem20*z | wc -l` = 293 |
| V10 | Sitemap estate index | **326 subsystems · 8,969 files · 468,134 code lines** | `.sitemap/sitemap.json` `totals` (generated 2026-10-03) |
| V11 | Transport | JSON-RPC 2.0 over **stdio**; `MEM20_TRANSPORT=http` for Streamable HTTP | `mcp/server.py:1048` |
| V12 | Health surface | `/health`, `/ready`, `/metrics` | `mcp/health.py`, README |
| V13 | Embedder | `sentence-transformers/all-MiniLM-L6-v2`, 384-dim | `memory_engine/memory.py:406-407` |
| V14 | Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `memory_engine/memory.py:80` |
| V15 | Simulated TTL | 30 days (`MEM20_SIM_TTL_DAYS`) | `memory_engine/memory.py:111` |

---

## 2. Live partition + audit evidence (captured run, HEAD `c274404`)

Harness: `gtm_assets/verify/partition_demo.py` → `partition_demo_output.json`. Throwaway store, `MEM20_TRANSPORT=stdio`.

| # | Check | Captured result | Verdict |
|---|-------|----------------|---------|
| A1 | Grounded write | `origin=grounded, store=grounded, action=remember` | ✅ verified |
| A2 | `remember(..., _allow_simulated=True)` | `PermissionError: remember() is grounded-only. Simulated content must use remember_simulated(); this call is refused to protect Step 7.4 separation.` | ✅ verified |
| A3 | `remember_simulated(...)` | `origin=simulated, store=simulated, epistemic_status=imagined, action=simulate` | ✅ verified |
| A4 | `recall()` default | 1 result, origins `[grounded]` only | ✅ verified |
| A5 | `recall(include_simulated=True)` | 2 results, origins `[grounded, simulated]` | ✅ verified |
| A6 | `audit_contamination()` | `contamination_rate=0.0`, `status=CLEAN`, **3** violation classes present and all empty | ✅ verified — **structure differs, see C8** |
| A7 | Promotion gate — bare | `PermissionError: Promotion blocked: requires explicit external confirmation OR real-world prediction-error resolution` | ✅ refused |
| A8 | Promotion gate — prediction-error boolean only | `PermissionError: ... requires structured evidence linking to a recorded prior prediction` | ✅ refused |
| A9 | Promotion gate — structured but unrecorded `prediction_ref` | `PermissionError: prediction_ref ... is not a recorded prior prediction` | ✅ refused |
| A10 | Promotion gate — **free-text `confirmation` alone** | `promoted: true` | ⚠️ **PROMOTES** — the gate is narrowed, not closed. See C9. |

**The strongest sales asset in the repo is A2's exact exception string.** Quote it verbatim.

---

## 3. Corrections applied to the v1 GTM assets

| # | v1 claim | Status | Correction | Evidence |
|---|----------|--------|-----------|----------|
| C1 | Repo `JaysonAIOnline/mem20` | **REPLACED** | `bythewayz66-glitch/mem20` | `JaysonAIOnline/mem20` = 404; canonical is `bythewayz66-glitch/mem20` |
| C2 | "~258–260 tools across 26 domains" | **REWORDED** | "268 tools across 26 domains" | V7, V8 |
| C3 | "26 domains" | **VERIFIED, unchanged** | keep | V8 |
| C4 | Domain list includes "revocation" | **REMOVED** | not one of the 26 domains in the README table | README §"Tool domains (26)" |
| C5 | "hit rate 1.000 direct / 0.800 multi-hop / 0.000 adversarial" | **WITHDRAWN** | no such numbers anywhere in the repo at this HEAD; `benchmarks/results/` does not exist | repo-wide grep for `hit_rate`/`adversarial`+`rate`; no `benchmarks/` dir |
| C6 | "leak rate 0.000" / "0.0 leak rate on clean stores" | **WITHDRAWN as a benchmark** | the only verifiable version is the live audit A6: `contamination_rate 0.0` on a clean throwaway store — present it as a *captured audit output*, not a published benchmark | A6 |
| C7 | Clone-audit: "65 distinct implementations of 293; 228 byte-identical clones" | **WITHDRAWN** | no `PROOF.md`, `bench/clone_audit.json` or `UPGRADE.md` in the canonical repo at this HEAD | `find` for those paths returns nothing |
| C8 | "six violation classes" in the audit | **REWORDED** | **three** violation classes at this HEAD: `violations_origin_not_grounded`, `violations_simulated_in_bm25_corpus`, `violations_simulated_in_grounded_index` | A6 `all_keys` |
| C9 | "evidence-based promotion" as an absolute | **QUALIFIED** | say "evidence-based with an append-only audit trail **and a documented residual free-text path**" — a free-text confirmation still promotes (A10). Never imply the gate refuses self-attestation. | A10 |
| C10 | Subsystem framing "303 / 327 / 301 organs" | **REWORDED** | "293 `mem20*z` packages; the sitemap indexes 326 subsystems" | V9, V10 |
| C11 | — (new, citable) | **ADDED** | self-audit proof at `proof/audit_response.md`: dynamic `eval()` on world-model rules replaced with an AST-restricted evaluator; MCP monolith decomposed into per-domain modules | `proof/audit_response.md` |

### Honesty note on V7 (it cuts both ways)

The 268-tool figure is the README's own headline. The in-tree audit at `proof/audit_response.md` describes the **pre-split** server as "~4,848 lines, **97 tools, 13 domains**" and records 97 registrations after decomposition. The repo therefore contains **97→268** as its own growth story. Cite 268 (the shipped surface, corroborated twice) and, if a reader challenges it, the honest answer is the same README text the ledger cites — not a different number invented to win the point.

---

## 4. In-repo drift the GTM assets should NOT propagate

These are internal-repo consistency problems. They are **not** GTM claims, but any developer who opens the docs will hit them — flag them, do not repeat them.

| Where | Problem | Count |
|-------|---------|-------|
| `README.md` lines 9, 10, 186, 203, 472 | still point at `JaysonAIOnline/mem20` (dead 404) | **6 refs** |
| `README.md` line 78 | `JaysonAIOnline/oreo` satellite link | 1 ref |
| `docs/README.md` lines 5, 6, 64, 117, 119 | old repo | **5 refs** |
| `docs/03-installation.md` lines 38, 65 | old clone URL | **2 refs** |
| `docs/05-complete-tools-reference.md` lines 3725, 3750, 4376 | old repo in examples | 3 refs |
| `docs/01-architecture.md` line 24, 107 + `docs/02-tools-reference.md` line 3 | still say **"111 tools / 15 domains"** vs README's 268 / 26 | **3 docs** |

**Total stale `JaysonAIOnline` references in shipped top-level docs: 17.** A `README.md` badge and Quick Start that 404 on `git clone` is the single highest-impact fix — it is the first command a launch reader runs.

---

## 5. Guardrails (unchanged, still binding)

- **No LoCoMo / LongMemEval / DMR claim.** There is not even a mem20-native benchmark result in the repo at this HEAD (C5/C6), so the no-comparison rule is now a no-number rule.
- Competitor figures (Mem0 LoCoMo 92.5, Zep DMR 94.8%, Letta 74.0%) are **third-party vendor self-reported** — cite as such and never as a baseline mem20 is measured against.
- **Describe promotion as "evidence-based with an append-only audit trail"** — never "tamper-proof", "unfakeable", "provably secure".
- **State the residual free-text path** wherever the promotion gate is described in detail (C9).
- Banned phrases: *provably secure, tamper-proof memory, matches Mem0, beats Zep, industry-leading retrieval, 0.0 leak rate (as a benchmark), 65 distinct implementations*.
- **`pip install mem20` is not published on PyPI.** The install path is `git clone` + `pip install .` from source. Do not print a PyPI one-liner.

---

## 6. Hand-off

Every asset in this directory is now consistent with this ledger. The **one** seat that must act next on the publishing leg is **Server Builder** — the Sidney/gabe ssh/sftp/rsync publish is not runnable from this sandbox (no SSH keys, `sidney`/`gabe` do not resolve). A publish packet with the exact manifest and commands is in `mem20-sidney-publish-packet.md`.
