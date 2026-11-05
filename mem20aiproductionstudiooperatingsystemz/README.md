# mem20aiproductionstudiooperatingsystemz — AI Production Studio OS

Schedule projects, allocate resources, track milestones, compute critical path and studio health, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20aiproductionstudiooperatingsystemz.domain import schedule_projects, resource_allocation, milestone_progress, critical_path, studio_health, estate_context

projects = [{"id": "p1", "priority": 2, "effort": 2}, {"id": "p2", "priority": 1, "effort": 1}]
print(schedule_projects(projects, capacity=3))
print(critical_path(["a", "b", "c"], {"b": ["a"], "c": ["b"]}))
print(studio_health(projects, capacity=5))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20aiproductionstudiooperatingsystemz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20aiproductionstudiooperatingsystemz/mem20aiproductionstudiooperatingsystemz/tests -q
```
