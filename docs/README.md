# mem20 MCP Server Documentation

> **Version:** 3.0.0
> **License:** MIT
> **Maintainer:** bythewayz66-glitch
> **Repository:** https://github.com/bythewayz66-glitch/mem20

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture Overview](01-architecture.md) | System design, memory model, tool domains, deployment |
| [Tools Reference](02-tools-reference.md) | Complete reference for the MCP tool surface (257 tools / 26 domains live) |
| [Installation Guide](03-installation.md) | Install, configure, and connect MCP hosts |
| [Usage Examples](04-usage-examples.md) | Practical examples for every tool domain |

## What is mem20?

**mem20** is a **persistent memory + cognition substrate for AI agents**. It provides:

- **Persistent memory** with hybrid retrieval (vector + BM25 + cross-encoder)
- **Strict separation** of grounded facts from imagined/hypothetical ones
- **Cognitive operations** — reasoning, planning, reflection, working memory
- **World modeling** — define variables, record predictions, resolve outcomes
- **Self-modeling** — track beliefs, values, emotions, goals
- **Multi-agent coordination** — A2A communication, shared namespaces
- **3D workflow automation** — optional Blender and Unity integration

## Architecture at a Glance

```
MCP client --stdio--> Mem20MCPServer (mcp/mcp_server.py)
                         |
         +---------------+---------------+
         |               |               |
   cognitive_engine    memory.py      roadmaps/
   (LLM-backed)    (store engine)   (JSON files)
```

## 257 Tools Across 26 Domains

Counts obtained by instantiating `Mem20MCPServer` and counting `server.tools`.

| Domain | Prefix | Count |
|--------|--------|-------|
| Core memory | `memory_*` | 49 |
| Cognitive processing | `cog_*` / `tot_*` / substrate | 15 |
| World forecasting | `world_model_*` | 9 |
| Version control | `vcs_*` | 11 |
| Cloud control planes | `cloud_*` | 10 |
| Databases | `db_*` | 10 |
| Productivity | `prod_*` | 10 |
| Sandboxed filesystem | `fs_*` | 13 |
| Content-addressed ledger | `braid_*` | 9 |
| Messaging | `comm_*` | 9 |
| Development | `dev_*` | 9 |
| Marketing | `mkt_*` | 9 |
| Web scraping | `scrape_*` | 8 |
| Object storage | `cloudstorage_*` | 8 |
| Design | `design_*` | 8 |
| Finance | `fin_*` | 8 |
| Imagination/Simulation | `imagination_*` | 8 |
| Blender automation | `blender_*` | 7 |
| Search | `search_*` | 7 |
| Values/Emotions/Goals | `affective_*` | 6 |
| Skill library | `procedural_*` | 6 |
| Agent-to-agent | `a2a_*` | 5 |
| Shared channel | `irc_*` | 5 |
| Unity automation | `unity_*` | 5 |
| Roadmap registry | `roadmap_*` | 4 |
| Self-model | `self_model_*` | 3 |
| Corrigibility/Shutdown | `corrigibility_*` | 2 |
| Theory of mind | `theory_of_mind_*` | 2 |
| Background jobs | `job_*` | 2 |

## Quick Start

```bash
# Install
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
export NVAPI_KEY="your-nvidia-api-key"

# Run
python mcp/mcp_server.py

# Verify
curl http://localhost:8080/health
```

## Connecting MCP Hosts

```bash
# Hermes Agent
hermes config set mcp.servers.mem20 '["python3", "/path/to/mem20/mcp/mcp_server.py"]'

# Claude Code
claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py
```

## Key Concepts

### Memory Partitions

- **Grounded** — real observations, user statements, events (indexed)
- **Simulated** — hypotheticals, counterfactuals, model output (not indexed)

### Contamination Controls

- Indexes are grounded-only
- Simulated content can NEVER leak into grounded indexes
- Promotion requires evidence (prediction-error resolution or external verification)

### Health & Observability

- `/health` — status check
- `/ready` — readiness probe
- `/metrics` — tool counters, contamination rate, event taxonomy

## SDKs

| SDK | Location | Status |
|---|---|---|
| Python | `mem20api/` | Published — the stable API over the engine |
| Ruby | `mem20-sdk-ruby/` | 0.2.0 |
| C++ | `docs/sdk/cpp/` | Documentation set |

## Optional Integrations

- **Blender** — 3D modeling, rendering, scene manipulation
- **Unity** — Game-engine scripting, builds, tests

Both degrade gracefully when the respective application is not installed.

## License

MIT — see [LICENSE](https://github.com/bythewayz66-glitch/mem20/blob/main/LICENSE).

Canonical repository: [bythewayz66-glitch/mem20](https://github.com/bythewayz66-glitch/mem20). Originally built by the JaysonAIOnline project.
