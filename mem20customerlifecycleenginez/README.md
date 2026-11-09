# mem20customerlifecycleenginez — Customer Lifecycle Engine

First-class mem20 subsystem for customer lifecycle modeling (stages, transitions, retention probability, lifetime value, segmentation) with **6 subsystem-specific peers**, a SQLite WAL event runtime, CLI, JSON HTTP API, a served web cockpit, docs/app monitor, and real MCP tools. Core public API is preserved.

## Peers (6, job-fitting)
`mem20simz` (economic/LTV context), `mem20autonomoussaleslaboratoryz` (pipeline/segment signal), `mem20crossproductloyaltygraphz` (loyalty/upsell context), `mem20demandforecastandcapacitybrainz` (demand signal), `mem20eventstreamsuperhighwayz` (lifecycle event stream), `mem20acquisitionandpartnershipscoutz` (growth/partnership fit). Each adapter calls real APIs and returns computed results; failures surface as `{"ok": false, "error": "..."}` (reported, not swallowed).

## Python API (runnable)
```python
from mem20customerlifecycleenginez.domain import (
    lifecycle_stage, transition, retention_probability, lifetime_value,
    segment_customers, lifecycle_report, probe, estate_context,
)

print(lifecycle_stage({"days_since_signup": 3, "purchases": 0}))  # onboarding
print(transition({"days_since_signup": 30, "purchases": 1}, "purchase"))  # active
print(retention_probability({"engagement": 0.5, "recency_days": 30}))  # 0.4167
print(lifetime_value({"avg_order_value": 50, "purchase_frequency": 2, "expected_lifespan_months": 12}))  # 1200.0
segs = segment_customers([{"id": "a", "days_since_signup": 3, "purchases": 0}])
print("a" in segs["onboarding"])  # True

r = lifecycle_report()
print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])             # True
print(estate_context()["peer_count"])  # 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerlifecycleenginez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerlifecycleenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerlifecycleenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerlifecycleenginez simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerlifecycleenginez serve --port 8798
```

## JSON HTTP API & web
`GET /api/health`, `GET|POST /api/status` (lifecycle report + 6 peers), `GET|POST /api/doctor`, `POST /api/simulate`, `GET /api/events`. Served cockpit at `/` from `web/`. docs/app monitor: `docs/app/customerlifecycleenginez/index.html` (no Vite edits), linked from `docs/app/README.md`.

## MCP & registration
Real tools `customerlifecycleenginez_status` / `customerlifecycleenginez_doctor` via `CustomerLifecycleEngineToolsMixin` in `mcp/tools/mem20customerlifecycleenginez_tools.py`, registered in `mcp/server.py`. Gateway `SUBSYSTEMS` entry in `gateway/mem20_gateway.py`.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20customerlifecycleenginez/mem20customerlifecycleenginez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20customerlifecycleenginez
```
Target **7/7**.
