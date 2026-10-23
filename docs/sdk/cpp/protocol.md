# mem20 C++ SDK — Protocol

Wire contract the SDK speaks to a mem20 server.
**Server baseline:** `mem20` 2.1.0rc2 · **Repo:** https://github.com/bythewayz66-glitch/mem20 (`main`)

Everything here is derived from the mem20 server source. Per-claim file paths and the
commit are listed in [`source-ledger.md`](source-ledger.md).

---

## 1. Transport

| Transport | Status | How it appears in the server |
|---|---|---|
| **stdio** | **Canonical** | `stdio_server()` in `mcp/server.py`; the server reads/writes JSON-RPC on stdin/stdout |
| **Streamable HTTP + SSE** | Optional | `StreamableHTTPSessionManager` mounted at `/` under uvicorn; `POST initialize` and `GET SSE` both live under `/` |

The SDK's primary transport is **stdio**: it spawns the server as a child process and
exchanges newline-delimited JSON-RPC frames on the child's stdin/stdout.

### stdio framing

One complete JSON-RPC message per line, UTF-8, terminated by `\n`. There is **no**
`Content-Length` header (this is not the LSP framing). A frame is never split across
lines; embedded newlines inside strings are JSON-escaped (`\n`). The SDK's reader
accumulates bytes until a `\n` and then parses one message.

> stderr is the server's log channel and is **not** part of the protocol. The SDK
> forwards it to an optional log sink and never parses it as JSON-RPC.

---

## 2. Message envelope (JSON-RPC 2.0)

Every request/response/notification follows JSON-RPC 2.0.

**Request**
```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {} }
```

**Response (success)**
```json
{ "jsonrpc": "2.0", "id": 1, "result": { "...": "..." } }
```

**Response (error)**
```json
{ "jsonrpc": "2.0", "id": 1, "error": { "code": -32602, "message": "Invalid params", "data": "..." } }
```

**Notification** — no `id`, no response expected:
```json
{ "jsonrpc": "2.0", "method": "notifications/initialized" }
```

The SDK assigns monotonic `id`s per session and correlates responses by `id`. Server
notifications (no `id`) are dispatched to the session's notification callback.

> Illustrative values only — the SDK never hard-codes request `id`s or server payload
> bodies. Shapes below match the server's MCP handlers.

---

## 3. Handshake

The MCP handshake is three steps. The SDK performs it inside
`Session::spawn(...)` / `Session::connect(...)`; `spawn` returns only after the
handshake completes (or fails).

### 3.1 `initialize` (client → server)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "<echoed/negotiated>",
    "capabilities": { "roots": { "listChanged": true } },
    "clientInfo": { "name": "mem20_sdk_cpp", "version": "0.1.0" }
  }
}
```

### 3.2 `initialize` result (server → client)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "<server value>",
    "capabilities": { "tools": { "listChanged": true } },
    "serverInfo": { "name": "mem20", "version": "2.1.0rc2" }
  }
}
```

`Mem20MCPServer` supplies its initialization options via
`self.server.create_initialization_options()` in `server.py`, so `serverInfo` and
`capabilities` come from the SDK-backed server object rather than a literal in mem20.

> **`protocolVersion` is negotiated, not assumed.** The SDK stores whatever the server
> returns in `Session::server_info().protocol_version` and exposes it to the caller. It
> does **not** hard-code a version string.

### 3.3 `notifications/initialized` (client → server)

```json
{ "jsonrpc": "2.0", "method": "notifications/initialized" }
```

Sent once, with no `id`. After this the session is ready for `tools/list` / `tools/call`.

---

## 4. Tool discovery — `tools/list`

**Request**
```json
{ "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {} }
```

`params` may carry a pagination `cursor`. The server registers its handler as
`on_list_tools=self._handle_list_tools` (which accepts `PaginatedRequestParams`),
returning a `ListToolsResult`.

**Result (shape)**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "memory_store",
        "title": "Store Memory",
        "description": "Store a fact in mem20's persistent memory system",
        "inputSchema": {
          "type": "object",
          "properties": {
            "content":  { "type": "string", "description": "The fact/content to store" },
            "category": { "type": "string", "enum": ["user_pref","project","tool","general"], "default": "general" },
            "tags":     { "type": "string", "description": "Comma-separated tags", "default": "" }
          },
          "required": ["content"]
        }
      }
    ]
  }
}
```

`ToolDescriptor` in the SDK captures `name`, `title`, `description`, and the raw
`inputSchema` (kept as JSON so unknown/future fields survive round-trips).

The documented baseline surface is **268 tools across 26 domains**; see `README.md`
for the domain table. Tool *names* are the authority — the SDK resolves a tool by exact
name and never invents one.

---

## 5. Tool invocation — `tools/call`

**Request**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "memory_store",
    "arguments": { "content": "hello", "category": "general", "tags": "demo" }
  }
}
```

The server registers `on_call_tool=self._handle_call_tool` and dispatches to
`_execute_tool()` by name.

**Result (shape)**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [ { "type": "text", "text": "Stored memory with ID <id>" } ],
    "isError": false
  }
}
```

mem20 tool handlers return **human-readable text** (for example
`memory_promote` returns `"PROMOTED -> grounded_id=<id>. <note>"`, and refusals return
`"VETO / BLOCKED: ..."`). The SDK therefore exposes both:

* `CallResult::text()` — the concatenated `content[].text` (string surface, exactly as
  the server emitted it), and
* `CallResult::is_error()` — reflecting `isError` (and the SDK additionally flags
  refusal prefixes such as `Error:` / `VETO` / `BLOCKED` so callers can branch without
  string-matching themselves).

Typed helpers (`store`, `recall`, `promote`, …) build `arguments`, issue the call, and
lift the text into a typed result. They never mutate the wire payload beyond adding
declared inputs.

---

## 6. Errors

| Layer | Surface | SDK behaviour |
|---|---|---|
| Transport | child exited / pipe closed / spawn failed | `Session` enters `Closed`; calls return `std::unexpected(TransportError{...})` |
| JSON | malformed frame | `std::unexpected(CodecError{...})`; the session stays usable |
| JSON-RPC | `error` object present | `std::unexpected(RpcError{code, message, data})` |
| Tool | `isError: true` or refusal text | returned as a **successful** `CallResult` with `is_error()==true` (matching MCP semantics: a tool refusal is a tool result, not a protocol error) |

The SDK does **not** throw across its public boundary. All fallible entry points return
`mem20::Result<T>` (`std::expected<T, Error>` when available, else a compatible
backport). Exceptions are permitted only inside `noexcept`-declared internals.

---

## 7. Lifecycle / shutdown

1. `Session::spawn(cfg)` — fork/exec the server, run the handshake.
2. … calls …
3. `Session::~Session()` — sends a graceful EOF/terminate to the child, waits with a
   bounded timeout, then escalates to `SIGKILL` if needed. Destructors never throw and
   never block indefinitely (configurable via `ServerConfig::shutdown_timeout`).

Because `Session` is RAII, an early `return` or a thrown exception in *caller* code
still tears the child process down deterministically.

---

## 8. Relationship to the `:8080` HTTP surface

The server also exposes `/health`, `/ready`, `/metrics` on port **8080**
(`MEM20_HEALTH_PORT`). These are **observability endpoints**, not MCP: the SDK does not
use them for the protocol. A helper `mem20::HealthProbe` is provided purely for
liveness/readiness checks outside the JSON-RPC session.

---

## 9. What this document does NOT claim

* No fixed `protocolVersion` string.
* No HTTP/SSE framing beyond "both `POST initialize` and `GET SSE` live under `/`" —
  the stdio path is the SDK's supported path.
* No tool name, schema field, or server behaviour that is not present in the canonical
  repo source (see [`source-ledger.md`](source-ledger.md)).
