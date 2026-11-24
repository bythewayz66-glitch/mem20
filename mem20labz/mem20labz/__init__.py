"""mem20 laboratory runtime.

Crew runtime grouping reviewed packages for joint integration under the
package-review rulings. Member systems live in their own directories;
this runtime provides the registry, CLI surface, and shared surface.
"""

from __future__ import annotations

__version__ = "4.0.0+ng"

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

__all__ = ["__version__", "MEMBERS"]
