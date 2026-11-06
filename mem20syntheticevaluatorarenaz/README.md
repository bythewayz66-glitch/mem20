# RM-067 — Synthetic Evaluator Arena

Outcome: Generate adversarial tasks and continuously compare model behavior under real constraints

Breakthrough: Model selection improves through live competition rather than marketing claims

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `analyze` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20syntheticevaluatorarenaz --help
python -m mem20syntheticevaluatorarenaz simulate
python -m mem20syntheticevaluatorarenaz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20syntheticevaluatorarenaz/mem20syntheticevaluatorarenaz/tests -q
```
