# RM-101 — WebAssembly Component Lab

**Owner:** OtherStack  
**Lane:** Experimental and incompatible technology incubator

## Outcome
Run language-neutral components with explicit interfaces and strong isolation

## Breakthrough
FreeStack gains a portable plugin future beyond Python packages

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-101 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## CLI

`mem20wasmz` ships a command line over the same runtime the MCP tools use. Every
number it prints is measured in-process; nothing is estimated.

```bash
cd mem20wasmz
python3 -m mem20wasmz inspect
python3 -m mem20wasmz run '{"text":"demo","cache":false}'
python3 -m mem20wasmz simulate
python3 -m mem20wasmz benchmark --runs 5
python3 -m mem20wasmz wiring
python3 -m pytest tests -q
```

`inspect` reports the roadmap identity and component surface:

```bash
$ python3 -m mem20wasmz inspect
{
  "global_id": 101,
  "title": "WebAssembly Component Lab",
  "owner": "OtherStack",
  "lane": "Experimental and incompatible technology incubator",
  "outcome": "Run language-neutral components with explicit interfaces and strong isolation",
  "phases": 3,
  "subphases": 6
}
```

`run` executes one component request and returns the real result plus an audit
block — canonical form, stable hash, and the state of the six wired subsystems:

```bash
$ python3 -m mem20wasmz run '{"text":"demo","cache":false}'
{
  "result": {"job_id": "...", "roadmap_id": 101, "mode": "local", ...},
  "audit": {
    "run": {"job_id": "...", "roadmap_id": 101, "mode": "local",
            "confidence": 0.89, "cache_hit": false,
            "output": {"compatible": true, "isolation": "component-sandbox",
                       "component_count": 2}},
    "stable_hash": "b84e88956d170b26...",
    "wired_modules": ["mem20core", "memory_engine", "toolchest",
                      "mem20verify", "mem20ops", "gateway"]
  }
}
```

`wiring` proves the six cross-module calls the 4.0 architecture rule requires
(mem20core, memory_engine, toolchest, mem20verify, mem20ops, gateway) and prints
the real value each one returned.

## MCP surface

Two tools are registered on the mem20 MCP server (`mcp/tools/wasmz_tools.py`,
`WasmzToolsMixin`):

| tool | what it does |
|---|---|
| `wasmz_inspect` | roadmap identity and component surface |
| `wasmz_run` | run one component request through the isolated runtime |

Both call the real `Runtime`; a failed run returns the real error text rather
than a plausible-looking result.
