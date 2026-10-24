# @mem20/sdk (TypeScript)

**First-class TypeScript/JavaScript client** for the mem20 MCP server.

- Protocol: JSON-RPC 2.0 over stdio, MCP `2025-06-18`
- Server baseline: mem20 **3.0.0**
- Runtime deps: **none** (Node 18+ `fetch` + `child_process` only)
- Access to the full ~270-tool surface via `tool()` plus `memoryStore` / `memoryRecall` helpers

## Install

```bash
# from monorepo
cd mem20-sdk-typescript && npm install && npm run build

# or link from a package.json
"@mem20/sdk": "file:../mem20-sdk-typescript"
```

## Quick start

```ts
import { Mem20Client } from '@mem20/sdk';

const client = Mem20Client.create({
  cwd: '/path/to/mem20',           // checkout root (mcp/mcp_server.py)
  timeoutMs: 60_000,               // first embedding call can be slow
});

await client.memoryStore({
  content: 'Prod runs build 4127',
  category: 'deploys',
  tags: ['prod'],
});

const hits = await client.memoryRecall({ query: 'what build is prod on', limit: 5 });
console.log(Mem20Client.text(hits));

await client.tool('memory_status', {});
await client.close();
```

## Contamination invariant

mem20 **guarantees** `contamination_rate == 0.0` at the store layer: simulated content cannot enter grounded indexes. This client does not weaken that invariant; it only speaks the protocol.

Index health is enforced by the engine (rebuild / drift fixes). Prefer `mem20api` health/rebuild when operating the store directly.

## API

| Method | Purpose |
|--------|---------|
| `tool(name, args)` | Call any registered MCP tool |
| `tools()` | List tool names |
| `memoryStore` / `memoryRecall` | Memory primitives |
| `health` / `ready` / `healthy` / `metrics` | HTTP observability on `:8080` |
| `close()` | Tear down child process |

## Tests

```bash
npm test
```

## License

MIT — same as the canonical mem20 monorepo.
