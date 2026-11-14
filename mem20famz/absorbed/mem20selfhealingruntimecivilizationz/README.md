# RM-217 — Self-Healing Runtime Civilization

**Outcome:** Coordinate prediction, diagnosis, repair, migration, and recovery across every runtime
**Breakthrough:** The ecosystem remains operational through failures that would stop ordinary platforms

A civilization here is a set of agents plus the dependency edges between them. An agent is usable
while its own health is unspent **and** the agents it depends on are usable — failure propagates
along the graph. One cycle is: **sample → quarantine → cascade → repair (bounded) → recover
(all-or-nothing)**.

Two invariants are the point of the design:

- **Bounded work.** A cycle performs at most one repair attempt per unhealthy agent, and an agent has
  a hard lifetime repair budget. A permanently dead dependency can never make the controller spin.
- **No silent recovery.** `status` reports `recovered` only when nothing is left unhealthy. A
  partially healed fleet reports `degraded` — it never rounds up.

## Install (source only — mem20 is not on PyPI)

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

There is no `pip install mem20`. The subsystem itself is standard-library-only; it reaches the rest
of mem20 through the repository tree, which is why it must run from a clone.

## Quickstart — run the demo cycle

```bash
cd mem20selfhealingruntimecivilizationz
python3 -m mem20selfhealingruntimecivilizationz demo
```

Real output (abridged to the decision-relevant fields):

```json
{
  "status": "healthy",
  "quarantined": ["gateway", "mcp", "memory_engine", "sdk"],
  "cascaded": ["mcp", "memory_engine", "sdk"],
  "repaired": ["gateway", "mcp", "memory_engine", "sdk"],
  "recovered": true,
  "remaining": [],
  "health": {"agents": 4, "alive": 4, "quarantined": 0, "dead": 0,
             "avg_health": 0.925, "usable_ratio": 1.0}
}
```

The gateway drops to 0.20 (below the 0.30 threshold); its dependents are quarantined by the cascade
and every agent is repaired inside the budget, so the cycle recovers in one pass.

## Run it against the real estate

```bash
cd mem20selfhealingruntimecivilizationz
python3 -m mem20selfhealingruntimecivilizationz probe              # which mem20 integrations resolve
python3 -m mem20selfhealingruntimecivilizationz --state-dir /tmp/sh run --cycles 2
python3 -m mem20selfhealingruntimecivilizationz report
python3 -m mem20selfhealingruntimecivilizationz serve --port 8099  # /health /ready /metrics
```

`probe` on this checkout reports **7/7** integrations:

```
available: 7 / 7
  MemoryEngineBridge     True memory
  RetrievalBridge        True retrieval_v2
  HealthSurfaceBridge    True mcp/health.py
  GatewayBridge          True mem20_gateway
  ToolchestBridge        True toolchest.catalog
  KilnBudgetBridge       True mem20kilnz.budgets
  PlansEngineBridge      True mem20selfhealingplansz
```

`run --cycles 2` builds the fleet from the real catalogue and repairs it:

```
cycle 1 | status healthy | quarantined 12 | repaired 12 | budget 3 | ts_validated True
cycle 2 | status healthy | quarantined 0  | repaired 0  | budget 3 | ts_validated True
```

Subsystems that are importable start near-full health, ones that are not start degraded, so the first
cycle has genuine work to do instead of a synthetic scenario.

## Library

```python
from mem20selfhealingruntimecivilizationz import Civilization, FleetController

civ = Civilization(threshold=0.3, repair_amount=0.5, max_repairs=3)
civ.add_agent("gateway")
civ.add_agent("mcp", depends_on=["gateway"])
civ.damage("gateway", 0.8)
record = civ.run_cycle()          # bounded; returns what happened
assert civ.status() == "healthy"  # recovered in one pass

controller = FleetController.from_catalogue(limit=6)
controller.cycle()
controller.metrics_snapshot()
```

## Substrate: what this subsystem actually uses (criterion 6)

Seven mem20 modules are imported **and called on a tested path** — see
`mem20selfhealingruntimecivilizationz/integrations.py` and
`tests/test_integration.py`:

| Module | What it actually does here |
|---|---|
| `memory_engine.memory` | `validate_event_time` stamps every cycle record; `redact_secrets` scrubs repair error text before persist/publish |
| `memory_engine.retrieval_v2` | `decompose_query` splits a failure description into repair targets |
| `mcp/health.py` | the shared `/health /ready /metrics` server, fed by a live adapter over this controller |
| `gateway.mem20_gateway` | `register_agent` announces the subsystem; `broadcast` publishes each cycle summary |
| `toolchest.catalog` | `discover_subsystems` is the fleet roster and the importability signal |
| `mem20kilnz` | `TRIANGLE_BUDGETS` is the source of the per-subsystem repair ceiling |
| `mem20selfhealingplansz` | `Engine.execute` decides the repair action (failover/restart) instead of a local rule |

## Tool surface (criterion 7)

Three MCP tools live in `mcp/tools/civilization_tools.py`, following the same
`*ToolsMixin` shape as `braid_tools.py`:

| Tool | What it does |
|---|---|
| `civilization_health` | fleet status, per-agent health, budget, resolved integrations |
| `civilization_cycle` | run 1–5 bounded cycles over the real catalogue and persist the records |
| `civilization_report` | full report: civilization state, planner actions, budget, metrics |

They are callable and tested today — the test imports the module exactly the way the server
does and calls every tool:

```bash
# from the repository root
python3 -c "import sys; sys.path.insert(0, 'mcp'); \
from tools.civilization_tools import CIVILIZATION_TOOLS, tool_specs; \
print(sorted(tool_specs())); \
print(CIVILIZATION_TOOLS['civilization_health'](None)['status'])"
```

Real output:

```
['civilization_cycle', 'civilization_health', 'civilization_report']
healthy
```

`mcp/server.py` composes its mixins from a hard-coded list and has no plugin/auto-discovery
hook, so serving these three tools also needs `CivilizationToolsMixin` added to
`Mem20MCPServer`'s bases — a one-line change in a 48 KB file that four other in-flight
branches also edit. That edit is deliberately **not** bundled here (it would conflict); it is
recorded as a follow-up in `docs/renovation/4.0/FINDINGS.md`. Until it lands the tools are
importable, tested and callable, but not yet served by the running server.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `MEM20_SELFHEALING_STATE` | `state/selfhealing` | state dir (SQLite WAL store, gateway spool, planner DB) |

`ControllerConfig(threshold=0.30, repair_amount=0.50, max_repairs=3, history_limit=200, announce=True)`
overrides the same knobs from code.

## Tests

```bash
python3 -m pytest mem20selfhealingruntimecivilizationz -q
```

Contract, unit, property-based (Hypothesis with a deterministic fallback grid) and integration tests,
including a real HTTP request to the health surface and real gateway state files on disk.

## Named limits (not claimed complete)

Live product surfaces, real provider credentials, production traffic, and governed FreeStack
deployment remain target-environment integration. The planner is asked for an action and its
vocabulary drives the recovery amount; it does not execute the failover itself.
