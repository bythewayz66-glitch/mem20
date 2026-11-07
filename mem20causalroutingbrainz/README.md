# mem20causalroutingbrainz — Causal Routing Brain

Estimate causal effects, route by causal weights, adjust for confounders, score interventions, and build causal graphs, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20causalroutingbrainz.domain import (
    causal_effect, route_by_cause, confounder_adjust, intervention_value, causal_graph, estate_context,
)

print(causal_effect([10, 12], [5, 6]))
print(route_by_cause({"x": 1, "y": 2}, {"x": 0.5, "y": 1.0}))
print(confounder_adjust(1.0, 0.2))
print(intervention_value(5, 8))
print(causal_graph([("a", "b"), ("b", "c")]))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20causalroutingbrainz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20causalroutingbrainz/mem20causalroutingbrainz/tests -q
```
