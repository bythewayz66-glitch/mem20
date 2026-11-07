# mem20autonomousdealdeskz — depth-first delivery record

## Purpose
Autonomous deal desk: price deals, score terms, gate approvals, negotiate rounds, and assess deal health, with real runtime and estate integration.

## Architecture
- `domain.py`: pure deal ops + `deal_report()`/`probe()`/`estate_context()`.
- `ecosystem.py`: 6 subsystem-specific peers (deal-desk fit, no generic template) with bootstrap/adapters; failures reported, never fatal.
- `runtime.py`: Service + SQLite WAL EventStore; CLI; JSON HTTP API; serves `web/` cockpit.
- `web/`: vanilla operator cockpit (no build).
- MCP: real `AutonomousDealDeskToolsMixin` registered in `mcp/server.py`.
- docs/app estate monitor + gateway SUBSYSTEMS entry.

## Peers (6)
1. `mem20businessmodelsimulatorz` — economics (revenue/profit/margin/scenario).
2. `mem20demandforecastandcapacitybrainz` — demand forecast/capacity headroom.
3. `mem20acquisitionandpartnershipscoutz` — strategic fit/ranking/synergy.
4. `mem20antiexploitationrewardshieldz` — approval guardrail/corroboration.
5. `mem20capabilitymarketplacez` — capability routing (consistent hashing).
6. `mem20autonomoussaleslaboratoryz` — pipeline value/conversion/segments.

## Verification
Tests assert real peer computed values (12 passed); conformance 7/7 target; CLI/API/cockpit real.
