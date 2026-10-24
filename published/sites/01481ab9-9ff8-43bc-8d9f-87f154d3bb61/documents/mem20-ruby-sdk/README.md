<p align="center">
  <img src="https://img.shields.io/badge/mem20--sdk--ruby-v0.2.0-cc342d?style=for-the-badge&logo=ruby" alt="mem20-sdk-ruby v0.2.0">
</p>
<p align="center">
  <strong>Ruby SDK for mem20 — a persistent memory + cognition substrate for AI agents.</strong>
</p>
<p align="center">
  <a href="https://github.com/bythewayz66-glitch/mem20/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/bythewayz66-glitch/mem20/tree/main/mem20-sdk-ruby"><img src="https://img.shields.io/badge/repo-canonical%20mem20-6366f1?style=for-the-badge&logo=github" alt="Canonical repo"></a>
  <a href="https://github.com/bythewayz66-glitch/mem20/blob/main/mem20-sdk-ruby/CHANGELOG.md"><img src="https://img.shields.io/badge/protocol-2025--06--18-4f46e5?style=for-the-badge" alt="MCP protocol 2025-06-18"></a>
</p>

---

An idiomatic Ruby (3.1+) client for the **mem20** MCP server. mem20 separates
*grounded* memory (real observations, user statements, events) from *simulated*
memory (hypotheticals, counterfactuals, model output), and exposes its surface as a
JSON-RPC 2.0 service over stdio.

This gem speaks that protocol directly — no Python SDK wrapper, no shelling out — and
gives you a small, thread-safe, frozen-config client you can drop into a Rails app,
a Sidekiq worker, or a plain script.

> **Repo location:** `mem20-sdk-ruby/` in the canonical mem20 monorepo —
> **<https://github.com/bythewayz66-glitch/mem20>** (default branch `main`, MIT).

## Requirements

| Requirement | Version |
|---|---|
| Ruby | >= 3.1 |
| mem20 server | v2.1.0rc2 (Python 3.11+) |
| Runtime deps | none (stdlib only: `json`, `open3`, `net/http`, `timeout`) |

## Install

### From a clone of the canonical repo

```bash
git clone --branch main https://github.com/bythewayz66-glitch/mem20.git
cd mem20/mem20-sdk-ruby
bundle install
bundle exec rake        # runs the RSpec suite
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

Full instructions, including building the mem20 server itself, are in
[`docs/INSTALL.md`](docs/INSTALL.md).

## Quick start

```ruby
require "mem20"

Mem20.configure do |c|
  c.cwd = "/opt/mem20/mem20"   # directory holding mcp/mcp_server.py
  c.timeout = 60.0             # the first embedding-backed call warms a model
end

client = Mem20.client

# Store a grounded fact.
client.memory_store(content: "The release sign-off lives in Sidney.",
                    category: "project",
                    tags: %w[release sidney])

# Search it back.
result = client.memory_recall(query: "where does the release sign-off live", limit: 5)
puts Mem20::Client.text(result)

# Any one of the 268 registered tools, by name…
client.tool("memory_status", {})
# …or as a dynamic binding.
client.memory_status

client.close
```

`examples/quickstart.rb` is this script, runnable as-is:

```bash
ruby -Ilib examples/quickstart.rb
```

## What is in the box

| Component | Purpose |
|---|---|
| `Mem20.configure` / `Mem20.client` | module-level entry points |
| `Mem20::Config` | frozen, validated configuration mapped to the documented `MEM20_*` variables |
| `Mem20::Client` | thread-safe facade: `#tool`, `#tools`, `#memory_store`, `#memory_recall`, `#health`, `#metrics` |
| `Mem20::Transport::Stdio` | JSON-RPC 2.0 over stdio with the MCP handshake, timeouts and mutex-serialised access |
| typed errors | `ConfigurationError`, `ToolError` (`#code`, `#data`), `TransportError` |

## Transport / protocol

- Transport: **stdio**, one JSON-RPC 2.0 message per line.
- Handshake: `initialize` → `notifications/initialized`, then `tools/list` / `tools/call`.
- Protocol revision: **`2025-06-18`**, as negotiated in `initialize`.
- The server registers **268 tools**; the SDK reaches every one through `#tool` or a
  dynamic binding, and ships convenience accessors for the memory primitives.
- The server also exposes `/health`, `/ready` and `/metrics` on `MEM20_HEALTH_PORT`
  (`8080` by default); `Client#health`, `#ready`, `#healthy?` and `#metrics` use them.

## Development

```bash
bundle install
bundle exec rspec        # unit + real child-process transport specs
bundle exec rubocop      # style gate
bundle exec rake build   # gem build mem20-sdk.gemspec
```

## Verification — reproduced results

The results below were produced by running the suite and a live round-trip on the
**Sidney** host (Kali Linux, Ruby 3.3.8) against the mem20 server at **v2.1.0rc2**. They
are this SDK's actual measured results; the raw command output is reproduced in
[`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Check | Result |
|---|---|
| `ruby -c` on every `lib/**/*.rb` | Syntax OK |
| `rspec` | **33 examples, 0 failures** |
| `rubocop` | 19 files inspected, **no offenses detected** |
| `gem build mem20-sdk.gemspec` | mem20-sdk **0.2.0** built |
| `require "mem20"` (installed gem) | loads mem20-sdk 0.2.0 |
| live stdio round-trip | **268 tools**, protocol **2025-06-18**, stored token recalled |

The round-trip stores a distinctive token with `memory_store` and reads it back with
`memory_recall` against the real server; the recorded run recovered the token in
**5.805 ms**.

## Scope and honest limits

This gem is a **client**. It makes no claims about mem20's memory quality, retrieval
accuracy, or cognition benchmarks — it has not measured any, and it reports no such
figures. The numbers above describe this SDK's own build, test and transport behaviour,
not the quality of the memory engine behind it.

## Documentation

| Document | Contents |
|---|---|
| [`docs/INSTALL.md`](docs/INSTALL.md) | server + gem install, configuration, troubleshooting |
| [`docs/USAGE.md`](docs/USAGE.md) | recipes: store/recall, health, errors, threads, Rails/Sidekiq |
| [`docs/API.md`](docs/API.md) | class-by-class API reference |
| [`docs/EVIDENCE.md`](docs/EVIDENCE.md) | what was verified, with the real output |

## License

MIT. See [`LICENSE`](LICENSE).
