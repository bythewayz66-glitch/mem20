# mem20autonomoussaleslaboratoryz — Autonomous Sales Laboratory

First-class mem20 subsystem for sales experiments: score leads, generate outreach, estimate conversion, value pipelines, and segment leads — with **6 sales-lab-specific estate peers** (anti-spam guarded; no generic template), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Peers (6, sales-lab specific)
| peer | real functions | role |
|---|---|---|
| `mem20loreragcontentgeneratorz` | `generate,rank_adapters,quality_score` | approved outreach content/quality |
| `mem20antiexploitationrewardshieldz` | `RewardShield` evaluate/exploit_ratio | anti-spam/guardrail corroboration |
| `mem20demandforecastandcapacitybrainz` | `DemandForecastAndCapacityBrain` | demand/timing signal |
| `mem20eventstreamsuperhighwayz` | `create_stream,publish,throughput` | experiment events |
| `mem20autonomousdealdeskz` | `price_deal,approval_required,negotiate_round` | deal handoff/pricing context |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` add/locate/distribution | channel/capability routing |

## Python API
```python
from mem20autonomoussaleslaboratoryz.domain import (
    lead_score, outreach_message, conversion_probability, pipeline_value, segment_leads,
    lab_report, probe, estate_context,
)
lead = {"name":"Bob","email":"b@x.com","budget":2000,"authority":True,"need":True,"timeline_days":10,"deal_value":1000}
print(lead_score(lead)); print(conversion_probability(lead,3)); print(pipeline_value([lead])); print(segment_leads([lead]))
report = lab_report([lead]); print(report["ok"], report["pipeline_value"], len(report["peers"]))  # 6
print(probe()["ok"])
```

## CLI
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz serve --port 8785
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `POST /api/score`, `GET /api/events|health`. Cockpit at `/`. State: `~/.mem20/autonomoussaleslaboratoryz/state.sqlite3` (SQLite WAL). docs/app: `docs/app/autonomoussaleslaboratoryz/index.html` (no Vite edits).

## MCP & registration
`AutonomousSalesLaboratoryToolsMixin` (`mcp/tools/mem20autonomoussaleslaboratoryz_tools.py`) in `mcp/server.py`. Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomoussaleslaboratoryz/mem20autonomoussaleslaboratoryz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomoussaleslaboratoryz
```
Target **7/7**.

## Limits
Deterministic experiment logic; real channel delivery/CRM/consent systems are target-environment integrations. Guardrails/peer failures surfaced, not fatal.
