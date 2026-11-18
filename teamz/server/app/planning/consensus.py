"""Multi-agent consensus for high-stakes decisions."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ConsensusStatus(str, Enum):
    """Consensus process status."""
    PROPOSED = "proposed"
    VOTING = "voting"
    REACHED = "reached"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"


class VoteType(str, Enum):
    """Types of votes."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    CONDITIONAL = "conditional"  # Approve with conditions


class DecisionType(str, Enum):
    """Types of decisions requiring consensus."""
    DEPLOYMENT = "deployment"
    ARCHITECTURE_CHANGE = "architecture_change"
    SECURITY_POLICY = "security_policy"
    DATA_MIGRATION = "data_migration"
    BREAKING_CHANGE = "breaking_change"
    RESOURCE_ALLOCATION = "resource_allocation"
    INCIDENT_RESPONSE = "incident_response"
    CUSTOM = "custom"


@dataclass
class ConsensusProposal:
    """A proposal requiring consensus."""
    id: str
    title: str
    description: str
    decision_type: DecisionType
    proposer: str
    options: List[Dict[str, Any]] = field(default_factory=list)  # Options to vote on
    required_voters: List[str] = field(default_factory=list)  # Agent IDs
    min_approval_ratio: float = 0.67  # 2/3 majority
    min_voters: int = 3
    deadline: Optional[float] = None  # Unix timestamp
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        if self.deadline is None:
            return False
        return time.time() > self.deadline


@dataclass
class ConsensusVote:
    """A vote on a proposal."""
    proposal_id: str
    voter_id: str
    vote_type: VoteType
    selected_option: Optional[str] = None  # For multi-option votes
    conditions: List[str] = field(default_factory=list)  # For conditional votes
    rationale: str = ""
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConsensusResult:
    """Result of a consensus process."""
    proposal_id: str
    status: ConsensusStatus
    winning_option: Optional[str] = None
    approval_ratio: float = 0.0
    votes: List[ConsensusVote] = field(default_factory=list)
    decided_at: Optional[float] = None
    dissenting_voters: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)


class ConsensusConfig(BaseModel):
    """Configuration for consensus engine."""
    default_timeout_hours: float = 24.0
    default_min_approval: float = 0.67
    default_min_voters: int = 3
    allow_abstain: bool = True
    allow_conditional: bool = True
    quorum_required: bool = True
    escalation_on_timeout: bool = True
    escalation_contact: Optional[str] = None
    weighted_voting: bool = False
    voter_weights: Dict[str, float] = Field(default_factory=dict)


class ConsensusEngine:
    """Manages multi-agent consensus processes."""

    def __init__(
        self,
        config: Optional[ConsensusConfig] = None,
        notifier: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
    ) -> None:
        self.config = config or ConsensusConfig()
        self.notifier = notifier
        self._proposals: Dict[str, ConsensusProposal] = {}
        self._votes: Dict[str, List[ConsensusVote]] = {}
        self._results: Dict[str, ConsensusResult] = {}

    def create_proposal(
        self,
        title: str,
        description: str,
        decision_type: DecisionType,
        proposer: str,
        options: Optional[List[Dict[str, Any]]] = None,
        required_voters: Optional[List[str]] = None,
        min_approval_ratio: Optional[float] = None,
        min_voters: Optional[int] = None,
        deadline_hours: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new consensus proposal."""
        proposal_id = str(uuid.uuid4())[:8]

        proposal = ConsensusProposal(
            id=proposal_id,
            title=title,
            description=description,
            decision_type=decision_type,
            proposer=proposer,
            options=options or [
                {"id": "approve", "label": "Approve"},
                {"id": "reject", "label": "Reject"},
            ],
            required_voters=required_voters or [],
            min_approval_ratio=min_approval_ratio or self.config.default_min_approval,
            min_voters=min_voters or self.config.default_min_voters,
            deadline=time.time() + (deadline_hours or self.config.default_timeout_hours) * 3600,
            metadata={},
        )

        self._proposals[proposal.id] = proposal
        self._votes[proposal.id] = []

        # Notify required voters
        self._notify_voters(proposal)

        return proposal.id

    def vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote_type: VoteType,
        selected_option: Optional[str] = None,
        conditions: Optional[List[str]] = None,
        rationale: str = "",
        confidence: float = 1.0,
    ) -> bool:
        """Cast a vote on a proposal."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return False

        if proposal.is_expired():
            return False

        # Check if voter is authorized
        if proposal.required_voters and voter_id not in proposal.required_voters:
            return False

        # Check if already voted
        existing = next(
            (v for v in self._votes.get(proposal_id, []) if v.voter_id == voter_id),
            None,
        )
        if existing:
            return False  # Already voted

        vote = ConsensusVote(
            proposal_id=proposal_id,
            voter_id=voter_id,
            vote_type=vote_type,
            selected_option=selected_option,
            conditions=conditions or [],
            rationale=rationale,
        )

        self._votes.setdefault(proposal_id, []).append(vote)

        # Check if consensus reached
        self._check_consensus(proposal_id)

        return True

    def _check_consensus(self, proposal_id: str) -> Optional[ConsensusResult]:
        """Check if consensus has been reached."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        votes = self._votes.get(proposal_id, [])

        # Count votes
        approve_votes = [v for v in votes if v.vote_type == VoteType.APPROVE]
        reject_votes = [v for v in votes if v.vote_type == VoteType.REJECT]
        abstain_votes = [v for v in votes if v.vote_type == VoteType.ABSTAIN]
        conditional_votes = [v for v in votes if v.vote_type == VoteType.CONDITIONAL]

        total_voters = len(votes)
        required_voters = proposal.required_voters or []
        voted_required = [v for v in votes if v.voter_id in required_voters]

        # Check quorum
        if self.config.quorum_required and len(voted_required) < proposal.min_voters:
            return None  # Not enough required voters have voted

        # Calculate approval ratio
        effective_votes = len(votes) - len(abstain_votes)
        if effective_votes == 0:
            return None

        # Count conditional as partial approval
        conditional_weight = 0.5
        approvals = len(approve_votes) + len(conditional_votes) * conditional_weight
        approval_ratio = approvals / max(effective_votes, 1)

        # Determine status
        status = ConsensusStatus.VOTING
        winning_option = None
        conditions = []

        if approval_ratio >= proposal.min_approval_ratio and total_votes >= proposal.min_voters:
            status = ConsensusStatus.REACHED
            winning_option = "approve"
            # Collect conditions from conditional votes
            for v in conditional_votes:
                conditions.extend(v.conditions)
        elif len(reject_votes) > total_votes * 0.5:
            status = ConsensusStatus.REJECTED
        elif proposal.is_expired():
            status = ConsensusStatus.TIMED_OUT

        # Create result
        result = ConsensusResult(
            proposal_id=proposal.id,
            status=status,
            winning_option=winning_option,
            approval_ratio=approval_ratio,
            votes=votes,
            decided_at=time.time() if status != ConsensusStatus.VOTING else None,
            conditions=conditions,
        )

        self._results[proposal.id] = result
        return result

    def get_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get proposal status."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        votes = self._votes.get(proposal_id, [])
        result = self._results.get(proposal_id)

        return {
            "proposal_id": proposal.id,
            "title": proposal.title,
            "status": result.status.value if result else ConsensusStatus.VOTING.value,
            "total_votes": len(votes),
            "approve": len([v for v in votes if v.vote_type == VoteType.APPROVE]),
            "reject": len([v for v in votes if v.vote_type == VoteType.REJECT]),
            "abstain": len([v for v in votes if v.vote_type == VoteType.ABSTAIN]),
            "conditional": len([v for v in votes if v.vote_type == VoteType.CONDITIONAL]),
            "min_voters": proposal.min_voters,
            "min_approval": proposal.min_approval_ratio,
            "deadline": proposal.deadline,
            "expired": proposal.is_expired(),
            "result": result.winning_option if result else None,
        }

    def get_vote_details(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get detailed vote information."""
        votes = self._votes.get(proposal_id, [])
        return [
            {
                "voter_id": v.voter_id,
                "vote_type": v.vote_type.value,
                "selected_option": v.selected_option,
                "conditions": v.conditions,
                "rationale": v.rationale,
                "confidence": v.confidence,
                "timestamp": v.timestamp,
            }
            for v in votes
        ]

    def _notify_voters(self, proposal: ConsensusProposal) -> None:
        """Notify required voters of new proposal."""
        if not self.notifier:
            return

        for voter in proposal.required_voters:
            try:
                self.notifier(
                    voter,
                    "consensus_proposal",
                    {
                        "proposal_id": proposal.id,
                        "title": proposal.title,
                        "description": proposal.description,
                        "decision_type": proposal.decision_type.value,
                        "deadline": proposal.deadline,
                    },
                )
            except Exception:
                pass  # Don't let notification failures block

    def list_proposals(
        self,
        status: Optional[ConsensusStatus] = None,
        proposer: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List proposals with optional filters."""
        results = []
        for proposal in self._proposals.values():
            if status and proposal.id in self._results:
                if self._results[proposal.id].status != status:
                    continue
            if proposer and proposal.proposer != proposer:
                continue

            proposal_status = self.get_status(proposal.id)
            if proposal_status:
                results.append(proposal_status)
        return results


# Voting strategy implementations

class WeightedVoting:
    """Weighted voting based on voter expertise/role."""

    def __init__(self, weights: Dict[str, float]) -> None:
        self.weights = weights

    def calculate_approval(self, votes: List[ConsensusVote]) -> float:
        """Calculate weighted approval ratio."""
        total_weight = 0.0
        approve_weight = 0.0

        for vote in votes:
            weight = self.weights.get(vote.voter_id, 1.0)
            total_weight += weight
            if vote.vote_type == VoteType.APPROVE:
                approve_weight += weight
            elif vote.vote_type == VoteType.CONDITIONAL:
                approve_weight += weight * 0.5

        return approve_weight / max(total_weight, 1.0)


class QuadraticVoting:
    """Quadratic voting for preference intensity."""

    def __init__(self, budget: int = 100) -> None:
        self.budget = budget

    def calculate_score(self, votes: List[ConsensusVote]) -> Dict[str, float]:
        """Calculate quadratic voting scores."""
        scores = {}
        for vote in votes:
            if vote.vote_type == VoteType.APPROVE:
                option = vote.selected_option or "approve"
                # Cost = votes^2, so influence = sqrt(cost)
                influence = vote.confidence  # 0-1 confidence as vote strength
                scores[option] = scores.get(option, 0) + influence
        return scores


# Global instance
_consensus_engine: Optional[ConsensusEngine] = None


def get_consensus_engine(config: Optional[ConsensusConfig] = None) -> ConsensusEngine:
    """Get global consensus engine instance."""
    global _consensus_engine
    if _consensus_engine is None:
        _consensus_engine = ConsensusEngine(config)
    return _consensus_engine