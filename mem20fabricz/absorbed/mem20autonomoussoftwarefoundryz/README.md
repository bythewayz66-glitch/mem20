# mem20autonomoussoftwarefoundryz — Autonomous Software Foundry

First-class mem20 subsystem that turns software specs into actionable build plans: decompose specs into tasks, score code quality, make deploy decisions, estimate effort, and produce build artifacts. It runs as a real service with **6 software-foundry-specific estate peers** (no generic template), a SQLite WAL event log, a CLI, a JSON HTTP API, a served operator cockpit, docs/app estate integration, and real MCP tools.

## At a glance

| item | value |
|---|---|
| package | `mem20autonomoussoftwarefoundryz` |
| console entry | `mem20autonomoussoftwarefoundryz` / `python -m mem20autonomoussoftwarefoundryz` |
| core modules | `domain.py`, `ecosystem.py`, `runtime.py` |
| web cockpit | `web/index.html`, `web/style.css`, `web/app.js` (served by runtime, no build step) |
| state | SQLite WAL `events` table (`~/.mem20/autonomoussoftwarefoundryz/state.sqlite3` or `--store` / `MEM20_SWFOUNDRY_STORE`) |
| cross-subsystem peers | 6, each called on the normal report/probe path with real APIs |
| registrations | `gateway/mem20_gateway.py` SUBSYSTEMS, `mcp/tools/mem20autonomoussoftwarefoundryz_tools.py` wired in `mcp/server.py`, `docs/app/autonomoussoftwarefoundryz/` linked from `docs/app/README.md` |
| conformance target | 7/7 |

## Architecture

- `domain.py` — pure foundry operations plus `foundry_report()`, `probe()`, and `estate_context()` (the report aggregates real peer results).
- `ecosystem.py` — the 6 peer adapters (bootstraps peer package paths). Every adapter calls real peer APIs and returns computed results; failures are reported as `{"ok": false, "subsystem": ..., "error": ...}` and never crash core operations.
- `runtime.py` — `Service` + SQLite WAL `EventStore`; argparse CLI; `ThreadingHTTPServer` JSON API that also serves the static `web/` cockpit with path-traversal protection and CORS headers.
- `web/` — vanilla operator cockpit (no compiled assets).
- `docs/PLAN.md` — depth-first delivery record.
- `docs/app/autonomoussoftwarefoundryz/index.html` — estate-shell monitor (static; no Vite asset edits), linking back to this README and `docs/app/README.md`.

## Domain model

| function | behavior |
|---|---|
| `spec_to_tasks(spec)` | expands `spec["features"]` into per-feature `todo` tasks and always adds `tests` + `deploy` tasks |
| `code_quality(metrics)` | scores 0–1.0: `+0.4` tests pass, `+0.3` coverage ≥ 0.8, `+0.3` lint clean (rounded to 3 decimals) |
| `deploy_decision(quality, threshold=0.7)` | boolean gate on quality |
| `estimate_effort(spec)` | `days = 2 * feature_count`; complexity `low`/`medium`/`high` |
| `build_artifact(spec, code)` | deterministic artifact record: name, `0.1.0`, 12-char SHA-256 checksum, line count |
| `foundry_report(...)` | computes core outputs and calls all 6 peers; `ok` is true only when every peer reports `ok` |
| `probe()` | runs the 6 peer probes and aggregates reachability |
| `estate_context(store_path=None)` | lightweight estate summary (`engine_status_checked`, `peer_count`, `peers_ok`, `checks`) |

## Ecosystem peers (6, software-foundry specific)

These peers were chosen for the *software foundry* job (build/tooling, versioned artifacts, build telemetry, safe deploys, spec quality, build economics). The set is different from other subsystems’ peer sets.

| peer | real functions/classes used | role in this subsystem |
|---|---|---|
| `mem20capabilitymarketplacez` | `CapabilityMarketplace(replicas=32)`, `add`, `locate`, `distribution` | route a build key to a tool/capability owner via consistent hashing and report distribution |
| `mem20pipez` | `version_asset`, `recover`, `vc_health` | version an artifact, recover a target version, and report version-control health |
| `mem20eventstreamsuperhighwayz` | `create_stream`, `publish`, `throughput` | publish build/foundry events to a stream and report throughput |
| `mem20faultcontainmentcellsz` | `FaultContainmentCells`, `CircuitOpen`, `call` | contain deploy execution behind a circuit breaker; open-circuit is reported, not fatal |
| `mem20loreragcontentgeneratorz` | `generate`, `rank_adapters`, `quality_score` | assess/spec-generate quality for a build prompt and select/rank adapters |
| `mem20simz` | `revenue`, `profit`, `margin`, `scenario_sim` | model effort economics (profit/margin/scenario periods) for the estimated build |

## Python API (runnable)

```python
from mem20autonomoussoftwarefoundryz.domain import (
    build_artifact,
    code_quality,
    deploy_decision,
    estate_context,
    estimate_effort,
    foundry_report,
    probe,
    spec_to_tasks,
)

spec = {"name": "app", "features": ["auth", "api"]}
metrics = {"tests_pass": True, "coverage": 0.9, "lint_clean": True}
code = "print('hi')\n"

tasks = spec_to_tasks(spec)
quality = code_quality(metrics)
print(len(tasks), quality, deploy_decision(quality))  # 4 1.0 True
print(estimate_effort(spec))                           # {'days': 4, 'complexity': 'low'}
print(build_artifact(spec, code)["checksum"])          # 12-char sha256 prefix

report = foundry_report(spec=spec, code=code, metrics=metrics)
print(report["ok"], report["quality"], report["deploy"], len(report["peers"]))  # 6 peers

p = probe()
print(p["ok"], sorted(p["checks"].keys()))

ctx = estate_context()
print(ctx["engine_status_checked"], ctx["peer_count"])  # True 6
```

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz serve --port 8786
```

`--store PATH` (or `MEM20_SWFOUNDRY_STORE`) selects the SQLite state file.

## HTTP API and web cockpit

The runtime serves a JSON API and the static cockpit at `/` (no separate frontend build).

| method | route | purpose |
|---|---|---|
| GET | `/api/health` | service health |
| GET/POST | `/api/status` | foundry report (POST accepts `spec`, `code`, `metrics`) |
| GET/POST | `/api/doctor` | peer probe |
| POST | `/api/simulate` | run internal scenarios (tasks/report/doctor) |
| POST | `/api/quality` | compute `code_quality` for posted `metrics` |
| GET | `/api/events?since=&limit=` | recent WAL event records |

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz serve --port 8786
# cockpit:        http://127.0.0.1:8786/
# estate monitor: docs/app/autonomoussoftwarefoundryz/index.html (set API base to the server)
```

## MCP and registration

- MCP mixin: `AutonomousSoftwareFoundryToolsMixin` (`mcp/tools/mem20autonomoussoftwarefoundryz_tools.py`), wired/registered in `mcp/server.py` as `autonomoussoftwarefoundryz_status` and `autonomoussoftwarefoundryz_doctor` (lazy/guarded import pattern).
- Gateway: `gateway/mem20_gateway.py` `SUBSYSTEMS["mem20autonomoussoftwarefoundryz"]` with purpose, working entry, owner, wave.
- Docs/app: `docs/app/autonomoussoftwarefoundryz/index.html` linked from `docs/app/README.md` (static HTML; no compiled Vite assets edited).

## Tests and conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomoussoftwarefoundryz/mem20autonomoussoftwarefoundryz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomoussoftwarefoundryz
node --check mem20autonomoussoftwarefoundryz/mem20autonomoussoftwarefoundryz/web/app.js
```

Target: **7/7** conformance (real domain, no stubs, real-value tests, CLI, runnable README examples, >=5 cross-module imports+calls on covered lines, MCP/gateway registration).

## Limits

- Build quality/deploy/effort logic is deterministic and local to this subsystem; real CI/CD, source hosting, artifact registries, and production deploy systems are target-environment integrations.
- Peer unavailability is surfaced in `foundry_report`/`probe`/`doctor` (and via MCP) rather than crashing core operations.
- The web cockpit and docs/app monitor are static frontends against the local HTTP API; they require the runtime server to be running.
