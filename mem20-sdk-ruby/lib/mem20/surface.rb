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
  #
  # 270 -> 272 (2026-11-01): two merged subsystems each register one more tool
  # by monkeypatching `VersionControlToolsMixin#register_versioncontrol_tools`
  # instead of adding a module, so {DOMAIN_COUNT} stays 27 while
  # {DOMAIN_TOOLS} grows by two:
  #
  #   + vcs_asset_release_audit        (RM-239, mcp/tools/rm239_tools.py)
  #   + graph_execute_reversible_plan  (RM-052, mcp/tools/rm052_tools.py)
  #
  # Verified against a live `tools/list` on main @ d99ab5d8, not by grepping
  # the sources: a static scan double-counts those two, because each name is
  # assigned both in the installer and in the patched method.
  module Surface
    # Number of domain mixin modules that register at least one tool.
    DOMAIN_COUNT = 27

    # Tools contributed by those domain modules.
    DOMAIN_TOOLS = 270

    # Tools registered by the server itself, outside any domain module.
    INFRA_TOOLS = ["job_status", "job_wait"].freeze

    # Every tool the server registers: the domain half plus the infra tools.
    TOOL_COUNT = DOMAIN_TOOLS + INFRA_TOOLS.size

    # The infra tools are excluded from {DOMAIN_COUNT} on purpose, so this
    # identity is the invariant the specs pin.
    def self.consistent?
      TOOL_COUNT == 272 && DOMAIN_TOOLS == 270 && DOMAIN_COUNT == 27
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
