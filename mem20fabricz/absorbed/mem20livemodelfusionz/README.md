# mem20livemodelfusionz — Live Model Fusion

Combine specialist model outputs dynamically (weighted fusion, confidence weighting, best-model selection, ensemble voting) with mem20 estate integration.

## Python API

```python
import tempfile
from mem20livemodelfusionz.domain import fuse, ensemble_vote, estate_context

models = [{"outputs": {"score": 1.0}, "confidence": 0.8}, {"outputs": {"score": 3.0}, "confidence": 0.2}]
print(fuse(models)["fused"])
print(ensemble_vote(["a", "b", "a"]))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20livemodelfusionz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20livemodelfusionz/mem20livemodelfusionz/tests -q
```
