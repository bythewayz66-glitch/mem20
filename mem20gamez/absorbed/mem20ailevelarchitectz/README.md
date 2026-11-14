# mem20ailevelarchitectz — AI Level Architect

Generate room layouts, difficulty curves, enemy placements, and pacing profiles, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20ailevelarchitectz.domain import (
    generate_layout, difficulty_curve, place_enemies, pacing_profile, validate_level, estate_context,
)

layout = generate_layout(width=30, height=20, rooms=5, seed=1)
print(len(layout["rooms"]))
print(difficulty_curve(levels=5))
print(place_enemies(layout, density=0.2, seed=1)[:2])
print(pacing_profile(total_time=120))
print(validate_level(layout))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20ailevelarchitectz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20ailevelarchitectz/mem20ailevelarchitectz/tests -q
```
