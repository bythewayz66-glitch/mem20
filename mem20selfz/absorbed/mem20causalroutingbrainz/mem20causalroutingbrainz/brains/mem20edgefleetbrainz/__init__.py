"""Edge Fleet Brain (RM-041).

Coordinate heterogeneous computers, phones, servers and appliances as one
capability-aware fleet.

The public surface is intentionally small:

* :class:`mem20causalroutingbrainz.service.FleetService` — the stateful scheduler.
* :mod:`mem20causalroutingbrainz.domain` — pure models, scoring, energy and faults.
* :mod:`mem20causalroutingbrainz.store` — the SQLite state plane.
* :mod:`mem20causalroutingbrainz.ecosystem` — the six peer judgements.
* :func:`main`, :func:`make_server`, :func:`serve` — CLI and HTTP.
"""

from .domain import (
    DeviceKind,
    FaultForecast,
    Node,
    NodeStatus,
    PlacementDecision,
    PlacementScore,
    Workload,
    WorkloadState,
)
from .runtime import main, make_server, serve
from .service import FleetService, ValidationError
from .store import ConflictError, FleetStore, NotFoundError

__all__ = [
    "ConflictError",
    "DeviceKind",
    "FaultForecast",
    "FleetService",
    "FleetStore",
    "Node",
    "NodeStatus",
    "NotFoundError",
    "PlacementDecision",
    "PlacementScore",
    "ValidationError",
    "Workload",
    "WorkloadState",
    "main",
    "make_server",
    "serve",
]

__version__ = "1.0.0"
