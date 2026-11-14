# RM-052 — Reversible Execution Graph

Outcome: Make every multi-step action capable of compensation, pause, branch, and rollback

Breakthrough: Autonomous systems can recover from mistakes without restarting everything

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `graph` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Install

mem20 is **not on PyPI**. Install from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

## Run the CLI

```bash
cd mem20/mem20reversibleexecutiongraphz
python3 -m mem20reversibleexecutiongraphz simulate
```

## Runnable example: execute a reversible plan

`execute_reversible_plan()` records each step on the graph and audits the run
against the rest of the estate — credential screening (`mem20secretz`), per-step
budget (`mem20kilnz`), grounded ledger write + read-back (`memory_engine`),
store round-trip (`mem20verify`), estate registration (`toolchest`), and the
fleet registry (`gateway`). `reversible` is True only when every step was
accepted and the graph cursor sits on the last node, i.e. the whole run can be
undone.

```python
import json
import sys

# run from the mem20 repo root
sys.path.insert(0, "mem20reversibleexecutiongraphz")

from mem20reversibleexecutiongraphz.integration import execute_reversible_plan

report = execute_reversible_plan(
    plan_id="p1",
    steps=[
        {"id": "s1", "payload": {"op": "resize"}, "triangles": 3000},
        {"id": "s2", "payload": {"op": "retexture"}, "triangles": 4000},
    ],
    family="prop",
)

print(json.dumps(report, indent=2, sort_keys=True))
print("reversible:", report["reversible"])
```

Real output from that script:

```text
{
  "budgets": [
    {
      "ok": true,
      "reason": "within standard 2000-6000",
      "step": "s1"
    },
    {
      "ok": true,
      "reason": "within standard 2000-6000",
      "step": "s2"
    }
  ],
  "fleet": {
    "agents": 0
  },
  "health": {
    "cursor": 1,
    "history": 2,
    "nodes": 2
  },
  "integrity": {
    "checked": 11,
    "error": "",
    "ok": true,
    "roundtrip_ok": 11
  },
  "inventory": {
    "entries": 312,
    "path": "/workspace/mem20/toolchest/inventory.json",
    "subsystem_registered": true
  },
  "ledger": {
    "ok": true,
    "rows": 4,
    "topic": "plan.p1"
  },
  "ok": true,
  "plan_id": "p1",
  "refused": [],
  "reversible": true,
  "secrets": []
}
reversible: True
```

A step whose payload carries a credential, or whose triangle count is outside
its family budget, is listed in `refused` and the run reports
`reversible: false` — the plan is not silently half-applied.

`rollback_plan()` undoes every step and records the rollback in the ledger.

## MCP surface

Registered with the mem20 MCP server as `graph_execute_reversible_plan`
(`mcp/tools/rm052_tools.py`):

```json
{"plan_id": "p1", "steps": [{"id": "s1", "payload": {"op": "resize"}, "triangles": 3000}]}
```

## Tests

```bash
python3 -m pytest mem20reversibleexecutiongraphz -q
```
