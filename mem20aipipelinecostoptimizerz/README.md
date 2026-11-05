# mem20aipipelinecostoptimizerz — AI Pipeline Cost Optimizer

Estimate stage/pipeline costs, detect bottlenecks, and optimize throughput under budget, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20aipipelinecostoptimizerz.domain import stage_cost, pipeline_cost, optimize_throughput, bottleneck, estate_context

stages = [{"id": "embed", "base_cost": 1.0, "cost_per_unit": 0.1}, {"id": "infer", "base_cost": 0.5, "cost_per_unit": 0.2}]
print(pipeline_cost(stages, throughput=10))
print(bottleneck(stages, {"embed": 5, "infer": 2}))
print(optimize_throughput(stages, budget=10.0))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20aipipelinecostoptimizerz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20aipipelinecostoptimizerz/mem20aipipelinecostoptimizerz/tests -q
```
