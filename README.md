<p align="center">
  <img src="https://img.shields.io/badge/mem20-v3.0.0-6366f1?style=for-the-badge&logo=github" alt="mem20 v3.0.0">
</p>
<p align="center">
  <strong>A memory substrate and agent runtime for AI systems that have to be trusted.</strong>
</p>
<p align="center">
  <a href="https://mem20.jaysonai.online"><img src="https://img.shields.io/badge/Website-mem20.jaysonai.online-FFD700?style=for-the-badge" alt="Website"></a>
  <a href="https://github.com/bythewayz66-glitch/mem20/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/bythewayz66-glitch/mem20/releases"><img src="https://img.shields.io/github/v/release/bythewayz66-glitch/mem20?style=for-the-badge" alt="Release"></a>
</p>

<p align="center">
  <a href="#what-this-is">What this is</a> · <a href="#the-honest-claim">The honest claim</a> · <a href="#benchmarks">Benchmarks</a> · <a href="#the-estate">The estate</a> · <a href="#quick-start">Quick start</a> · <a href="docs/">Docs</a>
</p>

---

**mem20 started as a memory store for AI agents. It is now the runtime those agents live in.**

The original idea — separate *grounded* facts from *simulated* ones and refuse to promote a hypothesis without evidence — is still enforced at the lowest append path and is still the thing that distinguishes mem20 from every other memory product. But that is one subsystem. Around it there are **301 organs**, **17 services**, **28 live systemd units**, an append-only cryptographic ledger in Rust, a dream engine with an eight-model critique panel, an IRC channel where agents coordinate with each other, a 3D modeler with procedural node graphs, a visual programming language, and a chat front-end with its own model gateway.

If you came here for a memory library, read [What this is](#what-this-is) and stop. If you came to see what an agent platform looks like when one person builds the whole stack, keep going.

---

## What this is

### The original: a memory substrate that cannot lie to itself

The store keeps two partitions that never mix.

**Grounded** memory holds facts from real observations, user statements, or events. **Simulated** memory holds counterfactuals, hypotheses, and model output. The separation is enforced in code, not by convention:

- `remember()` refuses any record not tagged `origin="grounded"`. An explicit `_allow_simulated=True` is *rejected on purpose*, so no future refactor can quietly route simulation through the grounded path.
- The vector and BM25 indexes call `_assert_grounded()` on every write. A simulated record reaching an index raises immediately rather than being caught later by an audit.
- Promotion from simulated to grounded requires evidence: either a prior prediction that resolved in the fact's favor, or attestation from a registered external verifier. A boolean flag and a free-text note are refused.
- `audit_contamination()` returns a `contamination_rate`. A clean store reports `0.0`.

[Mem0](https://github.com/mem0ai/mem0) reports LoCoMo 92.5 and LongMemEval 94.4. [Zep](https://github.com/getzep/zep) reports DMR 94.8%. Those are recall-quality numbers on their own corpora. mem20 publishes its own numbers — see [Benchmarks](#benchmarks) — including the ones nobody else reports.

### The retrieval layer

Four retrieval modes over the same store:

| Mode | What it does | When to use it |
|---|---|---|
| `recall()` | Reverse-chronological filter by topic and tags | You know the topic |
| `recall_semantic()` | Vector search over MiniLM embeddings, optional cross-encoder rerank | You remember the meaning, not the words |
| `recall_hybrid()` | Reciprocal Rank Fusion of vector + BM25, then rerank | Default. Best recall |
| `recall_graph()` | Multi-hop traversal over an entity/edge graph built at write time | "What is connected to X?" |

Every retrieval result carries a diagnostic. This is the difference from a normal vector store:

```python
from mem20api import open_store

with open_store() as store:
    r = store.semantic("what build is prod on")
    r["hits"]           # the results
    r["healthy"]        # False if the index has drifted from the ledger
    r["diagnostic"]     # exactly how many stale pointers exist
```

That is not decoration. Semantic retrieval on this repository's own live store was returning **zero results while reporting success**: the FAISS index held 2,681 vectors, the ledger held 371 records, and 2,312 index entries pointed at records that no longer existed. Every one was found by the search and then silently dropped because its content could not be resolved. A caller could not distinguish "nothing matches" from "your index is stale." That defect is fixed, measured by [`index_health()`](mem20api/README.md), and covered by tests that truncate a ledger and assert the diagnostic fires.

### The cognitive layer

Reasoning in five modes (deductive, inductive, abductive, analogical, causal), hierarchical planning, reflection, working memory, a 28-paradigm substrate, and tree-of-thought search. Planning enforces an **epistemic veto**: a plan whose supporting facts are still marked `hypothesis` or `imagined` is refused unless clearance is granted.

This is exposed as tools, not as a library you call — an agent reasons through the same surface it uses for memory.

### Dreaming and imagination

**The dream engine** ([`mem20dreamz`](mem20dreamz/README.md)) iterates on artifacts with a panel of eight *distinct* models, each critiquing in its own domain. The design rule is that iteration must **improve**, never **condense**: a lineage keeps the full artifact, every intermediate version, an invention register, and its own evolving config. It runs as a systemd service (`mem20-dreamer.service`) with an idle timer.

Why eight models rather than one: a single-model panel makes its own blind spot *systematic*. Every member can be confidently wrong the same way, and agreement gets laundered into consensus. `assert_roster_valid()` **raises** on a duplicate model rather than deduplicating silently — which is what previously deleted a role and left the invention register permanently empty with nothing reporting why.

**Imagination** is a separate tool family: counterfactuals, generative simulation, concept recombination, mental models, and adversarial critique. Simulated output lands in the simulated partition and cannot contaminate grounded memory. It becomes real only through evidence-based promotion.

---

## The honest claim

> **mem20 does not win on recall quality. It wins on recall trustworthiness.**

The incumbents have more data, more benchmark iterations, and more engineers. Pretending otherwise would be marketing, and a competitor publishes one comparison and the claim is dead.

What is uncontested is the axis mem20 is built around: **a memory system that tells you when it does not know, and never silently degrades.** Concretely:

- A contaminated store reports `contamination_rate > 0`. It cannot look healthy while leaking.
- An index that has drifted from its ledger reports it, with exact counts, on every retrieval call.
- Hybrid search reports which halves actually ran, so a silent fallback to keyword-only is visible.
- Graph retrieval reports honestly when an entity is absent instead of returning an empty result.
- Promotion out of the simulated partition requires evidence, not a flag.

These are all measured in [Benchmarks](#benchmarks). A system that answers confidently from a stale index can post an excellent hit rate and score terribly here. That is the point of measuring it.

**Where mem20 is behind, stated plainly:** no bi-temporal (event-time + ingestion-time) model — Zep's is genuinely best-in-class and ours is deferred; no temporal graph at all; Python-only SDK, where Mem0 ships Python, TypeScript, and Go; and a small corpus, so the quality numbers above are from 14 facts and 13 queries, which is enough to catch a regression and not enough to claim parity with anything.

---

## Benchmarks

Published at [`benchmarks/results/latest.md`](benchmarks/results/latest.md), regenerated with:

```bash
mem20benchmarkz run --out benchmarks/results
```

Retrieval quality, per query kind (a single average hides that keyword search handles direct queries and nothing else):

| Mode | direct | multi-hop | adversarial leak |
|---|---:|---:|---:|
| `keyword` (BM25 only) | 1.000 | 0.800 | 0.000 |
| `semantic` (vector) | 1.000 | 0.800 | 0.000 |
| `hybrid` (RRF + rerank) | 1.000 | 0.800 | 0.000 |
| `graph` (multi-hop) | — | 1.000 | — |

Trustworthiness — the axis mem20 claims:

| Check | Value | Required |
|---|---:|---|
| Contamination rate | **0.0** | 0.0 |
| Simulated records in BM25 corpus | **0** | 0 |
| Stale pointer rate | **0.000000** | 0.0 |
| Index healthy | **True** | True |

Latency, and the finding that came out of measuring it:

| Mode | p50 | p95 | p99 |
|---|---:|---:|---:|
| `graph` | 0.8 ms | 0.8 ms | 0.8 ms |
| `semantic` | 17.6 ms | 26.8 ms | 32.1 ms |
| `hybrid` (rerank on) | 182.4 ms | 219.3 ms | 258.6 ms |
| `hybrid` (`MEM20_RERANK=0`) | **18.0 ms** | — | — |

Cross-encoder reranking costs an order of magnitude in latency and buys direct-query ranking, not multi-hop recall. It now has an opt-out (`MEM20_RERANK=0`) because the benchmark found the tax was invisible.

> **These numbers are not comparable to competitor benchmarks.** Mem0's LoCoMo (92.5) and LongMemEval (94.4) figures and Zep's DMR (94.8%) come from different corpora — two of the three are private or vendor-defined — and different metrics. Nothing here reproduces or refutes them. This corpus is `mem20-agent-kb-v1`, 14 facts and 13 queries. It is small on purpose: it is a regression gate, not a leaderboard.

---

## The estate

**327 indexed subsystems** — 301 organs, 17 services, 9 other. 8,969 source files, ~468k code lines.

Find code with the sitemap instead of grepping:

```bash
/sitemap search "graph node eval"     # ranked across names, entry points, keywords
/sitemap show mem20dreamz             # full detail for one subsystem
/sitemap build                        # rescan after adding a subsystem
```

| Layer | What lives there |
|---|---|
| `memory_engine/` | The store: append-only ledger, vector + BM25 + graph indexes, contamination firewall |
| `mem20api/` | Stable Python API over the engine — bind a store, get honest diagnostics |
| `mem20benchmarkz/` | The benchmark suite in this README |
| `mcp/` | MCP server: **270 tools across 27 domains** |
| `cog/` | Cognitive engine (reasoning, planning, reflection) |
| `braid/` | **Append-only cryptographic ledger in Rust** — see below |
| `mem20dreamz/` | The dream engine |
| `mem20oreo/` | OREO — visual, natural-language-first language |
| `mem20kilnz/engine/` | kiln — Linux 3D modeler with procedural node graphs |
| `mem20agentz/` | Full agent platform: sessions, skills, projects, gateway, desktop |
| `mem20owebz/` | Chat front-end + LiteLLM model gateway |
| `mem20ircz/`, `mem20botz/` | The IRC channel where agents talk and take jobs |
| `mem20controlz/` | Unified control plane with per-subsystem panels |
| `toolchest/` | Registry of 889 capabilities (270 MCP tools, 318 CLIs, 303 subsystems) with runtime status |

### Braid: the ledger everything else could be built on

[`braid/`](braid/README.md) is a Cargo workspace of nine crates implementing an append-only Merkle-DAG ledger where **every write is signed**.

- `braid_core` — Ed25519 signing, BLAKE3 hashing, `br`-prefixed CIDs, a parent-CID spine, and `proof()` to genesis. `node_is_proven(node)` is the single fact gate every door shares: audit verification *and* re-derivation of the node's committed CID, because a signature alone covers the strand, not the payload.
- Capability grants are **one-directional** — only the granting side may wildcard — so a narrow rule cannot mint broad power.
- Escalation binds two triplets (base + human-gated) to one node. The base policy must *deny* the operation for escalation to be reachable at all.
- `braid_intent` treats a desire as an ordinary committed node. It stays OPEN until a *later proven* node references it. Resolution is ledger motion, never imagined execution: an injected unsigned resolver leaves the intent OPEN, and that is unit-tested.

### The MCP surface

270 tools in 27 domains. The largest:

| Prefix | Tools | Domain |
|---|---:|---|
| `memory_*` | 52 | Core memory, retrieval, epistemic audit |
| `cog_*`, `tot_*` + substrate | 18 | Reasoning, planning, tree-of-thought |
| `world_model_*` | 15 | Forecasting with a prediction ledger |
| `vcs_*` | 11 | Git and GitHub |
| `cloud_*`, `cloudstorage_*` | 18 | AWS, Azure, GCP, K8s, Docker, R2 |
| `db_*` | 10 | SQL across six engines |
| `fs_*` | 10 | Sandboxed filesystem |
| `braid_*` | 9 | The ledger |
| `comm_*` | 9 | Email, Slack, Discord, Telegram, SMS |
| `dev_*` | 9 | Tests, lint, search, sandboxed exec |
| `scrape_*` | 8 | Web scraping, forms, Playwright |
| `imagination_*` | 8 | Counterfactuals, recombination, mental models |

Plus `blender_*` and `unity_*` as **optional** integrations that require the external application and return an informative message when absent rather than failing.

---

## What you can do with mem20

- **Give your AI agent a persistent memory** that survives across sessions, with hybrid retrieval (vector + BM25 + cross-encoder reranking) and automatic fact extraction.
- **Keep grounded facts strictly separate from imagined ones** — contamination guards at the storage layer make it impossible for hypotheticals to pollute your real memory.
- **Run cognitive operations** — reasoning (deductive, inductive, abductive, analogical, causal), planning with hierarchical decomposition, reflection, and working memory.
- **Simulate the future** — imagination tools for counterfactuals and generative simulation, with an evidence-based promotion path back to grounded memory.
- **Model other agents' perspectives** — theory-of-mind tools that simulate what another agent believes, knows, or intends.
- **Track the world** — world-model tools with variables, rules, and a prediction ledger that measures how often simulations come true.
- **Give your agent a self-model** — affective values, emotional states, and goal tracking for richer agent introspection.
- **Build a procedural skill library** — reusable how-to knowledge with steps, preconditions, and effects.
- **Run standups, reviews, and retrospectives** — roadmap registry for multi-phase project plans with phase tracking.
- **Automate 3D workflows** — optional Blender and Unity integration for modeling, rendering, and game-engine automation.
- **Sandboxed filesystem access** — let your agent read/write files within a controlled scope.
- **Observe everything** — `/health`, `/ready`, and `/metrics` endpoints with tool counters, contamination rate, and event taxonomy.

---

## Architecture

```
                        ┌────────────────────────────────────────────┐
   MCP client  --stdio▶│  mcp/mcp_server.py  (Mem20MCPServer)       │
   (Hermes, Claude,    │  JSON-RPC 2.0 · 270 tools · 27 domains     │
    any MCP host)      └────────────────────────┬───────────────────┘
                                           │ calls
                 ┌─────────────────────────┼─────────────────────────┐
                 ▼                         ▼                         ▼
        cog/cognitive_engine.py    mem20/mem (store)         roadmaps/*.json
        (plan/chain/reason/        memory.py engine:          (roadmap registry)
         reflect/working memory)   grounded vs simulated,
                                   vector + BM25 indexes,
                                   append-only ledger)
```

### Transport / protocol

- **MCP server** speaking JSON-RPC 2.0 over stdio. `mcp/` is a script directory, not an importable package — it has no `__init__.py`, so importing it as `mcp.*` would shadow the upstream `mcp` SDK. That is why `mcp_server.py` does `from server import main` (script-dir relative) and why the installed console script `mem20-mcp` goes through `launcher.py` instead.
- `Mem20MCPServer` (in `server.py`) aggregates per-domain mixin classes and dispatches in `_execute_tool()`. It exposes **270 tools across 27 domains** (verified by instantiating the server and counting `server.tools`).
- Tool schemas + handlers live in per-domain modules under `mcp/` and `mcp/tools/`: `memory_tools.py`, `enhanced_memory_tools.py`, `cognitive_tools.py`, `thought_process.py`, `roadmap_tools.py`, `tools/world_tools.py`, `tools/braid_tools.py`, `tools/blender_tools.py` (OPTIONAL Blender), `tools/unity_tools.py` (OPTIONAL Unity), and `tools/integration_tools.py` (filesystem + blank template for new optional integrations).
- `mcp_server.py` is a thin entry-point shim preserving the systemd unit path.

### Monorepo

The core substrate is a fraction of the tree. Three nested projects carry their own `.git` and are consumed by the root repo as gitlinks:

| Path | Own repo | Notes |
|------|----------|-------|
| `mem20oreo/` | [mem20oreo](https://github.com/bythewayz66-glitch/oreo) | OREO visual/NL-first language. The `IDE/` tree was restructured into a proper `mem20oreo/` package. |
| `mem20kilnz/engine/` | separate repo | Rust/C++ mesh and geometry modeler ("kiln"), built with CMake. |
| `kanban-mcp/` | upstream fork | Vendored third-party MCP kanban server. Modifications are local and not published from here. |

> These three are recorded as ordinary untracked paths, not gitlinks — see
> [CHANGELOG 3.0.0](CHANGELOG.md). Their previous mode-160000 entries pointed at
> commits that do not exist in this repository, which broke every recursive checkout.

### Cognitive layer (`cog/`)

- `cognitive_engine.py` wraps an OpenAI-compatible LLM (`llm.py`) to provide thought processing, chains, reasoning, planning (`plan`/`aplan`), reflection, and working memory.
- Planning enforces the epistemic veto (see Governance).

### Memory layer (`mem/` + store engine `memory.py`)

- The durable memory engine lives on `MEM20_STORE_PATH` (default `~/.mem20/store`).
- It owns the ledger, the vector index (SentenceTransformer embeddings), and the BM25 corpus.

### Roadmap registry (`roadmaps/`)

- JSON files describing multi-phase project plans.

### Deployment (`systemd/`)

- A user service unit runs the MCP server under a virtualenv.

---

## Tool domains (27)

Counts below are the live surface, obtained by instantiating `Mem20MCPServer` and counting its registered tools. 270 total across 27 domains; the 29 rows below are tool *prefixes*, and several prefixes share one domain.

| Prefix | Tools | Domain | What it does |
|--------|------:|--------|-------------|
| `memory_*` | 49 | Core memory | Store, recall, probe entities, reason across entities, contradiction detection, epistemic audit, namespaces, pins, contamination audit |
| `cog_*`, `tot_*`, `cognitive_substrate`, `beam_search`, `react_reason`, `least_to_most`, `reflexion` | 15 | Cognitive processing | Reasoning (deductive, inductive, abductive, analogical, causal), planning, reflection, working memory, 28-paradigm substrate, tree-of-thought diagnostics |
| `world_model_*` | 9 | World forecasting | Variables and rules, record predictions, resolve against observed outcomes |
| `vcs_*` | 11 | Version control | Git status/diff/log/branch/commit/stash/remote/tag, GitHub issues and PRs |
| `cloud_*` | 10 | Cloud control planes | AWS EC2/Lambda/S3, Azure blob, GCP storage, Kubernetes, Docker, Heroku, DigitalOcean, Cloudflare Workers |
| `db_*` | 10 | Databases | SQL across sqlite/postgres/mysql/redis/mongodb, schema inspection, transactions |
| `prod_*` | 10 | Productivity | Tasks, projects, notes, goals, habits, meetings, time tracking |
| `fs_*` | 13 | Sandboxed filesystem | Read/write/list/search/watch, permissions, metadata, archives, diff, disk usage |
| `braid_*` | 9 | Content-addressed ledger | Hash, read, write, prove provenance, intent strand, bridge signer |
| `comm_*` | 9 | Messaging | Email (SMTP/IMAP), Slack, Discord, Telegram, SMS, push, calendar invites, contacts |
| `dev_*` | 9 | Development | Run tests, lint, format, search code, dependency analysis, sandboxed exec (bash/python/js), API test |
| `mkt_*` | 9 | Marketing | A/B tests, analytics, SEO, social posts, content generation, email campaigns, competitor analysis |
| `scrape_*` | 8 | Web scraping | Page/structured/RSS/sitemap/API scraping, form submission, dynamic Playwright rendering |
| `cloudstorage_*` | 8 | Object storage | S3/GCS/Azure/R2 list, upload, download, copy, delete, presigned URLs, rclone sync |
| `design_*` | 8 | Design | Image generation and editing, SVG generation, color palettes, typography, UI components, Figma, asset optimization |
| `fin_*` | 8 | Finance | Stock and crypto quotes, portfolio, expenses, budget, invoices, tax estimates, market news |
| `blender_*` | 7 | Blender automation | **OPTIONAL** — 3D modeling, rendering, scene manipulation (requires Blender app) |
| `search_*` | 7 | Search | Web, news, images, academic (arXiv/Semantic Scholar), code, knowledge base, local files |
| `affective_*` | 6 | Values, emotions, goals | Track agent values, emotional states, and goal hierarchies |
| `procedural_*` | 6 | Skill library | Add, get, execute, and search reusable procedural skills (how-to knowledge) |
| `a2a_*` | 5 | Agent-to-agent | Discover, call, and orchestrate peer agents over A2A |
| `irc_*` | 5 | Shared channel | Join, read, send on the IRC room where agents coordinate |
| `unity_*` | 5 | Unity automation | **OPTIONAL** — Game-engine scripting, project builds, test runs (requires Unity Editor) |
| `imagination_*` | 8 | Counterfactual simulation | Generate hypotheticals, run "what-if" scenarios, simulate futures, recombine concepts, mental models |
| `roadmap_*` | 4 | Roadmap registry | Create, list, get, and update multi-phase project plans |
| `self_model_*` | 3 | Agent self-model | Track the agent's own identity, capabilities, and values over time |
| `corrigibility_*` | 2 | Shutdown / capability tiers | Control the agent's capability levels and shutdown behavior |
| `theory_of_mind_*` | 2 | Perspective simulation | Model what another agent believes, knows, or intends |
| `job_*` | 2 | Background jobs | Poll and await long-running mem20 jobs |

> **Naming note:** the table lists tool prefixes; some prefixes are spelled differently from their domain name (`world_model_*` for world forecasting, `vcs_*` for version control, `fs_*` for filesystem, `tot_*` for tree-of-thought).

---

## Memory model

mem20 keeps two logical partitions:

- **Grounded memory** — facts derived from real observations, user statements, or events.
- **Simulated memory** — hypotheticals, imagined scenarios, counterfactuals, or model output.

### Hard invariants enforced by the store engine

1. **Indexes are grounded-only.** `_add_to_vector_index()` and `_add_to_bm25_index()` call `_assert_grounded()`; a simulated record reaching either index raises immediately.
2. **`remember()` is grounded-only by default** (`_allow_simulated=False`). Simulated content uses its own path (`remember_simulated` / `memory_simulate_store`).
3. **Append-only ledger with validated tags.** Every ledger entry carries `origin` (e.g. `user`, `tool`, `simulated`) and `store` (`memory`/`imaginated`). `_validate_partition_tags()` rejects mismatches at the lowest append path.
4. **Promotion is evidence-based.** `promote_simulated_to_grounded()` accepts a simulated record only when it carries `prediction_error_evidence` — either a linked prior prediction resolved in its favor, or vouched for by a registered external verifier.
5. **Epistemic status is authoritative on the record.** `set_epistemic_status()` stamps the status directly onto the original grounded ledger line and the deep-store markdown header.

### Store layout (`MEM20_STORE_PATH`)

```
store/
  memory.py                 # the engine
  ledger.jsonl              # append-only operation log (origin/store tagged)
  embeddings.npy / index    # vector index (grounded only)
  bm25_corpus.json          # BM25 corpus (grounded only)
  records/<id>.md           # deep-store markdown (header carries epistemic_status)
  simulated/                # simulated partition (never indexed)
```

---

## Governance & Contamination Controls

- **Contamination guards** — `_assert_grounded()` at the vector/BM25 write paths.
- **Origin/store assertion** — `_validate_partition_tags()` at the ledger append path.
- **Epistemic veto / clearance** — `require_epistemic_clearance()` plus the plan-execution guard `run_plan_execution_guard()`. The cognitive engine enforces this on `plan`/`aplan`.
- **Audit** — `memory_audit_contamination()` inspects both the grounded store and the BM25 corpus for simulated records, returning `contamination_rate`, `violations`, and `violations_simulated_in_bm25_corpus`. A clean system reports rate `0.0`.
- **Prediction ledger** — `world_model_record_prediction` / `world_model_resolve_prediction` couple a forecast to its observed outcome, feeding the promotion gate and prediction-accuracy metrics.

---

## Quick Start

### Install from source

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20

# Create venv and install core deps
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run the server (stdio)
MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py
```

### Install on Android with UserLAnd

UserLAnd runs a normal Ubuntu or Debian userspace without requiring Android
root. Use the matching section below inside the UserLAnd session. These
sessions generally do not run `systemd`, so start mem20 directly instead of
using `install.sh` as a system service.

#### Ubuntu UserLAnd

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip python3-dev build-essential

git clone https://github.com/bythewayz66-glitch/mem20.git ~/mem20
cd ~/mem20
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

mkdir -p ~/.mem20/store
MEM20_STORE_PATH="$HOME/.mem20/store" .venv/bin/python mcp/mcp_server.py
```

#### Debian UserLAnd

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip python3-dev build-essential

git clone https://github.com/bythewayz66-glitch/mem20.git ~/mem20
cd ~/mem20
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

mkdir -p ~/.mem20/store
MEM20_STORE_PATH="$HOME/.mem20/store" .venv/bin/python mcp/mcp_server.py
```

If the UserLAnd image already opens as root, omit `sudo`. Keep the repository
and store under the UserLAnd home directory when possible; shared Android
storage can be slower and may have different file-permission behavior.

Verify the server from the same session:

```bash
curl http://127.0.0.1:8080/health
```

To leave it running after closing the shell, use the UserLAnd session's own
background behavior or run it explicitly with `nohup`:

```bash
nohup env MEM20_STORE_PATH="$HOME/.mem20/store" \
  "$HOME/mem20/.venv/bin/python" "$HOME/mem20/mcp/mcp_server.py" \
  >"$HOME/.mem20/server.log" 2>&1 &
```

### Install on Android with Termux (no root)

Termux does not need, and should not use, `sudo`, `su`, or Android root. Install
the repository in the Termux home directory:

```bash
pkg update
pkg upgrade
pkg install -y git python clang make cmake

git clone https://github.com/bythewayz66-glitch/mem20.git "$HOME/mem20"
cd "$HOME/mem20"
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

mkdir -p "$HOME/.mem20/store"
MEM20_STORE_PATH="$HOME/.mem20/store" .venv/bin/python mcp/mcp_server.py
```

Check it with:

```bash
pkg install -y curl
curl http://127.0.0.1:8080/health
```

Termux is a native Android environment, not a glibc Linux distribution. If
`faiss-cpu` or another native dependency has no compatible Android wheel, the
full requirements install will stop there; run the Ubuntu/Debian UserLAnd
instructions instead. Do not work around that failure by installing root
tools. A Termux process also stops when Android reclaims the app, so use
`termux-wake-lock` while it is active and restart the command when needed:

```bash
termux-wake-lock
MEM20_STORE_PATH="$HOME/.mem20/store" "$HOME/mem20/.venv/bin/python" \
  "$HOME/mem20/mcp/mcp_server.py"
```

Press `Ctrl-C` to stop mem20 and run `termux-wake-unlock` afterward. None of
the Android paths above install a system service or write outside the user's
home directory.

### Install on Android with postmarketOS

postmarketOS uses Alpine Linux packages (`apk`) and commonly uses OpenRC. The
commands below keep mem20 in the normal user home and run it manually; no
Android root or system service is required. On a postmarketOS image where the
package-install command is already running as root, omit `doas`.

```bash
doas apk update
doas apk add git python3 py3-pip py3-virtualenv python3-dev build-base curl

git clone https://github.com/bythewayz66-glitch/mem20.git "$HOME/mem20"
cd "$HOME/mem20"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

mkdir -p "$HOME/.mem20/store"
MEM20_STORE_PATH="$HOME/.mem20/store" .venv/bin/python mcp/mcp_server.py
```

Check the health endpoint from the postmarketOS terminal:

```bash
curl http://127.0.0.1:8080/health
```

To run it in the background for the current session:

```bash
nohup env MEM20_STORE_PATH="$HOME/.mem20/store" \
  "$HOME/mem20/.venv/bin/python" "$HOME/mem20/mcp/mcp_server.py" \
  >"$HOME/.mem20/server.log" 2>&1 &
```

postmarketOS uses musl on many device images, and Android-device builds may
not have compatible wheels for `faiss-cpu` or another native dependency. If
`pip install -r requirements.txt` reports that no distribution is available,
use the Ubuntu or Debian UserLAnd path above, which provides a glibc userspace;
do not replace the failure with a root install of unrelated system packages.

### Install on Penguin Linux (ChromeOS Crostini)

Penguin Linux is Debian-based — the standard systemd install works perfectly:

```bash
# Clone and install as a system service (recommended for always-on)
git clone https://github.com/bythewayz66-glitch/mem20.git /opt/mem20
sudo /opt/mem20/install.sh --user $USER --dir /opt/mem20

# Verify it's running
curl http://localhost:8080/health
```

**What the installer does:**
- Creates a Python venv at `/opt/mem20/.venv`
- Installs core deps from `requirements.txt` (mcp, pydantic, numpy, faiss-cpu, sentence-transformers)
- Creates `/etc/systemd/system/mem20.service` and enables/starts it
- Default store path: `/opt/mem20/store`

**If you want to run without systemd (simpler for testing):**
```bash
sudo /opt/mem20/install.sh --no-systemd
# Then run manually:
MEM20_STORE_PATH=/opt/mem20/store /opt/mem20/.venv/bin/python /opt/mem20/mcp/mcp_server.py
```

**Note:** Penguin Linux has systemd, so the default install (without `--no-systemd`) is recommended. The service runs on port 8080.

### Install with systemd (recommended for always-on)

```bash
sudo ./install.sh --user $USER --dir /opt/mem20
```

`install.sh` creates the venv, installs deps, generates the systemd unit from `systemd/mem20.service.template`, and enables + starts it.

After start, probe health:

```bash
curl http://localhost:8080/health   # → {"status":"ok", ...}
curl http://localhost:8080/metrics  # → tool counters + contamination_rate
```

Point an MCP host at the server (stdio).

### Connect from Hermes Agent

```bash
# In your Hermes config, add mem20 as an MCP server
hermes config set mcp.servers.mem20 '["python3", "/path/to/mem20/mcp/mcp_server.py"]'
```

### Connect from Claude Code / Cursor

```bash
claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py
```

---

## Optional integrations

Blender and Unity ship as *separate, pluggable modules*. They require the respective external application installed:

- **Blender** — install Blender; ensure `blender` is on PATH or set `MEM20_BLENDER_EXECUTABLE`.
- **Unity** — install the Unity Editor; set `MEM20_UNITY_EXECUTABLE`.

When absent, the tools return an informative message instead of failing. See `requirements-optional.txt`.

To add your own optional integration, see `IntegrationToolsMixin.register_integration_template()` in `mcp/tools/integration_tools.py`.

---

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MEM20_STORE_PATH` | `~/.mem20/store` | Memory engine module + store location |
| `MEM20_COG_PATH` | (mem20 `cog/` dir) | Cognitive engine location |
| `MEM20_LLM_BASE_URL` | `https://integrate.api.nvidia.com/v1` | LLM chat-completions base URL |
| `MEM20_LLM_MODEL` | (project default) | Model name |
| `NVAPI_KEY` / `NVIDIA_API_KEY` / `MEM20_LLM_API_KEY` | — | LLM bearer token (required) |
| `MEM20_ENV_FILE` | — | Optional `.env` to load API keys from |
| `MEM20_FLAG_WORLDMODEL_20` | `1` (ON) | Kill-switch for world-model / self-model / affective / procedural tools |

---

## Roadmap registry

Roadmaps are JSON files in `roadmaps/`. Schema:

```json
{
  "name": "mem20_build",
  "description": "Build mem20 from scratch",
  "phases": [
    { "name": "mcp",        "status": "planned", "notes": "" },
    { "name": "memory",     "status": "planned", "notes": "" },
    { "name": "cognitive",   "status": "planned", "notes": "" },
    { "name": "production",  "status": "planned", "notes": "" }
  ],
  "created": "1787804510.8459408"
}
```

Tools: `roadmap_create`, `roadmap_list`, `roadmap_get`, `roadmap_update_phase`.

---

## Installation

mem20 is distributed through four channels. All of them run the **same**
server (`mcp/mcp_server.py`): an MCP stdio JSON-RPC server plus an HTTP health endpoint
on `:8080` (`/health`, `/ready`, `/metrics`). Pick whichever fits your environment.

### 1. pip (Python)

```bash
pip install .                 # builds the wheel, installs the `mem20-mcp` command
mem20-mcp                     # starts the MCP server + :8080 health endpoint
# or run the repo directly (always supported, never changes):
#   python mcp/mcp_server.py
```

`mem20-mcp` is a thin launcher (`launcher.py`) that locates the bundled `mcp/`
directory and runs it as a script — so `from mcp.server import Server` (the SDK)
is never shadowed. Override the port with `MEM20_HEALTH_PORT`.

### 2. Docker

```bash
docker build -t mem20 .
docker run -p 8080:8080 -e MEM20_HEALTH_PORT=8080 -v mem20-store:/data mem20
# or with compose (persists the store in a named volume):
docker compose up -d
curl http://localhost:8080/health
```

The image runs `python mcp/mcp_server.py` as the canonical entrypoint (health on `:8080`).

### 3. npm (web dashboard)

The `dashboard/` app (Vite + React) shows live server status and the memory
store. It talks to the **optional** HTTP bridge (`bridge/server.py`), which
proxies `/health`, `/ready`, `/metrics` and adds `/api/memory`, `/api/recall`.

```bash
# optional bridge (completely separate from the MCP server):
pip install fastapi uvicorn httpx
python bridge/server.py                 # :8000

# dashboard:
cd dashboard
npm install
npm run build                           # → dashboard/dist/ (static)
npx serve dashboard/dist                # or any static server
# dev mode with hot reload:
npm run dev                             # http://localhost:5173
```

### 4. apt (.deb)

```bash
make deb                                # → packaging/deb/mem20_*.deb
sudo dpkg -i packaging/deb/mem20_*.deb  # installs venv + systemd unit + health probe
sudo systemctl status mem20             # enabled + started by postinst
mem20-health                            # probe /health
```

See `packaging/README.md` for how each channel is built and why `mcp/` is kept
out of the Python import path (shadowing the `mcp` SDK would break the server).

---

## Dependencies

Core (Python, pip) — `requirements.txt`:

- `mcp` — MCP server framework
- `sentence-transformers` — `SentenceTransformer` (embeddings) and `CrossEncoder` (reranking)
- `numpy` — vector math
- `faiss-cpu` — vector index
- `pydantic`, `anyio` — MCP transport
- LLM access — `cog/` talks to an OpenAI-compatible chat-completions endpoint via `llm.py` (default NVIDIA `integrate.api.nvidia.com/v1`); requires an API key, no SDK beyond `httpx`

Optional / integration-only (external applications — degrade gracefully when absent):

- **Blender** — install Blender; ensure `blender` is on PATH or set `MEM20_BLENDER_EXECUTABLE`
- **Unity** — install the Unity Editor; set `MEM20_UNITY_EXECUTABLE`

Install core:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
# or, with dev + integration extras:
#   .venv/bin/pip install -e ".[dev]"
```

---

## Repository layout

The tree is large, so find code through the sitemap rather than by browsing. `/sitemap search "<terms>"` ranks matches across subsystem names, entry points, keywords, and descriptions.

| Path | What lives there |
|------|------------------|
| `mcp/` | MCP server: tool schemas, per-domain mixins, health/metrics |
| `cog/` | Cognitive engine (LLM-backed reasoning, planning, reflection) |
| `memory_engine/` | Core memory store engine |
| `mem20api/` | Stable Python API over the engine |
| `mem20benchmarkz/` | Benchmark suite and published results |
| `mem20-sdk-ruby/` | Ruby SDK 0.2.0 |
| `braid/` | Rust append-only cryptographic ledger |
| `toolchest/` | Tool registry — MCP tools, CLI binaries, subsystems, with runtime status |
| `roadmaps/` | Roadmap registry (JSON) |
| `systemd/` | Service unit templates |
| `verification/` | Verification scripts |
| `mem20*z/` | 293 `mem20*z` subsystem packages ("organs"). The sitemap indexes 327 subsystems in total, of which 301 are categorised `organ`; the rest are engines and services (see below). |
| `braid/`, `cog/`, `memory_engine/`, `chroma/`, `dashboard/`, `gateway/`, `mcp/`, `kanban/`, `toolchest/`, `reference_store/` | Engines and services. Unprefixed **by design** — they are infrastructure, not organs. Do not rename them. |

Naming is `mem20<name>z` for organs, with deliberate exceptions that must not be "fixed": `mem20agentz_sdk` (the SDK's suffix is its identity), `mem20messenger`, `mem20oreo`, `mem20zimr`, `toolchest`, `mem20ops` (a role over the fleet, not an organ), `mem20sitemapz`.

Current index: **327 subsystems, 8,969 source files, 468k code lines**. Per the sitemap, **632 of 875 registered capabilities report `ok`**, 142 are `unpackaged` (real, but no `pyproject.toml`), and 101 are `degraded`.

---

## Development

- **Engine logic** lives in the store engine, not in the MCP server. MCP tools are thin handlers that call engine functions.
- **Verify claims by execution.** [`mem20verify`](mem20verify/README.md) exists because claims were being trusted instead of verified.
- **Run the full suite.** A bare `pytest` from the repo root collects every package's tests (see `pytest.ini`); `pytest tests/` covers only the core suite.
- **Contamination must stay at 0.0** after any memory-layer change.

```bash
pytest                                   # whole estate
mem20verify tests                        # per-package, with timeouts
mem20benchmarkz run                      # retrieval benchmarks
```

### Adding a tool

Pick the domain module, add the `self.tools["name"] = mt.Tool(...)` block, and add a dispatch branch + handler. Run `verification/verify_refactor.py` after changes.

### Adding an optional integration

Create `mcp/tools/<name>_tools.py` with a `<Name>ToolsMixin`, guard any external executable with a graceful check, add the mixin to `Mem20MCPServer`'s bases, and call `self.register_<name>_tools()` in `_setup_tools()`.

### Roadmaps

Plain JSON in `roadmaps/`; edit via the `roadmap_*` tools or directly.

---

## Documentation

Full docs live at **[mem20.jaysonai.online](https://mem20.jaysonai.online)**.

| Resource | What's covered |
|----------|----------------|
| [`README.md`](README.md) | This file — overview, quick start, architecture |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes, version history |
| [`docs/`](docs/) | Extended tool, architecture and usage reference |
| [`benchmarks/results/latest.md`](benchmarks/results/latest.md) | Published benchmark results |
| [`2.0_roadmap/`](2.0_roadmap/) | 2.0 roadmap deliverables and human execution package |
| [`systemd/mem20.service.template`](systemd/mem20.service.template) | Systemd unit template for production deployment |
| [`verification/verify_refactor.py`](verification/verify_refactor.py) | Refactor verification script |
| [`tests/`](tests/) | pytest suite covering contamination firewall, eval safety, dispatch, metrics |
| [`roadmaps/`](roadmaps/) | Roadmap registry (JSON) |
| [`SITEMAP.md`](SITEMAP.md) | Generated map of every subsystem — run `/sitemap search "<terms>"` to find code without grepping |
| [`toolchest/`](toolchest/) | Runtime-checked tool registry (MCP tools, CLI binaries, subsystems) with status |
| [`mcp/`](mcp/) | MCP server implementation and tool modules |
| [`cog/`](cog/) | Cognitive engine (LLM-backed reasoning, planning, reflection) |
| [`memory_engine/`](memory_engine/) | Core memory store engine |
| [`proof/`](proof/) | Audit responses and verification artifacts |

---

## Contributing

Contributions are welcome! Before submitting a PR:

1. Run `verification/verify_refactor.py` if you touched engine code.
2. Run `pytest tests/` to confirm all tests pass. A bare `pytest` from the repo root collects **every** package's tests through the root `conftest.py` (see `pytest.ini`) — a bare run restricted to `tests/` covers only the core suite.
3. Confirm `contamination_rate == 0.0` after any memory-layer changes.
4. Update docs when behavior or architecture changes.

---

## License

MIT — see [LICENSE](LICENSE).

Canonical repository: [bythewayz66-glitch/mem20](https://github.com/bythewayz66-glitch/mem20). Originally built by the JaysonAIOnline project.
