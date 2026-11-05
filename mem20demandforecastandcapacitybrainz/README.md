# mem20demandforecastandcapacitybrainz — Demand Forecast and Capacity Brain

EWMA-based demand forecasting with honest prediction intervals and capacity headroom, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain, estate_context

b = DemandForecastAndCapacityBrain()
for v in [10, 12, 11, 13, 12, 14, 13, 15]:
    b.observe(v)
print(b.forecast())
print(b.capacity_for(0.99))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20demandforecastandcapacitybrainz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20demandforecastandcapacitybrainz/mem20demandforecastandcapacitybrainz/tests -q
```
