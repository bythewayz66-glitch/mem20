# mem20livingagenteconomyz — Living Agent Economy

A lightweight agent economy (balances, earn/spend/trade, reputation) with mem20 estate integration.

## Python API

```python
import tempfile
from mem20livingagenteconomyz.domain import create_economy, earn, trade, estate_context

econ = create_economy(["agent-a", "agent-b"])
earn(econ, "agent-a", 50, "task")
trade(econ, "agent-a", "agent-b", 10)
print(econ["agents"]["agent-b"]["balance"])

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20livingagenteconomyz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20livingagenteconomyz/mem20livingagenteconomyz/tests -q
```
