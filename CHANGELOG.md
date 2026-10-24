# Changelog

All notable changes to mem20 are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed
- **`mcp/server.py` is now the authoritative implementation.** It was a bootstrap loader
  that reconstructed the server from `git show 6a2bdaab…:mcp/server.py`, which failed on
  `git clone --depth 1` checkouts with *"mem20 MCP server implementation not found."* The
  implementation now lives directly in the file, so a shallow clone with zero git history
  and no network access starts correctly. Removed: `mem20liez/_server_impl.py.gz.b64`,
  `mem20liez/regen_server_impl.py`, and the `MEM20_MCP_AUTO_FETCH` / `MEM20_GOOD_COMMIT`
  environment knobs.
- **Tool counts reconciled to the live surface: 270 tools across 27 domains.** The docs
  carried **257 / 26**, which was wrong in two ways: the `memory_*` row listed 49 tools
  against 52 registered, and the 10 `lie_*` tools were absent from every table. Corrected
  across `README.md`, `docs/`, the SDK READMEs, `toolchest/`, `roadmaps/` and
  `published/`. The handshake count is the authority.

### Added
- **`.github/workflows/mcp-verify.yml`** — CI job that checks out with `fetch-depth: 1`
  (deliberately shallow, to keep the shallow-clone fix honest), installs the core deps,
  runs the `verify_mcp.py` handshake and fails unless the tool count is exactly 270.
- **`verify_mcp.py`** — the handshake verifier used by that job and by the troubleshooting
  guide.
- **`docs/troubleshooting-mcp-server-startup.md`** — reproduction-based startup guide.

## [3.0.0] — 2026-10-18 (consolidation baseline)

3.0.0 is the **consolidation release**: every outstanding agent branch is merged into
`main`, generated output is out of the index, the SDKs and the benchmark suite are
published from `main`, and the tree is guarded by CI. No capability was removed to
achieve this — conflicts were resolved as unions, and repairs were made in place.

### Added
- **Benchmark suite on `main`** — `benchmarks/results/latest.json` and
  `benchmarks/results/latest.md`, the published output of `mem20benchmarkz run`,
  covering retrieval quality (hit rate, MRR, leak rate), latency percentiles and the
  trustworthiness axis (contamination 0.0, stale pointers 0.000000). `mem20api/` and
  `mem20benchmarkz/` travel with it.
- **Ruby SDK 0.2.0** (`mem20-sdk-ruby/`) — transport, client, config, errors, examples,
  docs and specs; plus root `.github/workflows/ruby-sdk.yml` and `release.yml`.
- **C++ SDK documentation set** (`docs/sdk/cpp/`) — protocol, API reference, source
  ledger and the `store_recall_audit.cpp` example.
- **CI** (`.github/workflows/ci.yml`) — Python syntax gate plus a `gitlink-guard` job
  that fails on any mode-160000 entry, so dangling submodules cannot return.
- **Pages publishing** (`.github/workflows/pages.yml`) — publishes `docs/` via GitHub
  Actions, removing the recursive submodule checkout that broke the legacy builder.
- **Repo governance files** — `CANONICAL.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, issue/PR templates and `CODEOWNERS`.
- **`VERSION`** — single-file version marker, kept in step with `pyproject.toml`.

### Changed
- **`README.md` is now the union of both development lines.** The narrative positioning
  ("What this is", "The honest claim", "Benchmarks", "The estate") sits above the
  operational reference ("What you can do", "Architecture", "Tool domains", "Memory
  model", "Governance", "Quick Start", "Installation"), so no section from either side
  was dropped. The duplicate `## Development` headings were merged into one.
- **Version is 3.0.0** across `pyproject.toml`, `VERSION`, the README badge and
  `docs/README.md`; the release badge moved off the 2.1-rc2 static badge.
- **Tool counts reconciled to the single house number: 268 tools across 26 domains.**
  Prose that had drifted to 258 or 260 is corrected; the 26 domain modules are
  unchanged. The domain table labels its rows as tool *prefixes*, since several
  prefixes share one domain.
- **Repository URLs updated** from `JaysonAIOnline/mem20` to
  `bythewayz66-glitch/mem20` across README, docs and the release badge, which
  previously queried the retired org and would have rendered against the wrong
  repository. Historical credit to the JaysonAIOnline project is retained in prose.
- **Generated output untracked** — `build/`, `__pycache__/`, `node_modules/`,
  `dashboard/dist/`, `mem20.egg-info/` and `*.pyc` are out of the index; `.gitignore`
  gained `.mypy_cache/`. Source is untouched: the build step still regenerates these
  locally.
- **Dangling gitlinks removed** — `kanban-mcp`, `mem20oreo` and `mem20kilnz/engine`
  were mode-160000 entries pointing at commits that do not exist in this repository,
  so every recursive checkout failed. They are now ordinary untracked paths; the
  guard job prevents reintroduction.

### Fixed
- **`mem20agentz` desktop path resolution** — `CREWZ_ROOT`/`GAMEZ_ROOT` no longer
  hardcode `/opt/mem20`; they resolve from `MEM20_CREWZ_ROOT`/`MEM20_GAMEZ_ROOT` with
  a repo-relative fallback, so the office surface works from a checkout.
- **`docs/README.md` stale links** — removed references to files that do not exist
  (`reproduce-not-1386`, `CLAUDE.md`, `notes`), which rendered as dead links.

### Merged branches
`gtm-optionc-conversion`, `ruby-sdk-0.2.0`, `chore/repo-cleanup-2026-10`,
`ci/gitlink-guard`, `fix/pages-submodule-checkout`, `fix/mem20agentz-hygiene`.
`fix/mem20crewz-hygiene` was closed as stale: it carried 0 unique commits and was 16
commits behind `main`, so there was no work to preserve.

### Note on house numbers
The commercial figures are **unchanged by this release** and are deliberately not
restated as new measurements: 268 tools / 26 domains, TAM $1.28B / SAM $282M / SOM
$1.68M, blended ACV $14,000.

## [2.2.0-dev] — 2026-09-04 (cognitive substrate + A2A tools)

2.2 is the "cognitive substrate + A2A inter-bot communication" increment.

### Added
- **28-layer cognitive substrate** — 5-category reasoning framework with JSON schema + Pydantic models
  (`mcp/resources/cognitive_substrate.py`, `mcp/resources/cognitive_substrate_schema.json`).
- **Thought process tools** (`mcp/tools/thought_process.py`) — ToT, Reflexion, Least-to-Most, ReAct,
  Beam Search, plus `cognitive_substrate` paradigm invoker and `get_cognitive_tree_state` telemetry query.
- **A2A tools** (`mcp/tools/a2a_tools.py`) — `a2a_list`, `a2a_call`, `a2a_discover`, `a2a_history`,
  `a2a_orchestrate` for agent-to-agent communication.
- **Cross-session Tree-of-Thought learning** — persistent ToT state via SQLite (`tot_state.db`),
  evolutionary historical lesson retrieval, 5-key compressed telemetry schema.
- **Server routing** updated to include `A2AToolsMixin` and `ThoughtProcessMixin`.
- **Fleetwide Mem20 + A2A Setup roadmap** (`roadmaps/Fleetwide Mem20 + A2A Setup.json`).
- **Test suite** (`test/`) — comprehensive + extreme test coverage for all cognitive tools.

### Changed
- Tool domain count: 13 → 16 (added `a2a_*`, `tot_*`, `cognitive_substrate`).
- Total tools: ~80 → ~95.

## [2.1.0-rc2] — 2026-08-28 (frozen; QA audit → GitHub release)

2.1 is the "pluggable integrations + standalone packaging" increment. Code is
frozen here until the GitHub release is cut.

### Added
- **Pluggable integrations:** Blender and Unity ship as separate optional modules
  (`mcp/tools/blender_tools.py`, `mcp/tools/unity_tools.py`). Each degrades
  gracefully (informative message) when the external application is absent
  (`MEM20_BLENDER_EXECUTABLE` / `MEM20_UNITY_EXECUTABLE`, or on PATH).
- Blank integration template: `IntegrationToolsMixin.register_integration_template()`
  documents how to add a new optional integration (e.g., Figma).
- **Standalone packaging:** `requirements.txt` (pinned core deps),
  `requirements-optional.txt` (external-app integrations), `pyproject.toml`,
  `systemd/mem20.service.template`, and `install.sh` (venv + deps + unit generation).
- `LICENSE` (MIT), `.gitignore`, `CHANGELOG.md`.
- Step 16 instrumentation: `/metrics` exposes an event taxonomy and per-tool
  counters, plus cached `contamination_rate` / `grounding_coverage`.
- pytest suite (`tests/`) covering contamination firewall, eval safety, dispatch, metrics.
- 2.0 roadmap deliverables (`2.0_roadmap/`) and a human execution package.

### Changed
- Hard-coded `/opt/mem20/...` and `/root/.hermes/...` defaults replaced with
  env-driven / `~`-relative defaults (`MEM20_STORE_PATH`, `MEM20_COG_PATH`,
  `MEM20_ROADMAPS_DIR`, `MEM20_BLENDER_WORKDIR`, `MEM20_ENGINE_SRC`).
- Engine brought into the repo as `memory_engine/` (code only; no user data).

### Fixed
- `eval()` replaced with `safe_eval_condition` (AST-restricted) for world-model rules.
- Contamination firewall: simulated records cannot reach grounded/BM25 indexes;
  `audit_contamination()` reports `contamination_rate == 0.0`.

## [2.0.0] — hardening baseline
- Phase 7 hardening, modular MCP decomposition (97 tools across 13 domains),
  health endpoint, audit response.

## [1.0.0] — initial release
