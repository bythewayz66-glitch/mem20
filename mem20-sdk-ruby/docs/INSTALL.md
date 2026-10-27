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