"""Approval gates: agent pauses for human ✅/❌ on sensitive steps."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    AUTO_APPROVED = "auto_approved"


class ApprovalPriority(str, Enum):
    """Priority levels for approval requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalType(str, Enum):
    """Types of approval requests."""
    DEPLOYMENT = "deployment"
    DATA_MIGRATION = "data_migration"
    SCHEMA_CHANGE = "schema_change"
    SECRETS_ACCESS = "secrets_access"
    PRODUCTION_CHANGE = "production_change"
    SECURITY_POLICY = "security_policy"
    BREAKING_CHANGE = "breaking_change"
    RESOURCE_ALLOCATION = "resource_allocation"
    CUSTOM = "custom"


@dataclass
class ApprovalRequest:
    """An approval request awaiting human decision."""
    id: str
    title: str
    description: str
    approval_type: ApprovalType
    priority: ApprovalPriority
    requester: str  # Agent ID or user ID
    required_approvers: List[str] = field(default_factory=list)  # User IDs or roles
    min_approvals: int = 1
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    decisions: List["ApprovalDecision"] = field(default_factory=list)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def can_decide(self, user_id: str) -> bool:
        if not self.required_approvers:
            return True
        return user_id in self.required_approvers

    def approval_count(self) -> int:
        return len([d for d in self.decisions if d.decision == "approve"])

    def rejection_count(self) -> int:
        return len([d for d in self.decisions if d.decision == "reject"])

    def is_complete(self) -> bool:
        if self.status != ApprovalStatus.PENDING:
            return True
        if self.is_expired():
            return True
        return self.approval_count() >= self.min_approvals


@dataclass
class ApprovalDecision:
    """A decision on an approval request."""
    request_id: str
    user_id: str
    decision: str  # approve, reject
    rationale: str = ""
    conditions: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ApprovalRule:
    """Rule for automatic approval routing."""
    id: str
    name: str
    conditions: Dict[str, Any]  # Match against request context
    required_approvers: List[str] = field(default_factory=list)
    min_approvals: int = 1
    priority: ApprovalPriority = ApprovalPriority.NORMAL
    timeout_hours: float = 24.0
    auto_approve_if: Optional[Dict[str, Any]] = None  # Conditions for auto-approval
    metadata: Dict[str, Any] = field(default_factory=dict)


class ApprovalConfig(BaseModel):
    """Configuration for approval gate."""
    default_timeout_hours: float = 24.0
    default_min_approvals: int = 1
    escalation_enabled: bool = True
    escalation_timeout_hours: float = 4.0
    escalation_contact: Optional[str] = None
    notification_webhook: Optional[str] = None
    auto_approve_low_risk: bool = False
    low_risk_threshold: float = 0.3
    rules: List[ApprovalRule] = Field(default_factory=list)


class ApprovalGate:
    """Manages approval gates for sensitive operations."""

    def __init__(
        self,
        config: Optional[ApprovalConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        risk_assessor: Optional[Callable[[Dict[str, Any]], float]] = None,
    ) -> None:
        self.config = config or ApprovalConfig()
        self.notifier = notifier
        self.risk_assessor = risk_assessor
        self._requests: Dict[str, ApprovalRequest] = {}
        self._user_requests: Dict[str, Set[str]] = {}  # user_id -> request_ids

    def request_approval(
        self,
        title: str,
        description: str,
        approval_type: ApprovalType,
        requester: str,
        context: Dict[str, Any],
        priority: Optional[ApprovalPriority] = None,
        required_approvers: Optional[List[str]] = None,
        min_approvals: Optional[int] = None,
        timeout_hours: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new approval request."""
        request_id = str(uuid.uuid4())[:8]

        # Check for auto-approval
        if self._should_auto_approve(context):
            return self._auto_approve(request_id, title, description, approval_type, requester, context)

        # Match rules
        rule = self._match_rule(context)
        approvers = required_approvers or (rule.required_approvers if rule else [])
        min_approvals = min_approvals or (rule.min_approvals if rule else self.config.default_min_approvals)
        priority = priority or (rule.priority if rule else ApprovalPriority.NORMAL)
        timeout = timeout_hours or (rule.timeout_hours if rule else self.config.default_timeout_hours)

        request = ApprovalRequest(
            id=request_id,
            title=title,
            description=description,
            approval_type=approval_type,
            priority=priority,
            requester=requester,
            required_approvers=approvers,
            min_approvals=min_approvals,
            context=context,
            metadata=metadata or {},
            expires_at=time.time() + timeout * 3600,
        )

        self._requests[request_id] = request
        for approver in approvers:
            self._user_requests.setdefault(approver, set()).add(request_id)

        # Notify approvers
        self._notify_approvers(request)

        # Schedule expiration check
        # In production, this would use a proper scheduler

        return request_id

    def _should_auto_approve(self, context: Dict[str, Any]) -> bool:
        """Check if request should be auto-approved."""
        if not self.config.auto_approve_low_risk:
            return False

        if self.risk_assessor:
            risk = self.risk_assessor(context)
            return risk <= self.config.low_risk_threshold

        return False

    def _auto_approve(
        self,
        request_id: str,
        title: str,
        description: str,
        approval_type: ApprovalType,
        requester: str,
        context: Dict[str, Any],
    ) -> str:
        """Auto-approve a request."""
        request = ApprovalRequest(
            id=request_id,
            title=title,
            description=description,
            approval_type=approval_type,
            priority=ApprovalPriority.LOW,
            requester=requester,
            context=context,
            status=ApprovalStatus.AUTO_APPROVED,
        )
        self._requests[request_id] = request
        return request_id

    def _match_rule(self, context: Dict[str, Any]) -> Optional[ApprovalRule]:
        """Match context to an approval rule."""
        for rule in self.config.rules:
            match = True
            for key, value in rule.conditions.items():
                if key not in context or context[key] != value:
                    match = False
                    break
            if match:
                return rule
        return None

    def decide(
        self,
        request_id: str,
        user_id: str,
        decision: str,  # approve, reject
        rationale: str = "",
        conditions: Optional[List[str]] = None,
    ) -> bool:
        """Record a decision on an approval request."""
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.status != ApprovalStatus.PENDING:
            return False

        if not request.can_decide(user_id):
            return False

        approval_decision = ApprovalDecision(
            request_id=request_id,
            user_id=user_id,
            decision=decision,
            rationale=rationale,
            conditions=conditions or [],
        )
        request.decisions.append(approval_decision)

        # Update status
        if decision == "reject":
            request.status = ApprovalStatus.REJECTED
        elif request.is_complete():
            request.status = ApprovalStatus.APPROVED

        # Notify requester
        self._notify_requester(request, decision)

        return True

    def cancel(self, request_id: str, user_id: str) -> bool:
        """Cancel an approval request."""
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.requester != user_id and not request.can_decide(user_id):
            return False

        request.status = ApprovalStatus.CANCELLED
        return True

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        return self._requests.get(request_id)

    def get_pending_for_user(self, user_id: str) -> List[ApprovalRequest]:
        """Get all pending requests for a user."""
        request_ids = self._user_requests.get(user_id, set())
        return [
            self._requests[rid] for rid in request_ids
            if rid in self._requests and self._requests[rid].status == ApprovalStatus.PENDING
        ]

    def get_requests_by_requester(self, requester: str) -> List[ApprovalRequest]:
        """Get all requests by a requester."""
        return [r for r in self._requests.values() if r.requester == requester]

    def cleanup_expired(self) -> int:
        """Clean up expired requests."""
        expired = []
        for request_id, request in self._requests.items():
            if request.status == ApprovalStatus.PENDING and request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                expired.append(request_id)

        for rid in expired:
            request = self._requests.get(rid)
            if request:
                self._notify_requester(request, "expired")

        return len(expired)

    def add_rule(self, rule: ApprovalRule) -> None:
        """Add an approval routing rule."""
        self.config.rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an approval rule."""
        for i, rule in enumerate(self.config.rules):
            if rule.id == rule_id:
                self.config.rules.pop(i)
                return True
        return False

    def _notify_approvers(self, request: ApprovalRequest) -> None:
        """Notify approvers of new request."""
        if not self.notifier:
            return

        for approver in request.required_approvers:
            try:
                self.notifier(
                    approver,
                    "approval_request",
                    {
                        "request_id": request.id,
                        "title": request.title,
                        "description": request.description,
                        "type": request.approval_type.value,
                        "priority": request.priority.value,
                        "expires_at": request.expires_at,
                    },
                )
            except Exception:
                pass

    def _notify_requester(self, request: ApprovalRequest, decision: str) -> None:
        """Notify requester of decision."""
        if not self.notifier:
            return

        try:
            self.notifier(
                request.requester,
                "approval_decision",
                {
                    "request_id": request.id,
                    "title": request.title,
                    "decision": decision,
                    "approval_count": request.approval_count(),
                    "rejection_count": request.rejection_count(),
                },
            )
        except Exception:
            pass


# Global instance
_approval_gate: Optional[ApprovalGate] = None


def get_approval_gate(config: Optional[ApprovalConfig] = None) -> ApprovalGate:
    """Get global approval gate instance."""
    global _approval_gate
    if _approval_gate is None:
        _approval_gate = ApprovalGate(config)
    return _approval_gate