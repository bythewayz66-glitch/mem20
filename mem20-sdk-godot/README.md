# mem20 Godot SDK

**First-class Godot 4.x addon** — GDScript client for the mem20 MCP server
(JSON-RPC 2.0 over stdio, protocol `2025-06-18`).

Designed for game agents, NPC memory, and studio tooling that runs inside the editor or exported games (desktop platforms that can spawn a process).

- Server baseline: mem20 **3.1.2**
- No third-party addons required
- Same surface as the Ruby / TypeScript / Perl clients: `memory_store`, `memory_recall`, `tool()`, health probes

## Install

1. Copy `addons/mem20/` into your Godot project’s `addons/` folder.
2. Project → Project Settings → Plugins → enable **mem20**.
3. Point `server_cwd` at a mem20 checkout (directory that contains `mcp/mcp_server.py`).

`mem20_client.gd` drives the committed `mem20_bridge.py` helper; do not copy one
without the other. The bridge uses only the Python standard library, but the
*server* needs the mem20 dependencies. If `server_cwd` contains a `.venv/`, the
client uses that interpreter automatically; otherwise it runs `python3`
(`python` on Windows). Override both explicitly if needed:

```gdscript
client.configure({
    "server_cwd": "/opt/mem20",
    "server_command": ["/opt/mem20/.venv/bin/python", "mcp/mcp_server.py"],
    "env": {"MEM20_STORE_PATH": "/opt/mem20/store"},
    "timeout_sec": 120.0,
})
```

## Quick start

```gdscript
var client := Mem20Client.new()
client.configure({
    "server_cwd": "/opt/mem20",
    "timeout_sec": 120.0,
})
var err := client.start()          # one real initialize handshake
if err != OK:
    push_error(client.last_error())

var stored = client.memory_store({
    "content": "Player found the blue key in room 3",
    "category": "quest",
    "tags": ["player", "key"],
    "epistemic_status": "observed",   # required: how the claim is known
})

var hits = client.memory_recall({"query": "where is the blue key", "limit": 5})
print(Mem20Client.text(hits))

client.close()
```

`epistemic_status` is required by the tool's own `inputSchema`. Omitting it does
not raise a JSON-RPC error: the server answers `isError=false` with an explanatory
string, which callers mistake for success. This client refuses to send the request
without it and rejects `imagined` (invented content belongs in
`memory_simulate_store`).

Allowed grounded values: `observed`, `inferred`, `user_stated`, `hypothesis`,
`agent_generated`, `unlabeled`.

## Process model

Godot's `OS.execute()` cannot write to a child process's stdin while it runs, so
the bridge is **one-shot**: each call starts the server, writes `initialize`, the
`notifications/initialized` notification and the request in one batch, then reads
the matching response. `start()` runs the initialize handshake once so a bad
command, checkout or interpreter fails immediately; `close()` releases client
state because no child process survives a call.

`health()` / `ready()` use a real `HTTPRequest` and therefore talk to a
**separately running** mem20 server on `health_host`/`health_port` (default
`127.0.0.1:8080`). The one-shot bridge process has already exited by the time an
HTTP probe runs, so a null result means "no server is listening", not "the
client is broken".

## Exported games

`mem20_bridge.py` is a plain file next to the client script. Add it to the export
preset’s **Resources → Filters to export non-resource files** (`*.py`) so it lands
on disk beside the executable; `res://` files are otherwise packed into the PCK
and Python cannot read them.

## Tests

```bash
# Fast, no server required:
python3 mem20-sdk-godot/tests/test_bridge.py

# Full round-trip against a real checkout and a real health endpoint:
GODOT=/path/to/godot4 ./mem20-sdk-godot/tests/run_headless.sh
```

The headless test asserts `start()`, `health()`, `ready()`, `memory_status`, the
`epistemic_status` guard, a grounded `memory_store`, and that a configured
`server_command` is honoured.

## Contamination invariant

The store **guarantees** `contamination_rate == 0.0`. Simulated / hypothetical content never reaches grounded indexes. This addon is a protocol client only.

## Platform notes

- Requires OS feature `OS.execute` (editor and desktop exports).
- Web / HTML5 exports cannot spawn the Python server; use an external mem20 process and HTTP bridge if you need browser targets.

## License

MIT.
