# App / product narrative — `docs/app/`

Entry point for the `docs/app/` documentation set. **36 tracked file(s).**

## Contents

- [`.nojekyll`](.nojekyll)
- [`assets/index-BMgU54DU.css`](assets/index-BMgU54DU.css)
- [`assets/index-DCqPYDUE.js`](assets/index-DCqPYDUE.js)
- [`continuum/index.html`](continuum/index.html)
- [`deck/PERMANENT_URL.md`](deck/PERMANENT_URL.md)
- [`energy-foundation/index.html`](energy-foundation/index.html)
- [`engine-runtime/index.html`](engine-runtime/index.html)
- [`episodic-memory-graph/index.html`](episodic-memory-graph/index.html)
- [`design-stress-lab/index.html`](design-stress-lab/index.html)
- [`concept-scope-pipeline/index.html`](concept-scope-pipeline/index.html)
- [`execution-digital-twin/index.html`](execution-digital-twin/index.html)
- [`fabricz/index.html`](fabricz/index.html)
- [`facez/index.html`](facez/index.html)
- [`federated-research-grid/index.html`](federated-research-grid/index.html)
- [`ethical-incentive-simulator/index.html`](ethical-incentive-simulator/index.html)
- [`energy-migration/index.html`](energy-migration/index.html)
- [`transport/index.html`](transport/index.html)
- [`deck/index.html`](deck/index.html)
- [`deck/slides/README.md`](deck/slides/README.md)
- [`deck/slides/slide_01.html`](deck/slides/slide_01.html)
- [`deck/slides/slide_02.html`](deck/slides/slide_02.html)
- [`deck/slides/slide_03.html`](deck/slides/slide_03.html)
- [`deck/slides/slide_04.html`](deck/slides/slide_04.html)
- [`deck/slides/slide_05.html`](deck/slides/slide_05.html)
- [`deck/slides/slide_06.html`](deck/slides/slide_06.html)
- [`deck/slides/slide_07.html`](deck/slides/slide_07.html)
- [`deck/slides/slide_08.html`](deck/slides/slide_08.html)
- [`deck/slides/slide_09.html`](deck/slides/slide_09.html)
- [`deck/slides/slide_10.html`](deck/slides/slide_10.html)
- [`deck/slides/slide_11.html`](deck/slides/slide_11.html)
- [`deck/slides/slide_12.html`](deck/slides/slide_12.html)
- [`deck/slides/slide_13.html`](deck/slides/slide_13.html)
- [`desktop-packaging.md`](desktop-packaging.md)
- [`fleet/index.html`](fleet/index.html)
- [`index.html`](index.html)
- [`narrative/serial-2026-10-27.md`](narrative/serial-2026-10-27.md)

## Continuum monitor (`continuum/`)

[`continuum/index.html`](continuum/index.html) is the estate-shell view of the
Edge-to-Cloud Intelligence Continuum (RM-214). Static page, reads the
subsystem's JSON API (`?api=http://host:port`), shows health/targets/workloads
and can run `doctor`. It owns no state.

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20edgetocloudintelligencecontinuumz serve --port 8791
# -> http://127.0.0.1:8000/continuum/?api=http://127.0.0.1:8791
```













## Federated Research Grid monitor (`federated-research-grid/`)

[`federated-research-grid/index.html`](federated-research-grid/index.html) — static monitor for RM-043 (#313). Reads `/spec`/`/metrics`/`/doctor` (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20federatedresearchgridz serve --port 8793
```

## mem20facez monitor (`facez/`)

[`facez/index.html`](facez/index.html) — static monitor for #312 (8-member interface/workspace runtime). Reads `/status`/`/doctor` (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20facez serve --port 8792
```

## mem20fabricz Integration Fabric monitor (`fabricz/`)

[`fabricz/index.html`](fabricz/index.html) — static monitor for #311 (23-member crew runtime). Reads `/status`/`/doctor` (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20fabricz serve --port 8791
```

## Execution Digital Twin monitor (`execution-digital-twin/`)

[`execution-digital-twin/index.html`](execution-digital-twin/index.html) — static monitor for RM-059 (#310). Reads `/spec`/`/metrics`/`/doctor` (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20executiondigitaltwinz serve --port 8790
```

## Concept & Scope Pipeline monitor (`concept-scope-pipeline/`)

[`concept-scope-pipeline/index.html`](concept-scope-pipeline/index.html) — static monitor for RM-237 (#309). Reads `/spec`/`/metrics`/`/doctor` (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20executablegameconceptandscopepipelinez serve --port 8789
```

## Design Stress Lab monitor (`design-stress-lab/`)

[`design-stress-lab/index.html`](design-stress-lab/index.html) — static monitor for RM-221 (#308). Reads `/spec`/`/metrics`/`/doctor` (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20executabledesignstresslabz serve --port 8788
```

## Ethical Incentive Simulator monitor (`ethical-incentive-simulator/`)

[`ethical-incentive-simulator/index.html`](ethical-incentive-simulator/index.html) — static monitor for RM-203 (#307). Reads `/spec`/`/metrics`/`/doctor` (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20ethicalincentivesimulatorz serve --port 8787
```

## Episodic Memory Graph monitor (`episodic-memory-graph/`)

[`episodic-memory-graph/index.html`](episodic-memory-graph/index.html) — static estate monitor for
Episodic Memory Graph (RM-021, #306). Reads subsystem JSON API (`?api=`), shows status/doctor.

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20episodicmemorygraphz serve --port 8786
```

## Engine runtime monitor (`engine-runtime/`)

[`engine-runtime/index.html`](engine-runtime/index.html) — static estate monitor for
`mem20enginez` crew runtime (#305). Shows member/status summary and doctor/peer probe
via the subsystem JSON API (`?api=http://host:port`). No estate state is owned.

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20enginez serve --port 8785
# -> http://127.0.0.1:8000/engine-runtime/?api=http://127.0.0.1:8785
```

## Energy foundation monitor (`energy-foundation/`)

[`energy-foundation/index.html`](energy-foundation/index.html) — static estate monitor for Energy-Aware Foundation (power thresholds/budgets/actions). Reads subsystem API (`?api=`).

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20energyawarefoundationz serve --port 8784
```

## Energy-aware migration monitor (`energy-migration/`)

[`energy-migration/index.html`](energy-migration/index.html) is the estate-shell view of
Energy-Aware Compute Migration (RM-047). Static page, reads the subsystem JSON API
(`?api=http://host:port`), shows status/nodes/workloads and can run `doctor`.

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20energyawarecomputemigrationz serve --port 8783
# -> http://127.0.0.1:8000/energy-migration/?api=http://127.0.0.1:8783
```

## Transport fabric monitor (`transport/`)

[`transport/index.html`](transport/index.html) is the estate-shell view of the
Edge Transport Fabric (RM-077). Static page, reads the subsystem JSON API
(`?api=http://host:port`), shows fabric health/nodes/links/flows and can run
`doctor`. It owns no state.

```bash
PYTHONPATH=/opt/mem20 python3 -m mem20edgetransportfabricz serve --port 8782
# -> http://127.0.0.1:8000/transport/?api=http://127.0.0.1:8782
```

## Fleet monitor (`fleet/`)

[`fleet/index.html`](fleet/index.html) is the estate-shell view of the Edge Fleet
Brain (RM-041). It is a static page: it owns no state and reads the subsystem's
own JSON API, so the operator cockpit served by the fleet process and this page
cannot drift apart.

```bash
# start the subsystem that owns the state plane
PYTHONPATH=/opt/mem20 python3 -m mem20edgefleetbrainz --store /tmp/fleet.db serve --port 8771

# open the monitor against it (also accepts ?api=http://host:port)
python3 -m http.server 8000 --directory docs/app
# -> http://127.0.0.1:8000/fleet/?api=http://127.0.0.1:8771
```

The page shows fleet health, node load, the workload queue, the fault forecast,
the 24 h energy projection and the live event stream, and it can run the six
scenario simulator, probe all six ecosystem peers and plan a rebalance. The
`API` field persists in `localStorage`; `?api=` overrides it for the session.
The full operator cockpit (node registration, dispatch, drain/evacuate) is
served by the fleet process itself at its root URL.

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`

- [Audio/Voice/Music Pipeline monitor](audiovoiceandmusicpipelinez/index.html) — run `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez serve --port 8781` and connect the estate monitor to its API.
- [Autonomous Deal Desk monitor](autonomousdealdeskz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782`
- [Autonomous Micro-SaaS Foundry monitor](autonomousmicrosaasfoundryz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz serve --port 8783`
- [Autonomous Recovery Director monitor](autonomousrecoverydirectorz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousrecoverydirectorz serve --port 8784`
- [Autonomous Sales Laboratory monitor](autonomoussaleslaboratoryz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz serve --port 8785`
- [Autonomous Software Foundry monitor](autonomoussoftwarefoundryz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz serve --port 8786`
- [Autonomous Workcells monitor](autonomousworkcellsz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz serve --port 8787`
- [Business Model Simulator monitor](businessmodelsimulatorz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20businessmodelsimulatorz serve --port 8788`
- [Causal Routing Brain monitor](causalroutingbrainz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20causalroutingbrainz serve --port 8789`
- [Collective Model Intelligence monitor](collectivemodelintelligencez/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez serve --port 8790`
- [Community Challenge Engine monitor](communitychallengeenginez/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20communitychallengeenginez serve --port 8791`
- [Compounding Product Ecosystem monitor](compoundingproductecosystemz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20compoundingproductecosystemz serve --port 8792`
- [Counterfactual Memory Simulator monitor](counterfactualmemorysimulatorz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20counterfactualmemorysimulatorz serve --port 8794`
- [Cross-Platform Microkernel monitor](crossplatformmicrokernelz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossplatformmicrokernelz serve --port 8795`
- [Cross-Product Loyalty Graph monitor](crossproductloyaltygraphz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz serve --port 8796`
- [Customer Digital Twin Lab monitor](customerdigitaltwinlabz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerdigitaltwinlabz serve --port 8797`
- [Customer Lifecycle Engine monitor](customerlifecycleenginez/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerlifecycleenginez serve --port 8798`
- [Data Locality Optimizer monitor](datalocalityoptimizerz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz serve --port 8799`
- [Deterministic Configuration Graph monitor](deterministicconfigurationgraphz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz serve --port 8800`
- [Device Capability Compiler monitor](devicecapabilitycompilerz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz serve --port 8801`
- [Dynamic Narrative Engine monitor](dynamicnarrativeenginez/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicnarrativeenginez serve --port 8802`
- [Dynamic Quest Reward Composer monitor](dynamicquestrewardcomposerz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz serve --port 8803`
- [Dynamic Skill Graph monitor](dynamicskillgraphz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz serve --port 8804`
- [Player Motivation Twin monitor](playermotivationtwinz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20playermotivationtwinz serve --port 8805`
- [Predictive Recall Engine monitor](predictiverecallenginez/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20predictiverecallenginez serve --port 8806`
- [Production Planning and Task Orchestration Pipeline monitor](productionplanningandtaskorchestrationpipelinez/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productionplanningandtaskorchestrationpipelinez serve --port 8807`
- [Product-Led Growth Simulator monitor](productledgrowthsimulatorz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productledgrowthsimulatorz serve --port 8808`
- [Protocol Auto-Discovery Engine monitor](protocolautodiscoveryenginez/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20protocolautodiscoveryenginez serve --port 8809`
- [Reality-to-Software Compiler monitor](realitytosoftwarecompilerz/index.html) — `PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz serve --port 8810`
