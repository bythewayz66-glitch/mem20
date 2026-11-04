# mem20 Architecture Overview

**Version:** 3.1.2  
**License:** MIT  
**Maintainer:** bythewayz66-glitch  

## What is mem20?

mem20 is a trusted, auditable memory + world-model layer for agents. It provides persistent memory that survives sessions, records provenance and epistemic status, and can be audited after the fact. mem20 ships as an MCP server (JSON-RPC 2.0 over stdio) with 311 tools across 39 domains, plus a large estate of independently packaged subsystems.

## Architecture Layers

mem20 is built in three dependency layers:

| Layer | Path | Purpose |
|---|---|---|
| **Memory Engine** | `memory_engine/`, `memory.py` | Global memory, ledger, vector store, and epistemic tracking. The durable substrate. |
| **MCP Server** | `mcp/` | Exposes the engine and wider estate as MCP tools over stdio (JSON-RPC 2.0). Note: `mcp/` is a script directory (no `__init__.py`) to avoid shadowing the upstream `mcp` SDK. |
| **Subsystems** | `mem20*/` | ~300 independently packaged capability modules, each with its own `pyproject.toml`. These extend the core functionality across domains. |

## Key Components

### Memory System
- **Grounded Memory**: Facts with epistemic status (observed, inferred, user_stated, agent_generated, hypothesis, unlabeled). Unlabeled facts are refused by the epistemic veto.
- **Simulated Memory**: Separate partition for imagined/counterfactual content. Cannot be promoted to grounded memory without explicit confirmation or real-world prediction-error resolution.
- **Ledger**: Append-only audit trail of all memory operations.
- **Vector Store**: Semantic search and retrieval capabilities.

### MCP Interface
- **Transport**: stdio (primary), HTTP health/metrics on port 8080
- **Tools**: 311 tools across 39 domains, exposed via JSON-RPC 2.0
- **Authentication/Access**: Controlled through the tool surface

### Epistemic Framework
- All grounded facts must declare epistemic status
- Epistemic veto prevents plans from relying primarily on unvalidated simulated beliefs
- Provenance tracking throughout the system
- Contamination auditing between simulated and grounded partitions

## Data Flow

1. Agents interact with mem20 via MCP tools (stdio)
2. Tools route to appropriate subsystems or core memory engine
3. All operations go through the memory engine with epistemic tracking
4. Results are returned via JSON-RPC responses
5. All actions are logged to the ledger for auditability

## Design Principles

- **Auditability**: Every memory has provenance and epistemic status
- **Separation of concerns**: Simulated and grounded memories are strictly separated
- **Modularity**: Subsystems are independently packaged and composable
- **Trust**: Epistemic constraints prevent hallucinated facts from contaminating grounded memory
- **Transparency**: All operations are traceable through the ledger
