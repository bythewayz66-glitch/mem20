# RM-225 — Visual Agent Blackboard

**Outcome:** Expose agent perceptions, goals, memory, plans, messages, and live actions

**Breakthrough:** Autonomous behavior becomes understandable and debuggable

This package is the machine-executable local implementation derived from the supplied Off Record Lab roadmap. It includes versioned typed state, SQLite WAL persistence, event history/snapshots, SDK CRUD/subscription, resumable idempotent jobs, cancellation, retries/timeouts/quotas/backpressure, deterministic replica reconciliation, local/hybrid/cloud placement/failover, roadmap-specific `search` logic, decision confidence/explanations, feedback, CLI, HTTP console/API, safety guards, simulator, benchmark/metrics, and rollback-capable installer.

Named live product surfaces, real provider/device credentials, production traffic, and governed FreeStack deployment remain target-environment integration and are not claimed complete.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20visualagentblackboardz --help
python -m mem20visualagentblackboardz simulate
python -m mem20visualagentblackboardz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20visualagentblackboardz/mem20visualagentblackboardz/tests -q
```
