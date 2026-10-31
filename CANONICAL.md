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
| Tracked files | 9,882 |
| `mem20*z` subsystem packages | 293 |
| Primary languages | Python (1,709), JavaScript (1,428), TypeScript (518+81 tsx), Rust (65), C# (50) |
| License | MIT |
| Default branch | `main` |

Major trees include the Python MCP server (`mem20_mcp/`, `mcp/`, `mcp_server_dir/`), the
`braid` Rust workspace (core / drive / her / keys / sonic / ui_bridge / wire), the
`dashboard`, `roadmaps/`, `2.0_roadmap/`, `packaging/`, `toolchest/`, `reference_store/`,
`memory_engine/`, `tests/` and `verification/`.

## Canonical designation

The full codebase is published to this repository. No other repository is canonical.

The former `JaysonAIOnline/*` organisation is **retired** (2026-10-31): no documentation,
badge, install snippet, config or launch copy references it, and nothing is published to
it.

One code-level reference is retained deliberately: the `mem20oreo` dependency in
`mem20agentz/pyproject.toml` still resolves to a `JaysonAIOnline/oreo` git URL, because
the package has not been mirrored to a live host. It is a build input, not a publication
target, and it is the only remaining reference in executable code.

## Content & editorial surfaces

All user-facing content and editorial assets — the root `README.md`, everything under
`docs/`, install snippets, badges, clone commands and example tool calls — are re-pointed
to this canonical repository, so every published copy, install path and link resolves to
`bythewayz66-glitch/mem20`. Canonical clone + install snippet:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20 && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

mem20 is distributed from source; it is **not yet published to PyPI**, so every install
snippet resolves to this repository.

## Publication routing

Publication is **GitHub-only**. The former Sidney host and the `gabe` publish authority
are **retired** (2026-10-31); no publish path routes through either, and no credential,
hostname or runbook for them is operative.

- GitHub publication channel: this repository (`main`).
- Website publication channel: GitHub Pages, built from `docs/` (custom domain `mem20.com`).

## Snapshot record

- Canonical designation recorded: 2026-10-14
- Base snapshot commit (previous full push): `64c73359f3f7602b350b29d81c82630a86e01c5d`
  ("fix(verification): hoist regex out of f-string for Python 3.11 compatibility",
  2026-10-05, branch `main`)
- Latest upstream push at time of this record: 2026-10-12

_This file is maintained as the canonical marker for the mem20 repository._
