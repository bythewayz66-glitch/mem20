"""mem20adapz — first-class unified adaptive systems runtime.

Consolidates every former mem20adaptive* organ into one product surface with
real implementations (not generic templates):

  achievement   Adaptive Achievement Engine (progress, tiers, rewards)
  dispatch      Capability / load / trust / urgency mission assignment
  forgetting    Ebbinghaus spaced-repetition retention + review queue
  inference     Double-auction inference-capacity marketplace
  interface     Adaptive Interface Composer (capability → UI plan)
  personality   Context-aware communication style + initiative
  pricing       Elasticity-fitted adaptive pricing brain
"""

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
    "__version__",
    "MEMBERS",
    "FORMER_PACKAGES",
    "AdaptiveRuntime",
    "RuntimeConfig",
    "achievement",
    "dispatch",
    "forgetting",
    "inference",
    "interface",
    "personality",
    "pricing",
]
