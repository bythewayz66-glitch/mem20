# mem20faultcontainmentcellsz — Fault Containment Cells

Circuit-breaker style fault containment (closed → open → half-open) with fail-fast behavior, plus mem20 estate integration.

## Python API

```python
import tempfile
from mem20faultcontainmentcellsz.domain import FaultContainmentCells, estate_context

cell = FaultContainmentCells(threshold=2, cool_down=10.0)
print(cell.call(lambda: 42))
print(cell.state)

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20faultcontainmentcellsz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20faultcontainmentcellsz/mem20faultcontainmentcellsz/tests -q
```
