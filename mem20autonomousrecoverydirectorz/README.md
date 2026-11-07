# mem20autonomousrecoverydirectorz — Autonomous Recovery Director

Triage incidents, plan rollbacks, remediate safely, estimate recovery time, and assess post-recovery health, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20autonomousrecoverydirectorz.domain import (
    triage, rollback_plan, remediate, recovery_time, health_after, estate_context,
)

print(triage({"severity": "critical"}))
print(rollback_plan({"version": 2}, {"version": 1}))
print(remediate({}, [{"safe": True}, {"safe": False}]))
print(recovery_time({"severity": "low"}))
print(health_after({"success_rate": 0.8}))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20autonomousrecoverydirectorz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20autonomousrecoverydirectorz/mem20autonomousrecoverydirectorz/tests -q
```
