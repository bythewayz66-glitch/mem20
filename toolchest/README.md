# toolchest

Runtime-checked tool inventory/registry for the mem20 agent fleet.

`toolchest` walks the real box — the MCP server registry, every console script on
PATH, and the mem20 native subsystems under `/opt/mem20` — and produces one
machine-readable manifest: `inventory.json`.

It is a **registry, not a guess**: MCP entries come from actually instantiating
`Mem20MCPServer` (268 real tools), CLI entries are binned binaries that are
classified (`elf | script | symlink | broken-symlink`), and subsystem entries
record declared vs. actually-installed state per pyproject, with real
`importlib` import checks and on-disk PATH verification.

## Install

```
cd /opt/mem20/toolchest
python3 -m pip install -e .
```

## Usage

```
python -m toolchest refresh [--no-help-samples] [--output FILE]   # rebuild inventory.json
python -m toolchest list    [--category CAT] [--kind mcp|cli|subsystem] [--json]
python -m toolchest search  TERM [--kind ...] [--json]            # name + description search
python -m toolchest show    NAME [--check-path]                   # full entry
python -m toolchest stats                                        # summary counts
python -m toolchest wiring [--root DIR] [--json]                 # prove the cross-subsystem edges
```

## Cross-subsystem wiring

`toolchest` is not an island: a registry is only useful if it can describe the
rest of the estate truthfully. `toolchest.integrations` calls six real public
APIs, and `toolchest wiring` exercises every one of them on a real path:

| edge | what it proves |
|------|----------------|
| `memory_engine.pin_block` | the inventory summary is pinned as a grounded block |
| `mem20kanbanz.sha256` | the inventory file's content identity, via the kanban hasher |
| `mem20ops.clicheck` | every console script declared by a mem20* pyproject |
| `mem20corez.CharMLP` | a real model's real parameter count |
| `mem20cliz.build_envelope` | the estate-wide CLI JSON envelope |
| `mem20verify.testrun` | which packages actually carry a test suite |

```
$ python -m toolchest wiring
estate root: /opt/mem20
  OK    memory_engine.pin_block            -> {'block_id': 'toolchest:inventory', 'pinned': True, ...}
  OK    mem20kanbanz.sha256                -> 6b382d72c5b38c448db5b848f0085156b706a806db898ea70451046057d604b3
  OK    mem20ops.declared_scripts          -> 282
  OK    mem20corez.CharMLP                 -> 7121
  OK    mem20cliz.build_envelope           -> mem20.cli/1
  OK    mem20verify.discover_packages      -> 298

6/6 edges live
```

A subsystem that is genuinely absent is reported as `FAIL` with the real import
error — never as a pass. The same two capabilities are exposed to agents as the
MCP tools `toolchest_inventory` and `toolchest_wiring` (`mcp/tools/toolchest_tools.py`).

Query commands read the generated `inventory.json` (fast). `refresh` performs
full runtime checks and takes roughly 20-30s (dominated by instantiating the MCP
server); subprocess `--help` sampling is bounded and concurrent.

There is also a console script entry point once installed: `toolchest ...`.

## Entry schema

Every entry has the required fields:

| field           | meaning                                                            |
|-----------------|--------------------------------------------------------------------|
| `id`            | `mcp:<name>`, `cli:<name>`, or `subsystem:<name>`                  |
| `kind`          | `mcp`, `cli`, or `subsystem`                                       |
| `name`          | tool name                                                          |
| `category`      | `mcp`, `cli`, `agent-platform`, `games-3d`, `infra-model-ui`, `other` |
| `subcategory`   | domain (MCP), bin-type class (CLI), `native-subsystem`/`unpackaged` (subsystem) |
| `description`   | authoritative one-liner                                            |
| `source`        | on-disk path (or repo-relative for MCP registration modules)       |
| `runtime_status`| `ok`, `degraded`, `broken`, `missing`                              |
| `runtime_detail`| evidence for the status                                            |
| `checks`        | list of `{check, ok, detail}` verification results                 |
| `meta`          | kind-specific detail (help summary, dist, entry-points, deps...)   |

MCP entries additionally record the schema-prop count from `input_schema` in
`meta.input_schema_props`.

## Category sources

- `agent-platform`, `games-3d`, `infra-model-ui`: the AGENTS.md subsystem
  crosscheck table (`/root/AGENTS.md` — the row for `toolchest/` is
  `/root/AGENTS.md:63`; there is no `/opt/mem20/AGENTS.md`).
- `other/native-subsystem`: mem20* packages with a pyproject.toml not listed in
  that table.
- `other/unpackaged`: mem20* directories without a pyproject.toml
  (`mem20_mcp`, `mem20-orchestration`) — reported, not hidden.
- `mem20bjorkz` is noted in `inventory.notes` when absent ("if present").

## Health notes (what it reports truthfully)

- mem20corez: v0.2.0 installed in root venv, real model serving.
- mem20mktz: NOT in root venv; installed in its own `/opt/mem20/mem20mktz/.venv`
  (import check runs in root venv → reports `importable=False` on root env; the
  local venv install is recorded in `meta.installed`).
- mem20crewz: pyproject present but not pip-installed anywhere.
- 23 subsystems carry a pyproject.toml; 2 do not.

## Tests

```
python3 -m pytest /opt/mem20/toolchest -v
```

Tests perform **real** runtime discovery (must run on the mem20 box) and
additionally verify the MCP dump subprocess independently.
