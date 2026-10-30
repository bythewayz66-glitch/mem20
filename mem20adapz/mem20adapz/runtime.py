"""Unified AdaptiveRuntime — first-class surface for every adaptive organ."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import achievement, dispatch, forgetting, inference, interface, personality, pricing


@dataclass
class RuntimeConfig:
    forgetting_threshold: float = 0.5
    pricing_objective: str = "revenue"
    pricing_cost: float = 0.0
    pricing_floor: float = 0.01
    pricing_ceiling: float = 1000.0


class AdaptiveRuntime:
    """Single entry point that owns real implementations of all adaptive organs."""

    def __init__(self, config: RuntimeConfig | None = None):
        self.config = config or RuntimeConfig()
        self.forgetting = forgetting.ForgettingEngine(threshold=self.config.forgetting_threshold)
        self.pricing = pricing.PricingBrain(
            cost=self.config.pricing_cost,
            price_floor=self.config.pricing_floor,
            price_ceiling=self.config.pricing_ceiling,
            objective=self.config.pricing_objective,
        )
        self.inference = inference.InferenceMarketplace()
        self.dispatch = dispatch.DispatchEngine()
        self.personality = personality.PersonalityRuntime()
        self.achievement = achievement.AchievementEngine()
        self.interface = interface.InterfaceComposer()

    def health(self) -> dict[str, Any]:
        return {
            "runtime": "mem20adapz",
            "version": "1.0.0",
            "organs": {
                "forgetting": {"items": len(self.forgetting)},
                "pricing": {"observations": len(self.pricing.observations)},
                "inference": {"open_orders": len(self.inference.orders)},
                "dispatch": {"agents": len(self.dispatch.agents)},
                "personality": {"history": len(self.personality.history)},
                "achievement": {
                    "goals": len(self.achievement.goals),
                    "points": self.achievement.total_points,
                },
                "interface": {"capabilities": len(self.interface.capabilities)},
            },
        }

    def members(self) -> list[str]:
        return [
            "achievement", "dispatch", "forgetting", "inference",
            "interface", "personality", "pricing",
        ]
