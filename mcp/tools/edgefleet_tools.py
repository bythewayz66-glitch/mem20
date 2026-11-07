"""mem20edgefleetbrainz MCP tools — capability-aware fleet control surface.

Exposes the Edge Fleet Brain (RM-041) to MCP hosts. Tools call the real
:class:`mem20edgefleetbrainz.service.FleetService` over a SQLite state plane.

The subsystem import is lazy and guarded: tool registration never imports the
fleet package, and a missing or broken install is reported by the handler
instead of taking down the MCP server.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover
    MCP_SDK_AVAILABLE = False
    mt = None  # type: ignore[assignment]

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_STORE = os.path.expanduser("~/.mem20/edgefleet/fleet.db")


def _fleet_service(store_path: str | None = None):
    """Import and construct the fleet service, preferring the project directory."""
    project = os.path.join(_REPO_ROOT, "mem20edgefleetbrainz")
    if project not in sys.path:
        sys.path.insert(0, project)
    from mem20edgefleetbrainz.service import FleetService  # type: ignore[import-not-found]

    path = store_path or os.environ.get("MEM20_EDGEFLEET_STORE") or _DEFAULT_STORE
    return FleetService(Path(path).expanduser())


def _dumps(value: Any) -> str:
    return json.dumps(value, indent=2, default=str)


class EdgeFleetToolsMixin:
    """Edge Fleet Brain tools for the mem20 MCP server."""

    def register_edgefleet_tools(self):
        if not MCP_SDK_AVAILABLE:
            return
        self.tools["edgefleet_status"] = mt.Tool(
            name="edgefleet_status",
            title="Edge Fleet Status",
            description=(
                "Report Edge Fleet Brain health, capacity, queue, energy and fault "
                "forecast. Read-only. Uses MEM20_EDGEFLEET_STORE or the default store."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "store_path": {"type": "string", "description": "Optional SQLite store path"},
                },
            },
        )
        self.tools["edgefleet_doctor"] = mt.Tool(
            name="edgefleet_doctor",
            title="Edge Fleet Doctor",
            description=(
                "Probe the six fleet-specific peer subsystems (swarm, energy, device "
                "capability, hardware marketplace, roaming scheduler, sleep/wake) and "
                "report which are reachable."
            ),
            inputSchema={
                "type": "object",
                "properties": {"store_path": {"type": "string"}},
            },
        )
        self.tools["edgefleet_simulate"] = mt.Tool(
            name="edgefleet_simulate",
            title="Edge Fleet Simulator",
            description=(
                "Run the fleet's six end-to-end scenarios (success, malformed, "
                "disconnection, overload, provider loss, restart recovery) on a "
                "throwaway store. Does not affect the live store."
            ),
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["edgefleet_nodes_list"] = mt.Tool(
            name="edgefleet_nodes_list",
            title="Edge Fleet Nodes",
            description="List registered fleet nodes with status, capacity and load.",
            inputSchema={
                "type": "object",
                "properties": {"store_path": {"type": "string"}},
            },
        )
        self.tools["edgefleet_node_register"] = mt.Tool(
            name="edgefleet_node_register",
            title="Register Fleet Node",
            description=(
                "Register a heterogeneous node. Returns swarm admission, device fit "
                "and hardware quote from the fleet-specific peer subsystems."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "object",
                        "description": "Node spec (node_id, kind, cpu_cores, memory_gb, gpu_count, capabilities, region, reliability, price_per_hour, auto_capabilities, ...)",
                    },
                    "store_path": {"type": "string"},
                },
                "required": ["node"],
            },
        )
        self.tools["edgefleet_workload_submit"] = mt.Tool(
            name="edgefleet_workload_submit",
            title="Submit Fleet Workload",
            description=(
                "Submit a workload. Validates before storing; idempotency_key replays "
                "the original workload. Returns compatible nodes and a roaming preview."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workload": {
                        "type": "object",
                        "description": "Workload spec (workload_id, cpu, memory_gb, required_capabilities, priority, duration_s, deadline_s, max_price_per_hour, energy_budget_wh, idempotency_key, ...)",
                    },
                    "store_path": {"type": "string"},
                },
                "required": ["workload"],
            },
        )
        self.tools["edgefleet_dispatch"] = mt.Tool(
            name="edgefleet_dispatch",
            title="Dispatch Fleet Workload",
            description=(
                "Place queued work. Returns the placement decision (score, components, "
                "alternatives, bottlenecks, confidence) plus energy, roaming and sleep "
                "peer judgements."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workload_id": {"type": "string"},
                    "limit": {"type": "integer"},
                    "store_path": {"type": "string"},
                },
            },
        )
        self.tools["edgefleet_predict"] = mt.Tool(
            name="edgefleet_predict",
            title="Predict Fleet Faults",
            description="Forecast node fault risk over a horizon with drivers and recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "horizon_s": {"type": "number", "default": 3600},
                    "store_path": {"type": "string"},
                },
            },
        )

    # ------------------------------------------------------------- handlers
    def _edgefleet_error(self, exc: Exception) -> str:
        return _dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}",
                        "subsystem": "mem20edgefleetbrainz"})

    async def _edgefleet_status(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps(_fleet_service(args.get("store_path")).status())
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)

    async def _edgefleet_doctor(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps(_fleet_service(args.get("store_path")).doctor())
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)

    async def _edgefleet_simulate(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps(_fleet_service(args.get("store_path")).simulate())
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)

    async def _edgefleet_nodes_list(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps({"ok": True, "nodes": _fleet_service(args.get("store_path")).list_nodes()})
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)

    async def _edgefleet_node_register(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps(_fleet_service(args.get("store_path")).register_node(args.get("node") or {}))
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)

    async def _edgefleet_workload_submit(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps(_fleet_service(args.get("store_path")).submit_workload(args.get("workload") or {}))
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)

    async def _edgefleet_dispatch(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps(_fleet_service(args.get("store_path")).dispatch(
                args.get("workload_id"), args.get("limit")))
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)

    async def _edgefleet_predict(self, args: Dict[str, Any]) -> str:
        try:
            return _dumps({"ok": True, "forecasts": _fleet_service(args.get("store_path")).predict(
                float(args.get("horizon_s", 3600)))})
        except Exception as exc:  # noqa: BLE001
            return self._edgefleet_error(exc)
