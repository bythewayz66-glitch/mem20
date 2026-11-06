# RM-099 — Self-Tuning Resource Governor

Outcome: Continuously adjust CPU, memory, I/O, and queue budgets by observed value and demand

Breakthrough: The platform stays responsive under changing workloads

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `search` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20selftuningresourcegovernorz --help
python -m mem20selftuningresourcegovernorz simulate
python -m mem20selftuningresourcegovernorz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20selftuningresourcegovernorz/mem20selftuningresourcegovernorz/tests -q
```
