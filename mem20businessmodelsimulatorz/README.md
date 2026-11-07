# mem20businessmodelsimulatorz — Business Model Simulator

First-class mem20 subsystem for business model simulation: revenue, cost, profit, margin, break-even, multi-period scenarios, and sensitivity analysis — with **6 business-model-specific estate peers** (unique set, no generic template), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools. Core functions (`revenue`, `cost`, `profit`, `margin`, `break_even`, `scenario_sim`, `sensitivity`) remain stable for dependent subsystems.

## Architecture
- `domain.py` — core modeling ops + `model_report()`/`probe()`/`estate_context()`
- `ecosystem.py` — 6 peer adapters (real API calls; failures reported `{"ok":false,"error":...}`, never fatal)
- `runtime.py` — `Service` + SQLite WAL `EventStore`; CLI; `ThreadingHTTPServer` JSON API serving `web/`
- `web/` — vanilla cockpit (no build). `docs/PLAN.md`, `docs/app/businessmodelsimulatorz/`, gateway, MCP.

## Ecosystem peers (6, business-model specific)
| peer | real functions/classes | role |
|---|---|---|
| `mem20demandforecastandcapacitybrainz` | `DemandForecastAndCapacityBrain` (observe/forecast/capacity_for) | demand/capacity assumptions & headroom |
| `mem20counterfactualmemorysimulatorz` | `counterfactual`, `compare`, `outcome_probability` | counterfactual scenario/what-if analysis |
| `mem20acquisitionandpartnershipscoutz` | `strategic_fit`, `synergy_estimate`, `target_score` | partnership/strategic fit & synergy inputs |
| `mem20customerlifecycleenginez` | `lifecycle_stage`, `lifetime_value`, `retention_probability` | lifecycle stage, LTV, retention |
| `mem20crossproductloyaltygraphz` | `add_edge`, `recommend_products`, `loyalty_score`, `centrality` | loyalty/upsell graph signals |
| `mem20autonomoussaleslaboratoryz` | `pipeline_value`, `conversion_probability`, `segment_leads` | pipeline/conversion revenue signals |

## Python API (runnable)
```python
from mem20businessmodelsimulatorz.domain import (
    revenue, cost, profit, margin, break_even, scenario_sim, sensitivity,
    model_report, probe, estate_context,
)

print(revenue(100, 10))                 # 1000.0
print(cost(500, 2, 100))                 # 700.0
print(profit(1000, 700), margin(1000, 700))  # 300.0 0.3
print(break_even(1000, 10, 6))           # 250
scen = scenario_sim(100, 10, 500, 3, 0.1, 3)
print(len(scen), scen[-1]["units"] > 100)    # 3 True
print(sensitivity(10, 100, 500, 3)["base"])  # base profit

report = model_report(base_units=100, price=10.0, fixed=200.0, var=4.0)
print(report["ok"], report["break_even_units"], len(report["peers"]))  # 6 peers
print(probe()["ok"], estate_context()["peer_count"])                   # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz serve --port 8788
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `POST /api/sensitivity`, `GET /api/events|health`. Cockpit at `/`. State: `~/.mem20/businessmodelsimulatorz/state.sqlite3` (WAL) or `--store`/`MEM20_BIZMODEL_STORE`. docs/app: `docs/app/businessmodelsimulatorz/index.html` (no Vite edits), linked from `docs/app/README.md`.

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz serve --port 8788
```

## MCP & registration
`BusinessModelSimulatorToolsMixin` (`mcp/tools/mem20businessmodelsimulatorz_tools.py`) in `mcp/server.py` (`businessmodelsimulatorz_status|doctor`). Gateway `SUBSYSTEMS["mem20businessmodelsimulatorz"]`.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20businessmodelsimulatorz/mem20businessmodelsimulatorz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20businessmodelsimulatorz
node --check mem20businessmodelsimulatorz/mem20businessmodelsimulatorz/web/app.js
```
Target **7/7**.

## Limits
Deterministic modeling; real accounting/market data integrations are target-environment concerns. Peer unavailability surfaced, not fatal. Core API preserved for dependents.
