"""Pair programming mode: human + agent share terminal + editor."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class PairRole(str, Enum):
    """Roles in a pair programming session."""
    DRIVER = "driver"      # Controls keyboard/mouse
    NAVIGATOR = "navigator"  # Reviews, guides, thinks ahead
    OBSERVER = "observer"  # Watches only


class SessionStatus(str, Enum):
    """Status of pair session."""
    WAITING = "waiting"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


@dataclass
class PairParticipant:
    """A participant in a pair session."""
    user_id: str
    name: str
    role: PairRole
    joined_at: float = field(default_factory=time.time)
    is_agent: bool = False
    capabilities: List[str] = field(default_factory=list)  # e.g., "terminal", "editor", "voice"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PairSession:
    """A pair programming session."""
    id: str
    title: str
    participants: List[PairParticipant] = field(default_factory=list)
    status: SessionStatus = SessionStatus.WAITING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    current_driver: Optional[str] = None  # user_id
    shared_resources: Dict[str, Any] = field(default_factory=dict)  # terminal, editor, etc.
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_participant(self, user_id: str) -> Optional[PairParticipant]:
        return next((p for p in self.participants if p.user_id == user_id), None)

    def get_driver(self) -> Optional[PairParticipant]:
        if self.current_driver:
            return self.get_participant(self.current_driver)
        return None

    def get_navigator(self) -> Optional[PairParticipant]:
        for p in self.participants:
            if p.role == PairRole.NAVIGATOR:
                return p
        return None

    def is_active(self) -> bool:
        return self.status == SessionStatus.ACTIVE


class PairConfig(BaseModel):
    """Configuration for pair programming."""
    max_participants: int = 3
    allow_role_swap: bool = True
    auto_assign_roles: bool = True
    session_timeout_minutes: float = 120.0
    activity_tracking: bool = True
    recording_enabled: bool = False
    shared_terminal: bool = True
    shared_editor: bool = True
    voice_enabled: bool = False


class PairSessionManager:
    """Manages pair programming sessions."""

    def __init__(
        self,
        config: Optional[PairConfig] = None,
        terminal_provider: Optional[Callable[[str], Any]] = None,
        editor_provider: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self.config = config or PairConfig()
        self.terminal_provider = terminal_provider
        self.editor_provider = editor_provider
        self._sessions: Dict[str, PairSession] = {}
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids

    def create_session(
        self,
        title: str,
        creator_id: str,
        creator_name: str,
        is_agent: bool = False,
    ) -> str:
        """Create a new pair programming session."""
        session_id = str(uuid.uuid4())[:8]

        creator = PairParticipant(
            user_id=creator_id,
            name=creator_name,
            role=PairRole.DRIVER if self.config.auto_assign_roles else PairRole.NAVIGATOR,
            is_agent=is_agent,
            capabilities=["terminal", "editor"] + (["voice"] if False else []),
        )

        session = PairSession(
            id=session_id,
            title=title,
            participants=[creator],
            status=SessionStatus.WAITING,
        )

        self._sessions[session_id] = session
        self._user_sessions.setdefault(creator_id, set()).add(session_id)

        return session_id

    def join_session(
        self,
        session_id: str,
        user_id: str,
        name: str,
        preferred_role: Optional[PairRole] = None,
        is_agent: bool = False,
    ) -> bool:
        """Join an existing session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.status != SessionStatus.WAITING and session.status != SessionStatus.ACTIVE:
            return False

        if len(session.participants) >= self.config.max_participants:
            return False

        if session.get_participant(user_id):
            return True  # Already in session

        # Determine role
        if preferred_role:
            role = preferred_role
        else:
            # Auto-assign: if no navigator, become navigator
            has_navigator = any(p.role == PairRole.NAVIGATOR for p in session.participants)
            role = PairRole.NAVIGATOR if not has_navigator else PairRole.OBSERVER

        participant = PairParticipant(
            user_id=user_id,
            name=name,
            role=role,
            is_agent=is_agent,
            capabilities=["terminal", "editor"] + (["voice"] if False else []),
        )

        session.participants.append(participant)
        self._user_sessions.setdefault(user_id, set()).add(session_id)

        # Initialize shared resources
        if self.config.shared_terminal and self.terminal_provider:
            session.shared_resources["terminal"] = self.terminal_provider(session_id)

        if self.config.shared_editor and self.editor_provider:
            session.shared_resources["editor"] = self.editor_provider(session_id)

        # Log activity
        session.activity_log.append({
            "type": "join",
            "user_id": user_id,
            "timestamp": time.time(),
        })

        return True

    def leave_session(self, session_id: str, user_id: str) -> bool:
        """Leave a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        participant = session.get_participant(user_id)
        if not participant:
            return False

        # If driver leaves, reassign
        if session.current_driver == user_id:
            self._reassign_driver(session, user_id)

        session.participants = [p for p in session.participants if p.user_id != user_id]
        self._user_sessions.get(user_id, set()).discard(session_id)

        session.activity_log.append({
            "type": "leave",
            "user_id": user_id,
            "timestamp": time.time(),
        })

        # End session if no participants
        if not session.participants:
            self.end_session(session_id)

        return True

    def start_session(self, session_id: str) -> bool:
        """Start a waiting session."""
        session = self._sessions.get(session_id)
        if not session or session.status != SessionStatus.WAITING:
            return False

        session.status = SessionStatus.ACTIVE
        session.started_at = time.time()

        # Assign initial driver if not set
        if not session.current_driver and session.participants:
            session.current_driver = session.participants[0].user_id

        return True

    def pause_session(self, session_id: str) -> bool:
        """Pause an active session."""
        session = self._sessions.get(session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            return False

        session.status = SessionStatus.PAUSED
        return True

    def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        session = self._sessions.get(session_id)
        if not session or session.status != SessionStatus.PAUSED:
            return False

        session.status = SessionStatus.ACTIVE
        return True

    def end_session(self, session_id: str) -> bool:
        """End a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.status = SessionStatus.ENDED
        session.ended_at = time.time()

        # Clean up user sessions
        for participant in session.participants:
            self._user_sessions.get(participant.user_id, set()).discard(session_id)

        return True

    def swap_roles(self, session_id: str, user_id: str, new_role: PairRole) -> bool:
        """Request a role swap."""
        session = self._sessions.get(session_id)
        if not session or not session.is_active():
            return False

        participant = session.get_participant(user_id)
        if not participant:
            return False

        if not self.config.allow_role_swap:
            return False

        # Handle driver/navigator swap
        if new_role == PairRole.DRIVER and session.current_driver != user_id:
            # Request to become driver
            current_driver = session.get_driver()
            if current_driver and current_driver.role == PairRole.DRIVER:
                # Swap roles
                current_driver.role = PairRole.NAVIGATOR
                participant.role = PairRole.DRIVER
                session.current_driver = user_id

                session.activity_log.append({
                    "type": "role_swap",
                    "from": current_driver.user_id,
                    "to": user_id,
                    "timestamp": time.time(),
                })
                return True
        elif new_role == PairRole.NAVIGATOR and participant.role == PairRole.DRIVER:
            # Driver giving up control
            navigator = session.get_navigator()
            if navigator:
                navigator.role = PairRole.DRIVER
                participant.role = PairRole.NAVIGATOR
                session.current_driver = navigator.user_id

                session.activity_log.append({
                    "type": "role_swap",
                    "from": user_id,
                    "to": navigator.user_id,
                    "timestamp": time.time(),
                })
                return True
        else:
            participant.role = new_role
            return True

        return False

    def _reassign_driver(self, session: PairSession, leaving_user: str) -> None:
        """Reassign driver when current driver leaves."""
        # Prefer navigator, then first available
        navigator = session.get_navigator()
        if navigator and navigator.user_id != leaving_user:
            navigator.role = PairRole.DRIVER
            session.current_driver = navigator.user_id
        else:
            # Find first non-leaving participant
            for p in session.participants:
                if p.user_id != leaving_user:
                    p.role = PairRole.DRIVER
                    session.current_driver = p.user_id
                    break

    def log_activity(
        self,
        session_id: str,
        user_id: str,
        activity_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """Log activity in session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.activity_log.append({
            "type": activity_type,
            "user_id": user_id,
            "data": data,
            "timestamp": time.time(),
        })
        return True

    def get_session(self, session_id: str) -> Optional[PairSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> List[PairSession]:
        """Get all sessions for a user."""
        session_ids = self._user_sessions.get(user_id, set())
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def get_active_sessions(self) -> List[PairSession]:
        """Get all active sessions."""
        return [s for s in self._sessions.values() if s.is_active()]

    def cleanup_inactive(self, timeout_minutes: Optional[float] = None) -> int:
        """Clean up inactive sessions."""
        timeout = timeout_minutes or self.config.session_timeout_minutes
        cutoff = time.time() - timeout * 60

        ended = 0
        for session in list(self._sessions.values()):
            if session.status == SessionStatus.ACTIVE and session.started_at:
                if session.started_at < cutoff:
                    self.end_session(session.id)
                    ended += 1
        return ended


# Global instance
_pair_session_manager: Optional[PairSessionManager] = None


def get_pair_session(config: Optional[PairConfig] = None) -> PairSessionManager:
    """Get global pair session manager instance."""
    global _pair_session_manager
    if _pair_session_manager is None:
        _pair_session_manager = PairSessionManager(config)
    return _pair_session_manager