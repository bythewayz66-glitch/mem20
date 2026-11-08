"""mem20labz — laboratory runtime (1st-class).

Crew runtime grouping 10 reviewed lab subsystems for joint integration:
registry, health probes, simulation orchestration, 6-peer ecosystem signals,
durable SQLite WAL run history, CLI, JSON/HTTP API, and served web frontend.
"""
from __future__ import annotations

__version__ = "0.1.0"

MEMBERS = (
    "mem20autonomoussaleslaboratoryz",
    "mem20continuouscompatibilitylabz",
    "mem20customerdigitaltwinlabz",
    "mem20dependencymutationlabz",
    "mem20executabledesignstresslabz",
    "mem20modelgenomelabz",
    "mem20neuromorphiceventlabz",
    "mem20outcomesimulationlabz",
    "mem20remoteexperimentlabz",
    "mem20webassemblycomponentlabz",
)

from . import cli, domain, ecosystem, runtime, server  # noqa: E402

__all__ = ["__version__", "MEMBERS", "cli", "domain", "ecosystem", "runtime", "server"]
