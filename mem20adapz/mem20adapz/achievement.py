"""Adaptive Achievement Engine (RM-202)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class Goal:
    id: str
    title: str
    target: float
    current: float = 0.0
    unit: str = ""
    adaptive: bool = True
    created_ts: float = field(default_factory=time.time)

    @property
    def progress(self) -> float:
        if self.target <= 0:
            return 1.0
        return min(1.0, max(0.0, self.current / self.target))

    @property
    def complete(self) -> bool:
        return self.current >= self.target


@dataclass
class Achievement:
    id: str
    title: str
    description: str
    tier: str
    points: int
    unlocked_ts: float | None = None
    goal_id: str | None = None

    @property
    def unlocked(self) -> bool:
        return self.unlocked_ts is not None


TIER_THRESHOLDS = {"bronze": 0.25, "silver": 0.50, "gold": 0.75, "platinum": 1.00}
TIER_POINTS = {"bronze": 10, "silver": 25, "gold": 50, "platinum": 100}


def adaptive_target(history: list[float], base_target: float, stretch: float = 1.15) -> float:
    if len(history) < 3:
        return base_target
    recent = history[-5:]
    avg = sum(recent) / len(recent)
    if avg >= base_target * 0.95:
        return round(base_target * stretch, 4)
    return base_target


@dataclass
class AchievementEngine:
    goals: dict[str, Goal] = field(default_factory=dict)
    achievements: dict[str, Achievement] = field(default_factory=dict)
    progress_history: dict[str, list[float]] = field(default_factory=dict)
    total_points: int = 0

    def add_goal(self, goal_id: str, title: str, target: float, unit: str = "", adaptive: bool = True) -> Goal:
        g = Goal(id=goal_id, title=title, target=target, unit=unit, adaptive=adaptive)
        self.goals[goal_id] = g
        self.progress_history.setdefault(goal_id, [])
        for tier, thresh in TIER_THRESHOLDS.items():
            aid = f"{goal_id}:{tier}"
            self.achievements[aid] = Achievement(
                id=aid, title=f"{title} — {tier.title()}",
                description=f"Reach {int(thresh*100)}% of {title}",
                tier=tier, points=TIER_POINTS[tier], goal_id=goal_id,
            )
        return g

    def record(self, goal_id: str, value: float, *, absolute: bool = False) -> dict[str, Any]:
        g = self.goals[goal_id]
        if absolute:
            g.current = value
        else:
            g.current += value
        self.progress_history[goal_id].append(g.current)
        if g.adaptive and g.complete:
            new_target = adaptive_target(self.progress_history[goal_id], g.target)
            if new_target > g.target:
                g.target = new_target
                g.current = min(g.current, g.target)
        unlocked: list[Achievement] = []
        for tier, thresh in TIER_THRESHOLDS.items():
            aid = f"{goal_id}:{tier}"
            ach = self.achievements[aid]
            if not ach.unlocked and g.progress >= thresh:
                ach.unlocked_ts = time.time()
                self.total_points += ach.points
                unlocked.append(ach)
        return {
            "goal_id": goal_id,
            "progress": round(g.progress, 4),
            "current": g.current,
            "target": g.target,
            "complete": g.complete,
            "newly_unlocked": [a.id for a in unlocked],
            "points_awarded": sum(a.points for a in unlocked),
            "total_points": self.total_points,
            "reward_signal": min(1.0, sum(a.points for a in unlocked) / 100.0),
        }

    def status(self, goal_id: str | None = None) -> dict[str, Any]:
        if goal_id:
            g = self.goals[goal_id]
            unlocked = [a for a in self.achievements.values() if a.goal_id == goal_id and a.unlocked]
            return {
                "goal": {"id": g.id, "title": g.title, "progress": round(g.progress, 4),
                         "current": g.current, "target": g.target, "complete": g.complete},
                "unlocked": [a.id for a in unlocked],
                "total_points": self.total_points,
            }
        return {
            "goals": {gid: {"progress": round(g.progress, 4), "current": g.current,
                           "target": g.target, "complete": g.complete}
                      for gid, g in self.goals.items()},
            "total_points": self.total_points,
            "unlocked_count": sum(1 for a in self.achievements.values() if a.unlocked),
        }
