"""mem20 Gateway package.

The gateway composes relay policy from the sibling subsystems that own each
rule: mem20secretz classifies secrets, memory_engine detects them, mem20kilnz
owns asset budgets, mem20verify owns store integrity, and toolchest owns the
estate inventory.
"""

from .routing import (
    RouteDecision,
    ScreenVerdict,
    check_asset_budget,
    inventory_subsystems,
    route,
    screen_payload,
    target_is_known,
    verify_store,
)

__all__ = [
    "RouteDecision",
    "ScreenVerdict",
    "check_asset_budget",
    "inventory_subsystems",
    "route",
    "screen_payload",
    "target_is_known",
    "verify_store",
]
__version__ = "0.2.0"
