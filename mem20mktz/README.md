# mem20mktz

mem30 Phase 2 marketplace organs on the mem20 estate. Two marketplaces trade
real offers (release gate), plus service bundling, adaptive pricing, and
braid-journaled resource trades:

- **Inference Marketplace** (RM-070) on top of the Model Genome Lab (RM-061)
- **Resource Exchange Market** (RM-012) — quote, escrow, execute, then the
  settled trade is journaled as a signed, provable node on the mem20 braid
  ledger (the exit test: *the trade is a braid node*).
- **Capability Marketplace** (RM-010) on the Universal Capability Graph
  (live at `MEM20_UCG_URL`, default `http://127.0.0.1:8781`)
- **Adaptive Pricing Brain** (RM-015) — deterministic margin/fairness pricing
  from the real cost stack of a bundle
- **Service Bundling Engine** (RM-087) — compose priced composite offers from
  real model genomes + real UCG capability nodes

Everything endpoints here does real work. Honesty contract: a trade is only
ever reported executed when it was journaled; if the braid ledger is down the
call raises instead of fabricating a receipt.

## Install

```bash
cd /opt/mem20/mem20mktz
# the package's own venv already carries the compiled braid_python wheel so
# journaled trades can reach the real ledger:
.venv/bin/pip install -e .        # runtime + fs-mkt entry point
.venv/bin/pip install -e '.[dev]' # + pytest/httpx for the test suite
```

`braid_python` (and the `braid_keyz` source package it leans on) ship from
`/opt/mem20`, not PyPI — pip-install the wheel found under
`/opt/mem20/braid_python/target/wheels/` first if it is not already installed.

## CLI (`fs-mkt`)

Runs real code against real state planes and the real braid ledger:

```bash
fs-mkt health                    # descriptors, UCG client, braid_ok
fs-mkt descriptors               # the six real marketplace descriptors
fs-mkt genome seed               # seed the lab with the real local model estate
fs-mkt genome list
fs-mkt pricing quote --bundle '<json>' --margin 0.2 --policy fair
fs-mkt resource offer token 100 0.01 "agent-a"
fs-mkt resource take <offer_id> "agent-b" 10
fs-mkt inference list-model genome.litellm.fast 0.01
fs-mkt inference match "write tests" --caps code
fs-mkt capability nodes              # live UCG graph
fs-mkt capability publish cap.cv-inference.v1 0.05 --seller "mem30"
fs-mkt capability buy <listing_id> "agent-b"
fs-mkt bundle compose "AR stack" --models genome.litellm.fast --caps cap.cv-inference.v1
fs-mkt bundle price <bundle_id> --margin 0.2
fs-mkt bundle ar-training            # factory bundle for the Phase-2 exit test
fs-mkt trade execute "agent-a" --bundle '<json>' --reference 0.5   # real braid journal
fs-mkt trade all
fs-mkt journal tail               # head of the real braid ledger
fs-mkt journal node <cid>         # read + prove one node
fs-mkt journal prove <cid>
fs-mkt serve --port 8785          # real HTTP API (FastAPI + uvicorn)
```

Bundles can also be built from real registered genomes:

```bash
fs-mkt pricing quote --from-genomes genome.litellm.fast genome.litellm.balanced --margin 0.2
```

## HTTP API (`fs-mkt serve`)

Real endpoints, one per organ:

| Method | Path | Real backing |
|---|---|---|
| GET | `/health` | `MarketService.health()` + braid status |
| GET | `/descriptors` | `descriptor.all_descriptors()` |
| GET/POST | `/genomes` | `ModelGenomeLab` |
| POST | `/genomes/seed` | `genome.seed_default_genomes()` |
| POST | `/pricing/quote` | `AdaptivePricingBrain.quote()` |
| GET | `/pricing/decisions` | pricing decision plane |
| GET/POST | `/resource/offers` | `ResourceExchangeMarket.offer/listings` |
| POST | `/resource/take` | `ResourceExchangeMarket.take()` |
| GET | `/resource/trades` | settled trades plane |
| GET | `/inference/listings` | `InferenceMarketplace.listings()` |
| POST | `/inference/list-model` | `InferenceMarketplace.list_model()` |
| POST | `/inference/match` | `InferenceMarketplace.match()` |
| POST | `/inference/transact` | `InferenceMarketplace.transact()` |
| GET | `/inference/trades` | inference trade plane |
| GET | `/capability/nodes` | live UCG graph |
| GET/POST | `/capability/listings` | `CapabilityMarketplace.publish/listings` |
| POST | `/capability/buy` | `CapabilityMarketplace.buy()` |
| GET | `/capability/trades` | capability trade plane |
| POST | `/capability/simulate` | six runtime scenarios vs real listings |
| POST | `/bundle/compose` | `ServiceBundlingEngine.compose()` (genomes + UCG nodes) |
| POST | `/bundle/ar-training` | Phase-2 factory bundle |
| GET/POST | `/bundle` | list / price a bundle |
| POST | `/trade/quote` | `ResourceExchange.quote()` |
| POST | `/trade/execute` | `ResourceExchange.execute()` → real braid journal |
| GET | `/trades` | `ResourceExchange.all()` |
| GET | `/trades/{trade_id}` | `ResourceExchange.get()` |
| GET | `/journal/tail` | braid ledger head |
| GET | `/journal/node?cid=` | read + prove one braid node |
| GET | `/journal/prove?cid=` | prove a cid |

## Tests

```bash
.venv/bin/pytest
```

The suite asserts real behavior: braid-journaled trade happy path (provenance
`cid` present and `prove()`-able), CLI subcommands executing real organs, and
HTTP endpoints responding against a temp store.

## State

All planes default to `MEM20_STORE_PATH ~/.mem20/store` (shared with the rest
of the estate). Set `MEM20_MKTZ_STORE` to redirect the marketplace planes to a
different directory (the journal tests use this to stay hermetic).

## Honest gaps

- Everything wired in the CLI/HTTP surface is real. The capability market and
  service bundling require a live Universal Capability Graph; the estate runs
  one at `http://127.0.0.1:8781` (override with `MEM20_UCG_URL`). If the UCG
  is down, `fs-mkt capability *` / `fs-mkt bundle *` and the matching endpoints
  fail honestly with `UCGUnavailable` (HTTP 502) instead of faking a graph.
- Journaled commands require the braid ledger to be reachable through
  `/opt/mem20/braid_bridge.py`; if it is down, `fs-mkt journal *` and
  `fs-mkt trade execute` (journal mode) fail honestly with `BraidUnavailable`.

## Managed members (package-review integration)

Single-purpose marketplace organs grouped here by reference; they live in
their own top-level directories and are smoke-verified there:

- `mem20adaptiveinferencemarketplacez`
- `mem20adaptivepricingbrainz`
- `mem20capabilitymarketplacez`
- `mem20connectormarketplacez`
- `mem20globalcapabilitymarketplacez`
- `mem20hardwaremarketplacez`
- `mem20offerassemblyfabricz`
- `mem20resourceexchangemarketz`

## Absorbed: `mem20capabilitymarketplacez`

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

## Absorbed: `mem20connectormarketplacez`

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

## Absorbed: `mem20globalcapabilitymarketplacez`

# mem20globalcapabilitymarketplacez — Global Capability Marketplace (RM-218, #318)

**Outcome:** distribute portable capabilities, models, connectors, workflows, and microapps with instant trials.  
**Breakthrough:** FreeStack becomes known as the place where executable AI abilities are exchanged.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `match` operation is backward-compatible for generic demand/supply and provides meaningful marketplace composition for listings/requirements.

## Legacy domain API (preserved)
`list_capability(seller,cap,price)`, `search_marketplace(listings,query)`, `match(listings,requirement)`, `transaction(listing,buyer)`, `marketplace_health(listings)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Marketplace role |
|---|---|---|
| `mem20offerassemblyfabricz` | `create_offer`,`add_component`,`price_offer`,`publish` | assembles and publishes priced offers |
| `mem20offergenomeenginez` | `create_genome`,`mutate`,`fitness` | optimizes offer fitness |
| `mem20instantappsynthesisz` | `validate_spec`,`scaffold` | synthesizes instant-trial scaffolds |
| `mem20securecomputecapsulesz` | `create_capsule`,`capsule_health` | validates secure trial execution |
| `mem20runtimepromptoptimizerz` | `tokenize`,`compress`,`optimize` | optimizes listing discovery queries |
| `mem20studioz` | `remix_variants`,`transform_asset` | produces capability/asset variants |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20globalcapabilitymarketplacez simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20globalcapabilitymarketplacez execute '{"listings":[{"seller":"s1","capability":"workflow ai","price":10,"available":true}],"requirement":{"capability":"workflow"},"buyer":"b1","query":"workflow"}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20globalcapabilitymarketplacez serve --port 8798
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20globalcapabilitymarketplacez/tests mem20globalcapabilitymarketplacez/mem20globalcapabilitymarketplacez/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20globalcapabilitymarketplacez
```

## Absorbed: `mem20hardwaremarketplacez`

# mem20hardwaremarketplacez — Hardware Marketplace (RM-048, #323)

**Outcome:** Match workloads to volunteered, owned, or rented compute under explicit limits.
**Breakthrough:** Users can monetize or share spare compute without surrendering control.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator (`match` operation kind). `match` is meaningful for marketplace payloads (`listings`/`workloads`) and backward-compatible for generic demand/supply matching.

## Legacy domain API (preserved)
`list_hardware(seller,hw,price)`, `search(listings,query)`, `price_estimate(hw)`, `transaction(listing,buyer)`, `marketplace_health(listings)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Marketplace role (feeds match outcome) |
|---|---|---|
| `mem20causalroutingbrainz` | `Node`,`Workload`,`estimate_energy_wh`,`estimate_cost`,`score_placement` | placement/energy/cost fit per listing |
| `mem20devicecapabilitycompilerz` | `compile_for_device`,`compatibility`,`feature_flags` | capability + explicit limits enforcement |
| `mem20datalocalityoptimizerz` | `optimal_placement`,`migration_cost`,`placement_score`,`locality_report` | locality and migration-cost fit |
| `mem20energyawarecomputemigrationz` | `ComputeNode`,`Workload`,`greenest_node`,`carbon_footprint`,`energy_cost` | carbon/energy-aware selection |
| `mem20zerotouchnodeswarmz` | `register_node`,`discover`,`assign_task`,`load_distribution`,`heal` | volunteered pool availability/load |
| `mem20roamingworkloadschedulerz` | `schedule`,`migrate`,`node_load`,`scheduler_health` | workload scheduling/migration fit |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwaremarketplacez simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwaremarketplacez execute '{"listings":[{"seller":"gpu-a","hardware_spec":{"cores":8,"memory_gb":16,"gpu":true},"price":40,"available":true}],"workloads":[{"id":"train","cpu":2,"memory_gb":4,"gpu":1}]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwaremarketplacez serve --port 8803
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20hardwaremarketplacez/tests mem20hardwaremarketplacez/mem20hardwaremarketplacez/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20hardwaremarketplacez
```

## Absorbed: `mem20offerassemblyfabricz`

# mem20offerassemblyfabricz — Offer Assembly Fabric

First-class mem20 subsystem for offer assembly (create_offer/add_component/price_offer/publish/offer_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousdealdeskz`, `mem20servicebundlingenginez`, `mem20simz`, `mem20revenueleakhunterz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offerassemblyfabricz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offerassemblyfabricz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offerassemblyfabricz serve --port 8847
```

## Absorbed: `mem20resourceexchangemarketz`

# mem20resourceexchangemarketz — Resource Exchange Market

First-class mem20 subsystem for resource exchange markets (list/buy/price history/market health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20causalroutingbrainz`, `mem20simz`, `mem20crossproductloyaltygraphz`.

## Python API (runnable)
```python
from mem20resourceexchangemarketz.domain import list_resource, buy, market_report, probe
l=list_resource("alice","cpu",10,2.0); print(buy(l,"bob",3)["cost"])  # 6.0
r=market_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz serve --port 8816
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/resourceexchangemarketz/index.html` (no Vite edits).

## MCP & registration
`ResourceExchangeMarketToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20resourceexchangemarketz/mem20resourceexchangemarketz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20resourceexchangemarketz
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

## Absorbed: `mem20datalocalityoptimizerz`

# mem20datalocalityoptimizerz — Data Locality Optimizer

First-class mem20 subsystem for data locality optimization (placement scoring, optimal placement, migration cost, locality reporting, rebalance) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20zerotouchnodeswarmz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20universalhealthnervoussystemz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20datalocalityoptimizerz.domain import placement_score, optimal_placement, migration_cost, locality_report, rebalance, placement_report, probe
nodes=[{"id":"n1","latency_ms":1,"capacity_gb":10,"used_gb":0},{"id":"n2","latency_ms":20,"capacity_gb":10,"used_gb":0}]
print(optimal_placement({"size_gb":1}, [dict(n) for n in nodes])["id"])  # n1
print(migration_cost({"size_gb":10},{"egress_cost":0.1},{})==1.0)  # True
print(locality_report([{"local":True},{"local":False}])["ratio"])  # 0.5
r=placement_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz serve --port 8799
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/datalocalityoptimizerz/index.html` (no Vite edits).

## MCP & registration
`DataLocalityOptimizerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20datalocalityoptimizerz/mem20datalocalityoptimizerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20datalocalityoptimizerz
```
Target **7/7**.

## Absorbed: `mem20devicecapabilitycompilerz`

# mem20devicecapabilitycompilerz — Device Capability Compiler

First-class mem20 subsystem for device capability detection and compilation targeting (detect, compile optimizations, feature flags, compatibility) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20crossplatformmicrokernelz`, `mem20datalocalityoptimizerz`, `mem20zerotouchnodeswarmz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20universalhealthnervoussystemz`.

## Python API (runnable)
```python
from mem20devicecapabilitycompilerz.domain import detect_capabilities, compile_for_device, feature_flags, compatibility, compile_report, probe
c=detect_capabilities({"cpu_cores":4,"memory_gb":8}); print(c["tier"])  # high
print("ml_acceleration" in compile_for_device("x",c)["optimizations"])  # True
print(compatibility({"memory_gb":2},["memory_4gb"])["compatible"])  # False
r=compile_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz serve --port 8801
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/devicecapabilitycompilerz/index.html` (no Vite edits).

## MCP & registration
`DeviceCapabilityCompilerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20devicecapabilitycompilerz/mem20devicecapabilitycompilerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20devicecapabilitycompilerz
```
Target **7/7**.

## Absorbed: `mem20energyawarecomputemigrationz`

# mem20energyawarecomputemigrationz — Energy-Aware Compute Migration (RM-047)

**Outcome:** schedule compute around battery, thermal limits, electricity price, and renewable availability.  
**Breakthrough:** the fleet optimizes both performance and energy use.

A real, first-class migration control plane: legacy-compatible domain primitives (preserved for `mem20causalroutingbrainz`), advanced energy/carbon/battery/thermal/renewable scoring and migration planning, SQLite WAL state, service/CLI/JSON HTTP API, served cockpit, `docs/app` monitor, and six **unique** cross-subsystem peers (different set from #300, #301, #302).

## Legacy-compatible API (preserved)
`energy_cost(node, workload_size)`, `migrate_decision(src, dst, workload)`, `carbon_footprint(node, workload_size)`, `greenest_node(nodes, workload)` (deterministic tie-break by node id), `migration_plan(workloads, nodes)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls used | Contribution |
|---|---|---|
| `mem20batteryawareagentschedulerz` | `BatteryAwareAgentScheduler.schedule/cheapest_slot` | power-budget/battery feasibility and cheapest slot |
| `mem20energyawarefoundationz` | `power_reading`, `threshold_check`, `energy_budget`, `optimize_power`, `daily_energy` | energy thresholds/budget/optimization |
| `mem20datalocalityoptimizerz` | `placement_score`, `optimal_placement`, `migration_cost`, `locality_report` | data locality and migration/egress cost |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain.observe/forecast/residual_sigma/capacity_for` | capacity forecast with uncertainty |
| `mem20goaleconomyschedulerz` | `schedule_goals`, `goal_value`, `priority_queue`, `progress` | migration prioritization by value/cost |
| `mem20planetarybatchfabricz` | `submit_job`, `schedule`, `fabric_health`, `retry` | batch/workload placement and fabric health |

## CLI
```bash
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 status
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 doctor
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 simulate
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 node add --id green --power 50 --speed 2 --rate 0.10 --carbon 100 --renewable 80
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 node add --id dirty --power 200 --speed 1 --rate 0.20 --carbon 600 --renewable 0
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 workload add --id job-1 --size 10 --current-node dirty
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 plan
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 migrate --workload job-1 --to green
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 serve --port 8783
```

## Runnable example (verified)
```bash
cd /opt/mem20
DB=/tmp/eam-demo.sqlite3
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" node add --id green --power 50 --speed 2 --rate 0.10 --carbon 100 --renewable 80 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" node add --id dirty --power 200 --speed 1 --rate 0.20 --carbon 600 --renewable 0 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" workload add --id job-1 --size 10 --current-node dirty >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" plan
```

Observed (real run, key fields):
```text
ok=true
plan.counts: workloads=1 migrations=1 (dirty -> green when savings/feasibility justify)
signals: capacity_forecast, goal_scheduler, data_locality, batch_fabric all ok
placement: target chosen by energy+carbon+battery/thermal/renewable feasibility scoring
```

`migrate` applies the move in durable state and returns energy/locality signals. `doctor` probes all 6 peers; `simulate` runs real scenarios.

## HTTP API / web
`GET /api/status|doctor|nodes|workloads|events|migrations`, `POST /api/nodes|workloads|plan|migrate|snapshot|restore|simulate|benchmark`, cockpit at `/`. Docs monitor: `docs/app/energy-migration/index.html` (`?api=`).

## Tests
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20energyawarecomputemigrationz/tests -q
```
Covers legacy domain compatibility (including tie-break), 6 ecosystem peers (real calls), service plan/migrate/status/doctor/simulate, and HTTP/cockpit.

## Conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20energyawarecomputemigrationz
```
Target 7/7.

## Limits
No claim of production grid/carbon market feeds, real device power telemetry, live data replication, or managed workload migration agents. Decisions are modeled over declared node/workload state; actual execution hooks are integration points.

## Absorbed: `mem20instantappsynthesisz`

# mem20instantappsynthesisz — Instant App Synthesis (RM-010, #327)

**Outcome:** Compile a plain-language objective into a working composition of existing FreeStack capabilities.
**Breakthrough:** Users describe an outcome and receive a usable app in minutes.

Preserves legacy domain API (**#318 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator (`compose` operation kind).

## Legacy domain API (preserved for #318)
`synthesize(spec)`, `scaffold(app)`, `estimate_size(app)`, `validate_spec(spec)`, `deploy_config(app,target="vercel")`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Synthesis role (feeds composition outcome) |
|---|---|---|
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | app/page config graph resolution |
| `mem20semanticobjectgraphz` | `canonical`,`stable_hash`,`words` | spec/component semantic identity |
| `mem20pipez` | `version_asset`,`vc_health` | synthesized artifact versioning |
| `mem20dynamicskillgraphz` | `add_skill`,`learning_path` | capability composition path |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | objective-to-composition intent context |
| `mem20capabilitygapmapperz` | `canonical`,`stable_hash` | capability gap/coverage check |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20instantappsynthesisz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20instantappsynthesisz execute '{"objective":"build a todo app","spec":{"name":"todo","pages":["home"],"components":["list","form"]}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20instantappsynthesisz serve --port 8807
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20instantappsynthesisz/tests mem20instantappsynthesisz/mem20instantappsynthesisz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20instantappsynthesisz
```

## Absorbed: `mem20roamingworkloadschedulerz`

# mem20roamingworkloadschedulerz — Roaming Workload Scheduler

First-class mem20 subsystem for roaming workload scheduling (schedule, migrate, node load, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20zerotouchnodeswarmz`, `mem20autonomousworkcellsz`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20roamingworkloadschedulerz.domain import schedule, migrate, scheduler_report, probe
nodes=[{"id":"a","load":0},{"id":"b","load":5}]; print(schedule([{"id":"w","cost":1}],nodes)[0]["node"])  # a
print(migrate("w","a","b")["to"])  # b
r=scheduler_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz serve --port 8820
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/roamingworkloadschedulerz/index.html` (no Vite edits).

## MCP & registration
`RoamingWorkloadSchedulerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20roamingworkloadschedulerz/mem20roamingworkloadschedulerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20roamingworkloadschedulerz
```
Target **7/7**.

## Absorbed: `mem20runtimepromptoptimizerz`

# mem20runtimepromptoptimizerz — Runtime Prompt Optimizer

First-class mem20 subsystem for runtime prompt optimization (tokenize, compress, score, optimize, prompt health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20rewardforgez`, `mem20causalroutingbrainz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20runtimepromptoptimizerz.domain import tokenize, compress, score_prompt, optimize, prompt_report, probe
print(tokenize("a b"))  # ['a', 'b']
print(score_prompt("hello world",{"hello":1}))  # 1.0
r=prompt_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz serve --port 8822
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/runtimepromptoptimizerz/index.html` (no Vite edits).

## MCP & registration
`RuntimePromptOptimizerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20runtimepromptoptimizerz/mem20runtimepromptoptimizerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20runtimepromptoptimizerz
```
Target **7/7**.

## Absorbed: `mem20securecomputecapsulesz`

# mem20securecomputecapsulesz — Secure Compute Capsules

First-class mem20 subsystem for secure compute capsules (create, run, isolate, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20secretslessworkloadidentityz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20deterministicconfigurationgraphz`.

## Python API (runnable)
```python
from mem20securecomputecapsulesz.domain import create_capsule, run_capsule, isolate, capsule_report, probe
c=create_capsule("1+1"); run_capsule(c, lambda code,lim: eval(code)); print(c["result"])  # 2
isolate(c); print(c["isolated"])  # True
r=capsule_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz serve --port 8824
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/securecomputecapsulesz/index.html` (no Vite edits).

## MCP & registration
`SecureComputeCapsulesToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20securecomputecapsulesz/mem20securecomputecapsulesz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20securecomputecapsulesz
```
Target **7/7**.

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

## Absorbed: `mem20zerotouchnodeswarmz`

# mem20zerotouchnodeswarmz — Zero-Touch Node Swarm

First-class mem20 subsystem for zero-touch node swarming (register_node/discover/node_score/assign_task/mark_failed/heal/quorum/load_distribution/join_token) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20roamingworkloadschedulerz`, `mem20causalroutingbrainz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20autonomousrecoverydirectorz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20zerotouchnodeswarmz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20zerotouchnodeswarmz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20zerotouchnodeswarmz serve --port 8846
```
