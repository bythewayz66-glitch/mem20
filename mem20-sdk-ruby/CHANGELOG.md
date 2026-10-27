# Changelog

All notable changes to the mem20 Ruby SDK are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **`Client#tool` rejected the documented call form.** `def tool(name, **params)` cannot
  accept a positional Hash under Ruby 3.x, so `client.tool("memory_status", {})` — the
  spelling used in `README.md`, `docs/USAGE.md` and `docs/API.md` — raised
  `ArgumentError: wrong number of arguments (given 2, expected 1)`. It now takes an
  optional trailing Hash (`tool(name, arguments = nil, **params)`), accepts String or
  Symbol keys, lets explicit keywords win, and raises a clear message for a non-Hash.
- **Stale tool-surface counts.** The gemspec and the `Client` docstring said **257** tools;
  `docs/INSTALL.md` predicted **268** from `tool_names.size`. The live surface is **270**.
  `268` was the domain-only subtotal and was being quoted as the total.

### Added
- `Mem20::Surface` (`lib/mem20/surface.rb`): the single source of truth for the surface —
  `TOOL_COUNT` (270), `DOMAIN_COUNT` (27), `DOMAIN_TOOLS` (268), `INFRA_TOOLS`
  (`job_status`, `job_wait`), plus `.consistent?` and `.summary`.
- `rake surface:check`: recounts registrations from `mcp/` and fails on drift from
  `Mem20::Surface`, so the count can no longer go stale silently.
- `spec/mem20/surface_spec.rb` and `spec/mem20/surface_binding_spec.rb`: pin the counts,
  guard the documented files against re-introducing 257/268, and cover both `#tool`
  argument shapes plus dynamic binding of non-memory tools.

## [0.2.0] - 2026-10-14

### Added
- `Mem20::PROTOCOL_VERSION` (`"2025-06-18"`) and `Mem20::SERVER_VERSION`
  (`"2.1.0rc2"`) constants; the handshake now sends the negotiated revision and
  `Transport::Stdio#initialize_session` returns a `Session` struct carrying the
  `protocol_version`, `server_info` and `capabilities` from the handshake.
- Memory primitives on the client: `#memory_store` (accepts `tags:` as an Array or a
  pre-formatted String) and `#memory_recall`, plus `Model::Client.text` for pulling the
  plain-text payload out of a result envelope.
- Dynamic tool bindings via `#method_missing` / `#respond_to_missing?`, so any of the
  270 registered tools can be called as a method with keyword arguments.
- `#tool_names` (cached), `#health`, `#ready` alongside the existing `#healthy?` and
  `#metrics`.
- `Config#protocol_version`, and validation for empty `server_command`, non-positive
  `timeout` and out-of-range `health_port`.
- `spec/support/mini_mcp_server.rb`: a minimal stdio JSON-RPC server, so the transport
  specs spawn a **real** child process and exercise the framing, handshake, error path,
  notification-skipping and process reaping end to end.
- `examples/` and `docs/EVIDENCE.md`.
- CI at the **repository root** — `.github/workflows/ruby-sdk.yml` (Ruby 3.1/3.2/3.3:
  syntax, RSpec, RuboCop, `gem build`) and `.github/workflows/release.yml` (tag-driven
  RubyGems publish, guarded by a tag ↔ `Mem20::VERSION` check). The earlier nested
  `mem20-sdk-ruby/.github/workflows/ruby.yml` was removed: GitHub Actions only reads
  `.github/workflows/` at the repository root, so a workflow under the gem directory
  never ran.

### Changed
- Repository identity repointed to the canonical monorepo owner (`bythewayz66`); gem
  metadata (`source_code_uri`, `changelog_uri`, `documentation_uri`) all resolve under
  <https://github.com/bythewayz66-glitch/mem20>.
- `required_ruby_version` raised to `>= 3.1`.

## [0.1.0] - 2026-10-14

### Added
- `Mem20::Client` — thread-safe facade over the mem20 tool surface with `#tool`,
  `#tools`, `#healthy?`, `#metrics`, `#close`.
- `Mem20::Config` — frozen, validated configuration mapping the documented `MEM20_*`
  environment variables.
- `Mem20::Transport::Stdio` — JSON-RPC 2.0 over newline-delimited stdio with the MCP
  `initialize` handshake, request timeouts, and mutex-serialised access.
- Module-level `Mem20.configure` / `Mem20.client` / `Mem20.configuration` entry points.
- Typed errors: `Mem20::ConfigurationError`, `Mem20::ToolError` (`#code`, `#data`),
  `Mem20::TransportError`.
- RSpec suite and RuboCop configuration; Rakefile with `spec`, `rubocop` and default tasks.
- Docs: `README.md`, `docs/INSTALL.md`, `docs/USAGE.md`, `docs/API.md`.

[0.2.0]: https://github.com/bythewayz66-glitch/mem20/releases/tag/mem20-sdk-ruby-v0.2.0
[0.1.0]: https://github.com/bythewayz66-glitch/mem20/releases/tag/mem20-sdk-ruby-v0.1.0
