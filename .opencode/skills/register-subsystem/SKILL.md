---
name: register-subsystem
description: Register a mem20 subsystem across gateway, toolchest, MCP, and sitemapz surfaces in one pass
---

# Register Subsystem (mem20)

Use this when making a `mem20*` subsystem first-class and it must appear in every registry that conformance, discovery, or operators rely on.

## Goal

**One tool/flow hits all registries**: gateway entry, toolchest inventory, MCP surface (if applicable), and sitemapz visibility — with real, verifiable entries (no placeholders).

## Registries

| Registry | Where | How to register | Verify |
|---|---|---|---|
| Gateway / conformance (criterion 7) | `gateway/mem20_gateway.py` `SUBSYSTEMS` | Add `name -> {purpose, entry, owner, wave}` with a working `entry` command | `python -m <name> status` (or the declared entry) runs; `grep -n name gateway/mem20_gateway.py` |
| Toolchest inventory | `toolchest/inventory.json` (generated) | Regenerate: `cd /opt/mem20 && PYTHONPATH=/opt/mem20 .venv/bin/python -m toolchest refresh` (or run the catalog builder for the estate root). Do not hand-edit generated fields except to fix a known-wrong entry when refresh is unsafe in a shared tree. | `.venv/bin/python -m toolchest show <name> --check-path` (or inspect entry: correct `source`, `pyproject`, description, importable/runtime detail) |
| MCP | `mcp/tools/*_tools.py` + `mcp/server.py` registration; and/or presence discoverable by conformance | Only add a dedicated `*_tools.py` when the subsystem exposes a real MCP-worthy surface. Implement real handlers (call the subsystem), register the mixin in `mcp/server.py`, add to the tool table. Otherwise ensure conformance criterion 7 is satisfied via gateway/mcp search. | Import `mcp.server` in a safe context if possible; `grep -rn name mcp/`; run the subsystem's own tests |
| Sitemapz | `mem20sitemapz` discovers from the filesystem (policy/index) | No manual registry file in normal cases — ensure the package exists at `<root>/<name>/` with real `pyproject.toml`/source and is not excluded by `sitemapz` policy. | `mem20sitemapz` build/index over the root includes the path; check `mem20sitemapz` policy if skipped |
| Package metadata | `<name>/pyproject.toml`, `README.md`, console script | Keep `name/version/description`, `[project.scripts]`, and package-data accurate | `python -m <name> --help`/`status` |
| Docs/app shell (if a UI exists) | `docs/app/*` (static) and subsystem `web/` | Add a static page under `docs/app/<topic>/` and link from `docs/app/README.md`; never edit compiled Vite assets | open page against the subsystem's API; JS syntax check |

## One-pass checklist (run in order)

```bash
cd /opt/mem20
NAME=mem20examplez

# 1) Package/CLI works
PYTHONPATH=/opt/mem20 .venv/bin/python -m "$NAME" status

# 2) Gateway
grep -n "\"$NAME\"" gateway/mem20_gateway.py || echo "ADD to SUBSYSTEMS"

# 3) Toolchest (refresh may be slow; in shared tree consider targeted fix only if necessary)
PYTHONPATH=/opt/mem20 .venv/bin/python -m toolchest show "$NAME" 2>&1 | head -40
# PYTHONPATH=/opt/mem20 .venv/bin/python -m toolchest refresh   # full regenerate

# 4) MCP/conformance presence
grep -rn "$NAME" mcp gateway 2>/dev/null | head -15

# 5) Sitemapz visibility (filesystem-discovered)
test -f "$NAME/pyproject.toml" && echo "package present for sitemapz discovery"

# 6) Conformance gate
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py "$NAME"
```

## Rules

- **No fake registrations.** Every entry must point to real, working code/commands.
- **Shared tree:** commit with `git commit --only <paths>`; never `git add -A`.
- **MCP tools:** real handlers only — no stubs, no `NotImplementedError`.
- **Toolchest:** prefer generator (`refresh`) over manual inventory edits; if manual is unavoidable in a shared tree, change only the target entry and keep fields truthful.
- **Cross-module wiring:** when fixing a subsystem to 7/7, its ≥5 cross-module peers must be a **different set** on each subsystem (no reused template).

## Helper

If `scripts/renovation/register_subsystem.py` exists, it automates the safe parts (gateway check/patch template, toolchest show, conformance). Read it before running and review diffs.
