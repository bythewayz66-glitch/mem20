"""Conflict resolution: two agents disagree → mediator agent."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class ConflictType(str, Enum):
    """Types of conflicts."""
    TECHNICAL = "technical"          # Technical disagreement
    ARCHITECTURAL = "architectural"  # Architecture decision
    PRIORITY = "priority"            # Priority conflict
    RESOURCE = "resource"            # Resource allocation
    PROCESS = "process"              # Process disagreement
    SCOPE = "scope"                  # Scope creep/definition
    PERSONAL = "personal"            # Interpersonal
    STRATEGIC = "strategic"          # Strategic direction


class ConflictSeverity(str, Enum):
    """Conflict severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(str, Enum):
    """Conflict resolution status."""
    OPEN = "open"
    MEDIATING = "mediating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    STALLED = "stalled"
    WITHDRAWN = "withdrawn"


class ResolutionStrategy(str, Enum):
    """Strategies for conflict resolution."""
    MEDIATION = "mediation"              # Facilitated discussion
    CONSENSUS = "consensus"              # All parties agree
    COMPROMISE = "compromise"            # Each side gives up something
    AUTHORITY = "authority"              # Decision by authority
    VOTING = "voting"                    # Democratic vote
    DEFER = "defer"                      # Defer to later
    EXPERT = "expert"                    # Expert opinion


@dataclass
class ConflictParty:
    """A party in a conflict."""
    agent_id: str
    name: str
    position: str  # Their stance
    interests: List[str] = field(default_factory=list)  # Underlying needs
    concerns: List[str] = field(default_factory=list)
    proposed_solution: Optional[str] = None
    willingness_to_compromise: float = 0.5  # 0-1


@dataclass
class Conflict:
    """A conflict between parties."""
    id: str
    title: str
    description: str
    type: ConflictType
    severity: ConflictSeverity
    parties: List[ConflictParty] = field(default_factory=list)
    status: ConflictStatus = ConflictStatus.OPEN
    mediator_id: Optional[str] = None
    strategy: Optional[ResolutionStrategy] = None
    resolution: Optional[str] = None
    agreed_actions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MediationSession:
    """A mediation session."""
    id: str
    conflict_id: str
    mediator_id: str
    participants: List[str] = field(default_factory=list)
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    agenda: List[str] = field(default_factory=list)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)


class ConflictConfig(BaseModel):
    """Configuration for conflict resolution."""
    auto_assign_mediator: bool = True
    mediator_pool: List[str] = Field(default_factory=list)
    default_severity: ConflictSeverity = ConflictSeverity.MEDIUM
    escalation_threshold_hours: float = 24.0
    max_mediation_sessions: int = 5
    auto_escalate_on_stall: bool = True
    stall_threshold_hours: float = 48.0
    notification_webhook: Optional[str] = None


class ConflictResolver:
    """Resolves conflicts between agents through mediation."""

    def __init__(
        self,
        config: Optional[ConflictConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        mediator_selector: Optional[Callable[[Conflict], Optional[str]]] = None,
    ) -> None:
        self.config = config or ConflictConfig()
        self.notifier = notifier
        self.mediator_selector = mediator_selector or self._default_mediator_selector
        self._conflicts: Dict[str, Conflict] = {}
        self._mediation_sessions: Dict[str, MediationSession] = {}
        self._agent_conflicts: Dict[str, Set[str]] = {}  # agent_id -> conflict_ids

    def _default_mediator_selector(self, conflict: Conflict) -> Optional[str]:
        """Select a mediator for a conflict."""
        if self.config.mediator_pool:
            # Simple round-robin or based on expertise
            return self.config.mediator_pool[0]
        return None

    def open_conflict(
        self,
        title: str,
        description: str,
        type: ConflictType,
        parties: List[Dict[str, Any]],  # {agent_id, name, position, interests, concerns}
        severity: Optional[ConflictSeverity] = None,
        reported_by: str = "",
    ) -> str:
        """Open a new conflict."""
        conflict_id = str(uuid.uuid4())[:8]

        conflict_parties = []
        for p in parties:
            conflict_parties.append(ConflictParty(
                agent_id=p["agent_id"],
                name=p.get("name", p["agent_id"]),
                position=p["position"],
                interests=p.get("interests", []),
                concerns=p.get("concerns", []),
            ))

        conflict = Conflict(
            id=conflict_id,
            title=title,
            description=description,
            type=type,
            severity=severity or self.config.default_severity,
            parties=conflict_parties,
            metadata={"reported_by": reported_by},
        )

        self._conflicts[conflict_id] = conflict

        for party in conflict_parties:
            self._agent_conflicts.setdefault(party.agent_id, set()).add(conflict_id)

        # Notify parties
        self._notify_parties(conflict, "conflict_opened", {
            "conflict_id": conflict_id,
            "title": title,
            "type": type.value,
            "severity": severity.value if severity else "medium",
        })

        # Auto-assign mediator if enabled
        if self.config.auto_assign_mediator:
            mediator = self.mediator_selector(conflict)
            if mediator:
                self.assign_mediator(conflict_id, mediator)

        return conflict_id

    def assign_mediator(self, conflict_id: str, mediator_id: str) -> bool:
        """Assign a mediator to a conflict."""
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return False

        conflict.mediator_id = mediator_id
        conflict.status = ConflictStatus.MEDIATING
        conflict.updated_at = time.time()

        # Notify mediator and parties
        self._notify_agent(mediator_id, "assigned_mediator", {
            "conflict_id": conflict_id,
            "title": conflict.title,
        })

        self._notify_parties(conflict, "mediator_assigned", {
            "conflict_id": conflict_id,
            "mediator": mediator_id,
        })

        return True

    def schedule_mediation(
        self,
        conflict_id: str,
        scheduled_at: float,
        agenda: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Schedule a mediation session."""
        conflict = self._conflicts.get(conflict_id)
        if not conflict or not conflict.mediator_id:
            return None

        session_id = str(uuid.uuid4())[:8]

        session = MediationSession(
            id=session_id,
            conflict_id=conflict_id,
            mediator_id=conflict.mediator_id,
            participants=[p.agent_id for p in conflict.parties],
            scheduled_at=scheduled_at,
            agenda=agenda or [
                "Opening statements",
                "Each party presents position",
                "Identify shared interests",
                "Explore options",
                "Agree on resolution",
            ],
        )

        self._mediation_sessions[session_id] = session

        # Notify participants
        for participant_id in session.participants:
            self._notify_agent(participant_id, "mediation_scheduled", {
                "session_id": session_id,
                "conflict_id": conflict_id,
                "scheduled_at": scheduled_at,
                "agenda": session.agenda,
            })

        return session_id

    def conduct_mediation(
        self,
        session_id: str,
        notes: List[Dict[str, Any]],
    ) -> bool:
        """Record mediation session outcomes."""
        session = self._mediation_sessions.get(session_id)
        if not session:
            return False

        session.status = "in_progress"
        session.started_at = time.time()
        session.notes = notes

        # Extract outcomes from notes
        for note in notes:
            if note.get("type") == "outcome":
                session.outcomes.append(note.get("content", ""))

        return True

    def complete_mediation(
        self,
        session_id: str,
        resolution: str,
        agreed_actions: List[str],
    ) -> bool:
        """Complete a mediation session with resolution."""
        session = self._mediation_sessions.get(session_id)
        if not session:
            return False

        conflict = self._conflicts.get(session.conflict_id)
        if not conflict:
            return False

        session.status = "completed"
        session.ended_at = time.time()

        # Update conflict
        conflict.resolution = resolution
        conflict.agreed_actions = agreed_actions
        conflict.status = ConflictStatus.RESOLVED
        conflict.resolved_at = time.time()
        conflict.updated_at = time.time()

        # Notify all parties
        self._notify_parties(conflict, "conflict_resolved", {
            "conflict_id": conflict.id,
            "resolution": resolution,
            "actions": agreed_actions,
        })

        return True

    def escalate_conflict(self, conflict_id: str, escalated_by: str, reason: str) -> bool:
        """Escalate a conflict to higher authority."""
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return False

        conflict.status = ConflictStatus.ESCALATED
        conflict.updated_at = time.time()
        conflict.metadata["escalation"] = {
            "escalated_by": escalated_by,
            "reason": reason,
            "timestamp": time.time(),
        }

        # Notify parties
        self._notify_parties(conflict, "conflict_escalated", {
            "conflict_id": conflict_id,
            "reason": reason,
        })

        return True

    def add_position(
        self,
        conflict_id: str,
        agent_id: str,
        position: str,
        interests: Optional[List[str]] = None,
        concerns: Optional[List[str]] = None,
        proposed_solution: Optional[str] = None,
    ) -> bool:
        """Add or update a party's position."""
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return False

        party = next((p for p in conflict.parties if p.agent_id == agent_id), None)
        if not party:
            return False

        party.position = position
        if interests:
            party.interests = interests
        if concerns:
            party.concerns = concerns
        if proposed_solution:
            party.proposed_solution = proposed_solution

        conflict.updated_at = time.time()
        return True

    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        """Get a conflict by ID."""
        return self._conflicts.get(conflict_id)

    def get_conflicts_for_agent(self, agent_id: str) -> List[Conflict]:
        """Get all conflicts for an agent."""
        conflict_ids = self._agent_conflicts.get(agent_id, set())
        return [self._conflicts[cid] for cid in conflict_ids if cid in self._conflicts]

    def get_open_conflicts(self, mediator_id: Optional[str] = None) -> List[Conflict]:
        """Get open conflicts, optionally filtered by mediator."""
        conflicts = [
            c for c in self._conflicts.values()
            if c.status in (ConflictStatus.OPEN, ConflictStatus.MEDIATING)
        ]
        if mediator_id:
            conflicts = [c for c in conflicts if c.mediator_id == mediator_id]
        return conflicts

    def get_mediation_session(self, session_id: str) -> Optional[MediationSession]:
        """Get a mediation session."""
        return self._mediation_sessions.get(session_id)

    def check_stalled_conflicts(self) -> List[Conflict]:
        """Check for stalled conflicts that need attention."""
        stalled = []
        cutoff = time.time() - self.config.stall_threshold_hours * 3600

        for conflict in self._conflicts.values():
            if conflict.status in (ConflictStatus.OPEN, ConflictStatus.MEDIATING):
                if conflict.updated_at < cutoff:
                    conflict.status = ConflictStatus.STALLED
                    stalled.append(conflict)

                    if self.config.auto_escalate_on_stall:
                        self.escalate_conflict(conflict.id, "system", "Conflict stalled")

        return stalled

    def _notify_parties(self, conflict: Conflict, event: str, data: Dict[str, Any]) -> None:
        """Notify all parties in a conflict."""
        if not self.notifier:
            return

        for party in conflict.parties:
            self._notify_agent(party.agent_id, event, data)

    def _notify_agent(self, agent_id: str, event: str, data: Dict[str, Any]) -> None:
        """Notify an agent of an event."""
        if not self.notifier:
            return

        try:
            self.notifier(agent_id, event, data)
        except Exception:
            pass


# Global instance
_conflict_resolver: Optional[ConflictResolver] = None


def get_conflict_resolver(config: Optional[ConflictConfig] = None) -> ConflictResolver:
    """Get global conflict resolver instance."""
    global _conflict_resolver
    if _conflict_resolver is None:
        _conflict_resolver = ConflictResolver(config)
    return _conflict_resolver