"""Social features: agent kudos, streaks, team velocity."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class KudosCategory(str, Enum):
    """Categories of kudos."""
    HELPFUL = "helpful"
    CREATIVE = "creative"
    THOROUGH = "thorough"
    FAST = "fast"
    COLLABORATIVE = "collaborative"
    MENTORING = "mentoring"
    PROBLEM_SOLVING = "problem_solving"
    QUALITY = "quality"
    INNOVATION = "innovation"
    CUSTOM = "custom"


class AchievementType(str, Enum):
    """Types of achievements."""
    STREAK = "streak"
    MILESTONE = "milestone"
    FIRST = "first"
    EXPERT = "expert"
    MENTOR = "mentor"
    REVIEWER = "reviewer"
    CONTRIBUTOR = "contributor"
    CUSTOM = "custom"


@dataclass
class Kudos:
    """A kudos given from one agent to another."""
    id: str
    from_agent: str
    to_agent: str
    category: KudosCategory
    message: str
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    visibility: str = "team"  # private, team, public
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> [agent_ids]
    created_at: float = field(default_factory=time.time)


@dataclass
class Streak:
    """A streak of consecutive days/activities."""
    id: str
    agent_id: str
    type: str  # daily_login, daily_task, daily_commit, etc.
    current_count: int = 0
    longest_count: int = 0
    last_activity_date: Optional[str] = None  # YYYY-MM-DD
    started_at: float = field(default_factory=time.time)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Achievement:
    """An achievement earned by an agent."""
    id: str
    agent_id: str
    type: AchievementType
    title: str
    description: str
    icon: str = "🏆"
    earned_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamVelocity:
    """Team velocity metrics."""
    team_id: str
    period_start: float
    period_end: float
    completed_tasks: int = 0
    completed_story_points: int = 0
    avg_cycle_time_hours: float = 0.0
    avg_lead_time_hours: float = 0.0
    throughput: float = 0.0  # tasks per day
    quality_score: float = 0.0  # 0-1
    collaboration_index: float = 0.0  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentProfile:
    """Social profile for an agent."""
    agent_id: str
    display_name: str
    avatar: Optional[str] = None
    bio: str = ""
    skills: List[str] = field(default_factory=list)
    kudos_given: int = 0
    kudos_received: int = 0
    achievements: List[Achievement] = field(default_factory=list)
    streaks: Dict[str, Streak] = field(default_factory=dict)  # streak_type -> streak
    joined_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SocialConfig(BaseModel):
    """Configuration for social features."""
    enable_kudos: bool = True
    enable_streaks: bool = True
    enable_achievements: bool = True
    enable_velocity: bool = True
    streak_types: List[str] = Field(default_factory=lambda: [
        "daily_login", "daily_task", "daily_commit", "daily_review"
    ])
    kudos_cooldown_hours: float = 1.0
    max_kudos_per_day: int = 10
    achievement_thresholds: Dict[str, int] = Field(default_factory=lambda: {
        "first_kudos": 1,
        "helpful_10": 10,
        "creative_5": 5,
        "streak_7": 7,
        "streak_30": 30,
        "streak_100": 100,
        "tasks_100": 100,
        "reviews_50": 50,
    })
    velocity_window_days: int = 14
    notification_webhook: Optional[str] = None


class SocialFeatures:
    """Manages social features for agents."""

    def __init__(
        self,
        config: Optional[SocialConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
    ) -> None:
        self.config = config or SocialConfig()
        self.notifier = notifier
        self._kudos: List[Kudos] = []
        self._streaks: Dict[str, Dict[str, Streak]] = defaultdict(dict)  # agent_id -> streak_type -> streak
        self._achievements: Dict[str, List[Achievement]] = defaultdict(list)  # agent_id -> achievements
        self._profiles: Dict[str, AgentProfile] = {}
        self._velocity_history: List[TeamVelocity] = []
        self._agent_kudos_given_today: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))  # agent_id -> date -> count

    def give_kudos(
        self,
        from_agent: str,
        to_agent: str,
        category: KudosCategory,
        message: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        visibility: str = "team",
    ) -> Optional[Kudos]:
        """Give kudos to another agent."""
        # Check cooldown
        today = time.strftime("%Y-%m-%d")
        if self._agent_kudos_given_today[from_agent][today] >= self.config.max_kudos_per_day:
            return None

        # Check if giving to self
        if from_agent == to_agent:
            return None

        kudos = Kudos(
            id=str(uuid.uuid4())[:8],
            from_agent=from_agent,
            to_agent=to_agent,
            category=category,
            message=message,
            project_id=project_id,
            task_id=task_id,
            visibility=visibility,
        )

        self._kudos.append(kudos)
        self._agent_kudos_given_today[from_agent][today] += 1

        # Update profiles
        self._ensure_profile(from_agent)
        self._ensure_profile(to_agent)
        self._profiles[from_agent].kudos_given += 1
        self._profiles[to_agent].kudos_received += 1

        # Check for achievements
        self._check_kudos_achievements(to_agent, category)

        # Notify recipient
        self._notify_agent(to_agent, "kudos_received", {
            "from": from_agent,
            "category": category.value,
            "message": message,
        })

        return kudos

    def get_kudos_for_agent(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[Kudos]:
        """Get kudos received by an agent."""
        received = [k for k in self._kudos if k.to_agent == agent_id]
        received.sort(key=lambda k: k.created_at, reverse=True)
        return received[:limit]

    def get_kudos_given_by_agent(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[Kudos]:
        """Get kudos given by an agent."""
        given = [k for k in self._kudos if k.from_agent == agent_id]
        given.sort(key=lambda k: k.created_at, reverse=True)
        return given[:limit]

    def update_streak(
        self,
        agent_id: str,
        streak_type: str,
        increment: bool = True,
    ) -> Optional[Streak]:
        """Update a streak for an agent."""
        today = time.strftime("%Y-%m-%d")
        yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))

        streak = self._streaks[agent_id].get(streak_type)

        if streak is None:
            streak = Streak(
                id=str(uuid.uuid4())[:8],
                agent_id=agent_id,
                type=streak_type,
            )
            self._streaks[agent_id][streak_type] = streak

        if increment:
            if streak.last_activity_date == today:
                return streak  # Already updated today

            if streak.last_activity_date == yesterday:
                streak.current_count += 1
            else:
                streak.current_count = 1

            streak.last_activity_date = today
            streak.longest_count = max(streak.longest_count, streak.current_count)
            streak.is_active = True

            # Check for streak achievements
            self._check_streak_achievements(agent_id, streak_type, streak.current_count)

        return streak

    def get_streak(self, agent_id: str, streak_type: str) -> Optional[Streak]:
        """Get a streak for an agent."""
        return self._streaks[agent_id].get(streak_type)

    def get_all_streaks(self, agent_id: str) -> Dict[str, Streak]:
        """Get all streaks for an agent."""
        return self._streaks.get(agent_id, {})

    def award_achievement(
        self,
        agent_id: str,
        type: AchievementType,
        title: str,
        description: str,
        icon: str = "🏆",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Achievement:
        """Award an achievement to an agent."""
        achievement = Achievement(
            id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            type=type,
            title=title,
            description=description,
            icon=icon,
            metadata=metadata or {},
        )

        self._achievements[agent_id].append(achievement)

        # Update profile
        self._ensure_profile(agent_id)
        self._profiles[agent_id].achievements.append(achievement)

        # Notify agent
        self._notify_agent(agent_id, "achievement_earned", {
            "title": title,
            "description": description,
            "icon": icon,
        })

        return achievement

    def get_achievements(self, agent_id: str) -> List[Achievement]:
        """Get all achievements for an agent."""
        return self._achievements.get(agent_id, [])

    def get_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """Get an agent's social profile."""
        return self._profiles.get(agent_id)

    def update_profile(
        self,
        agent_id: str,
        updates: Dict[str, Any],
    ) -> Optional[AgentProfile]:
        """Update an agent's profile."""
        self._ensure_profile(agent_id)
        profile = self._profiles[agent_id]

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        return profile

    def record_team_velocity(
        self,
        team_id: str,
        completed_tasks: int,
        completed_story_points: int,
        cycle_times_hours: List[float],
        lead_times_hours: List[float],
        quality_metrics: Dict[str, float],
        collaboration_data: Dict[str, Any],
    ) -> TeamVelocity:
        """Record team velocity for a period."""
        now = time.time()
        period_start = now - self.config.velocity_window_days * 86400

        velocity = TeamVelocity(
            team_id=team_id,
            period_start=period_start,
            period_end=now,
            completed_tasks=completed_tasks,
            completed_story_points=completed_story_points,
            avg_cycle_time_hours=sum(cycle_times_hours) / len(cycle_times_hours) if cycle_times_hours else 0,
            avg_lead_time_hours=sum(lead_times_hours) / len(lead_times_hours) if lead_times_hours else 0,
            throughput=completed_tasks / self.config.velocity_window_days,
            quality_score=quality_metrics.get("quality_score", 0.0),
            collaboration_index=collaboration_data.get("collaboration_index", 0.0),
            metadata={
                "quality_metrics": quality_metrics,
                "collaboration_data": collaboration_data,
            },
        )

        self._velocity_history.append(velocity)
        return velocity

    def get_team_velocity(
        self,
        team_id: str,
        limit: int = 10,
    ) -> List[TeamVelocity]:
        """Get velocity history for a team."""
        velocities = [v for v in self._velocity_history if v.team_id == team_id]
        velocities.sort(key=lambda v: v.period_end, reverse=True)
        return velocities[:limit]

    def get_leaderboard(
        self,
        metric: str = "kudos_received",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get leaderboard for a metric."""
        profiles = list(self._profiles.values())

        if metric == "kudos_received":
            profiles.sort(key=lambda p: p.kudos_received, reverse=True)
        elif metric == "kudos_given":
            profiles.sort(key=lambda p: p.kudos_given, reverse=True)
        elif metric == "achievements":
            profiles.sort(key=lambda p: len(p.achievements), reverse=True)
        elif metric == "longest_streak":
            profiles.sort(
                key=lambda p: max((s.longest_count for s in p.streaks.values()), default=0),
                reverse=True,
            )

        return [
            {
                "agent_id": p.agent_id,
                "display_name": p.display_name,
                "avatar": p.avatar,
                "value": getattr(p, metric, len(p.achievements)),
            }
            for p in profiles[:limit]
        ]

    def _ensure_profile(self, agent_id: str) -> AgentProfile:
        """Ensure profile exists for agent."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = AgentProfile(
                agent_id=agent_id,
                display_name=f"Agent {agent_id[:8]}",
            )
        return self._profiles[agent_id]

    def _check_kudos_achievements(self, agent_id: str, category: KudosCategory) -> None:
        """Check and award kudos-related achievements."""
        profile = self._ensure_profile(agent_id)
        received = len([k for k in self._kudos if k.to_agent == agent_id])

        thresholds = {
            "first_kudos": 1,
            "kudos_10": 10,
            "kudos_50": 50,
            "kudos_100": 100,
        }

        for achievement_id, threshold in thresholds.items():
            if received >= threshold:
                self._award_if_not_exists(agent_id, achievement_id, {
                    "first_kudos": (AchievementType.FIRST, "First Kudos", "Received your first kudos!", "🎉"),
                    "kudos_10": (AchievementType.MILESTONE, "10 Kudos", "Received 10 kudos!", "🌟"),
                    "kudos_50": (AchievementType.MILESTONE, "50 Kudos", "Received 50 kudos!", "💫"),
                    "kudos_100": (AchievementType.MILESTONE, "100 Kudos", "Received 100 kudos!", "🏆"),
                }[achievement_id])

        # Category-specific
        cat_received = len([k for k in self._kudos if k.to_agent == agent_id and k.category == category])
        if cat_received >= 10:
            self._award_if_not_exists(agent_id, f"{category.value}_expert", (
                AchievementType.EXPERT,
                f"{category.value.title()} Expert",
                f"Recognized for {category.value} contributions 10+ times!",
                "🎓",
            ))

    def _check_streak_achievements(self, agent_id: str, streak_type: str, count: int) -> None:
        """Check and award streak achievements."""
        thresholds = {
            "streak_3": 3,
            "streak_7": 7,
            "streak_30": 30,
            "streak_100": 100,
        }

        for achievement_id, threshold in thresholds.items():
            if count >= threshold:
                self._award_if_not_exists(agent_id, f"{streak_type}_{achievement_id}", (
                    AchievementType.STREAK,
                    f"{streak_type.replace('_', ' ').title()} Streak {threshold}",
                    f"Maintained {streak_type.replace('_', ' ')} streak for {threshold} days!",
                    "🔥",
                ))

    def _award_if_not_exists(
        self,
        agent_id: str,
        achievement_id: str,
        achievement_data: tuple,
    ) -> None:
        """Award achievement if not already earned."""
        existing = any(a.id == achievement_id for a in self._achievements.get(agent_id, []))
        if not existing:
            atype, title, desc, icon = achievement_data
            self.award_achievement(agent_id, atype, title, desc, icon, {"achievement_id": achievement_id})

    def _notify_agent(self, agent_id: str, event: str, data: Dict[str, Any]) -> None:
        """Notify an agent of an event."""
        if not self.notifier:
            return

        try:
            self.notifier(agent_id, event, data)
        except Exception:
            pass


# Global instance
_social_features: Optional[SocialFeatures] = None


def get_social_features(config: Optional[SocialConfig] = None) -> SocialFeatures:
    """Get global social features instance."""
    global _social_features
    if _social_features is None:
        _social_features = SocialFeatures(config)
    return _social_features