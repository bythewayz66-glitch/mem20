# mem20audiovoiceandmusicpipelinez — depth-first delivery record

## Purpose
Audio, voice, and music pipeline: mix, normalize, sync-to-beat, export, and mastering, with real operator/runtime surfaces and estate integration.

## Architecture
- `domain.py`: pure audio operations + `pipeline_report()`/`probe()`/`estate_context()` compatibility wrapper. No blind generic template.
- `ecosystem.py`: 6 **subsystem-specific** peers (different set, chosen for this pipeline) with bootstrap + adapters; failures reported (`{"ok": false, "error": ...}`), never fatal. `probe()` checks all peers.
- `runtime.py`: `Service` + SQLite WAL `EventStore` for durable local events; JSON HTTP API (`/api/status, /api/doctor, /api/simulate, /api/mix, /api/master, /api/events, /api/health`) and served cockpit from `web/`. CLI: `serve`, `status`, `doctor`, `simulate`, `mix`, `master`.
- `web/`: vanilla JS/CSS/HTML operator cockpit (no build step), served by runtime; talks to same-origin `/api/*` or configurable API base.
- MCP: real `AudioVoiceMusicPipelineToolsMixin` (`mcp/tools/mem20audiovoiceandmusicpipelinez_tools.py`) registered in `mcp/server.py` (lazy/guarded, real handlers).

## Ecosystem peers (6, subsystem-specific)
1. `mem20assetintakecatalogingandvalidationpipelinez` — validate/catalog asset intake.
2. `mem20aiproductionstudiooperatingsystemz` — schedule projects, allocate resources, studio health.
3. `mem20loreragcontentgeneratorz` — content/subtitle binding generation + adapter ranking/quality.
4. `mem20livemodelfusionz` — fuse/weight/select/health for model outputs.
5. `mem202dand3dartproductionoptimizationpipelinez` — optimize pipeline, frame budget, batch efficiency.
6. `mem20eventstreamsuperhighwayz` — create/publish/throughput for pipeline events.

## Verification
- Unit/domain/ecosystem tests assert real computed values and cover cross-module call sites.
- `scripts/renovation/conformance.py mem20audiovoiceandmusicpipelinez` target: 7/7.
- CLI `--help`/commands, HTTP routes + served cockpit, `node --check web/app.js`.

## Limits / honest notes
- Audio DSP here is deterministic sample math (not a DAW or external codec engine). External codecs/providers and production traffic are target-environment integrations.
- Peer unavailability degrades report status but does not crash the pipeline.
