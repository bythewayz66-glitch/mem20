# mem20capabilitymarketplacez — Capability Marketplace

Consistent-hashing capability routing with virtual nodes, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20capabilitymarketplacez.domain import CapabilityMarketplace, estate_context

m = CapabilityMarketplace(replicas=64)
for c in ("alpha", "beta", "gamma"):
    m.add(c)
print(m.locate("my-key"))
print(dict(m.distribution(500)))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20capabilitymarketplacez --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20capabilitymarketplacez/mem20capabilitymarketplacez/tests -q
```
