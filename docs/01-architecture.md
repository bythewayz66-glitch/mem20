# mem20 MCP Server — Architecture Overview

> **Version:** 2.1-rc2
> **License:** MIT
> **Author:** JaysonAIOnline

## What is mem20?

**mem20** is a **persistent memory + cognition substrate for AI agents**. It gives your AI agent:

- **Persistent memory** that survives across sessions, with hybrid retrieval (vector + BM25 + cross-encoder reranking)
- **Strict separation** of grounded facts from imagined/hypothetical ones
- **Cognitive operations** — reasoning, planning, reflection, working memory
- **World modeling** — define variables, record predictions, resolve against observed outcomes
- **Self-modeling** — track beliefs, values, emotions, goals
- **Multi-agent coordination** — A2A communication, shared namespaces
- **3D workflow automation** — optional Blender and Unity integration

## System Architecture

```
                        ┌──────────────────────────────────────────┐
   MCP client  --stdio─▶│  mcp/mcp_server.py  (Mem20MCPServer)     │
   (Hermes, Claude,      │  JSON-RPC 2.0 · 257 tools · 26 domains  │
    any MCP host)        └───────────────┬──────────────────────────┘
                                         │ calls
                 ┌───────────────────────┼─────────────────────────┐
                 ▼                        ▼                         ▼
        cog/cognitive_engine.py    mem20/mem (store)         roadmaps/*.json
        (plan/chain/reason/        memory.py engine:          (roadmap registry)
         reflect/working memory)   grounded vs simulated,
                                   vector + BM25 indexes,
                                   append-only ledger)
```

### Transport / Protocol

- **MCP server** (`mcp` package) speaking JSON-RPC 2.0 over stdio
- `Mem20MCPServer` (in `server.py`) aggregates per-domain mixin classes and dispatches in `_execute_tool()`
- Tool schemas + handlers live in per-domain modules:
  - `memory_tools.py` — 39 tools (core memory + self-model)
  - `tools/enhanced_memory_tools.py` — 13 tools (extended memory)
  - `cognitive_tools.py` — 18 tools (cognitive, imagination, theory-of-mind, corrigibility)
  - `roadmap_tools.py` — 4 tools (roadmap registry)
  - `tools/world_tools.py` — 14 tools (world model + affective)
  - `tools/procedural_tools.py` — 6 tools (procedural skill library)
  - `tools/blender_tools.py` — 7 tools (OPTIONAL Blender)
  - `tools/unity_tools.py` — 5 tools (OPTIONAL Unity)
  - `tools/a2a_tools.py` — 5 tools (agent-to-agent)
  - `tools/thought_process.py` — 9 tools (ToT, Reflexion, ReAct, etc.)
  - `tools/integration_tools.py` — 3 tools (filesystem)
  - the remaining `tools/*.py` domains (braid, cloud, cloudstorage, communication, database, design, dev, finance, irc, job, marketing, productivity, search, version-control, webscraping) — 119 tools

### Memory Engine (`memory.py`)

The durable memory engine lives on `MEM20_STORE_PATH` (default `~/.mem20/store`). It owns:

- **Ledger** — append-only operation log with origin/store tags
- **Vector index** — SentenceTransformer embeddings (grounded-only)
- **BM25 corpus** — keyword search (grounded-only)
- **Deep store** — markdown files with epistemic status headers
- **Simulated partition** — separate storage for hypotheticals

### Cognitive Engine (`cog/cognitive_engine.py`)

Wraps an OpenAI-compatible LLM (`llm.py`) to provide:

- Thought processing
- Reasoning chains
- Structured reasoning (deductive, inductive, abductive, analogical, causal)
- Hierarchical planning (`plan`/`aplan`)
- Reflection
- Working memory

### Memory Model — Two Partitions

| Partition | What it holds | Indexed? | Promotion path |
|-----------|---------------|----------|----------------|
| **Grounded** | Real observations, user statements, events | Yes (vector + BM25) | — |
| **Simulated** | Hypotheticals, counterfactuals, model output | No | Evidence-based only |

### Hard Invariants (enforced by store engine)

1. **Indexes are grounded-only** — simulated records reaching vector/BM25 indexes raise immediately
2. **`remember()` is grounded-only by default** — simulated content uses its own path
3. **Append-only ledger with validated tags** — every entry carries `origin` and `store`
4. **Promotion is evidence-based** — requires `prediction_error_evidence` or external verifier
5. **Epistemic status is authoritative** — stamped directly onto the record

### Store Layout

```
store/
  memory.py                 # the engine
  ledger.jsonl              # append-only operation log
  embeddings.npy / index    # vector index (grounded only)
  bm25_corpus.json          # BM25 corpus (grounded only)
  records/<id>.md           # deep-store markdown
  simulated/                # simulated partition (never indexed)
```

### Governance & Contamination Controls

- **Contamination guards** — `_assert_grounded()` at write paths
- **Origin/store assertion** — `_validate_partition_tags()` at ledger append
- **Epistemic veto** — `require_epistemic_clearance()` + plan-execution guard
- **Audit** — `memory_audit_contamination()` returns `contamination_rate`, `violations`
- **Prediction ledger** — couples forecasts to observed outcomes

### Tool Domains (26 domains, 257 tools)

Counts obtained by instantiating `Mem20MCPServer` and counting `server.tools`.

| Prefix | Domain | Count |
|--------|--------|-------|
| `memory_*` | Core memory | 49 |
| `cog_*` / `tot_*` / substrate | Cognitive processing | 15 |
| `world_model_*` | World forecasting | 9 |
| `vcs_*` | Version control | 11 |
| `cloud_*` | Cloud control planes | 10 |
| `db_*` | Databases | 10 |
| `prod_*` | Productivity | 10 |
| `fs_*` | Sandboxed filesystem | 13 |
| `braid_*` | Content-addressed ledger | 9 |
| `comm_*` | Messaging | 9 |
| `dev_*` | Development | 9 |
| `mkt_*` | Marketing | 9 |
| `scrape_*` | Web scraping | 8 |
| `cloudstorage_*` | Object storage | 8 |
| `design_*` | Design | 8 |
| `fin_*` | Finance | 8 |
| `blender_*` | Blender automation | 7 |
| `search_*` | Search | 7 |
| `affective_*` | Values, emotions, goals | 6 |
| `procedural_*` | Skill library | 6 |
| `a2a_*` | Agent-to-agent communication | 5 |
| `irc_*` | Shared channel | 5 |
| `unity_*` | Unity automation | 5 |
| `imagination_*` | Counterfactual simulation | 8 |
| `roadmap_*` | Roadmap registry | 4 |
| `self_model_*` | Agent self-model | 3 |
| `corrigibility_*` | Shutdown / capability tiers | 2 |
| `theory_of_mind_*` | Perspective simulation | 2 |
| `job_*` | Background jobs | 2 |

### Health & Observability

The server exposes an HTTP health endpoint on `:8080`:

- `/health` — `{"status":"ok", ...}`
- `/ready` — readiness probe
- `/metrics` — tool counters, contamination_rate, event taxonomy

### Deployment Options

1. **pip** — `pip install .` → `mem20-mcp` command
2. **Docker** — `docker run -p 8080:8080 -v mem20-store:/data mem20`
3. **systemd** — `sudo ./install.sh --user $USER --dir /opt/mem20`
4. **apt (.deb)** — `sudo dpkg -i mem20_*.deb`

### Connecting MCP Hosts

```bash
# Hermes Agent
hermes config set mcp.servers.mem20 '["python3", "/path/to/mem20/mcp/mcp_server.py"]'

# Claude Code / Cursor
claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py
```