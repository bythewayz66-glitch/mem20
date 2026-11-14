# mem20acquisitionandpartnershipscoutz — Acquisition & Partnerships Scout

Score and rank acquisition/partnership targets, estimate strategic fit and synergies, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20acquisitionandpartnershipscoutz.domain import (
    target_score, strategic_fit, rank_targets, outreach_priority, synergy_estimate, estate_context,
)

criteria = {"weights": {"revenue": 1.0}, "targets": {"revenue": 100}}
target = {"revenue": 80, "markets": ["devtools"], "tech": ["ai"]}
acquirer = {"revenue": 1000, "markets": ["devtools"], "tech": ["ai", "cloud"]}

print(target_score(target, criteria))
print(strategic_fit(acquirer, target))
print(rank_targets([target, {"revenue": 20}], criteria))
print(outreach_priority(target, criteria))
print(synergy_estimate(acquirer, target))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20acquisitionandpartnershipscoutz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20acquisitionandpartnershipscoutz/mem20acquisitionandpartnershipscoutz/tests -q
```
