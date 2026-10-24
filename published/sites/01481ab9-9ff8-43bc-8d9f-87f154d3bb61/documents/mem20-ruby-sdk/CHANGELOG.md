# Changelog

All notable changes to the mem20 Ruby SDK are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  268 registered tools can be called as a method with keyword arguments.
- `#tool_names` (cached), `#health`, `#ready` alongside the existing `#healthy?` and
  `#metrics`.
- `Config#protocol_version`, and validation for empty `server_command`, non-positive
  `timeout` and out-of-range `health_port`.
- `spec/support/mini_mcp_server.rb`: a minimal stdio JSON-RPC server, so the transport
  specs spawn a **real** child process and exercise the framing, handshake, error path,
  notification-skipping and process reaping end to end.
- `examples/`, `docs/EVIDENCE.md` and a GitHub Actions workflow (`ruby.yml`, Ruby
  3.1/3.2/3.3).

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
