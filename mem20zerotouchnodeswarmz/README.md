# RM-042 — Zero-Touch Node Swarm

Outcome: Discover, enroll, configure, update, and recover trusted nodes with minimal manual setup

Breakthrough: New devices join the fleet almost as easily as Bluetooth accessories

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `analyze` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20zerotouchnodeswarmz --help
python -m mem20zerotouchnodeswarmz simulate
python -m mem20zerotouchnodeswarmz benchmark
```

## Python API

```python
from mem20zerotouchnodeswarmz.domain import (
    register_node, discover, assign_task, heal, quorum,
)

swarm = {"nodes": []}
swarm = register_node(swarm, {"id": "node-a", "capacity": 4, "capabilities": ["cpu"]})
swarm = register_node(swarm, {"id": "node-b", "capacity": 2, "capabilities": ["gpu"]})
print(discover(swarm, capability="cpu"))
print(assign_task(swarm, {"id": "job-1", "capability": "cpu", "urgency": 0.8}))
print(quorum(swarm, 0.5))
print(heal(swarm))
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20zerotouchnodeswarmz/mem20zerotouchnodeswarmz/tests -q
```
