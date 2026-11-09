# mem20crossproductloyaltygraphz — Cross-Product Loyalty Graph

First-class mem20 subsystem for cross-product loyalty graphs (edges, degree, centrality, recommendations, loyalty score) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app, and real MCP tools. Core API preserved.

## Peers (6)
`mem20customerlifecycleenginez`, `mem20simz`, `mem20autonomoussaleslaboratoryz`, `mem20communitychallengeenginez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20crossproductloyaltygraphz.domain import add_edge, degree, centrality, recommend_products, loyalty_score, loyalty_report, probe
g={}; add_edge(g,"a","b",1); print(degree(g,"a"))  # 1
add_edge(g,"a","c"); print(centrality(g)["a"])     # 1.0
print(recommend_products(g,["a"],1)[0]["product"]) # b or c
print(loyalty_score(["a"],g) > 0)                   # True
r=loyalty_report(); print(r["ok"], len(r["peers"])) # True 6
print(probe()["ok"])                                # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz serve --port 8796
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/crossproductloyaltygraphz/index.html` (no Vite edits).

## MCP & registration
`CrossProductLoyaltyGraphToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20crossproductloyaltygraphz/mem20crossproductloyaltygraphz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20crossproductloyaltygraphz
```
Target **7/7**.
