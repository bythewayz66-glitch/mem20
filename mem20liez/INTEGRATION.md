# mem20liez — Integration & recovery

## MCP server wiring

Tools live in `mcp/tools/lie_tools.py` as `LieToolsMixin`.

The current `mcp/server.py` is a **loader** that:

1. Loads the full original server implementation from `mem20liez/_server_impl.py` (or recovery paths)
2. Subclasses `Mem20MCPServer`
3. Calls `register_lie_tools()` and dispatches any `lie_*` tool name to the mixin handlers

### One-time recovery (required if `_server_impl.py` is missing)

```bash
cd /path/to/mem20
git show 6a2bdaab2434611a2edee5d26b93bcc500edb87b:mcp/server.py > mem20liez/_server_impl.py
# restart MCP / systemd unit
```

Alternative — restore original server and patch manually:

```bash
git checkout 6a2bdaab2434611a2edee5d26b93bcc500edb87b -- mcp/server.py
```

Then add:

1. `from tools.lie_tools import LieToolsMixin`
2. `LieToolsMixin` to the `Mem20MCPServer` base list
3. `self.register_lie_tools()` in `_setup_tools`
4. `elif tool_name == "lie_...": return await self._lie_...(arguments)` branches in `_execute_tool`

## Grounded memory + braid on seal

`lie_seal_session` (in the mixin):

- Builds the sealed package via `LiveLieSession.seal()`
- Calls `remember(content, tags=[...], metadata={full_package})` when the memory engine is importable
- Calls `braid_commit(op="liez.session.sealed", ...)` when braid_bridge is available
- Returns `memory_receipt`, `braid_receipt`, `grounded_written`, `braid_journaled`

## Verifying tools are live

```text
lie_status  →  { available, memory_available, braid_available, sessions }
```

## Optional dependencies

```bash
pip install sounddevice pyttsx3 Pillow   # live mic + TTS + vision frames
```
