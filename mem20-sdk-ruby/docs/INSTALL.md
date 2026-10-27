# Installing the mem20 Ruby SDK

> Covers both halves: the **mem20 server** the SDK talks to, and the **gem** itself.
>
> Canonical repository: <https://github.com/bythewayz66-glitch/mem20> (`main`).
> SDK path: `mem20-sdk-ruby/`.

## 1. Prerequisites

| Component | Version | Why |
|---|---|---|
| Ruby | 3.1+ | the gem targets 3.1 and later |
| Bundler | 2.4+ | for the `github:` install path |
| Python | 3.11+ | runs the mem20 MCP server |
| LLM endpoint | OpenAI-compatible | mem20's `cog/` layer needs one (default: NVIDIA NIM) |
| Disk | ~500 MB | memory store + embeddings model |

No runtime gem dependencies: the SDK uses only the Ruby standard library
(`json`, `open3`, `net/http`, `timeout`).

## 2. Install the mem20 server

Clone the canonical repo. The SDK launches the server for you, but the server must
exist on disk first.

```bash
git clone --branch main https://github.com/bythewayz66-glitch/mem20.git /opt/mem20
cd /opt/mem20/mem20

# sanity check: the stdio server starts and answers initialize
/usr/bin/python3.14 mcp/mcp_server.py
```

For an always-on install with the `:8080` health endpoint:

```bash
sudo ./install.sh --user "$USER" --dir /opt/mem20
curl http://localhost:8080/health
```

See [`docs/03-installation.md`](../../docs/03-installation.md) in the monorepo for the
systemd / Docker channels in full.

## 3. Install the gem

### From a clone of the canonical repo (development)

```bash
git clone --branch main https://github.com/bythewayz66-glitch/mem20.git
cd mem20/mem20-sdk-ruby
bundle install
bundle exec rake          # RSpec suite
bundle exec rubocop       # style gate
gem build mem20-sdk.gemspec
```

### From the canonical repo through Bundler

```ruby
# Gemfile
source "https://rubygems.org"
gem "mem20-sdk", github: "bythewayz66-glitch/mem20", branch: "main", glob: "mem20-sdk-ruby/*.gemspec"
```

```bash
bundle install
```

### From a locally built gem

```bash
gem build mem20-sdk.gemspec
gem install ./mem20-sdk-0.2.0.gem
```

## 4. Configure

`Mem20::Config` mirrors the server's documented environment variables, so the same
`.env` works for both halves.

| Config attribute | Environment variable | Default |
|---|---|---|
| `store_path` | `MEM20_STORE_PATH` | `~/.mem20/store` (server side) |
| `cog_path` | `MEM20_COG_PATH` | mem20 `cog/` directory |
| `llm_base_url` | `MEM20_LLM_BASE_URL` | `https://integrate.api.nvidia.com/v1` |
| `llm_model` | `MEM20_LLM_MODEL` | project default |
| `llm_api_key` | `MEM20_LLM_API_KEY` / `NVAPI_KEY` / `NVIDIA_API_KEY` | — |
| `health_port` | `MEM20_HEALTH_PORT` | `8080` |
| `protocol_version` | — | `2025-06-18` |
| `server_command` | — | `["python3", "mcp/mcp_server.py"]` |
| `cwd` | — | `nil` (set it to the mem20 checkout) |
| `timeout` | — | `30.0` seconds |

Set them in the process environment:

```bash
export MEM20_STORE_PATH=/opt/mem20/store
export MEM20_LLM_BASE_URL=https://integrate.api.nvidia.com/v1
export NVAPI_KEY=nvapi-...
```

...or in Ruby:

```ruby
require "mem20"

Mem20.configure do |config|
  config.cwd = "/opt/mem20/mem20"       # directory holding mcp/mcp_server.py
  config.store_path = "/opt/mem20/store"
  config.llm_base_url = "http://localhost:11434/v1"  # local Ollama
  config.llm_api_key = "not-needed"
  config.llm_model = "llama3"
  config.timeout = 60.0
end
```

`configure` reads the environment first, then applies your overrides, and returns a
**frozen** config — mutating it afterwards raises.

## 5. Verify the connection

```ruby
require "mem20"

Mem20.configure { |c| c.cwd = "/opt/mem20/mem20" }
client = Mem20.client

puts client.transport.initialize_session.protocol_version  # "2025-06-18"
puts client.tool_names.size                                 # 270
puts client.tools.dig("tools").size                        # 270
puts Mem20::Surface.summary                                 # 270 tools across 27 domains
puts client.healthy?                                       # true when :8080/health answers 200

client.close
```

The live surface is **270 tools across 27 domains**: 268 tools registered by the 27
domain mixins (`mcp/tools/*.py` plus `mcp/memory_tools.py`, `cognitive_tools.py` and
`roadmap_tools.py`), plus the 2 job tools `job_status` / `job_wait` that
`mcp/server.py` registers itself. `Mem20::Surface` encodes that decomposition and
`rake surface:check` re-derives it from the Python sources.

Or from the shell:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/metrics
curl http://localhost:8080/ready
```

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Mem20::TransportError: failed to start mem20 server` | wrong `cwd`, or Python missing | point `cwd` at the mem20 checkout; confirm `python3 --version` is 3.11+ |
| `Mem20::TransportError: timed out waiting for response` | the first embedding-backed call loads a model | raise `config.timeout` to `60.0` |
| `Mem20::ToolError` with `code: -32602` | tool name/argument mismatch | `client.tools` lists the live schema |
| `client.healthy?` false but tools work | health endpoint disabled | keep using stdio, or enable the health endpoint |

## Publication routing

Docs and builds are published to the canonical GitHub repo (`main`) and to the
**Sidney** live surface, through **gabe** — the sole publish authority. Nothing
writes to the live surface by any other path.
