# mem20 C++ SDK — Source / Claim Ledger

Every factual statement in these SDK docs is mapped to a path in the canonical mem20
repository plus the pinned commit. Nothing here is inferred from memory or from a
previous repo location.

**Canonical repository:** https://github.com/bythewayz66-glitch/mem20
**Branch:** `main`
**Pinned commit:** `c274404a116f203b0ed99ab7156e3752f0953ea8`
("docs: designate canonical repository and record full-codebase publication", 2026-10-14)
**Base snapshot commit:** `64c73359f3f7602b350b29d81c82630a86e01c5d`
**License:** MIT

> Re-verify with:
> ```bash
> git clone https://github.com/bythewayz66-glitch/mem20.git && cd mem20
> git rev-parse HEAD
> ```

---

## 1. Server facts

| # | Claim | Source path | Verified by |
|---|---|---|---|
| S1 | Canonical repo URL is `github.com/bythewayz66-glitch/mem20`, branch `main`, MIT | `CANONICAL.md`, `LICENSE` | file read |
| S2 | `JaysonAIOnline/mem20` is **not** canonical (absent / historical) | `CANONICAL.md` § Canonical designation (`JaysonAIOnline/mcp-cognitive-substrate` "earlier, much smaller … Historical / reference only") | file read |
| S3 | Package name/version is `mem20` **2.1.0rc2**, `requires-python >=3.10` | `pyproject.toml` (`[project] name/version/requires-python`) | file read |
| S4 | Runtime deps: `mcp>=2.1.1`, `pydantic>=2.13.4`, `anyio>=4.14.2`, `numpy>=1.24`, `faiss-cpu>=1.7.4`, `sentence-transformers>=2.2.0` | `requirements.txt`, `pyproject.toml` | file read |
| S5 | Canonical entry point is the script `mcp/mcp_server.py` (thin shim → `server.py:main`) | `mcp/mcp_server.py` (`from server import main`) | file read |
| S6 | `mcp/` is a *script directory*, not an importable package (no `__init__.py`) | `README.md` § Transport/protocol; `launcher.py` docstring | file read |
| S7 | `mem20-mcp` console script is equivalent, via `launcher.py` (runpy) | `pyproject.toml` `[project.scripts]`; `launcher.py` | file read |
| S8 | Server speaks **JSON-RPC 2.0 over stdio** | `README.md` § Transport/protocol; `mcp/server.py` `stdio_server()` | file read |
| S9 | Optional Streamable HTTP + SSE: `StreamableHTTPSessionManager` mounted at `/` under uvicorn; `POST initialize` / `GET SSE` both under `/` | `mcp/server.py` (HTTP branch) + inline comment | file read |
| S10 | Health/observability on port **8080**: `/health`, `/ready`, `/metrics` (`MEM20_HEALTH_PORT`) | `README.md` § features + quick start; `docs/03-installation.md` | file read |
| S11 | Store location env var `MEM20_STORE_PATH` (default `~/.mem20/store`) | `README.md` § Memory layer; `docs/03-installation.md` env table | file read |

## 2. Protocol / MCP wiring

| # | Claim | Source path | Verified by |
|---|---|---|---|
| P1 | Tools are registered/dispatched through `on_list_tools` / `on_call_tool` | `mcp/server.py` (`self._handle_list_tools`, `self._handle_call_tool`) | file read |
| P2 | `tools/list` handler accepts `PaginatedRequestParams`, returns `ListToolsResult` | `mcp/server.py` `_handle_list_tools` signature | file read |
| P3 | `tools/call` handler accepts `CallToolRequestParams`, returns `CallToolResult` | `mcp/server.py` `_handle_call_tool` signature | file read |
| P4 | Dispatch is by tool name via `_execute_tool()` | `README.md` § Transport/protocol | file read |
| P5 | `protocolVersion` is negotiated in `initialize` (server supplies its own init options) | `mcp/server.py` `self.server.create_initialization_options()` | file read |
| P6 | The SDK must not hard-code a `protocolVersion` | derived from P5 | design rule |

## 3. Tool surface

| # | Claim | Source path | Verified by |
|---|---|---|---|
| T1 | The surface is **257 tools across 26 domains** | `README.md` § Transport/protocol ("exposes **257 tools across 26 domains** (verified by instantiating the server and counting `server.tools`)") | file read |
| T2 | Domain counts: `memory_*` 52, `cog_*`/`tot_*`/… 18, `world_model_*` 15, `vcs_*` 11, `cloud_*` 10, `db_*` 10, `prod_*` 10, `fs_*` 10, `braid_*` 9, … `blender_*` 7 (optional), `unity_*` 5 (optional) | `README.md` § Tool domains (26) table | file read |
| T3 | Server tool modules: `mcp/memory_tools.py`, `enhanced_memory_tools.py`, `cognitive_tools.py`, `thought_process.py`, `roadmap_tools.py`, `tools/world_tools.py`, `tools/braid_tools.py`, `tools/blender_tools.py`, `tools/unity_tools.py`, `tools/integration_tools.py` | `README.md` § Transport/protocol | file read |

## 4. Tools the SDK binds to (name + schema verified in source)

| # | Tool | Partition / role | Source path |
|---|---|---|---|
| M1 | `memory_store` — `content` (req), `category` ∈ {user_pref, project, tool, general} default general, `tags` (comma-separated) | grounded write | `mcp/memory_tools.py` (`self.tools["memory_store"]`) |
| M2 | `memory_recall` — `query` (req), `category`, `limit` (1..50, default 10) | grounded recall | `mcp/memory_tools.py` (`self.tools["memory_recall"]`) |
| M3 | `memory_simulate_store` — `topic`, `content`, `tags[]`; "NEVER written to grounded memory or the semantic indexes" | simulated write | `mcp/memory_tools.py` (`self.tools["memory_simulate_store"]`) |
| M4 | `memory_list_simulated` — lists the simulated partition | simulated read | `mcp/memory_tools.py` |
| M5 | `memory_promote` — `sim_id` (req); gate: non-empty `confirmation` **or** `resolved_via_prediction_error=true` + `resolution_note`; else refused | promotion | `mcp/memory_tools.py` (`self.tools["memory_promote"]`, `_memory_promote`) |
| M6 | Promotion success text: `"PROMOTED -> grounded_id=<id>. <note>"`; refusal: `"VETO / BLOCKED: ..."` | result parsing | `mcp/memory_tools.py` `_memory_promote` |
| M7 | `memory_audit_contamination` — no params; detects high-confidence memory whose provenance is simulation, and simulated leakage | audit | `mcp/memory_tools.py` (`self.tools["memory_audit_contamination"]`) |
| M8 | `memory_set_epistemic_status` — `fact_id`, `status` ∈ {observed, inferred, imagined, user_stated, hypothesis, agent_generated} | epistemic stamping | `mcp/memory_tools.py` (`self.tools["memory_set_epistemic_status"]`) |

## 5. Memory model / invariants

| # | Claim | Source path | Verified by |
|---|---|---|---|
| I1 | Two partitions: **grounded** (real observations/user statements/events, indexed) and **simulated** (hypotheticals/counterfactuals/model output, not indexed) | `README.md` § Memory model; `docs/01-architecture.md` | file read |
| I2 | Indexes are grounded-only; `_assert_grounded()` guards `_add_to_vector_index()` / `_add_to_bm25_index()` | `README.md` § Hard invariants | file read |
| I3 | `remember()` is grounded-only by default (`_allow_simulated=False`) | `README.md` § Hard invariants | file read |
| I4 | **Append-only ledger with validated tags**; entries carry `origin` and `store`; `_validate_partition_tags()` rejects mismatches | `README.md` § Hard invariants; `ledger.jsonl` (real entries carry `origin`,`store`,`epistemic_status`) | file read |
| I5 | Promotion is **evidence-based** (`promote_simulated_to_grounded()` needs `prediction_error_evidence`) | `README.md` § Hard invariants; `mcp/memory_tools.py` `_memory_promote` | file read |
| I6 | `set_epistemic_status()` stamps status onto the original grounded ledger line + deep-store markdown header | `README.md` § Hard invariants | file read |
| I7 | Store layout: `memory.py`, `ledger.jsonl`, `embeddings.npy`/index, `bm25_corpus.json`, `records/<id>.md`, `simulated/` | `README.md` § Store layout | file read |

## 6. Benchmark claims (kept verbatim, adversarial row visible)

| # | Claim | Source | Note |
|---|---|---|---|
| B1 | Published hit rate **1.000** direct, **0.800** multi-hop, **0.000** adversarial; leak rate **0.000** | repo claim ledger (project-level published benchmarks) | cited **only** from the repo ledger; adversarial **0.000** kept visible |
| B2 | **No** third-party conversational-memory benchmark result is claimed or implied | — | the C++ SDK publishes no retrieval benchmark numbers |

> **Not found in the repo at the pinned commit:** a file literally named a "claim ledger"
> containing the B1 numbers (searched `*.md` for the strings; the only near-matches are
> unrelated, e.g. `mem20gamez/README.md` success-rate figures). B1 is therefore carried
> as a **project-level published** number per the project's own documentation, quoted
> **unchanged** and with the adversarial row intact — never restated as an SDK result.
> The SDK docs make no independent benchmark claim.

## 7. Language / phrasing rules applied

| Rule | Applied |
|---|---|
| Promotion described exactly as "evidence-based with an append-only audit trail" | yes — no security-guarantee phrasing appears |
| Banned security-guarantee / competitor-comparison phrasing excluded | yes (scanned) |
| Ledger never mutable/deletable via SDK API | yes — no such API exists in the headers |
| No fabricated tool names / protocol fields / server behaviour | yes — every tool name in §4 read from `mcp/memory_tools.py` |
| Adversarial 0.000 kept visible | yes (§6 B1) |
| No third-party conversational-memory benchmark claims | yes (§6 B2) |

---

## 8. Stale references corrected in this pass

The docs previously pointed at a repository that no longer resolves. Corrected in the
repo documentation itself:

| File | Old value | New value |
|---|---|---|
| `README.md` (badges ×2, clone URL ×2) | `JaysonAIOnline/mem20` | `bythewayz66-glitch/mem20` |
| `docs/README.md` (header, quick start, license link) | `JaysonAIOnline/mem20` | `bythewayz66-glitch/mem20` |
| `docs/03-installation.md` (clone URL ×2) | `JaysonAIOnline/mem20` | `bythewayz66-glitch/mem20` |
| `docs/05-complete-tools-reference.md` (`repo` ×2) | `JaysonAIOnline/mem20` | `bythewayz66-glitch/mem20` |
| `docs/01-architecture.md` (diagram + heading) | `111 tools · 15 domains` | `257 tools · 26 domains` |
| `docs/02-tools-reference.md` (intro) | "all 111 tools" | "all 257 tools" |
| `docs/README.md` (tools table + version) | "111 MCP tools"; version `2.1-rc2` | "257 MCP tools"; version `2.1.0rc2` |

Remaining `JaysonAIOnline/*` mentions are **intentional**: `CANONICAL.md` deliberately
lists those repos as *non-canonical / satellite* so readers know not to use them.

> `roadmaps/README.md` also contains a historical log line referencing the old
> `111 tools` figure and a `/home/jayson/mem20/...` path. It is a **historical roadmap
> note**, not a current claim, so it was left as-is rather than rewritten (rewriting
> history would falsify the record).
