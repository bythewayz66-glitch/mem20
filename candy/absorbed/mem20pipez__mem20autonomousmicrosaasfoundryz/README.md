# mem20autonomousmicrosaasfoundryz — Autonomous Micro-SaaS Foundry

First-class mem20 subsystem for micro-SaaS founding: score ideas, generate MVP specs, plan launches, project revenue, and rank ideas — with **6 subsystem-specific estate peers** (no generic template), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Architecture
- `domain.py` — pure ops + `foundry_report()`/`probe()`/`estate_context()`
- `ecosystem.py` — 6 adapters (bootstrap); failures reported, never fatal
- `runtime.py` — `Service` + SQLite WAL `EventStore`; CLI; HTTP API; serves `web/`
- `web/` — vanilla cockpit (no build). `docs/PLAN.md`, `docs/app/` monitor, gateway, MCP.

## Peers (6, subsystem-specific)
| peer | real functions | role |
|---|---|---|
| `mem20simz` | `revenue,profit,margin,scenario_sim` | economics/margin/scenarios |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain` | demand forecast signal |
| `mem20studioz` | `schedule_projects,resource_allocation,studio_health` | MVP build scheduling |
| `mem20autonomoussaleslaboratoryz` | `pipeline_value,conversion_probability,segment_leads` | launch pipeline/leads |
| `mem20loreragcontentgeneratorz` | `generate,rank_adapters,quality_score` | landing/content quality |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` add/locate/distribution | capability/stack routing |

## Python API
```python
from mem20autonomousmicrosaasfoundryz.domain import (
    score_idea, mvp_spec, launch_plan, revenue_projection, idea_ranking,
    foundry_report, probe, estate_context,
)

idea = {"name": "tool", "market_size": 800, "competition": 2, "effort": 3, "features": ["auth","core","billing"], "price": 9}
print(score_idea(idea))
print(mvp_spec(idea))
print(launch_plan(idea))
print(revenue_projection(users=100, price=9))
print(idea_ranking([idea, {**idea, "market_size": 100}]))

report = foundry_report(idea)
print(report["ok"], report["idea_score"], len(report["peers"]))  # 6 peers
print(probe()["ok"])
print(estate_context()["peer_count"])
```

## CLI
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz serve --port 8783
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `POST /api/score`, `GET /api/events|health`. Cockpit at `/` (served). State: `~/.mem20/autonomousmicrosaasfoundryz/state.sqlite3` (SQLite WAL). docs/app: `docs/app/autonomousmicrosaasfoundryz/index.html` (no Vite assets edited), linked from `docs/app/README.md`.

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz serve --port 8783
```

## MCP & registration
`AutonomousMicroSaaSFoundryToolsMixin` (`mcp/tools/mem20autonomousmicrosaasfoundryz_tools.py`) in `mcp/server.py` (`autonomousmicrosaasfoundryz_status|doctor`). Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomousmicrosaasfoundryz/mem20autonomousmicrosaasfoundryz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomousmicrosaasfoundryz
node --check mem20autonomousmicrosaasfoundryz/mem20autonomousmicrosaasfoundryz/web/app.js
```
Target: **7/7**.

## Limits
Deterministic scoring/planning logic; real market/payment/hosting integrations are target-environment concerns. Peer unavailability surfaced, not fatal.
