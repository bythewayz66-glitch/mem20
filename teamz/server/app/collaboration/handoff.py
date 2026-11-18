"""Voice/chat handoff: "take over" / "resume autonomous"."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class HandoffType(str, Enum):
    """Types of handoff."""
    HUMAN_TO_AGENT = "human_to_agent"      # Human hands off to agent
    AGENT_TO_HUMAN = "agent_to_human"      # Agent hands off to human
    AGENT_TO_AGENT = "agent_to_agent"      # Agent to agent (escalation)
    HUMAN_TO_HUMAN = "human_to_human"      # Human to human (escalation)


class HandoffStatus(str, Enum):
    """Handoff status."""
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class HandoffReason(str, Enum):
    """Reasons for handoff."""
    COMPLEXITY = "complexity"              # Task too complex
    PERMISSION = "permission"              # Need human permission
    UNCERTAINTY = "uncertainty"            # Agent uncertain
    ERROR = "error"                        # Error occurred
    POLICY = "policy"                      # Policy requires human
    USER_REQUEST = "user_request"          # User asked for handoff
    ESCALATION = "escalation"              # Escalation needed
    COMPLETION = "completion"              # Task complete, handoff back


@dataclass
class HandoffContext:
    """Context transferred during handoff."""
    goal: str
    current_state: Dict[str, Any]
    completed_steps: List[Dict[str, Any]]
    pending_steps: List[Dict[str, Any]]
    key_decisions: List[str] = field(default_factory=list)
    assumptions: Dict[str, Any] = field(default_factory=dict)
    blockers: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HandoffRequest:
    """A handoff request."""
    id: str
    type: HandoffType
    reason: HandoffReason
    from_party: str  # user_id or agent_id
    to_party: str  # user_id or agent_id
    context: HandoffContext
    message: str = ""
    priority: int = 0  # 0=normal, 1=high, 2=critical
    status: HandoffStatus = HandoffStatus.REQUESTED
    requested_at: float = field(default_factory=time.time)
    responded_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoffResponse:
    """Response to a handoff request."""
    request_id: str
    accepted: bool
    responder: str
    message: str = ""
    conditions: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class HandoffConfig(BaseModel):
    """Configuration for handoff manager."""
    default_timeout_seconds: float = 60.0
    auto_accept_if_idle: bool = True
    idle_threshold_seconds: float = 300.0
    require_acknowledgment: bool = True
    transfer_conversation_history: bool = True
    max_history_items: int = 50
    notification_webhook: Optional[str] = None


class HandoffManager:
    """Manages handoffs between human and agent."""

    def __init__(
        self,
        config: Optional[HandoffConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        state_serializer: Optional[Callable[[Any], str]] = None,
        state_deserializer: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self.config = config or HandoffConfig()
        self.notifier = notifier
        self.state_serializer = state_serializer or (lambda x: json.dumps(x))
        self.state_deserializer = state_deserializer or (lambda x: json.loads(x))
        self._requests: Dict[str, HandoffRequest] = {}
        self._active_handoffs: Dict[str, HandoffRequest] = {}  # Current active handoffs

    def request_handoff(
        self,
        type: HandoffType,
        reason: HandoffReason,
        from_party: str,
        to_party: str,
        context: HandoffContext,
        message: str = "",
        priority: int = 0,
    ) -> str:
        """Request a handoff."""
        request_id = str(uuid.uuid4())[:8]

        request = HandoffRequest(
            id=request_id,
            type=type,
            reason=reason,
            from_party=from_party,
            to_party=to_party,
            context=context,
            message=message,
            priority=priority,
            status=HandoffStatus.REQUESTED,
        )

        self._requests[request_id] = request
        self._active_handoffs[to_party] = request

        # Notify target party
        self._notify_party(to_party, "handoff_requested", {
            "request_id": request_id,
            "type": type.value,
            "reason": reason.value,
            "from": from_party,
            "context_summary": self._summarize_context(context),
            "message": message,
            "priority": priority,
        })

        return request_id

    def respond(
        self,
        request_id: str,
        responder: str,
        accepted: bool,
        message: str = "",
        conditions: Optional[List[str]] = None,
    ) -> bool:
        """Respond to a handoff request."""
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.to_party != responder:
            return False

        if request.status != HandoffStatus.REQUESTED:
            return False

        response = HandoffResponse(
            request_id=request_id,
            accepted=accepted,
            responder=responder,
            message=message,
            conditions=conditions or [],
        )

        if accepted:
            request.status = HandoffStatus.ACCEPTED
            request.responded_at = time.time()
            request.status = HandoffStatus.IN_PROGRESS

            # Transfer context
            self._transfer_context(request)

            # Notify both parties
            self._notify_party(request.from_party, "handoff_accepted", {
                "request_id": request_id,
                "to": responder,
                "message": message,
            })
            self._notify_party(responder, "handoff_started", {
                "request_id": request_id,
                "from": request.from_party,
                "context": self._serialize_context(request.context),
            })
        else:
            request.status = HandoffStatus.DECLINED
            request.responded_at = time.time()

            self._notify_party(request.from_party, "handoff_declined", {
                "request_id": request_id,
                "reason": message,
            })

        return True

    def complete_handoff(
        self,
        request_id: str,
        completer: str,
        summary: str = "",
        next_steps: Optional[List[str]] = None,
    ) -> bool:
        """Complete a handoff."""
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.status != HandoffStatus.IN_PROGRESS:
            return False

        request.status = HandoffStatus.COMPLETED
        request.completed_at = time.time()
        request.metadata["completion_summary"] = summary
        request.metadata["next_steps"] = next_steps or []

        # Remove from active
        self._active_handoffs.pop(request.to_party, None)

        # Notify both parties
        self._notify_party(request.from_party, "handoff_completed", {
            "request_id": request_id,
            "completed_by": completer,
            "summary": summary,
            "next_steps": next_steps or [],
        })
        self._notify_party(completer, "handoff_completed", {
            "request_id": request_id,
            "summary": summary,
        })

        return True

    def cancel_handoff(self, request_id: str, canceller: str) -> bool:
        """Cancel a handoff."""
        request = self._requests.get(request_id)
        if not request:
            return False

        if canceller not in (request.from_party, request.to_party):
            return False

        request.status = HandoffStatus.CANCELLED

        # Notify both parties
        self._notify_party(request.from_party, "handoff_cancelled", {
            "request_id": request_id,
            "cancelled_by": canceller,
        })
        self._notify_party(request.to_party, "handoff_cancelled", {
            "request_id": request_id,
            "cancelled_by": canceller,
        })

        self._active_handoffs.pop(request.to_party, None)
        return True

    def get_active_handoff(self, party: str) -> Optional[HandoffRequest]:
        """Get active handoff for a party."""
        return self._active_handoffs.get(party)

    def get_pending_requests(self, party: str) -> List[HandoffRequest]:
        """Get pending handoff requests for a party."""
        return [
            r for r in self._requests.values()
            if r.to_party == party and r.status == HandoffStatus.REQUESTED
        ]

    def get_handoff_history(
        self,
        party: str,
        limit: int = 50,
    ) -> List[HandoffRequest]:
        """Get handoff history for a party."""
        history = [
            r for r in self._requests.values()
            if r.from_party == party or r.to_party == party
        ]
        history.sort(key=lambda r: r.requested_at, reverse=True)
        return history[:limit]

    def _transfer_context(self, request: HandoffRequest) -> None:
        """Transfer context to receiving party."""
        # In a real implementation, this would:
        # 1. Serialize context
        # 2. Transfer to receiving party's context store
        # 3. Initialize their state
        pass

    def _serialize_context(self, context: HandoffContext) -> Dict[str, Any]:
        """Serialize context for transfer."""
        return {
            "goal": context.goal,
            "current_state": context.current_state,
            "completed_steps": context.completed_steps,
            "pending_steps": context.pending_steps,
            "key_decisions": context.key_decisions,
            "assumptions": context.assumptions,
            "blockers": context.blockers,
            "artifacts": context.artifacts,
            "conversation_history": context.conversation_history[-self.config.max_history_items:],
        }

    def _summarize_context(self, context: HandoffContext) -> str:
        """Create a brief summary of context."""
        return (
            f"Goal: {context.goal[:100]}... "
            f"Steps done: {len(context.completed_steps)}, "
            f"Pending: {len(context.pending_steps)}, "
            f"Blockers: {len(context.blockers)}"
        )

    def _notify_party(self, party: str, event: str, data: Dict[str, Any]) -> None:
        """Notify a party of an event."""
        if not self.notifier:
            return

        try:
            self.notifier(party, event, data)
        except Exception:
            pass


# Global instance
_handoff_manager: Optional[HandoffManager] = None


def get_handoff_manager(config: Optional[HandoffConfig] = None) -> HandoffManager:
    """Get global handoff manager instance."""
    global _handoff_manager
    if _handoff_manager is None:
        _handoff_manager = HandoffManager(config)
    return _handoff_manager