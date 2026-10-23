# mem20liez — Integration

## MCP server (zero-config for new users)

`mcp/server.py` **auto-loads** the full implementation:

1. Uses `mem20liez/_server_impl.py` if you vendor a copy
2. Otherwise runs `git show 6a2bdaa…:mcp/server.py` from the local repo and applies the LieToolsMixin patch in memory

A normal `git clone https://github.com/bythewayz66-glitch/mem20.git` is enough. No recovery command.

Shallow clones should use sufficient depth to include commit `6a2bdaab2434611a2edee5d26b93bcc500edb87b` (e.g. `--depth 100`), or a full clone.

### Optional: vendor the impl (offline / non-git installs)

```bash
git show 6a2bdaab2434611a2edee5d26b93bcc500edb87b:mcp/server.py > mem20liez/_server_impl.py
```

Only needed for tarball installs without git history.

## Failure behaviour

`_bootstrap()` reports every failure as **`ImportError`**, never `SystemExit`:
a missing implementation, an unreachable git object, and the restored
implementation calling `sys.exit(1)` on a missing dependency all raise
`ImportError`. This matters for test runners — a module-level `SystemExit`
propagates out of `exec()` and aborts the process, which pytest escalates to
`INTERNALERROR` and aborts *collection for the whole session*. An `ImportError`
is confined to the importing module, so one unavailable dependency produces one
failing test file instead of a dead test run.

## Tools

`mcp/tools/lie_tools.py` — `LieToolsMixin` registered automatically by the restored server.

## Grounded + braid on seal

`lie_seal_session` calls `remember()` and `braid_commit(op="liez.session.sealed")` when those engines are available.
