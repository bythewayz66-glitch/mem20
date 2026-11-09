"""mem20 production pipeline runtime for game-maker and software pipelines.

Crew runtime grouping reviewed packages for joint integration under the
package-review rulings. Member systems live in their own directories;
this runtime provides the registry, CLI surface, and shared surface.
"""

from __future__ import annotations

__version__ = "0.1.0"

MEMBERS = (
    "mem20pipez",
    "mem20pipez",
    "mem20pipez",
    "mem20pipez",
    "mem20pipez",
    "mem20pipez",
    "mem20personalworkflowtwinz",
    "mem20pipez",
    "mem20pipez",
    "mem20pipez",
    "mem20pipez",
    "mem20pipez",
)

from . import cli  # noqa: E402
from .domain import pipeline_report, probe, estate_context  # noqa: E402

__all__ = ["__version__", "MEMBERS", "cli", "pipeline_report", "probe", "estate_context"]
