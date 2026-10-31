# mem20 Ruby SDK — API reference

> Canonical repo: <https://github.com/bythewayz66-glitch/mem20> (`main`) · SDK path: `mem20-sdk-ruby/`

The SDK is deliberately small: a module-level entry point, a client, a config object, a
transport, and three error classes.

```ruby
require "mem20"
```

---

## `Mem20` (module)

### `.configuration`

Returns the active `Mem20::Config`. Built lazily from `ENV` on first access.

```ruby
Mem20.configuration.health_port  # => 8080
```

### `.configure(**options) { |config| }`

Builds a fresh config from `ENV`, applies `options`, yields it for block-style setup, and
returns it. Also resets the memoised client.

```ruby
Mem20.configure(store_path: "/opt/mem20/store")
Mem20.configure { |c| c.timeout = 60.0 }
```

### `.client`

Returns a memoised `Mem20::Client` over `.configuration`.

### `.reset_configuration!` / `.reset_client!`

Drop the memoised config / client. `reset_client!` closes the underlying process first.

### Constants

| Constant | Value | Meaning |
|---|---|---|
| `Mem20::VERSION` | `"0.2.0"` | SDK version, tracked independently of the server |
| `Mem20::SERVER_VERSION` | `"2.1.0rc2"` | the mem20 release this SDK was validated against |
| `Mem20::PROTOCOL_VERSION` | `"2025-06-18"` | the MCP revision sent in the handshake |

---

## `Mem20::Client`

```ruby
client = Mem20::Client.new(Mem20.configuration)
client = Mem20::Client.new(cwd: "/opt/mem20/mem20")  # config built from ENV + options
```

| Method | Signature | Returns |
|---|---|---|
| `#tool` | `tool(name, **params)` | the tool's JSON-RPC `result` |
| `#tools` | `tools` | the `tools/list` result (name, description, `inputSchema`) |
| `#tool_names` | `tool_names` | cached `Array<String>` of registered tool names |
| `#memory_store` | `memory_store(content:, category: "general", tags: nil)` | the store result |
| `#memory_recall` | `memory_recall(query:, category: nil, limit: nil)` | the recall result |
| `#text` | `text(result)` | the plain-text payload of a result envelope |
| `#health` | `health` | parsed `/health` JSON, or `nil` |
| `#ready` | `ready` | parsed `/ready` JSON, or `nil` |
| `#healthy?` | `healthy?` | `true` when `GET :port/health` is 2xx |
| `#metrics` | `metrics` | parsed JSON from `GET :port/metrics` |
| `#transport` | `transport` | the lazily started `Transport::Stdio` |
| `#close` / `#shutdown` | `close` | `nil`; terminates the child process |
| `#config` | `config` | the frozen `Mem20::Config` |

`#tool` converts symbol argument keys to strings before sending, so
`client.tool(:memory_recall, query: "x")` and `client.tool("memory_recall", "query" => "x")`
are equivalent.

### Dynamic bindings

`Client#respond_to_missing?` resolves against the live tool list, so any registered tool
can be called as a method with keyword arguments:

```ruby
client.memory_status          # == client.tool("memory_status", {})
client.memory_probe           # == client.tool("memory_probe", {})
```

Unknown names raise `NoMethodError` as usual; positional arguments to a known tool raise
`ArgumentError`.

---

## `Mem20::Config`

A configuration object for a `Mem20::Client`. It is **mutable while being set up** —
through keyword options or the block DSL in `Mem20.configure` — and is **frozen once
handed to a client**, so a running client's config can never change underneath it.
Unknown options, an empty `server_command`, a non-positive `timeout` and an
out-of-range `health_port` all raise `ConfigurationError`, on construction and after
every writer.

```ruby
Mem20::Config.new(
  server_command: ["python3", "mcp/mcp_server.py"],
  cwd: "/opt/mem20/mem20",
  store_path: "/opt/mem20/store",
  cog_path: nil,
  llm_base_url: "https://integrate.api.nvidia.com/v1",
  llm_model: nil,
  llm_api_key: nil,
  health_port: 8080,
  health_host: "127.0.0.1",
  protocol_version: "2025-06-18",
  timeout: 30.0,
  env: {}
)
```

| Attribute | Type | Default | Mirrors |
|---|---|---|---|
| `server_command` | `Array<String>` | `["python3", "mcp/mcp_server.py"]` | — |
| `cwd` | `String?` | `nil` | — |
| `store_path` | `String?` | `nil` | `MEM20_STORE_PATH` |
| `cog_path` | `String?` | `nil` | `MEM20_COG_PATH` |
| `llm_base_url` | `String` | NVIDIA NIM | `MEM20_LLM_BASE_URL` |
| `llm_model` | `String?` | `nil` | `MEM20_LLM_MODEL` |
| `llm_api_key` | `String?` | `nil` | `MEM20_LLM_API_KEY` / `NVAPI_KEY` / `NVIDIA_API_KEY` |
| `health_port` | `Integer` | `8080` | `MEM20_HEALTH_PORT` |
| `health_host` | `String` | `"127.0.0.1"` | — |
| `protocol_version` | `String` | `"2025-06-18"` | — |
| `timeout` | `Float` | `30.0` | — |
| `env` | `Hash` | `{}` | extra child-process vars |

### `.from_env(**options)`

Reads `ENV` for every documented `MEM20_*` variable, then applies `options` on top.

### `.build(**options) { |config| }`

Builds a config, yields it for block-style setup, then returns it frozen.

### `#freeze!`

Freezes the config (and its `server_command` / `env`). Writers raise `FrozenError`
afterwards. `Mem20::Client` always freezes the config it is given.

### `.from_options_and_env(options, env)`

The testable form of the above — takes the environment hash explicitly.

### `#child_env`

The environment the child server process is launched with (base env + the `MEM20_*`
values this config carries).

### `#health_url`

`"http://<health_host>:<health_port>"`.

---

## `Mem20::Transport::Stdio`

JSON-RPC 2.0 over newline-delimited stdio, matching the mem20 server's transport.

| Method | Behaviour |
|---|---|
| `#request(method, params)` | writes `{jsonrpc, id, method, params}`, reads until the matching `id` arrives, returns `result` or raises `ToolError` |
| `#notify(method, params)` | fire-and-forget notification |
| `#initialize_session` | performs the MCP `initialize` handshake once; returns a `Session` struct |
| `#close` | terminates the child process (`TERM`, then reaps) |
| `#pid` | the child process id |

`Session` carries `protocol_version`, `server_info` and `capabilities` from the
handshake. Notifications and unrelated replies are skipped while waiting for a response,
so interleaved server chatter does not desynchronise the client. Every request honours
`config.timeout`, and the child reaps on `close`.

---

## Errors

```
Mem20::Error                 (StandardError)
├── Mem20::ConfigurationError
├── Mem20::ToolError         #code, #data
└── Mem20::TransportError
```

| Class | Raised when |
|---|---|
| `ConfigurationError` | unknown option, or an invalid configuration value |
| `ToolError` | the server returned a JSON-RPC `error`; exposes `#code` and `#data` |
| `TransportError` | process failed to start, pipe closed, a request timed out, or invalid JSON |

---

## Protocol notes

- Transport: **stdio**, one JSON-RPC 2.0 message per line.
- Handshake: `initialize` → `notifications/initialized`, then `tools/list` / `tools/call`.
- Protocol revision: `2025-06-18`.
- `mcp/` in the server is a script directory, not an importable package; the SDK therefore
  launches `mcp/mcp_server.py` with `cwd` set to the checkout rather than importing anything.
- The server also exposes `/health`, `/ready` and `/metrics` on `MEM20_HEALTH_PORT`
  (`8080`); `Client#health`, `#ready`, `#healthy?` and `#metrics` use them.

## Publication routing

Published to the canonical GitHub repo (`main`) only. The former **Sidney** live
surface and the **gabe** publish gate are **retired** and no longer exist.
