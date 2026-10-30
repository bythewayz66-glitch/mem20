"""Adaptive Interface Composer (RM-003 lineage)."""

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
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    cost_weight: float = 1.0
    latency_ms: float = 100.0
    reliability: float = 0.95

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "tags": list(self.tags), "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema), "cost_weight": self.cost_weight,
            "latency_ms": self.latency_ms, "reliability": self.reliability,
        }


@dataclass
class UserIntent:
    text: str
    constraints: dict[str, Any] = field(default_factory=dict)
    preferred_tags: list[str] = field(default_factory=list)
    max_cost: float | None = None
    max_latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text, "constraints": dict(self.constraints),
            "preferred_tags": list(self.preferred_tags),
            "max_cost": self.max_cost, "max_latency_ms": self.max_latency_ms,
        }


@dataclass
class InterfacePlan:
    plan_id: str
    intent_text: str
    steps: list[dict[str, Any]]
    estimated_cost: float
    estimated_latency_ms: float
    confidence: float
    alternatives: list[str] = field(default_factory=list)
    created_ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id, "intent_text": self.intent_text,
            "steps": list(self.steps), "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms,
            "confidence": self.confidence, "alternatives": list(self.alternatives),
            "created_ts": self.created_ts,
        }


def _score_capability(cap: Capability, intent: UserIntent) -> float:
    score = 0.0
    tags = set(t.lower() for t in cap.tags)
    preferred = set(t.lower() for t in intent.preferred_tags)
    text_tokens = set(intent.text.lower().split())
    if preferred:
        score += 0.4 * len(tags & preferred) / max(1, len(preferred))
    name_tokens = set(cap.name.lower().split()) | set(cap.description.lower().split())
    overlap = len(text_tokens & name_tokens)
    score += 0.3 * min(1.0, overlap / 3.0)
    score += 0.2 * cap.reliability
    score -= 0.05 * min(1.0, cap.cost_weight / 5.0)
    score -= 0.05 * min(1.0, cap.latency_ms / 2000.0)
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
    steps = []
    total_cost = 0.0
    total_lat = 0.0
    for rank, (s, cap) in enumerate(chosen, 1):
        steps.append({
            "order": rank, "capability_id": cap.id, "name": cap.name,
            "score": round(s, 4), "cost_weight": cap.cost_weight, "latency_ms": cap.latency_ms,
        })
        total_cost += cap.cost_weight
        total_lat += cap.latency_ms
    confidence = round(sum(s for s, _ in chosen) / max(1, len(chosen)), 4) if chosen else 0.0
    alternatives = [c.id for _, c in scored[top_k:top_k + 3]]
    return InterfacePlan(
        plan_id="plan_" + uuid.uuid4().hex[:12],
        intent_text=intent.text, steps=steps,
        estimated_cost=round(total_cost, 4),
        estimated_latency_ms=round(total_lat, 2),
        confidence=confidence, alternatives=alternatives,
    )


@dataclass
class InterfaceComposer:
    capabilities: dict[str, Capability] = field(default_factory=dict)
    plans: list[InterfacePlan] = field(default_factory=list)

    def register(self, cap: Capability) -> None:
        self.capabilities[cap.id] = cap

    def unregister(self, cap_id: str) -> bool:
        return self.capabilities.pop(cap_id, None) is not None

    def compose(self, intent: UserIntent, top_k: int = 5) -> InterfacePlan:
        plan = compose(intent, list(self.capabilities.values()), top_k=top_k)
        self.plans.append(plan)
        return plan

    def list_capabilities(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.capabilities.values()]
