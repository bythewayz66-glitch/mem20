# mem20businessmodelsimulatorz — Business Model Simulator

Simulate revenue, costs, profit, margins, break-even, scenarios, and sensitivity, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20businessmodelsimulatorz.domain import (
    revenue, cost, profit, margin, break_even, scenario_sim, sensitivity, estate_context,
)

r = revenue(100, 10)
c = cost(500, 2, 100)
print(r, c, profit(r, c), margin(r, c))
print(break_even(1000, 10, 4))
print(scenario_sim(100, 10, 500, 2, growth=0.1, periods=3))
print(sensitivity(10, 100, 500, 2))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20businessmodelsimulatorz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20businessmodelsimulatorz/mem20businessmodelsimulatorz/tests -q
```
