"""Compatibility module: re-exports mixins whose real homes are elsewhere."""
# --- compatibility re-exports ---
# The 2026-11-09 consolidation wave moved these classes into their own
# per-subsystem modules. mcp/server.py still imports them from here, so
# they are re-exported at module level to keep the server importable
# without dropping any mixin from Mem20MCPServer's bases.
from tools.mem20pipelinez_tools import PipelinezToolsMixin
from tools.mem20rigginganimationandmotionpipelinez_tools import RiggingAnimationAndMotionPipelineToolsMixin
from tools.mem20productionplanningandtaskorchestrationpipelinez_tools import ProductionPlanningAndTaskOrchestrationPipelineToolsMixin
from tools.mem20audiovoiceandmusicpipelinez_tools import AudioVoiceMusicPipelineToolsMixin
