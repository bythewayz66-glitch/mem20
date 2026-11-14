"""mem20edgetocloudintelligencecontinuumz — Edge-to-Cloud Intelligence Continuum.

Invisible, resilient, cost-aware workload placement across local, edge, private,
peer and cloud tiers.
"""

from . import domain, ecosystem
from .runtime import main, serve
from .service import ContinuumService, ValidationError
from .store import ContinuumStore, ConflictError, NotFoundError

__all__ = [
    "ContinuumService",
    "ContinuumStore",
    "ValidationError",
    "ConflictError",
    "NotFoundError",
    "domain",
    "ecosystem",
    "main",
    "serve",
]
