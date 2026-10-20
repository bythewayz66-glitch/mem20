# mem20 2.1.0rc2 — wheel packaging release note

**Producer:** Server Builder
**Canonical repository:** github.com/bythewayz66-glitch/mem20
**Source commit:** 8e2f80318c4fe0ad8df8d1ed769e6ed4ffea502d (main)
**Artifact:** `mem20-2.1.0rc2-py3-none-any.whl`
**sha256:** `c433f9780595acce811a443d2c16036a3376176b81273d41811e614dd553c3fc`
**Byte size:** 189868
**Wheel entries:** 52
**Payload files under `mem20_runtime/`:** 39

The canonical repository is github.com/bythewayz66-glitch/mem20.

## What was broken

A clean build of the stock tree produced a wheel with 13 entries that contained
no server at all — no `mem20_runtime/`, no `mcp_server.py`. Building appeared to
work only because a stale `build/lib/mem20_runtime/` directory was committed to
git, so setuptools reused that leftover output instead of the current source.
That stale copy held 33 Python files against 37 in `mcp/`, so it also silently
shipped seven-week-old tool code. Installed from such a wheel, the entrypoint
died at import.

Three defects were fixed:

1. **The bundled server tree was never declared.** The fix ships the bundled
   MCP server tree as the `mem20_runtime` package, staged from `mcp/` by
   `scripts/stage_runtime.sh` immediately before the build. It cannot be
   installed as a top-level `mcp` package, because that would shadow the `mcp`
   SDK the server itself imports.
2. **Build output was committed.** `build/`, `dist/`, `mem20_runtime/` and
   `*.egg-info/` are now ignored, so a stale tree can no longer mask a broken
   wheel.
3. **The launcher accepted any directory named `mcp`.** In an installed
   environment that path is the SDK, not the server. It now requires the
   `mcp_server.py` marker, so it refuses a lookalike instead of running the
   wrong tree.

One undeclared runtime import was also added to the dependency set: `aiohttp`,
imported unconditionally by `mcp/tools/a2a_tools.py`, whose absence aborted
startup with `ModuleNotFoundError`. `faiss-cpu` and `sentence-transformers`
remain optional extras, because the engine guards their import and falls back to
lexical recall; that is what makes the package installable on a bare system
interpreter such as Python 3.14. `mcp` is pinned below 2.2 because the server
uses `mcp.server.lowlevel.server.ServerRequestContext` and the `mcp_types`
module shipped by the 2.1.x series.

## The wheel contains no .pyc or __pycache__ entries

The wheel contains no `.pyc` or `__pycache__` entries: 0 of 52 entries are
bytecode. The previous bundle carried cpython-314 bytecode compiled on the
authoring host into a `py3-none-any` wheel.

## Reproduced from this exact wheel

- The installed console script is `mem20-mcp`, installed from the wheel above
  into a clean virtual environment, and it serves 257 tools over stdio.
- `initialize` returned `serverInfo.name = "mem20-mcp"` with
  `protocolVersion = "2025-06-18"`.
- `tools/list` returned 257 tools, beginning with `memory_store`,
  `memory_recall`, `memory_probe`, `memory_reason`, `memory_status`.
- The server starts from the installed wheel, not from the git checkout: the
  verification ran in a fresh virtual environment whose site-packages contained
  only the wheel and its declared dependencies, with `PYTHONPATH` cleared and
  the working directory outside the repository.

## House numbers

Unchanged and not affected by this packaging work: 257 tools across 26 domains;
TAM 1.28B USD, SAM 282M USD, SOM 1.68M USD; blended ACV 14,000 USD.

## Status of the Sidney publish

This note is the artifact submitted to gabe for publication on Sidney. The
service deployment that follows it is described in `systemd/mem20.service` and
`deploy_to_sidney.sh`. No claim is made here that the service is already
running on Sidney; that step requires an SSH credential for the host and is
tracked separately.
