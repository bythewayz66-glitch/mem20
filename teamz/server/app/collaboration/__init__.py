"""Collaboration & Human-in-the-Loop subsystem for Phase 12."""

from .approvals import ApprovalGate, ApprovalConfig, ApprovalRequest, ApprovalDecision, get_approval_gate
from .pair_programming import PairSession, PairConfig, PairRole, get_pair_session
from .code_review import CodeReview, ReviewConfig, ReviewComment, ReviewDecision, get_code_review
from .handoff import HandoffManager, HandoffConfig, HandoffStatus, get_handoff_manager
from .whiteboard import WhiteboardScene, WhiteboardConfig, WhiteboardElement, get_whiteboard
from .meeting_agent import MeetingAgent, MeetingConfig, TranscriptSegment, get_meeting_agent
from .digest import DigestGenerator, DigestConfig, DigestTemplate, get_digest_generator
from .guest_access import GuestAccessManager, GuestConfig, GuestToken, get_guest_access
from .conflict_resolution import ConflictResolver, ConflictConfig, Conflict, get_conflict_resolver
from .social import SocialFeatures, SocialConfig, Kudos, Streak, get_social_features
from .manager import CollaborationManager, CollaborationManagerConfig, get_collaboration_manager

__all__ = [
    "ApprovalGate", "ApprovalConfig", "ApprovalRequest", "ApprovalDecision", "get_approval_gate",
    "PairSession", "PairConfig", "PairRole", "get_pair_session",
    "CodeReview", "ReviewConfig", "ReviewComment", "ReviewDecision", "get_code_review",
    "HandoffManager", "HandoffConfig", "HandoffStatus", "get_handoff_manager",
    "WhiteboardScene", "WhiteboardConfig", "WhiteboardElement", "get_whiteboard",
    "MeetingAgent", "MeetingConfig", "TranscriptSegment", "get_meeting_agent",
    "DigestGenerator", "DigestConfig", "DigestTemplate", "get_digest_generator",
    "GuestAccessManager", "GuestConfig", "GuestToken", "get_guest_access",
    "ConflictResolver", "ConflictConfig", "Conflict", "get_conflict_resolver",
    "SocialFeatures", "SocialConfig", "Kudos", "Streak", "get_social_features",
    "CollaborationManager", "CollaborationManagerConfig", "get_collaboration_manager",
]