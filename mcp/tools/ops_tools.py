"""mem20ops tools for the mem20 MCP server.

Exposes the operator's console to agents: what the box claims to offer, whether
the fleet's CLIs honour the ``--json`` contract, and whether the ops subsystem's
cross-subsystem edges are live. Every tool runs a real check against the real
tree; none returns a canned answer.

Tools:

* ``ops_registry``   -- the tool registry's counts and generation time
* ``ops_cli_audit``  -- every declared console script, and which are missing
* ``ops_wiring``     -- prove mem20ops's cross-subsystem edges
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from mcp.server import Server
    from mcp.server.lowlevel.server import ServerRequestContext
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
    MCP_SDK_IMPORT_ERROR = None
except ImportError as _mcp_sdk_exc:  # pragma: no cover - only without the SDK
    # Never sys.exit() at import time: pytest imports this module during
    # collection and a SystemExit aborts the whole session instead of
    # reporting one collection error. Full note in mcp/server.py.
    MCP_SDK_AVAILABLE = False
    MCP_SDK_IMPORT_ERROR = _mcp_sdk_exc


def _ops():
    """Import mem20ops from the estate, wherever it lives."""
    try:
        import mem20ops  # noqa: F401
        from mem20ops import integrations, clicheck
        return integrations, clicheck
    except ImportError:
        pass
    root = Path(os.environ.get("MEM20_ROOT", "/opt/mem20"))
    candidate = root / "mem20ops" / "src"
    if (candidate / "mem20ops" / "__init__.py").is_file():
        sys.path.insert(0, str(candidate))
    from mem20ops import integrations, clicheck
    return integrations, clicheck


class OpsToolsMixin:
    """Operator console tools for mem20."""

    def register_ops_tools(self):
        """Register the mem20ops tools."""
        if not MCP_SDK_AVAILABLE:  # pragma: no cover
            return
        self.tools["ops_registry"] = mt.Tool(
            name="ops_registry",
            title="Ops Registry",
            description=(
                "Report the tool registry's real counts and generation time, so an "
                "operator can tell whether the tool list they are reading is current."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "estate root override"},
                },
                "required": [],
            },
        )
        self.tools["ops_cli_audit"] = mt.Tool(
            name="ops_cli_audit",
            title="Ops CLI Audit",
            description=(
                "List every console script declared by a mem20* pyproject, with the "
                "package that declares it and whether the entry point resolves. A "
                "declared-but-missing script is reported as a finding."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "estate root override"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": [],
            },
        )
        self.tools["ops_wiring"] = mt.Tool(
            name="ops_wiring",
            title="Ops Wiring",
            description=(
                "Prove mem20ops's cross-subsystem edges by calling each one: "
                "toolchest catalog, memory_engine pin_block, mem20kanbanz sha256, "
                "mem20corez CharMLP, mem20cliz build_envelope, mem20verify "
                "discover_packages. Returns per-edge ok/result."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "estate root override"},
                },
                "required": [],
            },
        )

    async def _ops_registry(self, arguments: Dict[str, Any]) -> str:
        integrations, _c = _ops()
        root = arguments.get("root")
        summary = integrations.registry_summary(Path(root) if root else None)
        return json.dumps({"ok": True, **summary}, indent=2, default=str)

    async def _ops_cli_audit(self, arguments: Dict[str, Any]) -> str:
        integrations, clicheck = _ops()
        root = Path(arguments.get("root")
                    or os.environ.get("MEM20_ROOT", "/opt/mem20"))
        limit = int(arguments.get("limit") or 50)
        # mem20ops owns the scanner, so call it directly rather than through
        # the wiring module (which deliberately does not re-export it).
        previous = getattr(clicheck, "REPO", None)
        clicheck.REPO = str(root)
        try:
            rows = clicheck.declared_scripts()
        finally:
            if previous is not None:
                clicheck.REPO = previous
        # "Resolves" means the script is physically present in the estate venv,
        # which is the only honest answer to "can an operator run this".
        installed = clicheck.installed_binaries()
        for row in rows:
            row["resolves"] = row["name"] in installed
        missing = [r for r in rows if not r["resolves"]]
        return json.dumps({
            "ok": not missing,
            "declared": len(rows),
            "installed": len(rows) - len(missing),
            "missing": len(missing),
            "returned": min(limit, len(rows)),
            "scripts": rows[:limit],
        }, indent=2, default=str)

    async def _ops_wiring(self, arguments: Dict[str, Any]) -> str:
        integrations, _c = _ops()
        root = arguments.get("root")
        return json.dumps(integrations.wiring_report(Path(root) if root else None),
                          indent=2, default=str)

# Re-exports for MCP server wiring (mcp/server.py imports these from tools.ops_tools).
# Each mixin is defined in its own mem20* tools module; re-exported here to keep
# the server's consolidated ops import working without removing or disabling any mixin.
from tools.mem20datalocalityoptimizerz_tools import DataLocalityOptimizerToolsMixin
from tools.mem20deterministicconfigurationgraphz_tools import DeterministicConfigurationGraphToolsMixin
from tools.mem20devicecapabilitycompilerz_tools import DeviceCapabilityCompilerToolsMixin
from tools.mem20dynamicnarrativeenginez_tools import DynamicNarrativeEngineToolsMixin
from tools.mem20dynamicquestrewardcomposerz_tools import DynamicQuestRewardComposerToolsMixin
from tools.mem20dynamicskillgraphz_tools import DynamicSkillGraphToolsMixin
from tools.mem20twinz_tools import PlayerMotivationTwinToolsMixin
from tools.mem20predictiverecallenginez_tools import PredictiveRecallEngineToolsMixin
from tools.mem20pipez_tools import ProductionPlanningAndTaskOrchestrationPipelineToolsMixin
from tools.mem20simz_tools import ProductLedGrowthSimulatorToolsMixin
from tools.mem20protocolautodiscoveryenginez_tools import ProtocolAutoDiscoveryEngineToolsMixin
from tools.mem20realitytosoftwarecompilerz_tools import RealityToSoftwareCompilerToolsMixin
from tools.mem20twinz_tools import RealTimeBusinessTwinToolsMixin
from tools.mem20realtimeeventautopilotz_tools import RealTimeEventAutopilotToolsMixin
from tools.mem20realtimeteampresencez_tools import RealTimeTeamPresenceToolsMixin
from tools.mem20realworldimpactrewardsz_tools import RealWorldImpactRewardsToolsMixin
from tools.mem20labz_tools import RemoteExperimentLabToolsMixin
from tools.mem20resourceexchangemarketz_tools import ResourceExchangeMarketToolsMixin
from tools.mem20revenueleakhunterz_tools import RevenueLeakHunterToolsMixin
from tools.mem20rewardforgez_tools import RewardForgeToolsMixin
from tools.mem20pipez_tools import RiggingAnimationAndMotionPipelineToolsMixin
from tools.mem20roamingworkloadschedulerz_tools import RoamingWorkloadSchedulerToolsMixin
from tools.mem20runtimecompatibilityenginez_tools import RuntimeCompatibilityEngineToolsMixin
from tools.mem20runtimepromptoptimizerz_tools import RuntimePromptOptimizerToolsMixin
from tools.mem20secretslessworkloadidentityz_tools import SecretslessWorkloadIdentityToolsMixin
from tools.mem20securecomputecapsulesz_tools import SecureComputeCapsulesToolsMixin
from tools.mem20selfhealingplansz_tools import SelfHealingPlansToolsMixin
from tools.mem20selfoptimizingkernelz_tools import SelfOptimizingKernelToolsMixin
from tools.mem20selftuningresourcegovernorz_tools import SelfTuningResourceGovernorToolsMixin
from tools.mem20selfz_tools import SelfzToolsMixin
from tools.mem20sensorymemoryingestz_tools import SensoryMemoryIngestToolsMixin
from tools.mem20servicebundlingenginez_tools import ServiceBundlingEngineToolsMixin
from tools.mem20simz_tools import SimzToolsMixin
from tools.mem20causalroutingbrainz_tools import SkillBasedProgressionBrainToolsMixin
from tools.mem20skillmemorytransferz_tools import SkillMemoryTransferToolsMixin
from tools.mem20spatialcommanduniversez_tools import SpatialCommandUniverseToolsMixin
from tools.mem20specialistmodelforgez_tools import SpecialistModelForgeToolsMixin
from tools.mem20speculativeworkflowenginez_tools import SpeculativeWorkflowEngineToolsMixin
from tools.mem20studioz_tools import StudiozToolsMixin
from tools.mem20styleguideagentz_tools import StyleGuideAgentToolsMixin
from tools.mem20syntheticevaluatorarenaz_tools import SyntheticEvaluatorArenaToolsMixin
from tools.mem20twinz_tools import TwinzToolsMixin
from tools.mem20uniteconomicsautopilotz_tools import UnitEconomicsAutopilotToolsMixin
from tools.mem20universalhealthnervoussystemz_tools import UniversalHealthNervousSystemToolsMixin
from tools.mem20universalintegrationcompilerz_tools import UniversalIntegrationCompilerToolsMixin
from tools.mem20visualagentblackboardz_tools import VisualAgentBlackboardToolsMixin
from tools.mem20visualdataflowcomposerz_tools import VisualDataflowComposerToolsMixin
from tools.mem20zerotouchnodeswarmz_tools import ZeroTouchNodeSwarmToolsMixin
from tools.mem20offerassemblyfabricz_tools import OfferAssemblyFabricToolsMixin
from tools.mem20offergenomeenginez_tools import OfferGenomeEngineToolsMixin
from tools.mem20opportunityradarz_tools import OpportunityRadarToolsMixin
from tools.mem20simz_tools import OutcomeSimulationLabToolsMixin
from tools.mem20personalautomationcanvasz_tools import PersonalAutomationCanvasToolsMixin
from tools.mem20personalcognitivesearchz_tools import PersonalCognitiveSearchToolsMixin
from tools.mem20personalmodelevolutionz_tools import PersonalModelEvolutionToolsMixin
from tools.mem20twinz_tools import PersonalWorkflowTwinToolsMixin
from tools.mem20pipez_tools import PipelinezToolsMixin
from tools.mem20planetarybatchfabricz_tools import PlanetaryBatchFabricToolsMixin
