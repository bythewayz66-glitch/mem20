# mem20 Godot SDK

**First-class Godot 4.x addon** — GDScript client for the mem20 MCP server
(JSON-RPC 2.0 over stdio, protocol `2025-06-18`).

Designed for game agents, NPC memory, and studio tooling that runs inside the editor or exported games (desktop platforms that can spawn a process).

- Server baseline: mem20 **3.0.0**
- No third-party addons required
- Same surface as the Ruby / TypeScript / Perl clients: `memory_store`, `memory_recall`, `tool()`, health probes

## Install

1. Copy `addons/mem20/` into your Godot project’s `addons/` folder.
2. Project → Project Settings → Plugins → enable **mem20**.
3. Point `server_cwd` at a mem20 checkout (directory that contains `mcp/mcp_server.py`).

## Quick start

```gdscript
var client := Mem20Client.new()
client.configure({
    "server_cwd": "/opt/mem20",
    "timeout_sec": 60.0,
})
await client.start()

await client.memory_store({
    "content": "Player found the blue key in room 3",
    "category": "quest",
    "tags": ["player", "key"],
})

var hits = await client.memory_recall({"query": "where is the blue key", "limit": 5})
print(Mem20Client.text(hits))

client.close()
```

## Contamination invariant

The store **guarantees** `contamination_rate == 0.0`. Simulated / hypothetical content never reaches grounded indexes. This addon is a protocol client only.

## Platform notes

- Requires OS feature `OS.execute` / `OS.create_process` (editor and desktop exports).
- Web / HTML5 exports cannot spawn the Python server; use an external mem20 process and HTTP bridge if you need browser targets.

## License

MIT.
