# mem20audiovoiceandmusicpipelinez — Audio, Voice & Music Pipeline

First-class mem20 subsystem for audio/voice/music pipeline operations: mix tracks, normalize levels, sync to beats, export formats, and apply mastering chains. Integrated as a real runtime with **6 subsystem-specific estate peers** (chosen for this pipeline’s job — **not** a generic memory/focus/catalog/webhook template), a durable local event log, CLI, JSON HTTP API, served operator cockpit, docs/app integration, and real MCP tools.

## Architecture

```
domain.py     pure audio ops + pipeline_report()/probe()/estate_context()
ecosystem.py  6 adapters (bootstrap) → real peer domain calls; failures reported, never fatal
runtime.py    Service + SQLite WAL EventStore; CLI; ThreadingHTTPServer JSON API; serves web/
web/          static operator cockpit (index.html, style.css, app.js), no build step
docs/PLAN.md  depth-first delivery record
mcp/tools/    real AudioVoiceMusicPipelineToolsMixin registered in mcp/server.py
gateway/      SUBSYSTEMS entry (working CLI entry)
docs/app/     estate monitor page + link from docs/app/README.md (no compiled Vite edits)
```

## Domain model (`domain.py`)

Pure, deterministic operations (no I/O): `mix_tracks(tracks, volumes)`, `normalize(samples, target_db)`, `sync_to_beat(audio_len_s, bpm, offset)`, `export_format(samples, fmt, sample_rate)`, `mastering_chain(stages, audio)`. `pipeline_report(...)` runs core audio ops and collects all 6 peer judgements; `probe()` checks peers; `estate_context()` is a compatibility wrapper returning a real report summary.

## Lifecycle & runtime (`runtime.py`)

- **Service** executes domain/ecosystem operations and appends events to a local **SQLite WAL** `EventStore` (`~/.mem20/audiovoiceandmusicpipelinez/state.sqlite3` by default, override `--store` / `MEM20_AVMP_STORE`).
- **CLI:** `serve`, `status`, `doctor`, `simulate`, `mix`, `master`.
- **HTTP API (JSON):** `GET/POST /api/status` (pipeline report), `GET/POST /api/doctor` (probe 6 peers), `POST /api/simulate`, `POST /api/mix`, `POST /api/master`, `GET /api/events`, `GET /api/health`. Static cockpit served at `/` and `/web/*` (path traversal refused). CORS enabled for estate monitor use.

## Ecosystem wiring (`ecosystem.py`) — 6 subsystem-specific peers

| peer | adapter | real functions called | pipeline role |
|---|---|---|---|
| `mem20assetintakecatalogingandvalidationpipelinez` | `asset_intake_plan` | `validate_asset`, `intake_pipeline`, `catalog_asset` | validate/catalog ingested audio assets |
| `mem20aiproductionstudiooperatingsystemz` | `production_schedule` | `schedule_projects`, `resource_allocation`, `studio_health` | schedule stages, allocate capacity/resources |
| `mem20loreragcontentgeneratorz` | `content_binding` | `generate`, `rank_adapters`, `quality_score` | bind subtitle/narrative context + quality |
| `mem20livemodelfusionz` | `model_fusion` | `fuse`, `weight_by_confidence`, `select_best`, `fusion_health` | fuse voice/model outputs |
| `mem202dand3dartproductionoptimizationpipelinez` | `pipeline_optimization` | `optimize_pipeline`, `frame_budget`, `batch_efficiency` | production pipeline/budget optimization |
| `mem20eventstreamsuperhighwayz` | `publish_events` | `create_stream`, `publish`, `throughput` | publish pipeline events and measure throughput |

Failures are surfaced as `{"ok": false, "error": ...}` and never abort the pipeline report.

## Python API (runnable)

```python
from mem20audiovoiceandmusicpipelinez.domain import (
    mix_tracks, normalize, sync_to_beat, export_format, mastering_chain,
    pipeline_report, probe, estate_context,
)

print(mix_tracks([{"id": "vox", "samples": [0.1, 0.2]}], volumes=[0.8]))
# {'tracks': [{'id': 'vox', 'gain': 0.8, 'samples': [0.1, 0.2]}], 'master_gain': 1.0}

print(normalize([0.5, 1.0, -0.8], target_db=-3.0))
print(sync_to_beat(audio_len_s=10.0, bpm=120))
print(export_format([0] * 44100, fmt="wav", sample_rate=44100))
print(mastering_chain(["limit"], [1.5, -1.2, 0.2]))

report = pipeline_report(tracks=[{"id": "vox", "samples": [0.1, 0.2]}], samples=[0.5, 1.0], prompt="bind subtitle")
print(report["ok"], len(report["peers"]))   # True 6 (when peers available)
print(probe()["ok"])                          # True (when peers available)
print(estate_context()["peer_count"])         # 6
```

## CLI

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez mix '[{"id":"a","samples":[0.1,0.2]}]'
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez master --stages limit --audio 0.5,1.2,-0.8
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez serve --port 8781
```

## Web frontend & docs site integration

- **Per-subsystem served cockpit:** `web/index.html|style.css|app.js` (vanilla, no build). Served by `runtime.py` at `GET /` when running `serve`.
- **docs/app integration (static):** `docs/app/audiovoiceandmusicpipelinez/index.html` links to subsystem README and connects to a configurable runtime API base. Linked from `docs/app/README.md`. **No compiled Vite assets edited.**

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20audiovoiceandmusicpipelinez serve --port 8781
# open http://127.0.0.1:8781/ (cockpit) or docs/app/audiovoiceandmusicpipelinez/index.html (estate monitor)
```

## MCP

Real tools via `mcp.tools.mem20audiovoiceandmusicpipelinez_tools.AudioVoiceMusicPipelineToolsMixin` registered in `mcp/server.py`: `audiovoiceandmusicpipelinez_status`, `_doctor`, `_mix`, `_master` (lazy/guarded imports, real handlers).

## Tests & conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20audiovoiceandmusicpipelinez/mem20audiovoiceandmusicpipelinez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20audiovoiceandmusicpipelinez
node --check mem20audiovoiceandmusicpipelinez/mem20audiovoiceandmusicpipelinez/web/app.js
```

Target: **7/7 conformance** (domain logic, no stubs, tests, CLI, README fenced examples, >=5 cross-modules on covered lines, MCP/gateway registered).

## Limits / honest notes

- DSP is deterministic sample math (not a DAW/external codec engine). Real codec/provider/device I/O and production traffic are target-environment integrations.
- Peer unavailability degrades report/probe status but does not crash operations; errors are surfaced in responses/events.
