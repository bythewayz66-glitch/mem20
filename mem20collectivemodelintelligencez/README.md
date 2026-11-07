# mem20collectivemodelintelligencez — Collective Model Intelligence

Combine model predictions via ensembles/voting, measure diversity, distill knowledge, and aggregate confidence, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20collectivemodelintelligencez.domain import (
    ensemble_predict, diversity_score, knowledge_distill, aggregate_confidence, estate_context,
)

print(ensemble_predict([1.0, 2.0, 3.0]))
print(ensemble_predict(["a", "b", "a"]))
print(diversity_score(["a", "b", "a"]))
print(knowledge_distill([1.0, 2.0], [1.1, 1.9]))
print(aggregate_confidence([0.8, 0.9]))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20collectivemodelintelligencez --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20collectivemodelintelligencez/mem20collectivemodelintelligencez/tests -q
```
