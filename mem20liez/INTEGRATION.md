# mem20liez — Integration

## MCP server (zero-config, works on `git clone --depth 1`)

`mcp/server.py` **is** the server. It is not a loader: it does not read git history, it
does not fetch objects, and it has no vendored fallback. Everything it needs is in the
working tree, so a `git clone --depth 1` checkout starts correctly with **zero git
history and no network access**.

```bash
git clone --depth 1 https://github.com/bythewayz66-glitch/mem20.git
cd mem20 && python3 ./launcher.py     # works — no unshallow, no extra fetch
```

There are no environment knobs for startup. The former `MEM20_MCP_AUTO_FETCH` and
`MEM20_GOOD_COMMIT` variables, the `mem20liez/_server_impl.py` vendored copy and
`mem20liez/regen_server_impl.py` have all been removed — see the history note below.

### Entry points

All three are equivalent and resolve to the same implementation:

| Command | Notes |
|---|---|
| `python mcp/server.py` | Direct |
| `python mcp/mcp_server.py` | Shim; preserves the systemd `ExecStart` path |
| `python launcher.py` | Backs the `mem20-mcp` console script |

### Verifying a checkout

```bash
python3 ./verify_mcp.py     # initialize + tools/list; exits non-zero unless 270 tools
```

CI runs the same script from a deliberately shallow checkout
(`.github/workflows/mcp-verify.yml`, `fetch-depth: 1`), so a regression in shallow-clone
support fails the build rather than shipping.

### History note

`mcp/server.py` used to be a bootstrap loader that reconstructed the implementation with
`git show 6a2bdaab2434611a2edee5d26b93bcc500edb87b:mcp/server.py`. On a `--depth 1` clone
that object is absent, so startup failed with *"mem20 MCP server implementation not
found."* The implementation now lives directly in `mcp/server.py`; the loader, the
resolution ladder and the vendored artefact are gone. See
[`docs/troubleshooting-mcp-server-startup.md`](../docs/troubleshooting-mcp-server-startup.md)
§ Symptom A for the full account.

## Tools

`mcp/tools/lie_tools.py` — `LieToolsMixin`, registered by `Mem20MCPServer.__init__` via
`self.register_lie_tools()`. It contributes the 10 `lie_*` tools to the 270-tool surface.

## Grounded + braid on seal

`lie_seal_session` calls `remember()` and `braid_commit(op="liez.session.sealed")` when
those engines are available.
