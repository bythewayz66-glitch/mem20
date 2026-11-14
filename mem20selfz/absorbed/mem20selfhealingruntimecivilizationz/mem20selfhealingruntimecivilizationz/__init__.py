"""mem20selfhealingruntimecivilizationz — self-healing runtime civilization.

Stable public API (4.0)
-----------------------
The names exported here are the substrate contract other mem20 subsystems may
build on. They are covered by ``mem20/API.md`` and are the ones the conformance
gate and the MCP tool surface use.

Domain model (pure, standard library only)::

    from mem20selfhealingruntimecivilizationz import Civilization

    civ = Civilization(threshold=0.3, repair_amount=0.5)
    civ.add_agent("gateway")
    civ.add_agent("mcp", depends_on=["gateway"])
    civ.damage("gateway", 0.8)
    civ.run_cycle()

Operational controller (wires the mem20 substrate)::

    from mem20selfhealingruntimecivilizationz import FleetController

    controller = FleetController.from_catalogue(limit=6)
    record = controller.cycle()
    controller.metrics_snapshot()

Compatibility: the 3.x dict-based helpers (``create_civilization``, ``damage``,
``heal``, ``auto_heal``, ``civ_health``) still exist and now operate on
:class:`Civilization` objects. They are deprecated in favour of the methods and
will be removed in 5.0.
"""
from __future__ import annotations

import sys as _sys

from .domain import (
    ALIVE,
    DEAD,
    DEGRADED,
    DOWN,
    HEALTHY,
    QUARANTINED,
    Agent,
    Civilization,
    CivilizationError,
    auto_heal,
    civ_health,
    create_civilization,
    damage,
    heal,
)
from .domain import main as domain_main
from .controller import ControllerConfig, FleetController, main
from .integrations import Substrate
from .runtime import Decision, Engine, SDK, Store, load_config

__version__ = "1.1.0"

__all__ = [
    # domain
    "Civilization",
    "Agent",
    "CivilizationError",
    "ALIVE",
    "QUARANTINED",
    "DEAD",
    "HEALTHY",
    "DEGRADED",
    "DOWN",
    # operational
    "FleetController",
    "ControllerConfig",
    "Substrate",
    # runtime primitives (kept for the HTTP surface and the SDK)
    "Store",
    "Engine",
    "SDK",
    "Decision",
    "load_config",
    # legacy dict API
    "create_civilization",
    "damage",
    "heal",
    "auto_heal",
    "civ_health",
    # entry points
    "main",
    "domain_main",
    "__version__",
]
