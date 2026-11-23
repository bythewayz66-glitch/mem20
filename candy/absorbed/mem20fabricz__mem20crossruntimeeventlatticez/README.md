# RM-005 — Cross-Runtime Event Lattice

**Outcome:** Connect independent runtimes through typed events, durable streams, and reactive subscriptions
**Breakthrough:** The ecosystem behaves like one nervous system without becoming monolithic
**Version:** 4.0.0 · **Subsystem:** `mem20crossruntimeeventlatticez`

The lattice is the causality layer of the mem20 estate. It emits typed events,
orders them, links them into a vector-clock DAG, and merges independent
lattices into one. Since 4.0 it is wired into the substrate rather than
standing alone: every lattice event can be persisted to durable memory,
searched multi-hop, announced to the fleet gateway, verified for ledger
integrity, and compacted for the wire.

## Install

mem20 is **not on PyPI**. Install from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

## Quick start — runnable example

This is the whole seam in one script: emit an event, link a child to it
causally, persist both, announce them to the fleet, read them back, and report
on the merged lattice. Run it from the repo root.

```bash
cd mem20
MEM20_STORE_PATH=/tmp/mem20-lattice-demo python3 - <<'PY'
import json, sys
sys.path.insert(0, "mem20crossruntimeeventlatticez")

from mem20crossruntimeeventlatticez import domain, integration

parent = domain.emit("session.start", {"user": "u-1"}, source="local")
out = integration.emit_and_record(
    "session.view", {"page": "/pricing"}, lattice="web", source="edge", parent=parent
)
print("event id       :", out["event"]["id"])
print("parent         :", out["event"]["parent"])
print("vector clock   :", out["event"]["vector"])
print("memory topic   :", out["memory_topic"])
print("announced by   :", out["announced"]["agent_name"])

rows = integration.recall_events("web", "session.view")
print("recalled rows  :", len(rows))
print("recalled body  :", json.loads(rows[0]["content"])["payload"])

report = integration.lattice_report(
    [{"events": [parent]}, {"events": [out["event"]]}], name="web"
)
print("lattice count  :", report["count"])
print("by type        :", report["by_type"])
print("sources        :", report["sources"])
print("causal links   :", report["causal_links"])
print("inventory total:", report["inventory"]["total"])
PY
```

Real output from a run of the block above:

```
Agent registered: lattice-web
  Location: mem20crossruntimeeventlatticez
  Agent ID: 6c39be61
  Registered: 2026-11-01T19:24:29.888889+00:00
Broadcast from lattice-web: session.view id=0544c243 source=edge...
event id       : 0544c243
parent         : 5ac56c4c
vector clock   : {'5ac56c4c': 1793561069.8869495}
memory topic   : lattice.web.session.view
announced by   : lattice-web
recalled rows  : 1
recalled body  : {'page': '/pricing'}
lattice count  : 2
by type        : {'session.start': 1, 'session.view': 1}
sources        : ['edge', 'local']
causal links   : 1
inventory total: 312
```

## CLI

```bash
# emit + link + persist + announce
python3 -m mem20crossruntimeeventlatticez emit \
    --type click --payload '{"x": 1}' --lattice web --source edge

# operational report for a merged lattice
python3 -m mem20crossruntimeeventlatticez report --lattice web --lattices 2 --events 2

# round-trip the memory engine and exit non-zero if the ledger is unfaithful
python3 -m mem20crossruntimeeventlatticez verify

# measured estate inventory counts
python3 -m mem20crossruntimeeventlatticez inventory

# multi-hop search over lattice history
python3 -m mem20crossruntimeeventlatticez search \
    "which runtime emitted the first failure and what did it cause"

# quantize a numeric payload for the wire
python3 -m mem20crossruntimeeventlatticez compact 1.0 2.0 3.0 4.0 --bits 8
```

## MCP tools

Registered on the mem20 MCP server (`mcp/server.py` → `LatticeToolsMixin`):

| Tool | What it does |
|---|---|
| `lattice_emit` | Emit, causally link, persist and announce one event |
| `lattice_report` | Merged-lattice health + substrate health in one call |
| `lattice_recall` | Read back persisted events for a lattice/type |
| `lattice_verify` | Round-trip the memory engine, report ledger fidelity |
| `lattice_search` | Decompose a compound causality question into sub-retrievals |

## Estate wiring (criterion 6)

Every one of these is a real call on a tested path — see
`mem20crossruntimeeventlatticez/tests/test_integration.py`.

| mem20 project | API used | Where |
|---|---|---|
| `memory_engine` | `memory.remember` / `memory.recall` / `memory.status` | `integration.remember_event`, `recall_events`, `memory_status` |
| `memory_engine` | `retrieval_v2.decompose_query` | `integration.search_history` |
| `toolchest` | `catalog.load_inventory` | `integration.capability_inventory` |
| `gateway` | `hermes_gateway.broadcast` / `register_agent` / `load_names` | `integration.announce` |
| `mem20verify` | `dataintegrity.check` | `integration.verify_memory_integrity` |
| `mem20ops` | `memchecks.identity_check` | `integration.identity_report` |
| `mem20corez` | `quantizer.quantize_tensor` | `integration.compact_payload` |

### Two estate traps this subsystem has to handle

Both are real and both are documented in `_bootstrap.py` rather than papered
over:

1. **Shim shadowing.** `mem20corez/__init__.py` is a version-only shim sitting
   next to the real package at `mem20corez/mem20corez/`. With the repo root on
   `sys.path`, `import mem20corez` resolves to the shim and `quantizer` is
   unreachable. `_bootstrap.ensure_estate_path()` puts the inner package parent
   ahead of the repo root and evicts an already-imported shim.
2. **`memory` shim vs engine.** The repo root ships a `memory.py` that
   re-exports `memory_engine.memory`. `mem20verify.dataintegrity.check()`
   rebinds `ENTRIES`/`LEDGER` on whatever `import memory` returns, so if the
   shim wins, the rebinding lands on the shim and the check reports 0
   round-trips while looking like a data-integrity failure.
   `verify_memory_integrity()` binds the real engine module first.

## Tests

```bash
python3 -m pytest mem20crossruntimeeventlatticez -q
```

## Conformance

```bash
python3 scripts/renovation/conformance.py mem20crossruntimeeventlatticez
```

## Public API

```python
from mem20crossruntimeeventlatticez import domain, integration

# domain — the lattice itself
domain.emit(event_type, payload, source="local") -> dict
domain.order_events(events) -> list[dict]
domain.causal_link(parent, child) -> dict
domain.lattice_merge(lattices) -> dict
domain.filter_by_type(events, etype) -> list[dict]

# integration — the seam onto the estate
integration.emit_and_record(event_type, payload, lattice="default", source="local", parent=None, announce_to_fleet=True) -> dict
integration.remember_event(event, lattice="default", actor="lattice") -> dict
integration.recall_events(lattice, event_type=None) -> list[dict]
integration.lattice_report(lattices, name="default", window_s=60) -> dict
integration.search_history(query, k=5) -> dict
integration.capability_inventory() -> dict
integration.announce(event, lattice="default", agent_name=None) -> dict
integration.verify_memory_integrity() -> dict
integration.identity_report() -> dict
integration.compact_payload(values, bits=8) -> dict
```
