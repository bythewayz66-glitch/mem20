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

## Verify

```bash
python3 -c "import mem20_mcp; print(mem20_mcp.__canonical_root__)"
```

That prints `/opt/mem20/mcp`.

## Related

- `/opt/mem20/mcp` — the canonical server and the real tool implementations
- `mem20-orchestration/` — **not packaged.** It currently contains a single file,
  `tools/blender_ops.json`, and no Python. It is an unfinished scaffold, not a
  subsystem, and is deliberately left unpackaged rather than shipped as an empty
  package.

## Loader-integrity audit

The failure mode of a forwarding package is silent: a shim that stops forwarding
and starts *containing* code still imports, still exposes the right names, and
still passes a smoke test — while the estate now has two implementations of the
same tool. `mem20_mcp.loader_audit` checks every shim for exactly that, and asks
the estate's own modules rather than re-deriving the rules.

```bash
# audit every forwarding shim in the package
python3 -m mem20_mcp.cli audit

# machine-readable, for CI
python3 -m mem20_mcp.cli audit --json

# declare what the audit is for; checked against the prohibited-use list
python3 -m mem20_mcp.cli audit --intended-use loader_integrity
```

Exit code 0 only when every shim forwards, is named like an estate module, and
has a real body. A broken shim is reported per module, never silently skipped:

```text
mem20_mcp loader audit: CLEAN
root: /opt/mem20/mem20_mcp
shims: 8  broken: 0

package naming: mem20-native

module              forwards  via                     stubs  result
blender_bridge.py   True      _load                       0  ok
mcp_server.py       True      from server import          0  ok
server.py           True      _load                       0  ok
```

Two forwarding routes are accepted: a direct `_load(...)` call, and importing
from a sibling shim (`mcp_server.py` gets `main` from the `server` shim, which is
itself a forwarder). A module that reaches neither is reported as drift.

The audit also records its result as a content-addressed provenance node through
`mem20dreamz.ledger`, and reports honestly when braid is unreachable
(`committed: false` with the reason) rather than pretending the node was written.

```bash
python3 -m pytest mem20_mcp/tests -q
```
