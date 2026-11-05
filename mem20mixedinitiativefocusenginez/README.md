# mem20mixedinitiativefocusenginez — Mixed-Initiative Focus Engine

Balances autonomous progress with moments requiring human judgment by scoring focus, ranking suggestions, and blending user/agent intent.

## Features
- `focus_score`, `focus_health`, `suggest`, `take_over`, `blend`
- `estate_context()` performs real integrations with `memory_engine`, `toolchest`, `mem20path`, `mem20webhooksupernetworkz`, and `mem20memorytimemachinez`

## CLI / Runtime

```bash
python -m mem20mixedinitiativefocusenginez --help
```

## Python API

```python
import tempfile
from mem20mixedinitiativefocusenginez.domain import focus_score, suggest, blend, estate_context

print(focus_score({"priority": 2, "distractions": 1}))
print(suggest({"distractions": 0}, [{"name": "a", "priority": 1}, {"name": "b", "priority": 3}])[0]["name"])
print(blend({"priority": 10}, {"priority": 0}, alpha=0.5))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20mixedinitiativefocusenginez/mem20mixedinitiativefocusenginez/tests -q
```
