# frozen_string_literal: true

module Mem20
  # The mem20 MCP tool surface this release of the SDK was verified against.
  #
  # These numbers are the only place in the gem where the surface size is
  # stated; the README and `docs/` quote them and `spec/mem20/surface_spec.rb`
  # asserts them against the live tool list. That way a stale count is a red
  # test rather than a documentation bug that ships silently.
  #
  # The count has two halves, and conflating them is what produced three
  # different published values (257 / 268 / 270) in earlier revisions:
  #
  # * {DOMAIN_TOOLS} - tools registered by the 27 mixins under `mcp/tools/`
  #   plus the three mixins that live directly in `mcp/` (`memory_tools`,
  #   `cognitive_tools`, `roadmap_tools`). One module == one domain.
  # * {INFRA_TOOLS}  - `job_status` and `job_wait`, registered by
  #   `Mem20MCPServer#register_job_tools` in `mcp/server.py`. They are
  #   transport plumbing for long-running tools, not a domain.
  #
  # `268 tools across 26 domains` described only the domain half; the live
  # `tools/list` returns every registered tool, so the SDK sees {TOOL_COUNT}.
  module Surface
    # Number of domain mixin modules that register at least one tool.
    DOMAIN_COUNT = 27

    # Tools contributed by those domain modules.
    DOMAIN_TOOLS = 268

    # Tools registered by the server itself, outside any domain module.
    INFRA_TOOLS = ["job_status", "job_wait"].freeze

    # Every tool the server registers: the domain half plus the infra tools.
    TOOL_COUNT = DOMAIN_TOOLS + INFRA_TOOLS.size

    # The infra tools are excluded from {DOMAIN_COUNT} on purpose, so this
    # identity is the invariant the specs pin.
    def self.consistent?
      TOOL_COUNT == 270 && DOMAIN_TOOLS == 268 && DOMAIN_COUNT == 27
    end

    # Human-readable summary used by `rake surface:check` and the README.
    def self.summary
      format("%<total>d tools across %<domains>d domains " \
             "(%<domain>d domain tools + %<infra>d infra tools: %<names>s)",
             total: TOOL_COUNT, domains: DOMAIN_COUNT, domain: DOMAIN_TOOLS,
             infra: INFRA_TOOLS.size, names: INFRA_TOOLS.join(", "))
    end
  end
end
