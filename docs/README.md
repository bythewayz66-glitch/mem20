# mem20 MCP Server Documentation

> **Version:** 3.1.2
> **License:** MIT
> **Maintainer:** bythewayz66-glitch
> **Repository:** https://github.com/bythewayz66-glitch/mem20

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture Overview](01-architecture.md) | System design, memory model, tool domains, deployment |
| [Tools Reference](02-tools-reference.md) | Complete reference for the MCP tool surface (311 tools / 39 domains live) |
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

## 311 Tools Across 39 Domains

The authoritative, generated mapping is [TOOL-DOMAINS.md](TOOL-DOMAINS.md); the
machine-readable source is [surface.json](surface.json). Both are regenerated
from the live `tools/list` response by `scripts/surface_manifest.py`.

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

## Dated records

Append-only records kept for provenance. They are **not** live guidance: where a
number here disagrees with the sections above, the section above wins.

| Document | What it records |
|---|---|
| [`agentz-evidence.md`](agentz-evidence.md) | OREO editor (agentZ) delivery evidence for PR #240. |
| [`attestations/`](attestations/) | Token-use attestations, one file per dated event. |
| [`app/narrative/serial-2026-11-01-publication-note.md`](app/narrative/serial-2026-11-01-publication-note.md) | Publication note for the 2026-11-01 narrative instalment. |
| [`gtm/launch-copy-refresh-2026-11-01.md`](gtm/launch-copy-refresh-2026-11-01.md) | What changed in the launch copy (v5) and why. |
| [`ops/analytics-reporter-reverify-2026-11-01.md`](ops/analytics-reporter-reverify-2026-11-01.md) | Re-verification of the analytics reporter. |
| [`ops/mem20-api-service-2026-11-01.md`](ops/mem20-api-service-2026-11-01.md) | State of the `mem20-api` service on 2026-11-01. |
| [`webdev/github-token-mandate-2026-11-01.md`](webdev/github-token-mandate-2026-11-01.md) | The GitHub-token handling mandate for web work. |
| [`recon/`](recon/) | Stale-file inventory and its regenerator. |
