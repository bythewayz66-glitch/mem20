# §1–§2 — Verified product facts and the surface of record

Part 2 of 6. Index: `claim-ledger.md`. Measured at `2ea44922`.

## 1. Verified product facts

| # | Claim | Verified value | Status | Command (settles it) | Adversarial |
|---|-------|---------------|--------|----------------------|-------------|
| V1 | Canonical repo | `bythewayz66-glitch/mem20` — `private=false`, `default_branch=main`, `license.spdx_id=MIT`, `stargazers_count=1`, `forks_count=0`, `open_issues_count=0` | **VERIFIED** | `GITHUB_GET_A_REPOSITORY(owner="bythewayz66-glitch", repo="mem20")` | `n/a: repo identity` |
| V2 | HEAD commit | `2ea4492209dfaae6afb22ca884132a0d1849bfcf` — *"docs(bench): land four-mode retrieval benchmark results for 2026-10-31"*; `git describe` → `v3.1.0-62-g2ea44922` | **VERIFIED** | `git log -1 --format='%H %ad %s' --date=iso` | `n/a: commit identity` |
| V3 | Tracked files | **8,536** | **VERIFIED** | `git ls-tree -r --name-only HEAD \| wc -l` | `n/a: repo size` |
| V4 | Version | **3.1.0** — repo contradicts itself (`pyproject.toml` 3.0.0, highest tag v3.1.1) | **VERIFIED** | `cat VERSION; grep -E '^version' pyproject.toml; git tag --sort=-v:refname \| head -3` | `n/a: version string` |
| V5 | License | **MIT** | **VERIFIED** | `head -1 LICENSE; grep license pyproject.toml` | `n/a: licensing` |
| V6 | Python floor | **>=3.10** | **VERIFIED** | `grep requires-python pyproject.toml` | `n/a: runtime requirement` |
| **V7** | **MCP tool surface** | **270 tools** | **VERIFIED** | `python3 verify_mcp.py` → `TOOL_COUNT: 270`, `RESULT: PASS` | `n/a: counts tools, not retrieval quality` |
| **V8** | **Tool domains** | **27** | **VERIFIED** | `sed -n '/def _setup_tools/,/^    def /p' mcp/server.py \| grep -cE 'self\.register_[a-z_]+_tools\(\)'` → `27` | `n/a: counts domains, not retrieval quality` |
| V9 | Transport | JSON-RPC 2.0 over **stdio** (default); Streamable HTTP via `MEM20_TRANSPORT=http` on `MEM20_MCP_PORT` (8082) | **VERIFIED** | `python3 verify_mcp.py` (stdio handshake, `protocolVersion 2025-06-18`) | `n/a: transport mechanism` |
| V10 | Health surface | `/health`, `/ready`, `/metrics`; a :8080 bind conflict degrades to a warning, not a failure | **VERIFIED** | `python3 verify_mcp.py` — observed `WARNING mem20.mcp health endpoint disabled (could not bind :8080)` and still `RESULT: PASS` | `n/a: operational surface` |
| V11 | Embedder | `sentence-transformers/all-MiniLM-L6-v2`, 384-dim | **VERIFIED** | `python3 -c "import json;print(json.load(open('benchmarks/results/latest.json'))['environment'])"` | `0.000` — the embedder behind every `vector` row in §0 |
| V12 | Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2`, on by default, `MEM20_RERANK=0` opt-out | **VERIFIED** | `grep -n 'cross_encoder\|MEM20_RERANK' memory_engine/memory.py`; `latest.json` → `environment.cross_encoder: true` | `0.000` — rerank on/off is now a scored mode pair, §5.2 |
| V13 | Hybrid retrieval | vector (`IndexFlatIP`) + BM25 (`BM25Okapi`), RRF fusion at `alpha=0.5` | **VERIFIED** | `grep -n 'def recall_hybrid' memory_engine/memory.py`; `latest.json` → `recall.hybrid` | `0.000` — `hybrid` adversarial_hard **0.050** (§0) |
| V14 | `epistemic_status` **required** on write | `ValueError: remember() requires an explicit epistemic_status. Declare how this claim was learned; one of ['observed', 'inferred', 'imagined', 'user_stated', 'hypothesis', 'agent_generated', 'unlabeled']` | **VERIFIED** | `python3 docs/gtm/verify/partition.py` → A7 | `n/a: write-path guard` |
| V15 | Issues on / Discussions off | `has_issues=true`, `has_discussions=false`, `has_wiki=true`, `has_projects=true`, `has_pages=true` | **VERIFIED** | `GITHUB_GET_A_REPOSITORY(owner="bythewayz66-glitch", repo="mem20")` | `n/a: repo configuration` |
| V16 | Repository description | *"Memory substrate and agent runtime for AI systems that have to be trusted — grounded facts and simulated hypotheses never mix, and every retrieval call reports index drift instead of hiding it."* | **VERIFIED** | `GITHUB_GET_A_REPOSITORY(...)` → `description` | `0.000` — makes an implicit retrieval claim; the asset still carries §0 |
| V17 | Clone-audit artifacts ship | `PROOF.md`, `UPGRADE.md`, `bench/clone_audit.json` present; **293 packages / 65 distinct / 228 duplicates** in 3 groups (94×273, 93×683, 44×348 LOC) | **VERIFIED** | `python3 -c "import json;d=json.load(open('bench/clone_audit.json'));print(d['packages'],d['distinct_implementations'],d['duplicate_packages'])"` | `n/a: repo audit` |

### 1.1 The version row is a defect, not an ambiguity

| Ref | `VERSION` | `pyproject.toml` | Note |
|---|---|---|---|
| `52ffe13` (tag **v3.1.1**) | **3.1.1** | 3.0.0 | `VERSION` bumped; `pyproject.toml` missed |
| `73343f6` (tag **v3.1.0**) | **3.1.0** | 3.0.0 | release commit **reverted** `VERSION` 3.1.1 → 3.1.0 |
| `main` @ `2ea44922` | **3.1.0** | **3.0.0** | both stale vs the highest tag; `v3.1.1..main` = **63** commits |

**GTM says:** *"Version 3.1.0 — `VERSION` on `main` at `2ea44922`."* One command, true.
**GTM never says:** "3.1.1", "3.0.0", or "the PyPI release is 3.1.0" (no PyPI release — D1). If asked about `pyproject.toml`: *"it still reads 3.0.0; the tag and `VERSION` are ahead of it. A packaging defect, filed, not a capability difference."*
**Consequence:** `pip install .` builds an artifact labelled **3.0.0** regardless of tag. Never ship an install path implying a 3.1.0 wheel.

### 1.2 The 270 / 27 figure — four agreeing measures

| Source | Value | Command |
|---|---|---|
| Live handshake | **270** | `python3 verify_mcp.py` → `TOOL_COUNT: 270` |
| `grep` unique quoted names | **270** (272 raw literal hits) | `grep -rhoE 'self\.tools\[["'"'"'][a-z0-9_]+' mcp/ \| sort -u \| wc -l` |
| `docs/finance/inputs.json` | `tool_surface.tools = 270`, `domains = 27` | `python3 -c "import json;print(json.load(open('docs/finance/inputs.json'))['tool_surface'])"` |
| CI pin | `MEM20_EXPECTED_TOOLS: "270"` | `grep -rn MEM20_EXPECTED_TOOLS .github/workflows/` |

The verifier needs `mcp>=2.1.1`, `mcp-types`, `aiohttp`, `pydantic`, `numpy` and `pip install -e ./mem20api`; with those it passes from a full clone at this HEAD.

**Residual documentation drift, measured this run.**

| File | What it prints | Status | Command |
|---|---|---|---|
| `docs/02-tools-reference.md:3-4` | **270 tools across 27 domains** — **FIXED since v6** | **VERIFIED (clean)** | `sed -n '1,8p' docs/02-tools-reference.md` |
| `docs/05-complete-tools-reference.md` | **268 tools across 26 domains** at header `:3` and totals row `:4679` | **STALE — live P1 drift** | `grep -cE '\b268\b' docs/05-complete-tools-reference.md` → `5` |
| `docs/index.html` | 270 × 10, 27 domains × 8, retired pair × 1 (labelled "retired surface"), **`v3.0.0` × 4** | **STALE on version only** | `grep -n 'v3\.0\.0' docs/index.html` → lines 179, 486, 574, 604 |
| `README.md` | 270 × 6, 27 domains × 5, retired pair × 0 — but the benchmark block still quotes the retired 14-fact / 13-query corpus | **STALE on benchmark only** | `grep -n 'mem20-agent-kb-v1\|14 facts\|13 queries' README.md` → lines 99, 140 |
| `CHANGELOG.md` | 270/27 in `[Unreleased]`; 257/258/268 only as named prior values | **VERIFIED (historical)** | `grep -nE '\b(257\|258\|268)\b' CHANGELOG.md` |
| `toolchest/inventory.json` | `counts = {mcp: 0, cli: 2, subsystem: 310, total: 312}`, `generated_at = 2026-10-29T05:54:53Z` | **VERIFIED (no longer counts MCP tools)** | `python3 -c "import json;d=json.load(open('toolchest/inventory.json'));print(d['counts'],d['generated_at'])"` |

A documentation defect, not a product ambiguity — quote the verifier and name the drift rather than matching it.

---

## 2. The surface of record

| Field | Value | Status | Command |
|---|---|---|---|
| Tools | **270** | **VERIFIED** | `python3 verify_mcp.py` |
| Domains | **27** | **VERIFIED** | `sed -n '/def _setup_tools/,/^    def /p' mcp/server.py \| grep -cE 'self\.register_[a-z_]+_tools\(\)'` |
| Retired tool values | three superseded counts | **RETIRED** — enumerated only in §7 | `python3 docs/gtm/verify/check_ledger.py` |
| Retired domain value | one superseded count | **RETIRED** — enumerated only in §7 | `python3 docs/gtm/verify/check_ledger.py` |

**Binding:** any asset naming the surface names it **"270 tools across 27 domains."** No "~270", no "over 250". If challenged, the answer is §1.2's command.
