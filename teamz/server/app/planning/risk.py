"""Risk assessment per step (blast radius, reversibility)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk severity levels."""
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    """Categories of risk."""
    DATA_LOSS = "data_loss"
    SERVICE_DOWNTIME = "service_downtime"
    SECURITY_BREACH = "security_breach"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    USER_IMPACT = "user_impact"
    FINANCIAL_LOSS = "financial_loss"
    REPUTATIONAL = "reputational"
    OPERATIONAL = "operational"
    TECHNICAL_DEBT = "technical_debt"


@dataclass
class RiskFactor:
    """A specific risk factor."""
    category: RiskCategory
    description: str
    likelihood: float  # 0-1
    impact: float  # 0-1
    blast_radius: str  # Description of affected scope
    reversibility: float  # 0-1 (1 = fully reversible)
    detection_time: str  # How long to detect
    mitigation: str  # How to mitigate
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def risk_score(self) -> float:
        """Calculate risk score (likelihood * impact)."""
        return self.likelihood * self.impact

    @property
    def level(self) -> RiskLevel:
        """Determine risk level from score."""
        score = self.risk_score
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.MEDIUM
        elif score >= 0.2:
            return RiskLevel.LOW
        return RiskLevel.NEGLIGIBLE


@dataclass
class StepRiskAssessment:
    """Risk assessment for a single step."""
    step_id: str
    step_name: str
    factors: List[RiskFactor] = field(default_factory=list)
    overall_score: float = 0.0
    overall_level: RiskLevel = RiskLevel.NEGLIGIBLE
    blast_radius_summary: str = ""
    reversibility_score: float = 1.0
    requires_approval: bool = False
    recommended_mitigations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_factor(self, factor: RiskFactor) -> None:
        """Add a risk factor and recalculate."""
        self.factors.append(factor)
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalculate overall risk metrics."""
        if not self.factors:
            self.overall_score = 0.0
            self.overall_level = RiskLevel.NEGLIGIBLE
            self.reversibility_score = 1.0
            return

        # Overall score: max of factor scores (conservative)
        self.overall_score = max(f.risk_score for f in self.factors)
        self.overall_level = max(self.factors, key=lambda f: f.risk_score).level

        # Reversibility: min of factor reversibilities
        self.reversibility_score = min(f.reversibility for f in self.factors)

        # Blast radius summary
        radii = [f.blast_radius for f in self.factors]
        self.blast_radius_summary = "; ".join(set(radii))

        # Requires approval if high/critical or low reversibility
        self.requires_approval = (
            self.overall_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) or
            self.reversibility_score < 0.3
        )

        # Collect mitigations
        self.recommended_mitigations = list(set(
            f.mitigation for f in self.factors if f.mitigation
        ))


@dataclass
class PlanRiskAssessment:
    """Risk assessment for entire plan."""
    plan_id: str
    step_assessments: List[StepRiskAssessment] = field(default_factory=list)
    overall_level: RiskLevel = RiskLevel.NEGLIGIBLE
    critical_steps: List[str] = field(default_factory=list)
    approval_required: bool = False
    total_mitigations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step_assessment(self, assessment: StepRiskAssessment) -> None:
        """Add step assessment and recalculate."""
        self.step_assessments.append(assessment)
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalculate plan-level metrics."""
        if not self.step_assessments:
            return

        self.overall_level = max(
            (s.overall_level for s in self.step_assessments),
            key=lambda l: ["negligible", "low", "medium", "high", "critical"].index(l.value)
        )

        self.critical_steps = [
            s.step_id for s in self.step_assessments
            if s.overall_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        ]

        self.approval_required = any(s.requires_approval for s in self.step_assessments)

        # Aggregate mitigations
        all_mitigations = []
        for s in self.step_assessments:
            all_mitigations.extend(s.recommended_mitigations)
        self.total_mitigations = list(set(all_mitigations))


class RiskConfig(BaseModel):
    """Configuration for risk assessor."""
    risk_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4,
        "low": 0.2,
    })
    require_approval_above: RiskLevel = RiskLevel.HIGH
    require_approval_if_irreversible: bool = True
    irreversibility_threshold: float = 0.3
    default_likelihood: float = 0.5
    default_impact: float = 0.5
    blast_radius_multipliers: Dict[str, float] = Field(default_factory=lambda: {
        "single_user": 0.1,
        "team": 0.3,
        "service": 0.5,
        "organization": 0.7,
        "global": 1.0,
    })


class RiskAssessor:
    """Assesses risk for plan steps."""

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        knowledge_base: Optional[Callable[[str, Dict[str, Any]], List[RiskFactor]]] = None,
    ) -> None:
        self.config = config or RiskConfig()
        self.knowledge_base = knowledge_base or self._default_knowledge_base
        self._risk_patterns: Dict[str, List[RiskFactor]] = {}

    def assess_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
    ) -> StepRiskAssessment:
        """Assess risk for a single step."""
        step_id = step.get("id", str(uuid.uuid4())[:8])
        step_name = step.get("name", step.get("tool", "unknown"))

        assessment = StepRiskAssessment(
            step_id=step_id,
            step_name=step_name,
        )

        # Get risk factors from knowledge base
        factors = self.knowledge_base(step_name, step)
        for factor in factors:
            assessment.add_factor(factor)

        # Add context-specific factors
        context_factors = self._assess_context(step, context)
        for factor in context_factors:
            assessment.add_factor(factor)

        return assessment

    def assess_plan(
        self,
        plan: List[Dict[str, Any]],
        context: Dict[str, Any],
        plan_id: Optional[str] = None,
    ) -> PlanRiskAssessment:
        """Assess risk for entire plan."""
        plan_id = plan_id or str(uuid.uuid4())[:8]
        assessment = PlanRiskAssessment(plan_id=plan_id)

        for step in plan:
            step_assessment = self.assess_step(step, context)
            assessment.add_step_assessment(step_assessment)

        return assessment

    def _default_knowledge_base(
        self,
        step_name: str,
        params: Dict[str, Any],
    ) -> List[RiskFactor]:
        """Default risk knowledge base."""
        factors = []

        # Tool-specific risks
        tool_risks = {
            "terminal": [
                RiskFactor(
                    category=RiskCategory.DATA_LOSS,
                    description="Terminal commands can delete/modify files",
                    likelihood=0.3,
                    impact=0.7,
                    blast_radius="repository",
                    reversibility=0.2,
                    detection_time="immediate",
                    mitigation="Use git for version control; test in branch first",
                ),
                RiskFactor(
                    category=RiskCategory.SERVICE_DOWNTIME,
                    description="Commands may stop/restart services",
                    likelihood=0.2,
                    impact=0.6,
                    blast_radius="service",
                    reversibility=0.5,
                    detection_time="minutes",
                    mitigation="Use graceful shutdown; health checks",
                ),
            ],
            "git": [
                RiskFactor(
                    category=RiskCategory.DATA_LOSS,
                    description="Force push or reset can lose commits",
                    likelihood=0.1,
                    impact=0.8,
                    blast_radius="repository",
                    reversibility=0.1,
                    detection_time="immediate",
                    mitigation="Use protected branches; require PR reviews",
                ),
            ],
            "npm": [
                RiskFactor(
                    category=RiskCategory.SECURITY_BREACH,
                    description="Malicious packages in dependencies",
                    likelihood=0.15,
                    impact=0.7,
                    blast_radius="application",
                    reversibility=0.3,
                    detection_time="hours",
                    mitigation="Use npm audit; lock files; trusted registry",
                ),
            ],
            "docker": [
                RiskFactor(
                    category=RiskCategory.SERVICE_DOWNTIME,
                    description="Container changes may break deployment",
                    likelihood=0.2,
                    impact=0.5,
                    blast_radius="service",
                    reversibility=0.6,
                    detection_time="minutes",
                    mitigation="Test in staging; blue-green deployment",
                ),
            ],
            "kubectl": [
                RiskFactor(
                    category=RiskCategory.SERVICE_DOWNTIME,
                    description="Kubernetes changes affect production",
                    likelihood=0.25,
                    impact=0.8,
                    blast_radius="organization",
                    reversibility=0.4,
                    detection_time="minutes",
                    mitigation="Use namespaces; canary deployment; rollback ready",
                ),
            ],
            "terraform": [
                RiskFactor(
                    category=RiskCategory.DATA_LOSS,
                    description="Infrastructure changes can destroy resources",
                    likelihood=0.2,
                    impact=0.9,
                    blast_radius="global",
                    reversibility=0.1,
                    detection_time="immediate",
                    mitigation="Use plan/apply workflow; state backups; drift detection",
                ),
            ],
            "database": [
                RiskFactor(
                    category=RiskCategory.DATA_LOSS,
                    description="Schema changes may lose data",
                    likelihood=0.3,
                    impact=0.9,
                    blast_radius="organization",
                    reversibility=0.1,
                    detection_time="immediate",
                    mitigation="Use migrations; backup before; test on copy",
                ),
            ],
        }

        base_factors = tool_risks.get(step_name, [])
        factors = copy.deepcopy(base_factors)

        # Adjust based on parameters
        for factor in factors:
            # Increase likelihood for destructive flags
            if params.get("force") or params.get("delete") or params.get("destroy"):
                factor.likelihood = min(1.0, factor.likelihood * 2)
                factor.reversibility = max(0.0, factor.reversibility * 0.5)

            # Adjust for production
            if params.get("environment") == "production" or params.get("prod"):
                factor.impact = min(1.0, factor.impact * 1.5)
                factor.likelihood = min(1.0, factor.likelihood * 1.2)

        return factors

    def _assess_context(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[RiskFactor]:
        """Assess context-specific risks."""
        factors = []

        # Time pressure
        if context.get("urgent") or context.get("deadline"):
            factors.append(RiskFactor(
                category=RiskCategory.OPERATIONAL,
                description="Time pressure increases error likelihood",
                likelihood=0.4,
                impact=0.5,
                blast_radius="plan",
                reversibility=0.3,
                detection_time="delayed",
                mitigation="Automate checks; pair programming; skip non-critical steps",
            ))

        # Team experience
        if context.get("junior_team"):
            factors.append(RiskFactor(
                category=RiskCategory.OPERATIONAL,
                description="Less experienced team may miss edge cases",
                likelihood=0.3,
                impact=0.4,
                blast_radius="plan",
                reversibility=0.5,
                detection_time="delayed",
                mitigation="Code review; mentoring; simpler approach",
            ))

        # Dependency risk
        deps = context.get("dependencies", [])
        if len(deps) > 3:
            factors.append(RiskFactor(
                category=RiskCategory.OPERATIONAL,
                description="Many dependencies increase failure surface",
                likelihood=0.2 * len(deps),
                impact=0.4,
                blast_radius="plan",
                reversibility=0.6,
                detection_time="varied",
                mitigation="Mock dependencies; circuit breakers; fallback paths",
            ))

        return factors

    def register_risk_pattern(
        self,
        tool_name: str,
        factors: List[RiskFactor],
    ) -> None:
        """Register custom risk pattern for a tool."""
        self._risk_patterns[tool_name] = factors

    def get_risk_pattern(self, tool_name: str) -> List[RiskFactor]:
        """Get registered risk pattern."""
        return self._risk_patterns.get(tool_name, [])


# Global instance
_risk_assessor: Optional[RiskAssessor] = None


def get_risk_assessor(config: Optional[RiskConfig] = None) -> RiskAssessor:
    """Get global risk assessor instance."""
    global _risk_assessor
    if _risk_assessor is None:
        _risk_assessor = RiskAssessor(config)
    return _risk_assessor