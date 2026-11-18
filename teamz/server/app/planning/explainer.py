"""Explainable AI: natural-language rationale for every decision."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ExplanationLevel(str, Enum):
    """Detail level for explanations."""
    SUMMARY = "summary"       # One sentence
    STANDARD = "standard"     # Paragraph with key points
    DETAILED = "detailed"     # Full reasoning with evidence
    TECHNICAL = "technical"   # Technical deep-dive


class ExplanationType(str, Enum):
    """Types of explanations."""
    DECISION = "decision"           # Why a decision was made
    ACTION = "action"               # Why an action was taken
    ALTERNATIVE = "alternative"     # Why an alternative was rejected
    FAILURE = "failure"             # Why something failed
    RISK = "risk"                   # Risk assessment rationale
    TRADEOFF = "tradeoff"           # Trade-off analysis
    PLAN = "plan"                   # Plan structure rationale


@dataclass
class Evidence:
    """Evidence supporting an explanation."""
    type: str  # fact, metric, rule, precedent, assumption
    description: str
    source: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepRationale:
    """Rationale for a single step/decision."""
    step_id: str
    step_name: str
    explanation_type: ExplanationType
    summary: str
    reasoning: str
    evidence: List[Evidence] = field(default_factory=list)
    alternatives_considered: List[Dict[str, Any]] = field(default_factory=list)
    tradeoffs: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanExplanation:
    """Complete explanation for a plan."""
    plan_id: str
    overall_summary: str
    step_rationales: List[StepRationale] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    risk_summary: str = ""
    alternatives_summary: str = ""
    assumptions_summary: str = ""
    generated_at: float = field(default_factory=time.time)
    level: ExplanationLevel = ExplanationLevel.STANDARD
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExplanationConfig(BaseModel):
    """Configuration for plan explainer."""
    default_level: ExplanationLevel = ExplanationLevel.STANDARD
    include_evidence: bool = True
    include_alternatives: bool = True
    include_tradeoffs: bool = True
    include_assumptions: bool = True
    max_alternatives_per_step: int = 3
    template_style: str = "natural"  # natural, structured, markdown
    language: str = "en"


class PlanExplainer:
    """Generates natural-language explanations for plans and decisions."""

    def __init__(
        self,
        config: Optional[ExplanationConfig] = None,
        llm_generator: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.config = config or ExplanationConfig()
        self.llm_generator = llm_generator
        self._templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load explanation templates."""
        return {
            "decision": (
                "I decided to {action} because {reason}. "
                "This approach {benefit}. "
                "{alternatives_text}"
                "{tradeoffs_text}"
                "{assumptions_text}"
            ),
            "action": (
                "To {goal}, I will {action}. "
                "This is the best approach because {reason}. "
                "{evidence_text}"
            ),
            "alternative": (
                "I considered {alternative} but rejected it because {reason}. "
                "Instead, {chosen} is better because {benefit}."
            ),
            "risk": (
                "This step carries {risk_level} risk due to {reason}. "
                "The main concerns are {concerns}. "
                "Mitigations include: {mitigations}."
            ),
            "tradeoff": (
                "There's a tradeoff between {option_a} and {option_b}. "
                "I chose {chosen} because {reason}. "
                "The cost is {cost}."
            ),
            "plan": (
                "This plan consists of {num_steps} steps to {goal}. "
                "The overall approach is {approach}. "
                "Key decisions: {decisions}. "
                "Main risks: {risks}."
            ),
        }

    def explain_plan(
        self,
        plan: List[Dict[str, Any]],
        context: Dict[str, Any],
        risk_assessment: Optional[Dict[str, Any]] = None,
        contingency: Optional[Dict[str, Any]] = None,
        level: Optional[ExplanationLevel] = None,
    ) -> PlanExplanation:
        """Generate explanation for an entire plan."""
        plan_id = str(uuid.uuid4())[:8]
        level = level or self.config.default_level

        # Generate step rationales
        step_rationales = []
        for i, step in enumerate(plan):
            rationale = self.explain_step(step, context, i, level)
            step_rationales.append(rationale)

        # Extract key decisions
        key_decisions = self._extract_key_decisions(step_rationales)

        # Generate summaries
        overall_summary = self._generate_overall_summary(plan, context, level)
        risk_summary = self._generate_risk_summary(risk_assessment)
        alternatives_summary = self._generate_alternatives_summary(step_rationales)
        assumptions_summary = self._generate_assumptions_summary(step_rationales)

        return PlanExplanation(
            plan_id=str(uuid.uuid4())[:8],
            overall_summary=overall_summary,
            step_rationales=step_rationales,
            key_decisions=key_decisions,
            risk_summary=risk_summary,
            alternatives_summary=alternatives_summary,
            assumptions_summary=assumptions_summary,
            level=level,
        )

    def explain_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
        step_index: int = 0,
        level: Optional[ExplanationLevel] = None,
    ) -> StepRationale:
        """Generate explanation for a single step."""
        level = level or self.config.default_level
        step_id = step.get("id", f"step_{step_index}")
        step_name = step.get("name", step.get("tool", "unknown"))

        # Generate components based on level
        if level == ExplanationLevel.SUMMARY:
            summary = self._generate_step_summary(step, context)
            reasoning = ""
            evidence = []
            alternatives = []
            tradeoffs = []
            assumptions = []
        elif level == ExplanationLevel.STANDARD:
            summary = self._generate_step_summary(step, context)
            reasoning = self._generate_reasoning(step, context)
            evidence = self._generate_evidence(step, context)
            alternatives = self._generate_alternatives(step, context)
            tradeoffs = self._generate_tradeoffs(step, context)
            assumptions = self._generate_assumptions(step, context)
        elif level == ExplanationLevel.DETAILED:
            summary = self._generate_step_summary(step, context)
            reasoning = self._generate_detailed_reasoning(step, context)
            evidence = self._generate_detailed_evidence(step, context)
            alternatives = self._generate_detailed_alternatives(step, context)
            tradeoffs = self._generate_detailed_tradeoffs(step, context)
            assumptions = self._generate_detailed_assumptions(step, context)
        else:  # TECHNICAL
            summary = self._generate_technical_summary(step, context)
            reasoning = self._generate_technical_reasoning(step, context)
            evidence = self._generate_technical_evidence(step, context)
            alternatives = self._generate_alternatives(step, context)
            tradeoffs = self._generate_detailed_tradeoffs(step, context)
            assumptions = self._generate_detailed_assumptions(step, context)

        # Determine explanation type
        exp_type = self._determine_explanation_type(step, context)

        return StepRationale(
            step_id=step_id,
            step_name=step_name,
            explanation_type=exp_type,
            summary=summary,
            reasoning=reasoning,
            evidence=evidence,
            alternatives_considered=alternatives,
            tradeoffs=tradeoffs,
            assumptions=assumptions,
            confidence=self._calculate_confidence(step, context),
        )

    def explain_decision(
        self,
        decision: str,
        context: Dict[str, Any],
        alternatives: List[Dict[str, Any]],
        chosen: str,
    ) -> str:
        """Explain a specific decision."""
        template = self._templates["decision"]

        alternatives_text = ""
        if alternatives:
            alt_names = [a.get("name", "alternative") for a in alternatives[:3]]
            alternatives_text = f" Alternatives considered: {', '.join(alt_names)}."

        return template.format(
            action=decision,
            reason=self._generate_reasoning({"name": decision}, {}),
            benefit=self._generate_benefit(decision, {}),
            alternatives_text=alternatives_text,
            tradeoffs_text="",
            assumptions_text="",
        )

    def explain_failure(
        self,
        step: Dict[str, Any],
        error: str,
        context: Dict[str, Any],
    ) -> str:
        """Explain why a step failed."""
        template = self._templates["failure"] if "failure" in self._templates else (
            "The step {step_name} failed with error: {error}. "
            "This happened because {reason}. "
            "Suggested fix: {suggestion}."
        )

        return template.format(
            step_name=step.get("name", "unknown"),
            error=error,
            reason=self._analyze_failure(error, step, context),
            suggestion=self._suggest_fix(error, step, context),
        )

    def _generate_step_summary(self, step: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate one-sentence summary."""
        tool = step.get("name", step.get("tool", "action"))
        goal = context.get("goal", "the objective")
        params = step.get("params", step.get("args", {}))

        param_str = ", ".join(f"{k}={v}" for k, v in list(params.items())[:3])
        if param_str:
            return f"Run {tool} ({param_str}) to advance toward {goal}"
        return f"Run {tool} to advance toward {goal}"

    def _generate_reasoning(self, step: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate reasoning for a step."""
        tool = step.get("name", step.get("tool", ""))
        goal = context.get("goal", "")

        reason_templates = {
            "terminal": "Running commands directly gives full control and visibility",
            "git": "Git operations ensure version control and collaboration",
            "pytest": "Tests verify correctness and prevent regressions",
            "npm": "Package management ensures consistent dependencies",
            "docker": "Containers provide reproducible environments",
            "kubectl": "Kubernetes orchestration manages deployment at scale",
            "terraform": "Infrastructure as code enables reproducible deployments",
        }

        base_reason = reason_templates.get(
            step.get("name", ""),
            f"This step is necessary to achieve {context.get('goal', 'the goal')}"
        )

        # Add context-specific reasoning
        if context.get("urgent"):
            base_reason += ". This is prioritized due to urgency."
        if context.get("dependencies"):
            base_reason += f" It depends on {len(context['dependencies'])} previous steps."

        return base_reason

    def _generate_detailed_reasoning(self, step: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate detailed reasoning."""
        reasoning = self._generate_reasoning(step, context)

        # Add parameter rationale
        params = step.get("params", step.get("args", {}))
        if params:
            param_reasons = []
            for key, value in params.items():
                param_reasons.append(f"{key}={value} (optimized for {self._infer_param_purpose(key, value)})")
            reasoning += f" Parameters: {', '.join(param_reasons)}."

        # Add dependency reasoning
        deps = step.get("dependencies", [])
        if deps:
            reasoning += f" Depends on {len(deps)} prior step(s) completing successfully."

        return reasoning

    def _infer_param_purpose(self, key: str, value: Any) -> str:
        """Infer purpose of a parameter."""
        purposes = {
            "timeout": "reliability",
            "retries": "resilience",
            "parallel": "performance",
            "coverage": "quality",
            "verbose": "debugging",
            "dry_run": "safety",
        }
        return purposes.get(key, "configuration")

    def _generate_evidence(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[Evidence]:
        """Generate supporting evidence."""
        evidence = []

        # Best practice evidence
        tool = step.get("name", step.get("tool", ""))
        best_practices = {
            "pytest": "Industry standard for Python testing",
            "ruff": "Fast, modern Python linter",
            "mypy": "Static type checking catches bugs early",
            "docker": "Containerization ensures consistency",
        }
        if tool in best_practices:
            evidence.append(Evidence(
                type="precedent",
                description=best_practices[tool],
                source="industry_standard",
                confidence=0.9,
            ))

        # Configuration evidence
        params = step.get("params", step.get("args", {}))
        if params.get("coverage"):
            evidence.append(Evidence(
                type="metric",
                description=f"Coverage target: {params['coverage']}%",
                source="configuration",
                confidence=1.0,
            ))

        return evidence

    def _generate_detailed_evidence(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[Evidence]:
        """Generate detailed evidence."""
        return self._generate_evidence(step, context)

    def _generate_evidence_text(self, evidence: List[Evidence]) -> str:
        """Format evidence for template."""
        if not evidence:
            return ""
        return "Evidence: " + "; ".join(e.description for e in evidence)

    def _generate_alternatives(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate considered alternatives."""
        tool = step.get("name", step.get("tool", ""))

        alternatives_map = {
            "pytest": [{"name": "unittest", "reason": "Built-in, no dependencies"}, {"name": "vitest", "reason": "For TypeScript projects"}],
            "npm": [{"name": "yarn", "reason": "Faster, workspaces support"}, {"name": "pnpm", "reason": "Disk efficient"}],
            "docker": [{"name": "podman", "reason": "Daemonless, rootless"}, {"name": "buildah", "reason": "Build-focused"}],
            "git": [{"name": "gh", "reason": "GitHub CLI integration"}],
        }

        return alternatives_map.get(tool, [])

    def _generate_detailed_alternatives(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed alternatives with reasoning."""
        alts = self._generate_alternatives(step, context)
        for alt in alts:
            alt["rejected_reason"] = f"Less suitable for {context.get('goal', 'this context')}"
        return alts

    def _generate_tradeoffs(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate tradeoffs."""
        tradeoffs = []

        tool = step.get("name", step.get("tool", ""))

        if tool == "pytest" and step.get("params", {}).get("coverage"):
            tradeoffs.append("High coverage increases test time but improves quality")

        if tool == "docker":
            tradeoffs.append("Container startup adds latency but ensures environment consistency")

        if step.get("params", {}).get("parallel"):
            tradeoffs.append("Parallel execution reduces time but increases resource usage")

        return tradeoffs

    def _generate_detailed_tradeoffs(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate detailed tradeoffs."""
        return self._generate_tradeoffs(step, context)

    def _generate_assumptions(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate assumptions."""
        assumptions = []

        if context.get("environment") == "production":
            assumptions.append("Running in production environment with real data")

        if step.get("dependencies"):
            assumptions.append("All dependent steps complete successfully")

        if context.get("resources_available"):
            assumptions.append("Required resources (CPU, memory, network) are available")

        return assumptions

    def _generate_detailed_assumptions(self, step: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate detailed assumptions."""
        return self._generate_assumptions(step, context)

    def _determine_explanation_type(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExplanationType:
        """Determine the type of explanation needed."""
        if context.get("failed_step") == step.get("id"):
            return ExplanationType.FAILURE
        if step.get("critical"):
            return ExplanationType.DECISION
        if step.get("alternative_considered"):
            return ExplanationType.ALTERNATIVE
        if step.get("tradeoff_documented"):
            return ExplanationType.TRADEOFF
        return ExplanationType.ACTION

    def _calculate_confidence(self, step: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate confidence in explanation."""
        confidence = 0.8  # Base

        # Higher confidence for well-known tools
        known_tools = {"git", "pytest", "npm", "docker", "kubectl", "terraform"}
        if step.get("name") in known_tools:
            confidence += 0.1

        # Lower confidence for custom/unknown tools
        if step.get("custom"):
            confidence -= 0.2

        return max(0.3, min(1.0, confidence))

    def _extract_key_decisions(self, rationales: List[StepRationale]) -> List[str]:
        """Extract key decisions from step rationales."""
        decisions = []
        for r in rationales:
            if r.explanation_type in (ExplanationType.DECISION, ExplanationType.TRADEOFF):
                decisions.append(f"{r.step_name}: {r.summary}")
        return decisions[:5]

    def _generate_overall_summary(
        self,
        plan: List[Dict[str, Any]],
        context: Dict[str, Any],
        level: ExplanationLevel,
    ) -> str:
        """Generate overall plan summary."""
        goal = context.get("goal", "the objective")
        num_steps = len(plan)
        tools = set(step.get("name", step.get("tool", "")) for step in plan)

        if level == ExplanationLevel.SUMMARY:
            return f"Plan with {num_steps} steps using {', '.join(tools)} to achieve {goal}"

        template = self._templates["plan"]
        return template.format(
            num_steps=num_steps,
            goal=goal,
            approach=f"sequential execution with {', '.join(tools)}",
            decisions=", ".join([s.get("name", "") for s in plan[:3]]),
            risks="managed through validation and rollback",
        )

    def _generate_risk_summary(self, risk_assessment: Optional[Dict[str, Any]]) -> str:
        """Generate risk summary."""
        if not risk_assessment:
            return "No formal risk assessment available"

        level = risk_assessment.get("overall_level", "unknown")
        critical = risk_assessment.get("critical_steps", [])

        return f"Overall risk: {level}. Critical steps: {len(critical)}"

    def _generate_alternatives_summary(self, rationales: List[StepRationale]) -> str:
        """Generate alternatives summary."""
        all_alts = []
        for r in rationales:
            all_alts.extend(r.alternatives_considered)

        if not all_alts:
            return "No alternatives documented"

        unique = set(a.get("name", "") for a in all_alts)
        return f"Alternatives evaluated: {', '.join(unique)}"

    def _generate_assumptions_summary(self, rationales: List[StepRationale]) -> str:
        """Generate assumptions summary."""
        all_assumptions = []
        for r in rationales:
            all_assumptions.extend(r.assumptions)

        if not all_assumptions:
            return "No explicit assumptions"

        unique = list(set(all_assumptions))
        return f"Key assumptions: {len(unique)} documented"

    def format_explanation(
        self,
        explanation: PlanExplanation,
        format: str = "natural",
    ) -> str:
        """Format explanation for output."""
        if format == "markdown":
            return self._format_markdown(explanation)
        elif format == "structured":
            return json.dumps({
                "plan_id": explanation.plan_id,
                "summary": explanation.overall_summary,
                "steps": [
                    {
                        "step_id": r.step_id,
                        "step_name": r.step_name,
                        "summary": r.summary,
                        "reasoning": r.reasoning,
                        "evidence": [e.description for e in r.evidence],
                        "alternatives": r.alternatives_considered,
                        "tradeoffs": r.tradeoffs,
                        "assumptions": r.assumptions,
                    }
                    for r in explanation.step_rationales
                ],
                "risk_summary": explanation.risk_summary,
            }, indent=2)
        else:
            return self._format_natural(explanation)

    def _format_natural(self, explanation: PlanExplanation) -> str:
        """Format as natural language."""
        parts = [
            f"Plan Explanation: {explanation.overall_summary}",
            "",
            f"Risk Assessment: {explanation.risk_summary}",
            "",
            "Step-by-step rationale:",
        ]

        for i, r in enumerate(explanation.step_rationales, 1):
            parts.append(f"\n{i}. {r.step_name}: {r.summary}")
            if r.reasoning:
                parts.append(f"   Reason: {r.reasoning}")
            if r.evidence:
                parts.append(f"   Evidence: {', '.join(e.description for e in r.evidence)}")
            if r.alternatives_considered:
                alt_names = [a.get("name", "") for a in r.alternatives_considered]
                parts.append(f"   Alternatives: {', '.join(alt_names)}")
            if r.tradeoffs:
                parts.append(f"   Tradeoffs: {', '.join(r.tradeoffs)}")
            if r.assumptions:
                parts.append(f"   Assumptions: {', '.join(r.assumptions)}")

        return "\n".join(parts)

    def _format_markdown(self, explanation: PlanExplanation) -> str:
        """Format as Markdown."""
        parts = [
            f"# Plan Explanation",
            "",
            explanation.overall_summary,
            "",
            f"## Risk Assessment",
            "",
            explanation.risk_summary,
            "",
            "## Step Rationale",
            "",
        ]

        for r in explanation.step_rationales:
            parts.append(f"### {r.step_name}")
            parts.append(f"**Summary:** {r.summary}")
            if r.reasoning:
                parts.append(f"**Reasoning:** {r.reasoning}")
            if r.evidence:
                parts.append("**Evidence:**")
                for e in r.evidence:
                    parts.append(f"- {e.description} (source: {e.source})")
            if r.alternatives_considered:
                parts.append("**Alternatives Considered:**")
                for a in r.alternatives_considered:
                    parts.append(f"- {a.get('name', '')}: {a.get('reason', '')}")
            if r.tradeoffs:
                parts.append("**Tradeoffs:**")
                for t in r.tradeoffs:
                    parts.append(f"- {t}")
            if r.assumptions:
                parts.append("**Assumptions:**")
                for a in r.assumptions:
                    parts.append(f"- {a}")
            parts.append("")

        return "\n".join(parts)


# Global instance
_plan_explainer: Optional[PlanExplainer] = None


def get_plan_explainer(config: Optional[ExplanationConfig] = None) -> PlanExplainer:
    """Get global plan explainer instance."""
    global _plan_explainer
    if _plan_explainer is None:
        _plan_explainer = PlanExplainer(config)
    return _plan_explainer