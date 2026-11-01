# mem20_mcp

Thin loader for the **canonical** mem20 MCP server.

The canonical, running server lives at `/opt/mem20/mcp`. That is proven
independently by:

- the live process table (`python3 /opt/mem20/mcp/mcp_server.py`)
- `mcp-server.service` (`WorkingDirectory=` and `ExecStart=`)
- `/root/.config/opencode/opencode.jsonc`

Every module in this package is a read-only forwarder to that tree. Nothing here
reimplements or caches tool logic: each module re-exports the canonical module
of the same name. This is why `mem20_mcp` boots the identical real tool set
instead of drifting away from it.

Set `MEM20_CANONICAL_MCP_ROOT` to point the forwarder at a different canonical
tree. That is used only by tests.

## Why this exists

`mem20_mcp` was originally a stale copy of the server whose
`tools/world_tools.py` had lost the `WorldToolsMixin` class, so
`server.py`'s import raised `ImportError` and the package could not boot. Rather
than maintaining a second implementation, the tree was reduced to a loader and
the canonical server became the single source of truth.

## What this package is not

- Not a second MCP server. Starting a server means running the canonical
  `/opt/mem20/mcp/mcp_server.py` (see `mcp-server.service`).
- Not a place to add tools. Add them to `/opt/mem20/mcp/tools/`, which this
  package forwards to.

## Preflight

A forwarder has exactly one failure mode and it is quiet: if the canonical tree
is stubbed or stale, this package boots it anyway and the estate runs the wrong
logic while looking healthy. So the tree is checked before it is loaded.

`preflight.py` consults six estate modules, and each answers a question a loader
cannot answer for itself:

| Estate module | Question it answers | Refusal |
|---|---|---|
| `mem20verify.linters.noop_bodies` | is a canonical tool's body real, or `pass`? | `stub_body` |
| `mem20ops.clicheck.classify_naming` | is the exposed tool name an estate address? | `naming` |
| `mem20liez.gates.check_prohibited_uses` | may this tree be exposed for the declared purpose? | `prohibited_use` |
| `mem20temporaldatabasefabricz.temporal.interval.contains` | is this instant inside the tree's release window? | `outside_window` |
| `mem20ircz.filter.classify` + `NoiseMeter` | which log lines are signal, and how much was swallowed? | (filters, never refuses) |
| `mem20dreamz.ledger.commit_raw` | which tree did this process actually load? | (records, never refuses) |

`canonical_root()` runs it, so a stubbed canonical tool raises `ImportError` at
boot instead of serving a well-formed nothing. Set `MEM20_MCP_PREFLIGHT=0` to
skip it when a caller has already run it.

Note that a module *filename* is not an MCP address: the canonical modules are
named `health`, `world_tools`, `braid_tools`, all of which classify as `other`.
The exposed name is what a client addresses, so that is what is checked.

## Verify

```bash
python3 -c "import mem20_mcp; print(mem20_mcp.__canonical_root__)"
```

That prints `/opt/mem20/mcp`.

```bash
# run the six admission checks over the canonical tree; exit 1 if refused
python3 mem20_mcp/cli.py preflight

# list the canonical tool modules and the naming class of each exposed name
python3 mem20_mcp/cli.py tools

# which tree would be checked
python3 mem20_mcp/cli.py root
```

A stubbed canonical tool is refused rather than served:

```bash
python3 mem20_mcp/cli.py preflight
```

```json
{
  "refused": true,
  "check": "stub_body",
  "reason": "stub_body: 1 stub body/bodies under /opt/mem20/mcp/tools, first at .../stub_tools.py:2 (noop_body)"
}
```

## Tests

```bash
python3 -m pytest mem20_mcp/tests -q
```

## Related

- `/opt/mem20/mcp` - the canonical server and the real tool implementations
- `mem20-orchestration/` - **not packaged.** It currently contains a single file,
  `tools/blender_ops.json`, and no Python. It is an unfinished scaffold, not a
  subsystem, and is deliberately left unpackaged rather than shipped as an empty
  package.
