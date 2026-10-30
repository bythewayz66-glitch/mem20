"""mem20adapz — first-class unified adaptive systems runtime."""

from __future__ import annotations

from .runtime import AdaptiveRuntime, RuntimeConfig
from . import achievement, dispatch, forgetting, inference, interface, personality, pricing

__version__ = "1.0.0"

MEMBERS = {
    "achievement": "mem20adaptiveachievementenginez",
    "dispatch": "mem20adaptivedispatchenginez",
    "forgetting": "mem20adaptiveforgettingenginez",
    "inference": "mem20adaptiveinferencemarketplacez",
    "interface": "mem20adaptiveinterfacecomposerz",
    "personality": "mem20adaptivepersonalityruntimez",
    "pricing": "mem20adaptivepricingbrainz",
}

FORMER_PACKAGES = tuple(MEMBERS.values())

__all__ = [
    "__version__", "MEMBERS", "FORMER_PACKAGES",
    "AdaptiveRuntime", "RuntimeConfig",
    "achievement", "dispatch", "forgetting", "inference",
    "interface", "personality", "pricing",
]
