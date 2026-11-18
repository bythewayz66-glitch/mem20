"""Collaboration Manager: unified interface for all collaboration subsystems."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from .approvals import ApprovalGate, ApprovalConfig, get_approval_gate
from .pair_programming import PairSessionManager, PairConfig, get_pair_session
from .code_review import CodeReviewManager, ReviewConfig, get_code_review
from .handoff import HandoffManager, HandoffConfig, get_handoff_manager
from .whiteboard import WhiteboardManager, WhiteboardConfig, get_whiteboard
from .meeting_agent import MeetingAgent, MeetingConfig, get_meeting_agent
from .digest import DigestGenerator, DigestConfig, get_digest_generator
from .guest_access import GuestAccessManager, GuestConfig, get_guest_access
from .conflict_resolution import ConflictResolver, ConflictConfig, get_conflict_resolver
from .social import SocialFeatures, SocialConfig, get_social_features


class CollaborationManagerConfig(BaseModel):
    """Configuration for collaboration manager."""
    approvals: Optional[ApprovalConfig] = None
    pair_programming: Optional[PairConfig] = None
    code_review: Optional[ReviewConfig] = None
    handoff: Optional[HandoffConfig] = None
    whiteboard: Optional[WhiteboardConfig] = None
    meeting_agent: Optional[MeetingConfig] = None
    digest: Optional[DigestConfig] = None
    guest_access: Optional[GuestConfig] = None
    conflict_resolution: Optional[ConflictConfig] = None
    social: Optional[SocialConfig] = None


@dataclass
class CollaborationSession:
    """A collaboration session tracking all artifacts."""
    id: str
    project_id: str
    participants: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Artifacts
    approval_requests: List[str] = field(default_factory=list)
    pair_sessions: List[str] = field(default_factory=list)
    code_reviews: List[str] = field(default_factory=list)
    handoffs: List[str] = field(default_factory=list)
    whiteboards: List[str] = field(default_factory=list)
    meetings: List[str] = field(default_factory=list)
    digests: List[str] = field(default_factory=list)
    guest_tokens: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    # Status
    status: str = "active"


class CollaborationManager:
    """Unified collaboration manager coordinating all subsystems."""

    def __init__(self, config: Optional[CollaborationManagerConfig] = None) -> None:
        self.config = config or CollaborationManagerConfig()
        self._approvals = get_approval_gate(self.config.approvals)
        self._pair = get_pair_session(self.config.pair_programming)
        self._reviews = get_code_review(self.config.code_review)
        self._handoffs = get_handoff_manager(self.config.handoff)
        self._whiteboards = get_whiteboard(self.config.whiteboard)
        self._meetings = get_meeting_agent(self.config.meeting_agent)
        self._digests = get_digest_generator(self.config.digest)
        self._guest = get_guest_access(self.config.guest_access)
        self._conflicts = get_conflict_resolver(self.config.conflict_resolution)
        self._social = get_social_features(self.config.social)

        self._sessions: Dict[str, CollaborationSession] = {}

    def create_session(self, project_id: str, participants: List[str]) -> str:
        """Create a new collaboration session."""
        session_id = str(uuid.uuid4())[:8]
        session = CollaborationSession(
            id=session_id,
            project_id=project_id,
            participants=participants,
        )
        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get a collaboration session."""
        return self._sessions.get(session_id)

    # --- Approval Gates ---

    def request_approval(
        self,
        session_id: str,
        title: str,
        description: str,
        approval_type: str,
        requester: str,
        context: Dict[str, Any],
        **kwargs,
    ) -> Optional[str]:
        """Request approval through the approval gate."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        request_id = self._approvals.request_approval(
            title=title,
            description=description,
            approval_type=approval_type,
            requester=requester,
            context=context,
            **kwargs,
        )

        if request_id:
            session.approval_requests.append(request_id)
            session.updated_at = time.time()

        return request_id

    def decide_approval(
        self,
        session_id: str,
        request_id: str,
        user_id: str,
        decision: str,
        rationale: str = "",
    ) -> bool:
        """Decide on an approval request."""
        session = self._sessions.get(session_id)
        if not session or request_id not in session.approval_requests:
            return False

        return self._approvals.decide(request_id, user_id, decision, rationale)

    # --- Pair Programming ---

    def start_pair_session(
        self,
        session_id: str,
        title: str,
        creator_id: str,
        creator_name: str,
    ) -> Optional[str]:
        """Start a pair programming session."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        pair_id = self._pair.create_session(title, creator_id, creator_name)
        if pair_id:
            session.pair_sessions.append(pair_id)
            session.updated_at = time.time()
        return pair_id

    def join_pair_session(
        self,
        session_id: str,
        pair_id: str,
        user_id: str,
        name: str,
        preferred_role: Optional[str] = None,
    ) -> bool:
        """Join a pair programming session."""
        session = self._sessions.get(session_id)
        if not session or pair_id not in session.pair_sessions:
            return False

        from .pair_programming import PairRole
        role = PairRole(preferred_role) if preferred_role else None
        return self._pair.join_session(pair_id, user_id, name, role)

    # --- Code Review ---

    def create_code_review(
        self,
        session_id: str,
        title: str,
        description: str,
        author: str,
        head_branch: str,
        base_branch: str = "main",
        files_changed: Optional[List[str]] = None,
        diff: str = "",
        reviewers: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Create a code review."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        review_id = self._reviews.create_review(
            title=title,
            description=description,
            author=author,
            head_branch=head_branch,
            base_branch=base_branch,
            files_changed=files_changed,
            diff=diff,
            reviewers=reviewers,
        )

        if review_id:
            session.code_reviews.append(review_id)
            session.updated_at = time.time()

        return review_id

    def submit_code_review(self, review_id: str) -> bool:
        """Submit a draft code review."""
        return self._reviews.submit_review(review_id)

    def add_review_comment(
        self,
        review_id: str,
        author: str,
        file_path: str,
        content: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        comment_type: str = "inline",
    ) -> Optional[str]:
        """Add a comment to a code review."""
        return self._reviews.add_comment(
            review_id=review_id,
            author=author,
            file_path=file_path,
            content=content,
            line_start=line_start,
            line_end=line_end,
            comment_type=comment_type,
        )

    def submit_review_decision(
        self,
        review_id: str,
        reviewer: str,
        decision: str,
        rationale: str = "",
    ) -> bool:
        """Submit a review decision."""
        return self._reviews.submit_decision(review_id, reviewer, decision, rationale)

    # --- Handoffs ---

    def request_handoff(
        self,
        session_id: str,
        type: str,
        reason: str,
        from_party: str,
        to_party: str,
        context: Dict[str, Any],
        message: str = "",
        priority: int = 0,
    ) -> Optional[str]:
        """Request a handoff."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        from .handoff import HandoffType, HandoffReason, HandoffContext

        handoff_id = self._handoffs.request_handoff(
            type=type,
            reason=reason,
            from_party=from_party,
            to_party=to_party,
            context=HandoffContext(**context),
            **{"message": "", "priority": 0},  # Additional params
        )

        if handoff_id:
            session.handoffs.append(handoff_id)
            session.updated_at = time.time()

        return handoff_id

    # --- Whiteboard ---

    def create_whiteboard(
        self,
        session_id: str,
        name: str,
        creator: str,
    ) -> Optional[str]:
        """Create a whiteboard."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        wb_id = self._whiteboards.create_scene(name, creator)
        if wb_id:
            session.whiteboards.append(wb_id)
            session.updated_at = time.time()
        return wb_id

    # --- Meetings ---

    def schedule_meeting(
        self,
        session_id: str,
        title: str,
        host_id: str,
        scheduled_at: float,
        description: str = "",
        participants: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Schedule a meeting."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        meeting_id = self._meetings.schedule_meeting(
            title=title,
            host_id=host_id,
            scheduled_at=scheduled_at,
            description=description,
            participants=participants,
        )

        if meeting_id:
            session.meetings.append(meeting_id)
            session.updated_at = time.time()
        return meeting_id

    def start_meeting(self, meeting_id: str) -> bool:
        """Start a meeting."""
        return self._meetings.start_meeting(meeting_id)

    def end_meeting(self, meeting_id: str) -> bool:
        """End a meeting."""
        return self._meetings.end_meeting(meeting_id)

    def add_meeting_transcript(
        self,
        meeting_id: str,
        speaker_id: str,
        speaker_name: str,
        text: str,
        start_time: float,
        end_time: float,
    ) -> Optional[str]:
        """Add transcript to meeting."""
        return self._meetings.add_transcript(
            meeting_id, speaker_id, speaker_name, text, start_time, end_time
        )

    # --- Digests ---

    def create_digest_template(
        self,
        name: str,
        description: str,
        sections: List[Dict[str, Any]],
        recipients: List[str],
        frequency: str = "daily",
        format: str = "markdown",
    ) -> str:
        """Create a digest template."""
        from .digest import DigestTemplate, DigestSection, ContentType, DigestFormat, DigestFrequency

        sections = [
            DigestSection(
                type=ContentType(s["type"]),
                title=s["title"],
                content=[],
                order=s.get("order", 0),
            )
            for s in sections
        ]

        template = DigestTemplate(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            sections=sections,
            format=DigestFormat(format),
            frequency=DigestFrequency(frequency),
            recipients=recipients,
        )

        return self._digests.create_template(template)

    def generate_digest(
        self,
        template_id: str,
        period_start: Optional[float] = None,
        period_end: Optional[float] = None,
    ) -> Optional[str]:
        """Generate a digest from a template."""
        digest = self._digests.generate_digest(template_id, period_start, period_end)
        return digest.id if digest else None

    def send_digest(self, digest_id: str) -> bool:
        """Send a generated digest."""
        digest = self._digests.get_digest(digest_id)
        if not digest:
            return False
        return self._digests.send_digest(digest)

    # --- Guest Access ---

    def create_guest_token(
        self,
        session_id: str,
        role: str,
        resource_type: str,
        resource_id: str,
        created_by: str,
        expires_in_hours: Optional[float] = None,
        max_uses: Optional[int] = None,
        resource_name: Optional[str] = None,
    ):
        """Create a guest access token."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        from .guest_access import GuestRole, ResourceType

        token = self._guest.create_token(
            role=role,
            resource_type=resource_type,
            resource_id=resource_id,
            created_by=created_by,
            expires_in_hours=expires_in_hours,
            max_uses=max_uses,
            resource_name=resource_name,
        )

        if token:
            session.guest_tokens.append(token.id)
            session.updated_at = time.time()

        return token

    # --- Conflict Resolution ---

    def open_conflict(
        self,
        session_id: str,
        title: str,
        description: str,
        type: str,
        parties: List[Dict[str, Any]],
        severity: Optional[str] = None,
        reported_by: str = "",
    ) -> Optional[str]:
        """Open a conflict."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        from .conflict_resolution import ConflictType, ConflictSeverity

        conflict_id = self._conflicts.open_conflict(
            title=title,
            description=description,
            type=type,
            parties=parties,
            severity=severity,
            reported_by=reported_by,
        )

        if conflict_id:
            session.conflicts.append(conflict_id)
            session.updated_at = time.time()

        return conflict_id

    def assign_mediator(self, conflict_id: str, mediator_id: str) -> bool:
        """Assign a mediator to a conflict."""
        return self._conflicts.assign_mediator(conflict_id, mediator_id)

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        agreed_actions: List[str],
    ) -> bool:
        """Resolve a conflict."""
        return self._conflicts.complete_mediation(conflict_id, resolution, agreed_actions)

    # --- Social Features ---

    def give_kudos(
        self,
        from_agent: str,
        to_agent: str,
        category: str,
        message: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """Give kudos to another agent."""
        from .social import KudosCategory

        kudos = self._social.give_kudos(
            from_agent=from_agent,
            to_agent=to_agent,
            category=KudosCategory(category),
            message=message,
            project_id=project_id,
        )
        return kudos.__dict__ if kudos else None

    def update_streak(self, agent_id: str, streak_type: str) -> Optional[Dict]:
        """Update a streak for an agent."""
        streak = self._social.update_streak(agent_id, streak_type)
        return streak.__dict__ if streak else None

    def award_achievement(
        self,
        agent_id: str,
        type: str,
        title: str,
        description: str,
        icon: str = "🏆",
    ) -> Optional[Dict]:
        """Award an achievement."""
        from .social import AchievementType

        achievement = self._social.award_achievement(
            agent_id=agent_id,
            type=type,
            title=title,
            description=description,
            icon=icon,
        )
        return achievement.__dict__ if achievement else None

    def record_velocity(
        self,
        team_id: str,
        completed_tasks: int,
        completed_story_points: int,
        cycle_times_hours: List[float],
        lead_times_hours: List[float],
        quality_metrics: Dict[str, float],
        collaboration_data: Dict[str, Any],
    ) -> Optional[Dict]:
        """Record team velocity."""
        velocity = self._social.record_team_velocity(
            team_id=team_id,
            completed_tasks=completed_tasks,
            completed_story_points=completed_story_points,
            cycle_times_hours=cycle_times_hours,
            lead_times_hours=lead_times_hours,
            quality_metrics=quality_metrics,
            collaboration_data=collaboration_data,
        )
        return velocity.__dict__ if velocity else None

    def get_leaderboard(self, metric: str = "kudos_received", limit: int = 10) -> List[Dict]:
        """Get leaderboard."""
        return self._social.get_leaderboard(metric, limit)

    # --- Session Management ---

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        return {
            "id": session.id,
            "project_id": session.project_id,
            "participants": session.participants,
            "status": session.status,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "counts": {
                "approvals": len(session.approval_requests),
                "pair_sessions": len(session.pair_sessions),
                "code_reviews": len(session.code_reviews),
                "handoffs": len(session.handoffs),
                "whiteboards": len(session.whiteboards),
                "meetings": len(session.meetings),
                "digests": len(session.digests),
                "guest_tokens": len(session.guest_tokens),
                "conflicts": len(session.conflicts),
            },
        }

    def list_sessions(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all collaboration sessions."""
        sessions = list(self._sessions.values())
        if project_id:
            sessions = [s for s in sessions if s.project_id == project_id]
        return [self.get_session_status(s.id) for s in sessions]


# Global instance
_collaboration_manager: Optional[CollaborationManager] = None


def get_collaboration_manager(config: Optional[CollaborationManagerConfig] = None) -> CollaborationManager:
    """Get global collaboration manager instance."""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = CollaborationManager(config)
    return _collaboration_manager