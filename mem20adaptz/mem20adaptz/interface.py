"""Adaptive Interface Composer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time
import uuid


@dataclass
class Capability:
    id: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    cost_weight: float = 1.0
    latency_ms: float = 100.0
    reliability: float = 0.95

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "description": self.description, "tags": list(self.tags), "cost_weight": self.cost_weight, "latency_ms": self.latency_ms, "reliability": self.reliability}


@dataclass
class UserIntent:
    text: str
    preferred_tags: list[str] = field(default_factory=list)
    max_cost: float | None = None
    max_latency_ms: float | None = None


@dataclass
class InterfacePlan:
    plan_id: str
    intent_text: str
    steps: list[dict[str, Any]]
    estimated_cost: float
    estimated_latency_ms: float
    confidence: float
    alternatives: list[str] = field(default_factory=list)


def _score_capability(cap: Capability, intent: UserIntent) -> float:
    score = 0.0
    tags = set(t.lower() for t in cap.tags)
    preferred = set(t.lower() for t in intent.preferred_tags)
    text_tokens = set(intent.text.lower().split())
    if preferred:
        score += 0.4 * len(tags & preferred) / max(1, len(preferred))
    name_tokens = set(cap.name.lower().split()) | set(cap.description.lower().split())
    score += 0.3 * min(1.0, len(text_tokens & name_tokens) / 3.0)
    score += 0.2 * cap.reliability
    return max(0.0, min(1.0, score))


def compose(intent: UserIntent, capabilities: list[Capability], top_k: int = 5) -> InterfacePlan:
    scored = []
    for cap in capabilities:
        if intent.max_cost is not None and cap.cost_weight > intent.max_cost:
            continue
        if intent.max_latency_ms is not None and cap.latency_ms > intent.max_latency_ms:
            continue
        s = _score_capability(cap, intent)
        if s > 0.05:
            scored.append((s, cap))
    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = scored[:top_k]
    steps = [{"order": i, "capability_id": c.id, "name": c.name, "score": round(s, 4)} for i, (s, c) in enumerate(chosen, 1)]
    confidence = round(sum(s for s, _ in chosen) / max(1, len(chosen)), 4) if chosen else 0.0
    return InterfacePlan(plan_id="plan_" + uuid.uuid4().hex[:12], intent_text=intent.text, steps=steps, estimated_cost=round(sum(c.cost_weight for _, c in chosen), 4), estimated_latency_ms=round(sum(c.latency_ms for _, c in chosen), 2), confidence=confidence, alternatives=[c.id for _, c in scored[top_k:top_k+3]])


@dataclass
class InterfaceComposer:
    capabilities: dict[str, Capability] = field(default_factory=dict)
    plans: list[InterfacePlan] = field(default_factory=list)

    def register(self, cap: Capability) -> None:
        self.capabilities[cap.id] = cap

    def compose(self, intent: UserIntent, top_k: int = 5) -> InterfacePlan:
        plan = compose(intent, list(self.capabilities.values()), top_k=top_k)
        self.plans.append(plan)
        return plan
