# mem20autonomousdealdeskz — Autonomous Deal Desk

First-class mem20 subsystem for autonomous deal operations: price deals, score terms, gate approvals, negotiate rounds, and assess deal health. Real runtime with **6 subsystem-specific estate peers** (deal-desk fit — **not** a generic template), SQLite WAL event log, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Architecture

- `domain.py` — pure deal ops + `deal_report()`/`probe()`/`estate_context()`
- `ecosystem.py` — 6 adapters (bootstrap); failures reported `{"ok": false, "error": ...}`, never fatal
- `runtime.py` — `Service` + SQLite WAL `EventStore`; CLI; `ThreadingHTTPServer` JSON API; serves `web/`
- `web/` — vanilla operator cockpit (no build)
- `docs/PLAN.md`, `docs/app/autonomousdealdeskz/` estate monitor, gateway entry, MCP mixin

## Ecosystem peers (6, subsystem-specific)

| peer | real functions | role |
|---|---|---|
| `mem20simz` | `revenue`, `profit`, `margin`, `scenario_sim` | deal economics/margin/scenarios |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain` (observe/forecast/capacity_for) | demand signal & capacity headroom |
| `mem20acquisitionandpartnershipscoutz` | `target_score`, `strategic_fit`, `rank_targets`, `synergy_estimate` | partnership/strategic fit & synergy |
| `mem20antiexploitationrewardshieldz` | `RewardShield.evaluate`/`exploit_ratio` | approval guardrail/corroboration |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` (add/locate/distribution) | capability routing via consistent hashing |
| `mem20autonomoussaleslaboratoryz` | `pipeline_value`, `conversion_probability`, `segment_leads` | pipeline value/conversion/segments |

## Python API

```python
from mem20autonomousdealdeskz.domain import (
    price_deal, terms_score, approval_required, negotiate_round, deal_health,
    deal_report, probe, estate_context,
)

print(price_deal({"price": 1000}, {"volume": 500}))
print(terms_score({"payment_days": 15, "contract_months": 12, "auto_renew": True}))
print(approval_required(9500, threshold=10000))
print(negotiate_round(1000, 850, rounds_left=2))
print(deal_health({"signed": True, "paid": False}))

report = deal_report(product={"price": 1200}, customer={"volume": 400}, deal={"deal_value": 1100})
print(report["ok"], report["price"], len(report["peers"]))  # True, ..., 6
print(probe()["ok"])  # True (all peers reachable)
```

## CLI

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782
```

## HTTP API & web cockpit

`GET/POST /api/status`, `GET/POST /api/doctor`, `POST /api/simulate`, `POST /api/price`, `POST /api/negotiate`, `GET /api/events`, `GET /api/health`. Cockpit served at `/` (static `web/`, no build). State: `~/.mem20/autonomousdealdeskz/state.sqlite3` (SQLite WAL) or `--store`/`MEM20_DEALDESK_STORE`.

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782
# cockpit: http://127.0.0.1:8782/  |  estate monitor: docs/app/autonomousdealdeskz/index.html
```

## MCP & registration

MCP: `AutonomousDealDeskToolsMixin` (`mcp/tools/mem20autonomousdealdeskz_tools.py`) registered in `mcp/server.py` (`autonomousdealdeskz_status|doctor|price`). Gateway: `gateway/mem20_gateway.py` SUBSYSTEMS entry. docs/app linked from `docs/app/README.md` (no compiled Vite assets edited).

## Tests & conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomousdealdeskz/mem20autonomousdealdeskz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomousdealdeskz
node --check mem20autonomousdealdeskz/mem20autonomousdealdeskz/web/app.js
```

Target: **7/7**.

## Limits

- Pricing/negotiation logic is deterministic rules for this subsystem; real commercial/legal/ERP integrations are target-environment concerns.
- Peer unavailability is surfaced in report/probe and does not crash core operations.
