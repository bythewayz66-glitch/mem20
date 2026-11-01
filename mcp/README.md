# mcp — the mem20 MCP server

The Model Context Protocol server for mem20. It is the single surface through
which a client reaches the rest of the estate: memory, cognition, roadmap,
filesystem, braid, IRC and behavioural-signal tools all register here.

`server.py` is the authoritative implementation. `mcp_server.py` is a shim that
preserves the systemd `ExecStart` path. Both start the same server.

## Install (source only)

mem20 is **not on PyPI**. Install from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

## Run the server

```bash
python mcp/server.py                        # stdio transport (default)
MEM20_TRANSPORT=http python mcp/server.py   # streamable HTTP on :8082
```

The operational endpoint (`/health`, `/ready`, `/metrics`) listens on `:8080`
unless `MEM20_HEALTH_DISABLE=1`.

## Tool-surface admission control

`surface.py` decides whether a tool may be registered. It does not invent its
own rules — each check is delegated to the subsystem that owns it:

| check | owner | what it refuses |
|---|---|---|
| naming | `mem20ops.clicheck` | a server that is not a fleet binary, a tool name that is not MCP snake_case |
| body | `mem20verify.linters` | a handler whose body is only `pass`, or whose branches are identical |
| intended-use | `mem20liez.gates` | a prohibited behavioural-signal use |
| notification | `mem20ircz.filter` | wire noise that is not worth an agent's tokens |
| temporal | `mem20temporaldatabasefabricz` | a time-boxed tool used outside its window |

### Runnable example

Admit one tool, then audit the live registry:

```bash
python mcp/cli.py admit memory_store --source mcp/health.py
python mcp/cli.py audit
```

Real output on this tree:

```
memory_store: admitted (3 checks passed)
tools: 270  admitted: 270  refused: 0
```

A refusal is diagnosable, not a bare `False`:

```bash
python mcp/cli.py admit "Bad Tool!" --source mcp/health.py
```

```
Bad Tool!: refused
  - naming: tool 'Bad Tool!' is not a valid MCP tool name (expected lowercase snake_case, e.g. memory_store)
```

Exit codes: `0` admitted / clean, `1` refused / refusals found.

## Tests

```bash
python -m pytest mcp/tests -q
```

## Layout

- `server.py` — the server: tool registry, JSON-RPC dispatch, job registry
- `surface.py` — admission verdicts: `admit_tool`, `audit_registry`
- `checks.py` — the five checks, one per owning subsystem
- `estate.py` — repo-relative estate bootstrap and the verdict types
- `cli.py` — `admit` / `audit` / `registry`
- `health.py` — `/health`, `/ready`, `/metrics`
- `install_tracker.py` — opt-out local install telemetry
- `tools/` — one mixin per tool family
