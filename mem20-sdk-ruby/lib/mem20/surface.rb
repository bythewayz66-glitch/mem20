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
  # Both land on 487 tools across 129 domains.
  #
  # Earlier revisions published five different values (257 / 268 / 270 / 311 /
  # 487) for the same surface because the domain half and the total were
  # conflated, and because a static `grep` of `self.tools["..."] =` is not a
  # measure of the live table at all: a name can be assigned twice, and several
  # modules define a `register_*_tools` function that `_setup_tools()` never
  # calls. Only a live `tools/list` counts.
  #
  # `job_status` / `job_wait` used to be counted as transport "infra" outside
  # any domain. In the current taxonomy `job` is a domain of its own, so every
  # tool belongs to exactly one of the 129 domains and {INFRA_TOOLS} is
  # empty. The per-domain table below is what makes that checkable: the values
  # sum to {TOOL_COUNT}, and the spec pins that sum.
  module Surface
    # Tools per domain, exactly as `docs/surface.json` records them. The single
    # source of truth in this file -- every other constant is derived from it,
    # so a domain cannot be counted twice or forgotten.
    DOMAIN_TOOL_COUNTS = {
      "a2a" => 5,
      "agentz" => 4,
      "blender" => 7,
      "braid" => 9,
      "cloudservice" => 10,
      "cloudstorage" => 8,
      "cognitive" => 19,
      "communication" => 9,
      "corez" => 4,
      "crewz" => 4,
      "database" => 10,
      "design" => 8,
      "dev" => 9,
      "dreamz" => 4,
      "edgefleet" => 8,
      "filesystem" => 10,
      "finance" => 8,
      "integration" => 3,
      "irc" => 5,
      "job" => 2,
      "kilnz" => 4,
      "lie" => 10,
      "marketing" => 9,
      "mem20alternativedatabaseplaygroundz" => 1,
      "mem20ambientdevicecompanionz" => 1,
      "mem20ambientteamradioz" => 1,
      "mem20architecturesimulationsandboxz" => 1,
      "mem20assetremixstudioz" => 1,
      "mem20asynccollaborationcapsulesz" => 1,
      "mem20audiovoiceandmusicpipelinez" => 4,
      "mem20autonomousdealdeskz" => 3,
      "mem20autonomousmicrosaasfoundryz" => 2,
      "mem20autonomousrecoverydirectorz" => 2,
      "mem20autonomoussaleslaboratoryz" => 2,
      "mem20autonomoussoftwarefoundryz" => 2,
      "mem20autonomoustrafficcontrollerz" => 1,
      "mem20autonomousworkcellsz" => 2,
      "mem20batteryawareagentschedulerz" => 1,
      "mem20businessmodelsimulatorz" => 2,
      "mem20causalroutingbrainz" => 2,
      "mem20collectivemodelintelligencez" => 2,
      "mem20communitychallengeenginez" => 2,
      "mem20compoundingproductecosystemz" => 2,
      "mem20contextcompressionforgez" => 2,
      "mem20counterfactualmemorysimulatorz" => 2,
      "mem20crdtcollaborationenginez" => 1,
      "mem20crossplatformmicrokernelz" => 2,
      "mem20crossproductloyaltygraphz" => 2,
      "mem20customerdigitaltwinlabz" => 2,
      "mem20customerlifecycleenginez" => 2,
      "mem20datalocalityoptimizerz" => 2,
      "mem20deterministicconfigurationgraphz" => 2,
      "mem20devicecapabilitycompilerz" => 2,
      "mem20dynamicnarrativeenginez" => 2,
      "mem20dynamicphasereplannerz" => 1,
      "mem20dynamicquestrewardcomposerz" => 2,
      "mem20dynamicskillgraphz" => 2,
      "mem20milestoneriskpredictorz" => 1,
      "mem20offerassemblyfabricz" => 2,
      "mem20offergenomeenginez" => 2,
      "mem20opportunityradarz" => 2,
      "mem20outcomesimulationlabz" => 2,
      "mem20personalautomationcanvasz" => 2,
      "mem20personalcognitivesearchz" => 2,
      "mem20personalmodelevolutionz" => 2,
      "mem20personalworkflowtwinz" => 2,
      "mem20pipelinez" => 2,
      "mem20planetarybatchfabricz" => 2,
      "mem20playermotivationtwinz" => 2,
      "mem20predictiverecallenginez" => 2,
      "mem20prioritycollisionresolverz" => 1,
      "mem20productionplanningandtaskorchestrationpipelinez" => 2,
      "mem20productledgrowthsimulatorz" => 2,
      "mem20protocolautodiscoveryenginez" => 2,
      "mem20realitytosoftwarecompilerz" => 2,
      "mem20realtimebusinesstwinz" => 2,
      "mem20realtimeeventautopilotz" => 2,
      "mem20realtimeteampresencez" => 2,
      "mem20realworldimpactrewardsz" => 2,
      "mem20remoteexperimentlabz" => 2,
      "mem20resourceexchangemarketz" => 2,
      "mem20revenueleakhunterz" => 2,
      "mem20rewardforgez" => 2,
      "mem20rigginganimationandmotionpipelinez" => 2,
      "mem20roamingworkloadschedulerz" => 2,
      "mem20runtimecompatibilityenginez" => 2,
      "mem20runtimepromptoptimizerz" => 2,
      "mem20secretslessworkloadidentityz" => 2,
      "mem20securecomputecapsulesz" => 2,
      "mem20selfhealingplansz" => 2,
      "mem20selfoptimizingkernelz" => 2,
      "mem20selftuningresourcegovernorz" => 2,
      "mem20selfz" => 2,
      "mem20sensorymemoryingestz" => 2,
      "mem20servicebundlingenginez" => 2,
      "mem20simz" => 2,
      "mem20skillbasedprogressionbrainz" => 2,
      "mem20skillmemorytransferz" => 2,
      "mem20spatialcommanduniversez" => 2,
      "mem20specialistmodelforgez" => 2,
      "mem20speculativeworkflowenginez" => 2,
      "mem20studioz" => 2,
      "mem20styleguideagentz" => 2,
      "mem20syntheticevaluatorarenaz" => 2,
      "mem20twinz" => 2,
      "mem20uniteconomicsautopilotz" => 2,
      "mem20universalhealthnervoussystemz" => 2,
      "mem20universalintegrationcompilerz" => 2,
      "mem20visualagentblackboardz" => 2,
      "mem20visualdataflowcomposerz" => 2,
      "mem20zerodowntimemigrationbrainz" => 1,
      "mem20zerotouchnodeswarmz" => 2,
      "memory" => 55,
      "ops" => 3,
      "procedural" => 6,
      "productivity" => 10,
      "rm052" => 1,
      "rm239" => 1,
      "roadmap" => 4,
      "search" => 7,
      "temporal" => 5,
      "thought_process" => 9,
      "toolchest" => 2,
      "unity" => 5,
      "verify" => 4,
      "versioncontrol" => 11,
      "webhook" => 5,
      "webscraping" => 8,
      "world" => 14
    }.freeze

    # Every tool the server registers: the sum of the per-domain counts.
    TOOL_COUNT = DOMAIN_TOOL_COUNTS.values.sum

    # Every domain the server registers at least one tool in.
    DOMAIN_COUNT = DOMAIN_TOOL_COUNTS.size

    # The domains, derived from the table rather than listed a second time.
    DOMAINS = DOMAIN_TOOL_COUNTS.keys.freeze

    # No tool is registered outside a domain any more: `job_status` and
    # `job_wait` are the `job` domain. Kept as an explicit empty list so the
    # "domain tools + infra tools == total" identity stays expressible.
    INFRA_TOOLS = [].freeze

    # The domain half of the surface. Equal to {TOOL_COUNT} for the same
    # reason {INFRA_TOOLS} is empty; retained because the docs and the
    # earlier revisions referred to the subtotal by this name.
    DOMAIN_TOOLS = TOOL_COUNT - INFRA_TOOLS.size

    # The invariants this release pins. `spec/mem20/surface_spec.rb` calls this
    # and also asserts the individual values, so a partial edit fails a test.
    def self.consistent?
      TOOL_COUNT == 487 &&
        DOMAIN_COUNT == 129 &&
        DOMAIN_TOOLS == TOOL_COUNT &&
        INFRA_TOOLS.empty? &&
        DOMAINS.length == DOMAIN_COUNT &&
        DOMAIN_TOOL_COUNTS.values.all?(&:positive?)
    end

    # The tool count a live `tools/list` response reports, or nil when the
    # response is not a tool list.
    def self.measured_tool_count(tools_list)
      tools = tools_list.is_a?(Hash) ? tools_list["tools"] : tools_list
      return nil unless tools.is_a?(Array)

      tools.length
    end

    # True when a live `tools/list` response matches {TOOL_COUNT}.
    def self.matches?(tools_list)
      measured_tool_count(tools_list) == TOOL_COUNT
    end

    # Human-readable summary used by `rake surface:check` and the README.
    def self.summary
      format("%<total>d tools across %<domains>d domains",
             total: TOOL_COUNT, domains: DOMAIN_COUNT)
    end
  end
end
