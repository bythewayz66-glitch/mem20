# RM-031 — Intent-to-Mission Compiler

Outcome: Convert a human objective into executable missions, dependencies, roles, and completion criteria

Breakthrough: A vague goal becomes a live operating plan in seconds

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `compose` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20intenttomissioncompilerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20intenttomissioncompilerz benchmark
```
