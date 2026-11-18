"""Goal negotiation: agent asks clarifying questions before starting."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class NegotiationStatus(str, Enum):
    """Negotiation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AGREED = "agreed"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    TIMED_OUT = "timed_out"


class QuestionType(str, Enum):
    """Types of clarification questions."""
    CHOICE = "choice"           # Multiple choice
    CONFIRM = "confirm"         # Yes/no confirmation
    INPUT = "input"             # Free text input
    PRIORITY = "priority"       # Priority ranking
    SCOPE = "scope"             # Scope selection
    CONSTRAINT = "constraint"   # Constraint specification


@dataclass
class ClarificationQuestion:
    """A clarification question."""
    id: str
    type: QuestionType
    question: str
    context: str
    options: List[str] = field(default_factory=list)  # For choice questions
    default: Optional[str] = None
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Answer:
    """An answer to a clarification question."""
    question_id: str
    value: Any
    confidence: float = 1.0
    answered_at: float = field(default_factory=time.time)


@dataclass
class NegotiationTurn:
    """A turn in the negotiation."""
    turn: int
    questions: List[ClarificationQuestion]
    answers: List[Answer]
    timestamp: float = field(default_factory=time.time)
    agent_notes: str = ""


@dataclass
class NegotiationContext:
    """Context for goal negotiation."""
    goal: str
    original_plan: List[Dict[str, Any]]
    assumptions: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    stakeholders: List[str] = field(default_factory=list)


class NegotiationConfig(BaseModel):
    """Configuration for goal negotiator."""
    max_turns: int = 5
    max_questions_per_turn: int = 3
    timeout_seconds: float = 300.0
    auto_accept_threshold: float = 0.9  # Auto-accept if confidence high
    require_human_for: List[str] = Field(default_factory=lambda: [
        "security", "deployment", "data_migration", "breaking_changes"
    ])
    escalation_contact: Optional[str] = None


class GoalNegotiator:
    """Negotiates goal clarification with human/agent."""

    def __init__(
        self,
        config: Optional[NegotiationConfig] = None,
        question_generator: Optional[Callable[[NegotiationContext], List[ClarificationQuestion]]] = None,
        answer_evaluator: Optional[Callable[[ClarificationQuestion, Any], float]] = None,
    ) -> None:
        self.config = config or NegotiationConfig()
        self.question_generator = question_generator or self._default_questions
        self.answer_evaluator = answer_evaluator or self._default_evaluator
        self._active_negotiations: Dict[str, Dict[str, Any]] = {}

    def start_negotiation(
        self,
        goal: str,
        plan: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        negotiation_id: Optional[str] = None,
    ) -> str:
        """Start a new negotiation."""
        negotiation_id = negotiation_id or str(uuid.uuid4())[:8]

        neg_context = NegotiationContext(
            goal=goal,
            original_plan=plan,
            assumptions=context.get("assumptions", {}) if context else {},
            constraints=context.get("constraints", {}) if context else {},
            preferences=context.get("preferences", {}) if context else {},
            stakeholders=context.get("stakeholders", []) if context else [],
        )

        self._active_negotiations[negotiation_id] = {
            "id": negotiation_id,
            "context": neg_context,
            "status": NegotiationStatus.PENDING,
            "turns": [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        return negotiation_id

    def get_next_questions(self, negotiation_id: str) -> List[ClarificationQuestion]:
        """Get next set of clarification questions."""
        negotiation = self._active_negotiations.get(negotiation_id)
        if not negotiation:
            return []

        if negotiation["status"] != NegotiationStatus.PENDING and \
           negotiation["status"] != NegotiationStatus.IN_PROGRESS:
            return []

        neg_context = negotiation["context"]
        turn_num = len(negotiation["turns"]) + 1

        if turn_num > self.config.max_turns:
            negotiation["status"] = NegotiationStatus.TIMED_OUT
            return []

        questions = self.question_generator(neg_context)

        # Filter out already answered questions
        answered_ids = {a.question_id for turn in negotiation["turns"] for a in turn.answers}
        questions = [q for q in questions if q.id not in answered_ids]

        # Limit questions per turn
        questions = questions[:self.config.max_questions_per_turn]

        # Check for auto-accept conditions
        if self._should_auto_accept(negotiation):
            negotiation["status"] = NegotiationStatus.AGREED
            return []

        negotiation["status"] = NegotiationStatus.IN_PROGRESS
        return questions

    def submit_answers(
        self,
        negotiation_id: str,
        answers: List[Answer],
        agent_notes: str = "",
    ) -> NegotiationStatus:
        """Submit answers to questions."""
        negotiation = self._active_negotiations.get(negotiation_id)
        if not negotiation:
            raise ValueError(f"Negotiation not found: {negotiation_id}")

        # Get the questions that were asked
        turn_num = len(negotiation["turns"]) + 1
        questions = self.get_next_questions(negotiation_id)

        # Validate answers
        validated_answers = []
        for answer in answers:
            question = next((q for q in questions if q.id == answer.question_id), None)
            if question:
                if question.required and answer.value is None:
                    continue  # Skip missing required answers
                validated_answers.append(answer)

        # Create turn record
        turn = NegotiationTurn(
            turn=turn_num,
            questions=questions,
            answers=validated_answers,
            agent_notes=agent_notes,
        )
        negotiation["turns"].append(turn)
        negotiation["updated_at"] = time.time()

        # Update context with answers
        for answer in validated_answers:
            self._apply_answer(negotiation["context"], answer)

        # Check if negotiation complete
        if self._is_complete(negotiation):
            negotiation["status"] = NegotiationStatus.AGREED
        elif turn_num >= self.config.max_turns:
            negotiation["status"] = NegotiationStatus.TIMED_OUT

        return negotiation["status"]

    def _apply_answer(self, context: NegotiationContext, answer: Answer) -> None:
        """Apply answer to negotiation context."""
        # Store in assumptions/constraints/preferences based on question type
        # This is simplified - real implementation would be more sophisticated
        context.assumptions[f"answer_{answer.question_id}"] = answer.value

    def _is_complete(self, negotiation: Dict[str, Any]) -> bool:
        """Check if negotiation is complete."""
        # Check if all required questions answered
        for turn in negotiation["turns"]:
            for question in turn.questions:
                if question.required:
                    answered = any(a.question_id == question.id for a in turn.answers)
                    if not answered:
                        return False
        return True

    def _should_auto_accept(self, negotiation: Dict[str, Any]) -> bool:
        """Check if should auto-accept based on confidence."""
        # If we have high confidence in assumptions, auto-accept
        return False  # Simplified

    def _default_questions(self, context: NegotiationContext) -> List[ClarificationQuestion]:
        """Generate default clarification questions based on context."""
        questions = []
        qid = 0

        def next_id() -> str:
            nonlocal qid
            qid += 1
            return f"q{qid}"

        # Check for ambiguous terms in goal
        goal_lower = context.goal.lower()

        # Security-related questions
        if any(kw in goal_lower for kw in ["deploy", "production", "release", "migrate"]):
            questions.append(ClarificationQuestion(
                id=next_id(),
                type=QuestionType.CONFIRM,
                question="Should this run in production environment?",
                context="Production deployments require extra verification",
                required=True,
            ))

        # Scope questions
        if "refactor" in goal_lower or "rewrite" in goal_lower:
            questions.append(ClarificationQuestion(
                id=next_id(),
                type=QuestionType.SCOPE,
                question="What is the scope of this refactoring?",
                context="Refactoring scope affects timeline and risk",
                options=["Single module", "Multiple modules", "Cross-service", "Full system"],
                required=True,
            ))

        # Priority questions
        if any(kw in goal_lower for kw in ["urgent", "asap", "quick", "fast"]):
            questions.append(ClarificationQuestion(
                id=next_id(),
                type=QuestionType.PRIORITY,
                question="What is the priority relative to other work?",
                context="Priority affects resource allocation",
                options=["Critical - drop everything", "High - next up", "Normal - scheduled", "Low - when time permits"],
                required=True,
            ))

        # Constraint questions
        if "test" not in goal_lower and "verify" not in goal_lower:
            questions.append(ClarificationQuestion(
                id=next_id(),
                type=QuestionType.CONFIRM,
                question="Should tests be run as part of this work?",
                context="Automated tests provide confidence but take time",
                default="yes",
                required=False,
            ))

        # Data migration questions
        if any(kw in goal_lower for kw in ["migrate", "schema", "database"]):
            questions.append(ClarificationQuestion(
                id=next_id(),
                type=QuestionType.CONFIRM,
                question="Does this involve data migration?",
                context="Data migrations require backup and rollback plan",
                required=True,
            ))

        # Breaking changes
        if any(kw in goal_lower for kw in ["api", "interface", "contract", "breaking"]):
            questions.append(ClarificationQuestion(
                id=next_id(),
                type=QuestionType.CONFIRM,
                question="Are there breaking changes to public APIs?",
                context="Breaking changes require version bump and migration guide",
                required=True,
            ))

        # Timeline questions
        questions.append(ClarificationQuestion(
            id=next_id(),
            type=QuestionType.INPUT,
            question="What is the target completion date?",
            context="Timeline affects approach and resource allocation",
            required=False,
        ))

        # Rollback questions
        questions.append(ClarificationQuestion(
            id=next_id(),
            type=QuestionType.CONFIRM,
            question="Is a rollback plan required?",
            context="Some changes cannot be easily rolled back",
            default="yes",
            required=False,
        ))

        return questions

    def _default_evaluator(self, question: ClarificationQuestion, answer: Any) -> float:
        """Evaluate answer quality."""
        if answer is None:
            return 0.0 if question.required else 0.5

        if question.type == QuestionType.CHOICE:
            return 1.0 if answer in question.options else 0.5

        if question.type == QuestionType.CONFIRM:
            return 1.0 if isinstance(answer, bool) else 0.5

        if question.type == QuestionType.INPUT:
            return min(1.0, len(str(answer)) / 50.0)

        return 0.8

    def get_negotiation_summary(self, negotiation_id: str) -> Optional[Dict[str, Any]]:
        """Get negotiation summary."""
        negotiation = self._active_negotiations.get(negotiation_id)
        if not negotiation:
            return None

        return {
            "id": negotiation_id,
            "goal": negotiation["context"].goal,
            "status": negotiation["status"].value,
            "turns": len(negotiation["turns"]),
            "total_questions": sum(len(t.questions) for t in negotiation["turns"]),
            "total_answers": sum(len(t.answers) for t in negotiation["turns"]),
            "created_at": negotiation["created_at"],
            "updated_at": negotiation["updated_at"],
            "context": {
                "assumptions": negotiation["context"].assumptions,
                "constraints": negotiation["context"].constraints,
                "preferences": negotiation["context"].preferences,
            },
        }

    def get_final_plan(self, negotiation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the final negotiated plan."""
        negotiation = self._active_negotiations.get(negotiation_id)
        if not negotiation or negotiation["status"] != NegotiationStatus.AGREED:
            return None

        # Apply all answers to create final plan
        # This would modify the original plan based on answers
        return negotiation["context"].original_plan


# Global instance
_goal_negotiator: Optional[GoalNegotiator] = None


def get_goal_negotiator(config: Optional[NegotiationConfig] = None) -> GoalNegotiator:
    """Get global goal negotiator instance."""
    global _goal_negotiator
    if _goal_negotiator is None:
        _goal_negotiator = GoalNegotiator(config)
    return _goal_negotiator