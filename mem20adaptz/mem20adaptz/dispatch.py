"""Adaptive mission dispatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Agent:
    id: str
    capabilities: set[str] = field(default_factory=set)
    load: float = 0.0
    location: str = ""
    trust: float = 1.0
    max_concurrent: int = 3
    active: int = 0


@dataclass
class Mission:
    id: str
    required_capabilities: set[str] = field(default_factory=set)
    urgency: float = 0.5
    preferred_location: str = ""
    min_trust: float = 0.0
    weight: float = 1.0


def score_agent(agent: Agent, mission: Mission) -> dict[str, Any]:
    if agent.active >= agent.max_concurrent:
        return {"total": -1.0, "reason": "saturated", "components": {}}
    req, have = mission.required_capabilities, agent.capabilities
    if req and not req.issubset(have):
        return {"total": -1.0, "reason": f"missing_capabilities:{sorted(req - have)}", "components": {}}
    if agent.trust < mission.min_trust:
        return {"total": -1.0, "reason": "trust_below_floor", "components": {}}
    cap_score = 1.0 if not req else len(req & have) / len(req)
    load_score = 1.0 - min(1.0, max(0.0, agent.load))
    loc_score = 1.0 if (not mission.preferred_location or agent.location == mission.preferred_location) else 0.3
    trust_score = max(0.0, min(1.0, agent.trust))
    urgency = max(0.0, min(1.0, mission.urgency))
    components = {"capability": round(cap_score, 4), "load": round(load_score, 4), "location": round(loc_score, 4), "trust": round(trust_score, 4), "urgency": round(urgency, 4)}
    total = 0.35 * cap_score + 0.25 * load_score + 0.15 * loc_score + 0.15 * trust_score + 0.10 * urgency
    return {"total": round(total, 6), "reason": "ok", "components": components}


def assign(mission: Mission, agents: list[Agent], *, top_k: int = 3) -> dict[str, Any]:
    ranked = [{"agent_id": a.id, "score": score_agent(a, mission)["total"], "detail": score_agent(a, mission)} for a in agents]
    ranked.sort(key=lambda r: r["score"], reverse=True)
    eligible = [r for r in ranked if r["score"] >= 0]
    return {"mission_id": mission.id, "candidates": eligible[:top_k], "best": eligible[0] if eligible else None, "rejected": len(ranked) - len(eligible)}


@dataclass
class DispatchEngine:
    agents: dict[str, Agent] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def register(self, agent: Agent) -> None:
        self.agents[agent.id] = agent

    def assign(self, mission: Mission, top_k: int = 3) -> dict[str, Any]:
        result = assign(mission, list(self.agents.values()), top_k=top_k)
        self.history.append(result)
        if result["best"]:
            aid = result["best"]["agent_id"]
            self.agents[aid].active += 1
            self.agents[aid].load = min(1.0, self.agents[aid].load + 0.15)
        return result

    def release(self, agent_id: str) -> None:
        a = self.agents[agent_id]
        a.active = max(0, a.active - 1)
        a.load = max(0.0, a.load - 0.15)
