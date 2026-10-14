# mem20 — Canonical Repository

**Status:** Canonical / authoritative source of truth
**Repository:** https://github.com/bythewayz66-glitch/mem20
**Default branch:** `main`
**License:** MIT

## What this repository is

This is the canonical mem20 monorepo: persistent memory + cognition substrate for AI
agents, together with the full platform surface built around it.

Verified contents of this canonical snapshot:

| Item | Value |
| --- | --- |
| Tracked files | 9,873 |
| `mem20*z` subsystem packages | 293 |
| Primary languages | Python (1,709), JavaScript (1,428), TypeScript (518+81 tsx), Rust (65), C# (50) |
| License | MIT |
| Default branch | `main` |

Major trees include the Python MCP server (`mem20_mcp/`, `mcp/`, `mcp_server_dir/`), the
`braid` Rust workspace (core / drive / her / keys / sonic / ui_bridge / wire), the
`dashboard`, `roadmaps/`, `2.0_roadmap/`, `packaging/`, `toolchest/`, `reference_store/`,
`memory_engine/`, `tests/` and `verification/`.

## Canonical designation

The full codebase is published to this repository. Related repositories are **not**
canonical:

- `JaysonAIOnline/mcp-cognitive-substrate` — earlier, much smaller Python MCP server
  (11 files, v1.0.1). Historical / reference only.
- `JaysonAIOnline/mem20-site` — marketing website, not the codebase.
- `JaysonAIOnline/mem20kilnz-engine`, `JaysonAIOnline/hermes-messenger`,
  `JaysonAIOnline/oreo`, `JaysonAIOnline/sales`, `JaysonAIOnline/mem20-unimpc-3d` —
  component / satellite repositories.

Direct pushes to `JaysonAIOnline/*` are read-only for the canonical publishing account.

## Publication routing

Per the project's publication mandate, work is published to the **Sidney** server via
`ssh` / `sftp` / `rsync`, and that publication is **routed through gabe**.

- GitHub publication channel: this repository (`main`).
- Server publication channel: Sidney, via ssh/sftp/rsync, routed through gabe.

## Snapshot record

- Canonical designation recorded: 2026-10-14
- Base snapshot commit (previous full push): `64c73359f3f7602b350b29d81c82630a86e01c5d`
  ("fix(verification): hoist regex out of f-string for Python 3.11 compatibility",
  2026-10-05, branch `main`)
- Latest upstream push at time of this record: 2026-10-12

_This file is maintained as the canonical marker for the mem20 repository._
