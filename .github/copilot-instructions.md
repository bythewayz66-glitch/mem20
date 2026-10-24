# Copilot instructions for mem20

mem20 is a **polyglot estate**, not a single package. It is a memory substrate and
agent runtime: a Python MCP server, a Rust append-only ledger workspace, a React
web shell, several language SDKs, and ~300 `mem20*z` subsystem packages.
Server baseline is **3.0.0** (`VERSION`, `pyproject.toml`).

Read this file before changing anything. For path-specific rules, see
`.github/instructions/*.instructions.md`.

## Layout (what lives where)

| Path | What it is |
| --- | --- |
| `mcp/` | The MCP server: `mcp_server.py`, `server.py`, `memory_tools.py`, `cognitive_tools.py`, `health.py`, `tools/`, `resources/`, `prompts/` |
| `memory_engine/`, `memory.py`, `procedural.py` | Core memory engine (grounded/simulated partitions, ledger, vectors) |
| `launcher.py` | `mem20-mcp` console script; runs `mcp/mcp_server.py` via `runpy` |
| `braid/` | Rust workspace (Cargo): `braid_core`, `braid_drive`, `braid_her`, `braid_keys`, `braid_sonic`, `braid_ui_bridge`, `braid_cli` |
| `web/` | React 18 + Vite + TypeScript web shell |
| `dashboard/` | React 19 + Vite dashboard |
| `mem20*z/` dirs | Nested subsystem packages, each with its own `pyproject.toml` and `tests/` |
| `sdk/{cpp,perl}`, `mem20-sdk-{ruby,typescript,godot}` | First-class clients (see `SDKS.md`) |
| `tests/` | Repo-root test suite |
| `.github/workflows/` | `ci.yml`, `pages.yml`, `release.yml`, `mem20-web.yml`, `ruby-sdk.yml` |
| `docs/`, `roadmaps/`, `2.0_roadmap/` | Docs, ADRs, planning artifacts — prose, not runtime |

## Hard invariants — never violate these

1. **The grounded/simulated partition never mixes.** `remember()` refuses any
   record not tagged `origin="grounded"`. `_allow_simulated=True` is rejected
   **on purpose** — do not add an escape hatch to satisfy a test.
2. **Index writes assert grounded.** `_assert_grounded()` runs on every vector
   and BM25 write. Never route a simulated record into an index.
3. **Promotion is evidence-based.** Simulated to grounded requires a resolved
   prediction or a registered external verifier. A boolean flag or a free-text
   note must be refused — do not weaken this to make a call site simpler.
4. **Contamination rate stays `0.0`.** `audit_contamination()` must report
   `0.0` on a clean store. A non-zero value is a bug, never "accepted drift".
5. **Index drift is a defect.** `recall_semantic()` returns `healthy` and a
   `diagnostic`. Never make a stale index look like "no results".

## Python: the single most common breakage

The repo root is on `sys.path` whenever pytest runs from it, and each package
lives at `<project>/<name>/` with no `__init__.py`. That lets the outer
directory win as a **namespace package**, producing
`ImportError: cannot import name ... (unknown location)`.

`conftest.py` fixes this by removing the repo root from `sys.path`, adding each
project root instead, and pre-binding real modules into `sys.modules`.

- **Never** "fix" a collection error by adding `__init__.py` to an outer project
  directory. That turns every project dir into a package containing a package.
- **Never** remove the `sys.path` manipulation in `conftest.py` or the pre-binding loop.
- **`mcp/` shadows the `mcp` SDK.** `mcp/` is a project directory whose name
  collides with the real SDK. `conftest.py` step 3b pre-imports the real SDK for
  exactly this reason. `mcp/memory_tools.py` calls `sys.exit(1)` on ImportError,
  which aborts the whole session. Do not introduce a bare `import mcp` at module
  scope in code that may run during collection.

## Test conventions

- `pytest.ini` sets `--import-mode=importlib` and `testpaths = .`. A bare
  `pytest` walks the whole estate — always narrow: `python3 -m pytest <package> -q`.
- Use markers: `-m unit` (fast, no optional native deps — the CI default) and
  `-m integration` (needs torch, blender, live network).
- `norecursedirs` excludes `backups`, `data`, `store`, `build`, `dist`, `mem`,
  `test`, `roadmaps`, `notes`, `proof`, `verification`, `systemd`, `docs`.
- CI's `tests` job runs a fixed **green set of 22 packages** and asserts the count
  is 22. If you add or remove a package from that list, update the `-ne 22` guard
  in the same commit.

## Things that must never be committed

`build/`, `dist/`, `__pycache__/`, `*.pyc`, `node_modules/`, `*.faiss`,
`ledger.jsonl`, `entries/*.json`, HuggingFace caches, and runtime state such as
`memory.db`, `memory.db-shm`, `memory.db-wal`. CI has an explicit
"Guard against tracked bytecode" step that fails the build.

`memory.py.broken` is a preserved artifact. **Never** resurrect it, import it, or
rename it back to `memory.py`.

## Verification before proposing a change

```bash
python3 -m compileall -q <paths you touched>
python3 -m pytest <package> -q          # never a bare pytest
```

For Rust: `cargo check --manifest-path braid/Cargo.toml`.
For web: `cd web && npm run typecheck && npm run build`.
For the Perl SDK: `prove -Isdk/perl/lib sdk/perl/t/*.t`.

## Style and review norms

- Lint is **syntax-level only**: pre-commit runs `ruff --select E9,F63,F7,F82`.
  Do not reformat unrelated code or add new lint rules in a feature PR.
- Branch names: `fix/<topic>`, `feat/<topic>`, `docs/<topic>` from `main`.
- Keep a change small and scoped to one package where possible.
- **Docs must match code in the same PR.** If you change a tool count, a port, or
  a version, grep and update the `README.md` / `docs/` references too.
- Moving an entry point (`mcp/mcp_server.py`, a systemd `ExecStart` target)
  requires updating the unit file **and** the docs that reference it.

## Working as an agent in this repo

`CONTRIBUTING.md` requires agents to read
`docs/handoff/AGENT-OPERATING-PROTOCOL.md` before touching a file and to claim
work in `docs/handoff/claims/`. One writer per file at a time. Honour that.

## What to avoid

- Do not add a new `mem20*z` package to solve a problem that belongs in an
  existing one. The estate is already large; consolidation is the preferred direction.
- Do not silence a failing invariant with `try/except` or a skip marker.
- Do not infer tool counts, ports, or versions. Read them from code.
- Do not touch `roadmaps/`, `2.0_roadmap/`, `DIARY.md`, `PROOF.md` unless the task
  is explicitly about those documents.
