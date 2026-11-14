"""mem20edgetransportfabricz (RM-077): Edge Transport Fabric."""
import importlib

from .domain import (
    FabricLink, FabricNode, FlowDemand, FlowState, LinkStatus, PathDecision, QosTier,
    admit_flow, allocate_bandwidth, classify_qos, fabric_health, qos_class, release_path,
    reserve_path, reroute_plan, route_path, shortest_path, sla_report, topology_from_legacy,
    transport_health,
)

__all__ = [
    "FabricLink", "FabricNode", "FlowDemand", "FlowState", "LinkStatus", "PathDecision", "QosTier",
    "TransportFabricService", "ValidationError",
    "admit_flow", "allocate_bandwidth", "classify_qos", "fabric_health", "qos_class", "release_path",
    "reserve_path", "reroute_plan", "route_path", "shortest_path", "sla_report", "topology_from_legacy",
    "transport_health",
    "ecosystem",
]


def __getattr__(name):
    if name in ("TransportFabricService", "ValidationError"):
        mod = importlib.import_module(".service", __name__)
        return getattr(mod, name)
    if name == "ecosystem":
        return importlib.import_module(".ecosystem", __name__)
    raise AttributeError(name)
