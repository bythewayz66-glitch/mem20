"""mem20labz — laboratory runtime (1st-class).

Crew runtime grouping 10 reviewed lab subsystems for joint integration:
registry, health probes, simulation orchestration, 6-peer ecosystem signals,
durable SQLite WAL run history, CLI, JSON/HTTP API, and served web frontend.
"""
from __future__ import annotations

__version__ = "0.1.0"

MEMBERS = (
    "mem20autonomoussaleslaboratoryz",
    "mem20labz",
    "mem20twinz",
    "mem20labz",
    "mem20labz",
    "mem20labz",
    "mem20labz",
    "mem20simz",
    "mem20labz",
    "mem20labz",
)

from . import cli, domain, ecosystem, runtime, server  # noqa: E402

__all__ = ["__version__", "MEMBERS", "cli", "domain", "ecosystem", "runtime", "server"]
