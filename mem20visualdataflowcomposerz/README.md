# RM-079 — Visual Dataflow Composer

Outcome: Build integrations by wiring live typed streams and transformations

Breakthrough: Complex automation becomes understandable and debuggable visually

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `compose` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20visualdataflowcomposerz --help
python -m mem20visualdataflowcomposerz simulate
python -m mem20visualdataflowcomposerz benchmark
```

## Python API

```python
from mem20visualdataflowcomposerz.domain import (
    create_pipeline, add_node, connect, execute, pipeline_health,
)

pipeline = create_pipeline("etl")
source = add_node(pipeline, "source", {"url": "feed"})
transform = add_node(pipeline, "transform", {"expr": "x * 2"})
connect(pipeline, source["id"], transform["id"])
print(pipeline_health(pipeline))
print(execute(pipeline, [1, 2, 3], lambda node, data: {"node": node["type"], "rows": len(data)}))
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20visualdataflowcomposerz/mem20visualdataflowcomposerz/tests -q
```
