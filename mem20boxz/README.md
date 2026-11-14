# mem20boxz — crew runtime

mem20 sandbox runtime.

## Members (4)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20simz`
- `mem20multiworldsandboxz`
- `mem20scopemutationsandboxz`
- `mem20spatialcomputingsandboxz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20boxz.mem20boxz --version
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20boxz.mem20boxz --members
```

## Absorbed: `mem20multiworldsandboxz`

# RM-057 — Multi-World Sandbox

Outcome: Run the same plan against simulated environments, providers, and failure conditions

Breakthrough: Actions are rehearsed before touching real systems

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `simulate` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20multiworldsandboxz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20multiworldsandboxz benchmark
```

## Absorbed: `mem20scopemutationsandboxz`

# RM-195 — Scope Mutation Sandbox

**Owner:** Patricia  
**Lane:** Executable planning, dependency modeling, and build sequencing

## Outcome
Apply proposed additions or cuts and calculate downstream impact immediately

## Breakthrough
Scope can evolve without losing control of the system

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-195 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20spatialcomputingsandboxz`

# RM-107 — Spatial Computing Sandbox

**Owner:** OtherStack  
**Lane:** Experimental and incompatible technology incubator

## Outcome
Build shared 3D workspaces that expose capabilities, agents, and data as spatial objects

## Breakthrough
Complex systems become explorable environments

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-107 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.
