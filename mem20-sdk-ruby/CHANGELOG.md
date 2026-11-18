# Changelog

All notable changes to the mem20 Ruby SDK are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-11-16

### Changed
- **The surface is now 487 tools across 129 domains**, up from the 311 / 39 this gem
  shipped with. `docs/surface.json` at the repository root is the authority: it is
  generated from a live `tools/list` response by `scripts/surface_manifest.py` and
  cross-checked against the AST catalog in `web/src/data/tools.json` (both 487, both
  129, with an empty symmetric difference). `Mem20::Surface::TOOL_COUNT` and
  `DOMAIN_COUNT` follow the manifest, and `spec/mem20/surface_spec.rb` pins them.
- **The per-domain tool table is now in the gem.** `Mem20::Surface::DOMAIN_TOOL_COUNTS`
  carries the count for each of the 129 domains, and `TOOL_COUNT` / `DOMAIN_COUNT` /
  `DOMAINS` are derived from it rather than typed a second time. The values sum to 487,
  so a domain can neither be double-counted nor dropped; the spec asserts the sum,
  the domain count and the table.
- **`Mem20::SERVER_VERSION` is `4.0.0`.** The gem was quoting `2.1.0rc2`, two majors
  behind. The repository `VERSION` file is `4.0.0`, and the SDK version is now
  independent of it by design (`0.3.0`).
- **The SDK version is `0.3.0`.** `Mem20::VERSION`, the gemspec, the README badge and
  the install examples all move together.

### Added
- `Mem20::Surface.measured_tool_count(tools_list)` / `Mem20::Surface.matches?(tools_list)`:
  count a live `tools/list` response and compare it with the surface this gem ships,
  so a caller can detect a server it was not built against instead of finding out from
  a `ToolError` later. Both accept the `tools/list` result Hash or a bare Array, and
  return `nil` / `false` rather than guessing when handed something else.
- Surface specs for the per-domain table: one entry per domain, values summing to the
  total, every domain non-empty, the document-vs-constant drift guard extended to the
  retired 311 / 39 pair, and coverage of the new measurement helpers.

### Fixed
- **Documentation drift across the whole SDK.** `README.md`, `docs/INSTALL.md`,
  `docs/USAGE.md` and `docs/EVIDENCE.md` still predicted `tool_names.size == 311` and
  quoted a 39-domain surface, and `docs/API.md` documented the pre-0.2.0 `#tool`
  signature. All of them now state 487 / 129 and the real signature, and
  `docs/EVIDENCE.md` § 0 records the 2026-11-16 measurement instead of the stale
  311-tool capture.

## [0.2.0] - 2026-10-14

### Fixed
- **Surface counts and server version aligned with the live value.** The gem quoted
  **272 tools across 27 domains** and server **v2.1.0rc2**. The live surface was
  **311 tools across 39 domains** (`docs/surface.json`, generated from a real
  `tools/list`), and the server release is **4.0.0**. `Mem20::Surface`,
  `Mem20::SERVER_VERSION`, the gemspec, the README and `docs/` now all state the live
  values, and `rake surface:check` compares them with `docs/surface.json`.
- **`Client#tool` rejected the documented call form.** `def tool(name, **params)` cannot
  accept a positional Hash under Ruby 3.x, so `client.tool("memory_status", {})` — the
  spelling used in `README.md`, `docs/USAGE.md` and `docs/API.md` — raised
  `ArgumentError: wrong number of arguments (given 2, expected 1)`. It now takes an
  optional trailing Hash (`tool(name, arguments = nil, **params)`), accepts String or
  Symbol keys, lets explicit keywords win, and raises a clear message for a non-Hash.
- **Stale tool-surface counts.** The gemspec and the `Client` docstring said **257** tools;
  `docs/INSTALL.md` predicted **268** from `tool_names.size`. Both were the domain-only
  subtotal or an older surface, quoted as the total. The live surface is **311**.

### Added
- `Mem20::Surface` (`lib/mem20/surface.rb`): the single source of truth for the surface —
  `TOOL_COUNT` (311), `DOMAIN_COUNT` (39), `DOMAIN_TOOLS` (311), `INFRA_TOOLS`
  (empty: `job_status` / `job_wait` are the `job` domain), plus `.consistent?` and
  `.summary`.
- `rake surface:check`: compares `Mem20::Surface` with the live manifest in
  `docs/surface.json`, so the count can no longer go stale silently.
- `spec/mem20/surface_spec.rb` and `spec/mem20/surface_binding_spec.rb`: pin the counts,
  guard the documented files against re-introducing 257/268, and cover both `#tool`
  argument shapes plus dynamic binding of non-memory tools.

### Added (0.2.0 feature set)
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

[0.3.0]: https://github.com/bythewayz66-glitch/mem20/releases/tag/mem20-sdk-ruby-v0.3.0
[0.2.0]: https://github.com/bythewayz66-glitch/mem20/releases/tag/mem20-sdk-ruby-v0.2.0
[0.1.0]: https://github.com/bythewayz66-glitch/mem20/releases/tag/mem20-sdk-ruby-v0.1.0
