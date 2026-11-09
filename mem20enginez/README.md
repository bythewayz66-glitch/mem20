# mem20enginez — crew runtime (#305)

First-class runtime for the 30-member mem20 engine crew. It provides a truthful member registry and filesystem/import probing, compatibility checks, deterministic dispatch planning, durable SQLite WAL state, CLI + JSON HTTP API + operator cockpit, and six **unique** cross-subsystem peer integrations (different set from #300-#304).

## Members (30)

`mem20adaptiveachievementenginez`, `mem20adaptivedispatchenginez`, `mem20adaptiveforgettingenginez`, `mem20adaptivepersonalityruntimez`, `mem20schoolz`, `mem20chaosnativeapplicationruntimez`, `mem20communitychallengeenginez`, `mem20communitypulseenginez`, `mem20completionconfidenceenginez`, `mem20crdtcollaborationenginez`, `mem20crosslanguagerefactorenginez`, `mem20customerlifecycleenginez`, `mem20dynamicnarrativeenginez`, `mem20featuredependencygraphenginez`, `mem20generativebrandworldenginez`, `mem20liveprojectdemonstrationenginez`, `mem20liveschemamorphingenginez`, `mem20mixedinitiativefocusenginez`, `mem20mobileedgeagentruntimez`, `mem20multilingualliveconversationenginez`, `mem20offergenomeenginez`, `mem20outcomeverificationruntimez`, `mem20peertopeerappruntimez`, `mem20predictiverecallenginez`, `mem20privatelocalreasoningenginez`, `mem20protocolautodiscoveryenginez`, `mem20runtimebugpredictionenginez`, `mem20runtimecompatibilityenginez`, `mem20servicebundlingenginez`, `mem20speculativeworkflowenginez`.

Member probing is truthful: present/healthy/importable members are reported as-is; missing or degraded members are surfaced, not hidden.

## Architecture

| Layer | File | Responsibility |
|---|---|---|
| Domain | `mem20enginez/domain.py` | Canonical registry, `check_member` filesystem/import probe, compatibility, capability-matched `dispatch_plan`, summary report. |
| State | `mem20enginez/store.py` | SQLite WAL objects/events/plans/runs/snapshots/restore. |
| Ecosystem | `mem20enginez/ecosystem.py` | 6 unique peer adapters (real calls, fail-open reporting). |
| Service | `mem20enginez/service.py` | members/status/doctor/plan/execute/events/runs/simulate/benchmark with peer signals. |
| Runtime | `mem20enginez/runtime.py` + `web/` | CLI, JSON HTTP API, static cockpit, CORS, 400/404/409 mapping. |

## Unique cross-subsystem wiring (criterion 6)

| Peer | Real calls used | Contribution |
|---|---|---|
| `mem20runtimecompatibilityenginez` | `check_python`, `check_deps`, `compatibility_report`, `suggest_fixes` | runtime/member compatibility checks |
| `mem20protocolautodiscoveryenginez` | `detect_protocol`, `parse_headers`, `register_protocol`, `list_protocols`, `protocol_health` | protocol discovery/registry for wiring |
| `mem20speculativeworkflowenginez` | `speculate`, `commit`, `rollback`, `speculative_health` | speculative dispatch planning |
| `mem20servicebundlingenginez` | `create_bundle`, `add_service`, `discount`, `bundle_health` | capability/service bundling |
| `mem20predictiverecallenginez` | `predict_next`, `recall_score`, `prefetch`, `cache_hit_rate`, `recall_health` | predictive member selection/routing |
| `mem20customerlifecycleenginez` | `lifecycle_stage`, `transition`, `retention_probability`, `lifetime_value`, `segment_customers` | runtime lifecycle/stage transitions |

## Runnable example (verified)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20enginez --db /tmp/engz-demo.sqlite3 plan --intent "protocol compatibility speculative dispatch"
```

Observed (real run, key fields):

```text
ok=true
plan.intent="protocol compatibility speculative dispatch"
plan.selected includes capability-matched healthy members (e.g. protocol/runtime-compatibility/speculative-capable members present in the estate)
signals.speculative_workflow.ok=true  (branches speculated/committed)
signals.predictive_recall.ok=true     (predictions/prefetch)
signals.service_bundling.ok=true      (capability bundle priced)
signals.runtime_lifecycle.ok=true     (lifecycle transitions/retention/segments)
```

```bash
python -m mem20enginez --version
python -m mem20enginez --members
python -m mem20enginez --db state/enginez.sqlite3 status
python -m mem20enginez --db state/enginez.sqlite3 doctor
python -m mem20enginez --db state/enginez.sqlite3 simulate
python -m mem20enginez --db state/enginez.sqlite3 serve --port 8785
```

## HTTP API

`GET /api/status|doctor|members|plans|runs|events`, `POST /api/plan|execute|simulate|benchmark|snapshot|restore`, cockpit at `/`.

## Web surfaces

- Served cockpit: `GET /` from `serve`.
- docs/app monitor: `docs/app/engine-runtime/index.html` (`?api=http://host:port`), linked from `docs/app/README.md`.

## Tests / conformance

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20enginez/tests -q
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20enginez
```

Target 7/7.
