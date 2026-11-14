# mem20biz — crew runtime

mem20 autonomous company and revenue runtime.

## Members (3)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20acquisitionandpartnershipscoutz`
- `mem20livingagenteconomyz`
- `mem20revenueleakhunterz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20biz.mem20biz --version
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20biz.mem20biz --members
```

## Absorbed: `mem20acquisitionandpartnershipscoutz`

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

## Absorbed: `mem20livingagenteconomyz`

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

## Absorbed: `mem20revenueleakhunterz`

# mem20revenueleakhunterz — Revenue Leak Hunter

First-class mem20 subsystem for revenue leak hunting (detect leaks, anomaly scoring, recoverable amounts) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20simz`, `mem20autonomousdealdeskz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20causalroutingbrainz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20revenueleakhunterz.domain import detect_leaks, anomaly_score, recoverable, leak_report, probe
leaks=detect_leaks([{"id":"a","amount":5}], {"a":10}); print(leaks[0]["delta"])  # -5
print(recoverable(leaks))  # 5.0
r=leak_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz serve --port 8817
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/revenueleakhunterz/index.html` (no Vite edits).

## MCP & registration
`RevenueLeakHunterToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20revenueleakhunterz/mem20revenueleakhunterz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20revenueleakhunterz
```
Target **7/7**.

## Absorbed: `mem20autonomousdealdeskz`

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

## Absorbed: `mem20webhooksupernetworkz`

# RM-078 — Webhook Supernetwork

Outcome: receive, verify, deduplicate, route, replay, and transform events from
any provider.

Breakthrough: webhook chaos becomes a dependable programmable event layer.

## What this package actually guarantees

| Guarantee | How |
|---|---|
| A forged delivery is refused | HMAC-SHA256 over `timestamp.body`, compared with `hmac.compare_digest` |
| A captured delivery cannot be replayed later | the timestamp is *inside* the signed material, and a tolerance window rejects anything stale |
| A redelivery does not double-process | a stable idempotency key per delivery, deduplicated through a bounded, optionally durable ledger |
| A replay cannot quietly re-deliver a subset | `mem20verify.dataintegrity.check` must prove the store round-trips a write first |
| A credential never enters the event log | `mem20secretz.sweep.classify` classifies field names *and* values, and the payload is refused rather than stored |
| A route cannot exist for a prohibited use | `mem20liez.gates.check_prohibited_uses` is consulted at construction |
| The sender's clock cannot poison the event time | `memory_engine.memory.validate_event_time` decides what a legal event time is |

Two defects fixed on this branch, both of which made the guarantees above hollow:

* the dedupe ledger was an unbounded in-memory `list`, so **every process
  restart forgot what it had delivered** and re-delivered everything. It is now
  a `DeliveryLedger` with a cap and an optional append-log.
* payloads were eligible to be persisted verbatim. A webhook log is durable and
  replayed, so persisting a payload containing a token turned the log into a
  credential archive that got re-read on every replay. `admit()` now refuses it.

## Quickstart

The block below is the real CLI, and it is the exact command used to verify this
package. It needs no secret and touches nothing outside a temporary directory:

```bash
python3 -m mem20webhooksupernetworkz.cli selftest
```

Expected (10 checks, all true):

```json
{
  "checks": 10,
  "failed": [],
  "ok": true,
  "passed": 10
}
```

## Wiring, end to end

```bash
# 1. Confirm every sibling project this receiver depends on is reachable.
python3 -m mem20webhooksupernetworkz.cli doctor --secret "$MEM20_WEBHOOK_SECRET"

# 2. Sign a body the way a provider would, for a timestamp inside the window.
python3 -m mem20webhooksupernetworkz.cli sign '{"deploy":"staging"}' \
    --timestamp 1772323200 --secret "$MEM20_WEBHOOK_SECRET"

# 3. Verify a delivery. Add --payload to also check the credential class.
python3 -m mem20webhooksupernetworkz.cli verify '{"deploy":"staging"}' \
    --timestamp 1772323200 --signature "$SIG" \
    --secret "$MEM20_WEBHOOK_SECRET" --now 1772323200

# 4. Deliver once per idempotency key - a repeat is skipped, not re-sent.
python3 -m mem20webhooksupernetworkz.cli deliver '{"deploy":"staging"}' \
    --timestamp 1772323200 --signature "$SIG" --idem deploy-1 \
    --secret "$MEM20_WEBHOOK_SECRET" --now 1772323200

# 5. Replay a stored event log - refuses if the store cannot round-trip.
python3 -m mem20webhooksupernetworkz.cli replay events.jsonl \
    --secret "$MEM20_WEBHOOK_SECRET"
```

Exit codes: `0` accepted, `2` verification refused, `3` payload refused,
`4` replay refused because the store failed verification.

## Estate dependencies

This package is wired into six sibling projects; each call answers a question
this receiver cannot answer alone.

| Project | Symbol | Question |
|---|---|---|
| `mem20secretz` | `sweep.classify` | may this payload be persisted |
| `mem20liez` | `gates.check_prohibited_uses` | may this route exist |
| `mem20verify` | `dataintegrity.check` | can the store be replayed from |
| `mem20ops` | `memchecks.identity_check` | which store is this |
| `memory_engine` | `memory.validate_event_time` | is the sender's time legal |
| `toolchest` | `catalog.load_inventory` | what may a route target |

`mem20` installs from source, not PyPI. Run from a checkout root so the seam can
find the sibling projects; `doctor` names any that are missing instead of
failing with one traceback.

## Note on the engine module

`memory_engine/memory.py` is imported by the estate under two names
(`memory_engine.memory` and `memory`). Python caches those as **two independent
modules**, so `STORE_DIR`/`LEDGER` and the vector/BM25 indexes exist twice for a
single store. The visible symptom is a false integrity failure — `mem20verify`
writes through one copy and reports "no ledger row written" about a healthy
store, which blocks every replay.

`estate.py` aliases the two names to one module object on import, and
`estate.resync_engine_store()` re-points and re-aliases after a store change.
`tests/test_estate_wiring.py::TestSingleEngineInstance` pins both.

## Tests

```bash
python3 -m pytest mem20webhooksupernetworkz -q
```
