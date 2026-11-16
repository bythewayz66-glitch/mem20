# `.vscode/` — editor integration for the mem20 MCP server

**Owner:** mem20-admin · **Status:** tool-owned config

Editor configuration that registers the mem20 MCP server with **GitHub Copilot agent
mode** in VS Code. mem20 *is* an MCP server, so this is the extension point that lets
Copilot call its memory, retrieval and cognitive tools directly.

## What lives here

| File | What it does |
|---|---|
| [`mcp.json`](./mcp.json) | Registers a `mem20` server over **stdio**, launched as `python3 ${workspaceFolder}/launcher.py`. |

The launcher resolves `mcp/` relative to the workspace and runs `mcp_server.py`
exactly as `python mcp/mcp_server.py` would. Transport is stdio; `PYTHONUNBUFFERED=1`
is set so tool output is not buffered behind the pipe.

## Rules

1. **Tool-owned.** `.gitignore` ignores `.vscode/*`; this README is tracked via a
   `!.vscode/README.md` negation. Do not add personal editor settings here — they will
   not be tracked and will conflict with other contributors.
2. **Launch through `launcher.py`, never a hardcoded absolute path.** The launcher is
   what makes the config portable across checkouts.
3. **stdio only.** Do not switch this to a network transport; the server's stdio
   contract is what the MCP host expects.

## Related

- [`mcp/README.md`](../mcp/README.md) — the server this config launches.
- [`launcher.py`](../launcher.py) — the workspace-relative entry point.
- [`docs/03-installation.md`](../docs/03-installation.md) — connecting other MCP hosts.
