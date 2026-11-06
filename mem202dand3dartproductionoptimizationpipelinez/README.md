# mem202dand3dartproductionoptimizationpipelinez — 2D/3D Art Production Optimization Pipeline

Asset budgeting, LOD selection, texture memory estimation, batching, and pipeline optimization, with mem20 estate integration.

## Python API

```python
import tempfile
from mem202dand3dartproductionoptimizationpipelinez.domain import (
    lod_level, texture_memory, batch_efficiency, optimize_pipeline, frame_budget, estate_context,
)

print(lod_level(poly_count=50000))
print(texture_memory(1024, 1024))
print(batch_efficiency(asset_count=100, batch_size=64))
print(optimize_pipeline([{"id": "hero", "polys": 20000, "tex_w": 1024, "tex_h": 1024}]))
print(frame_budget(60))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem202dand3dartproductionoptimizationpipelinez --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem202dand3dartproductionoptimizationpipelinez/mem202dand3dartproductionoptimizationpipelinez/tests -q
```
