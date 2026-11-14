# mem20connectormarketplacez — Connector Marketplace

Least-connections load balancing with health withdrawal and sticky sessions, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20connectormarketplacez.domain import ConnectorMarketplace, estate_context

r = ConnectorMarketplace(["backend-a", "backend-b"])
print(r.pick())
print(r.pick(key="session-1"))
print(r.in_flight)

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20connectormarketplacez --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20connectormarketplacez/mem20connectormarketplacez/tests -q
```
