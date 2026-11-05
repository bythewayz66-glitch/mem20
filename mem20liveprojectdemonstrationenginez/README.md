# mem20liveprojectdemonstrationenginez — Live Project Demonstration Engine

Create and step through live project demonstrations (flows, steps, progress) with mem20 estate integration.

## Python API

```python
import tempfile
from mem20liveprojectdemonstrationenginez.domain import create_demo, add_step, start, advance, progress, estate_context

demo = create_demo("my-project", steps=[{"title": "intro"}])
add_step(demo, {"title": "deep-dive"})
start(demo)
print(advance(demo))
print(progress(demo))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20liveprojectdemonstrationenginez --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20liveprojectdemonstrationenginez/mem20liveprojectdemonstrationenginez/tests -q
```
