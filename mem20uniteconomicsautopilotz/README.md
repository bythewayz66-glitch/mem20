# RM-082 — Unit Economics Autopilot

Outcome: Track contribution margins and recommend operational changes continuously

Breakthrough: Every product knows whether growth is actually healthy

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `optimize` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20uniteconomicsautopilotz --help
python -m mem20uniteconomicsautopilotz simulate
python -m mem20uniteconomicsautopilotz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20uniteconomicsautopilotz/mem20uniteconomicsautopilotz/tests -q
```
