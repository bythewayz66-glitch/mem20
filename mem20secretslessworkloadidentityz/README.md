# RM-094 — Secretsless Workload Identity

Outcome: Use short-lived cryptographic workload identities instead of long-lived application secrets

Breakthrough: Services authenticate safely without secret sprawl

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `graph` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20secretslessworkloadidentityz --help
python -m mem20secretslessworkloadidentityz simulate
python -m mem20secretslessworkloadidentityz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20secretslessworkloadidentityz/mem20secretslessworkloadidentityz/tests -q
```
