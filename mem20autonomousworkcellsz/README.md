# mem20autonomousworkcellsz — Autonomous Work Cells

Create work cells, enqueue tasks, assign workers, process work, and measure throughput/health, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20autonomousworkcellsz.domain import (
    create_cell, enqueue, assign_workers, process_next, throughput, cell_health, estate_context,
)

cell = create_cell("build", capacity=2)
enqueue(cell, {"id": "t1"})
assign_workers(cell, ["w1", "w2"])
print(process_next(cell))
print(throughput(cell))
print(cell_health(cell))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20autonomousworkcellsz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20autonomousworkcellsz/mem20autonomousworkcellsz/tests -q
```
