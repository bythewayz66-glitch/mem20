# frozen_string_literal: true

module Mem20
  # The mem20 MCP tool surface this release of the SDK was verified against.
  #
  # These numbers are the only place in the gem where the surface size is
  # stated; the README and `docs/` quote them and `spec/mem20/surface_spec.rb`
  # asserts them against the live tool list. That way a stale count is a red
  # test rather than a documentation bug that ships silently.
  #
  # The figure is read from `docs/surface.json`, which
  # `scripts/surface_manifest.py` generates from a live `tools/list` response
  # and cross-checks against the AST catalog in `web/src/data/tools.json` --
  # the two collections must be identical or the generator refuses to emit.
  # Both land on 311 tools across 39 domains.
  #
  # Earlier revisions published three different values (257 / 268 / 270) for
  # the same surface because the domain half and the total were conflated.
  # `job_status` / `job_wait` used to be counted as transport "infra" outside
  # any domain; in the current taxonomy `job` is a domain of its own, so every
  # tool belongs to exactly one of the 39 domains and there is no separate
  # infra layer.
  module Surface
    # Distinct owning domain modules the server registers.
    DOMAIN_COUNT = 39

    # Tools contributed by those domain modules. Every tool belongs to a
    # domain, so this is the whole surface.
    DOMAIN_TOOLS = 311

    # Tools registered outside any domain module. Empty in the current
    # taxonomy: `job_status` / `job_wait` are the `job` domain.
    INFRA_TOOLS = [].freeze

    # Every tool the server registers: the domain half plus the infra tools.
    TOOL_COUNT = DOMAIN_TOOLS + INFRA_TOOLS.size

    # The identity the specs pin.
    def self.consistent?
      TOOL_COUNT == 311 && DOMAIN_TOOLS == 311 && DOMAIN_COUNT == 39
    end

    # Human-readable summary used by `rake surface:check` and the README.
    def self.summary
      format("%<total>d tools across %<domains>d domains",
             total: TOOL_COUNT, domains: DOMAIN_COUNT)
    end
  end
end
