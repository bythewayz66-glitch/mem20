"""Planning Manager: unified interface for all planning subsystems."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .htn import HTNPlanner, HTNConfig, HTNState, HTNGoal, get_htn_planner
from .mcts import MCTSPlanner, MCTSConfig, MCTSState, get_mcts_planner
from .counterfactual import CounterfactualEngine, CounterfactualConfig, get_counterfactual_engine
from .verifier import PlanVerifier, VerificationConfig, VerificationResult, get_plan_verifier
from .negotiator import GoalNegotiator, NegotiationConfig, get_goal_negotiator
from .risk import RiskAssessor, RiskConfig, PlanRiskAssessment, get_risk_assessor
from .contingency import ContingencyPlanner, ContingencyConfig, get_contingency_planner
from .scheduler import PlanScheduler, SchedulerConfig, Schedule, get_plan_scheduler
from .consensus import ConsensusEngine, ConsensusConfig, get_consensus_engine
from .explainer import PlanExplainer, ExplanationConfig, PlanExplanation, get_plan_explainer


class PlanningManagerConfig(BaseModel):
    """Configuration for planning manager."""
    htn_config: Optional[HTNConfig] = None
    mcts_config: Optional[MCTSConfig] = None
    counterfactual_config: Optional[CounterfactualConfig] = None
    verifier_config: Optional[VerificationConfig] = None
    negotiator_config: Optional[NegotiationConfig] = None
    risk_config: Optional[RiskConfig] = None
    contingency_config: Optional[ContingencyConfig] = None
    scheduler_config: Optional[SchedulerConfig] = None
    consensus_config: Optional[ConsensusConfig] = None
    explainer_config: Optional[ExplanationConfig] = None


@dataclass
class PlanningSession:
    """A planning session tracking all artifacts."""
    id: str
    goal: str
    context: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Artifacts
    htn_plan: Optional[Any] = None
    mcts_result: Optional[Any] = None
    risk_assessment: Optional[Any] = None
    contingency_plan: Optional[Any] = None
    schedule: Optional[Any] = None
    verification_result: Optional[VerificationResult] = None
    negotiation_id: Optional[str] = None
    consensus_id: Optional[str] = None
    explanation: Optional[Any] = None

    # Status
    status: str = "initialized"  # initialized, planning, negotiating, verifying, scheduled, executing, completed, failed
    current_phase: str = "init"


class PlanningManager:
    """Unified planning manager coordinating all subsystems."""

    def __init__(self, config: Optional[PlanningManagerConfig] = None) -> None:
        self.config = config or PlanningManagerConfig()
        self._htn_planner = get_htn_planner(self.config.htn_config)
        self._mcts_planner = get_mcts_planner(self.config.mcts_config)
        self._counterfactual = get_counterfactual_engine(self.config.counterfactual_config)
        self._verifier = get_plan_verifier(self.config.verifier_config)
        self._negotiator = get_goal_negotiator(self.config.negotiator_config)
        self._risk_assessor = get_risk_assessor(self.config.risk_config)
        self._contingency = get_contingency_planner(self.config.contingency_config)
        self._scheduler = get_plan_scheduler(self.config.scheduler_config)
        self._consensus = get_consensus_engine(self.config.consensus_config)
        self._explainer = get_plan_explainer(self.config.explainer_config)

        self._sessions: Dict[str, PlanningSession] = {}

    async def plan(
        self,
        goal: str,
        context: Dict[str, Any],
        initial_state: Optional[Dict[str, Any]] = None,
        use_htn: bool = True,
        use_mcts: bool = True,
    ) -> Dict[str, Any]:
        """Generate a plan for a goal."""
        session_id = str(uuid.uuid4())[:8]
        session = PlanningSession(
            id=session_id,
            goal=goal,
            context=context,
        )
        self._sessions[session_id] = session
        session.status = "planning"
        session.current_phase = "decomposition"

        results = {
            "session_id": session_id,
            "goal": goal,
        }

        # HTN Planning
        if use_htn:
            htn_state = HTNState()
            if initial_state:
                htn_state.facts = initial_state.get("facts", {})
                htn_state.numeric = initial_state.get("numeric", {})
                htn_state.sets = initial_state.get("sets", {})

            htn_goal = HTNGoal(
                name=goal,
                conditions=[],  # Would be populated from context
            )

            htn_plan = self._htn_planner.plan(htn_state, htn_goal)
            if htn_plan:
                session.htn_plan = htn_plan
                results["htn_plan"] = {
                    "id": htn_plan.id,
                    "tasks": [str(t) for t in htn_plan.tasks],
                    "cost": htn_plan.total_cost,
                }

        session.current_phase = "step_selection"

        # MCTS Step Selection
        if use_mcts:
            # Convert context available_actions to MCTSAction objects
            raw_actions = context.get("available_actions", [])
            mcts_actions = []
            for a in raw_actions:
                if isinstance(a, dict):
                    from .mcts import MCTSAction
                    mcts_actions.append(MCTSAction(
                        name=a.get("name", "action"),
                        params=a.get("params", a.get("args", {})),
                        metadata=a.get("metadata", {}),
                    ))
                else:
                    mcts_actions.append(a)

            # Convert context to MCTS state (context first, then override available_actions)
            mcts_state = MCTSState(
                data={
                    **context,
                    "goal": goal,
                    "available_actions": mcts_actions,
                }
            )

            mcts_action, mcts_root = self._mcts_planner.search(mcts_state)
            session.mcts_result = (mcts_action, mcts_root)
            results["mcts_recommendation"] = {
                "action": mcts_action.name,
                "params": mcts_action.params,
                "confidence": mcts_root.average_reward if mcts_root.visits > 0 else 0,
            }

        # Generate concrete plan steps
        plan_steps = self._generate_plan_steps(goal, context, session)
        session.current_phase = "risk_assessment"

        # Risk Assessment
        risk_assessment = self._risk_assessor.assess_plan(plan_steps, context)
        session.risk_assessment = risk_assessment
        results["risk_assessment"] = {
            "overall_level": risk_assessment.overall_level.value,
            "critical_steps": risk_assessment.critical_steps,
            "approval_required": risk_assessment.approval_required,
            "mitigations": risk_assessment.total_mitigations,
        }

        # Contingency Planning
        contingency = self._contingency.generate_contingency_plan(
            plan_steps,
            risk_assessments={},
            context=context,
        )
        session.contingency_plan = contingency
        results["contingency"] = {
            "fallback_count": sum(
                1 + len(f.alternative_fallbacks) + (1 if f.escalation_fallback else 0)
                for f in contingency.fallback_plans.values()
            ),
            "rollback_points": contingency.rollback_points,
        }

        session.status = "planned"
        session.updated_at = time.time()

        return results

    def _generate_plan_steps(
        self,
        goal: str,
        context: Dict[str, Any],
        session: "PlanningSession",
    ) -> List[Dict[str, Any]]:
        """Generate concrete plan steps from planning results."""
        steps = []

        # Use HTN plan if available
        if session.htn_plan:
            for i, task in enumerate(session.htn_plan.tasks):
                steps.append({
                    "id": f"step_{i}",
                    "name": task.name,
                    "params": {},
                    "estimated_duration": 60.0,
                    "dependencies": [],
                    "critical": True,
                })

        # Fall back to MCTS recommendation
        elif session.mcts_result:
            action, _ = session.mcts_result
            steps.append({
                "id": "step_0",
                "name": action.name,
                "params": action.params,
                "estimated_duration": 60.0,
                "dependencies": [],
                "critical": True,
            })

        # Fall back to context actions
        elif "available_actions" in context:
            for i, action in enumerate(context["available_actions"]):
                steps.append({
                    "id": f"step_{i}",
                    "name": action.get("name", "action"),
                    "params": action.get("params", {}),
                    "estimated_duration": action.get("estimated_duration", 60.0),
                    "dependencies": action.get("dependencies", []),
                    "critical": action.get("critical", False),
                })

        return steps

    async def negotiate_goal(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """Start goal negotiation for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.current_phase = "negotiation"
        session.status = "negotiating"

        negotiation_id = self._negotiator.start_negotiation(
            goal=session.goal,
            plan=session.htn_plan.tasks if session.htn_plan else [],
            context=session.context,
        )
        session.negotiation_id = negotiation_id

        questions = self._negotiator.get_next_questions(negotiation_id)

        return {
            "negotiation_id": negotiation_id,
            "questions": [
                {
                    "id": q.id,
                    "type": q.type.value,
                    "question": q.question,
                    "context": q.context,
                    "options": q.options,
                    "required": q.required,
                }
                for q in questions
            ],
        }

    async def submit_negotiation_answers(
        self,
        session_id: str,
        answers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Submit answers to negotiation questions."""
        session = self._sessions.get(session_id)
        if not session or not session.negotiation_id:
            return {"error": "No active negotiation"}

        answer_objects = []
        for ans in answers:
            from .negotiator import Answer
            answer_objects.append(Answer(
                question_id=ans["question_id"],
                value=ans["value"],
            ))

        status = self._negotiator.submit_answers(
            session.negotiation_id,
            answer_objects,
        )

        return {
            "status": status.value,
            "summary": self._negotiator.get_negotiation_summary(session.negotiation_id),
        }

    async def verify_plan(
        self,
        session_id: str,
    ) -> VerificationResult:
        """Verify a plan."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        session.current_phase = "verification"

        plan_steps = self._generate_plan_steps(session.goal, session.context, session)
        result = await self._verifier.verify_plan(plan_steps, session.context)
        session.verification_result = result

        return result

    async def request_consensus(
        self,
        session_id: str,
        decision_type: str,
        title: str,
        description: str,
        required_voters: List[str],
    ) -> str:
        """Request consensus for a high-stakes decision."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        from .consensus import DecisionType
        consensus_id = self._consensus.create_proposal(
            title=title,
            description=description,
            decision_type=DecisionType(decision_type),
            proposer=session.context.get("agent_id", "planner"),
            required_voters=required_voters,
        )
        session.consensus_id = consensus_id

        return consensus_id

    def schedule_execution(
        self,
        session_id: str,
    ) -> Schedule:
        """Create execution schedule for a plan."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        session.current_phase = "scheduling"

        plan_steps = self._generate_plan_steps(session.goal, session.context, session)
        schedule = self._scheduler.create_schedule(plan_steps)
        session.schedule = schedule

        return schedule

    async def execute_schedule(
        self,
        session_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> Schedule:
        """Execute the scheduled plan."""
        session = self._sessions.get(session_id)
        if not session or not session.schedule:
            raise ValueError("No schedule to execute")

        session.status = "executing"
        session.current_phase = "execution"

        schedule = await self._scheduler.execute_schedule(
            session.schedule,
            progress_callback=progress_callback,
        )
        session.schedule = schedule

        if schedule.status.value == "completed":
            session.status = "completed"
        else:
            session.status = "failed"

        session.updated_at = time.time()
        return schedule

    def generate_explanation(
        self,
        session_id: str,
        level: str = "standard",
    ) -> PlanExplanation:
        """Generate natural-language explanation for a plan."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        from .explainer import ExplanationLevel
        plan_steps = self._generate_plan_steps(session.goal, session.context, session)

        expl = self._explainer.explain_plan(
            plan=plan_steps,
            context=session.context,
            risk_assessment={
                "overall_level": session.risk_assessment.overall_level.value if session.risk_assessment else "unknown",
                "critical_steps": session.risk_assessment.critical_steps if session.risk_assessment else [],
            } if session.risk_assessment else None,
            level=ExplanationLevel(level),
        )
        session.explanation = expl
        return expl

    def ask_what_if(
        self,
        session_id: str,
        question: str,
    ) -> List[Dict[str, Any]]:
        """Ask counterfactual question about a plan."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        plan_steps = self._generate_plan_steps(session.goal, session.context, session)
        results = self._counterfactual.ask_what_if(question, plan_steps, session.context)

        return [
            {
                "scenario": r.scenario.id,
                "recommendation": r.recommendation,
                "risk_delta": r.risk_delta,
                "comparison": r.comparison,
            }
            for r in results
        ]

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        return {
            "id": session.id,
            "goal": session.goal,
            "status": session.status,
            "phase": session.current_phase,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "has_plan": session.htn_plan is not None,
            "has_risk_assessment": session.risk_assessment is not None,
            "has_contingency": session.contingency_plan is not None,
            "has_schedule": session.schedule is not None,
            "has_verification": session.verification_result is not None,
            "has_explanation": session.explanation is not None,
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all planning sessions."""
        return [
            {
                "id": s.id,
                "goal": s.goal,
                "status": s.status,
                "phase": s.current_phase,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in self._sessions.values()
        ]


# Global instance
_planning_manager: Optional[PlanningManager] = None


def get_planning_manager(config: Optional[PlanningManagerConfig] = None) -> PlanningManager:
    """Get global planning manager instance."""
    global _planning_manager
    if _planning_manager is None:
        _planning_manager = PlanningManager(config)
    return _planning_manager