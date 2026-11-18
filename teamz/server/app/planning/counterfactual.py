"""Counterfactual reasoning engine: 'what if I used library Y instead?'"""

from __future__ import annotations

import copy
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


class InterventionType(str, Enum):
    """Types of counterfactual interventions."""
    REPLACE_ACTION = "replace_action"       # Replace one action with another
    REMOVE_ACTION = "remove_action"         # Remove an action
    ADD_ACTION = "add_action"               # Add a new action
    MODIFY_PARAM = "modify_param"           # Change action parameters
    CHANGE_ORDER = "change_order"           # Reorder actions
    ALTER_CONDITION = "alter_condition"     # Change preconditions


@dataclass
class Intervention:
    """A counterfactual intervention."""
    type: InterventionType
    target_step: int  # Step index in plan
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterfactualScenario:
    """A counterfactual scenario with modified plan."""
    id: str
    original_plan: List[Dict[str, Any]]
    interventions: List[Intervention]
    modified_plan: List[Dict[str, Any]]
    predicted_outcome: Dict[str, Any]
    confidence: float
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterfactualResult:
    """Result of counterfactual analysis."""
    scenario: CounterfactualScenario
    comparison: Dict[str, Any]  # Differences vs original
    recommendation: str
    risk_delta: float  # Change in risk score


class CounterfactualConfig(BaseModel):
    """Configuration for counterfactual engine."""
    max_scenarios: int = 10
    max_interventions_per_scenario: int = 3
    similarity_threshold: float = 0.7
    min_confidence: float = 0.5
    enable_auto_generation: bool = True
    comparison_metrics: List[str] = Field(default_factory=lambda: [
        "success_probability", "cost", "time", "risk", "quality"
    ])


class CounterfactualEngine:
    """Engine for generating and evaluating counterfactual scenarios."""

    def __init__(
        self,
        config: Optional[CounterfactualConfig] = None,
        predictor: Optional[Callable[[List[Dict[str, Any]], Dict[str, Any]], Dict[str, Any]]] = None,
        risk_assessor: Optional[Callable[[List[Dict[str, Any]], Dict[str, Any]], float]] = None,
        plan_validator: Optional[Callable[[List[Dict[str, Any]], Dict[str, Any]], bool]] = None,
    ) -> None:
        self.config = config or CounterfactualConfig()
        self.predictor = predictor
        self.risk_assessor = risk_assessor
        self.plan_validator = plan_validator
        self._scenario_cache: Dict[str, CounterfactualScenario] = {}

    def generate_scenarios(
        self,
        original_plan: List[Dict[str, Any]],
        context: Dict[str, Any],
        focus_areas: Optional[List[str]] = None,
    ) -> List[CounterfactualScenario]:
        """Generate counterfactual scenarios for a plan."""
        scenarios = []

        # Generate interventions based on focus areas
        interventions = self._generate_interventions(original_plan, context, focus_areas)

        # Group interventions into scenarios
        for intervention_group in self._group_interventions(interventions):
            if len(intervention_group) > self.config.max_interventions_per_scenario:
                intervention_group = intervention_group[:self.config.max_interventions_per_scenario]

            scenario = self._apply_interventions(original_plan, intervention_group, context)
            if scenario and scenario.confidence >= self.config.min_confidence:
                scenarios.append(scenario)

        # Sort by confidence and diversity
        scenarios.sort(key=lambda s: (-s.confidence, s.id))
        return scenarios[:self.config.max_scenarios]

    def _generate_interventions(
        self,
        plan: List[Dict[str, Any]],
        context: Dict[str, Any],
        focus_areas: Optional[List[str]] = None,
    ) -> List[Intervention]:
        """Generate possible interventions for a plan."""
        interventions = []

        for i, step in enumerate(plan):
            step_name = step.get("name", step.get("tool", ""))
            step_params = step.get("params", step.get("args", {}))

            # Replace action interventions
            alternatives = self._get_alternatives(step_name, step_params, context)
            for alt in alternatives:
                interventions.append(Intervention(
                    type=InterventionType.REPLACE_ACTION,
                    target_step=i,
                    description=f"Replace {step_name} with {alt['name']}",
                    params={"replacement": alt},
                ))

            # Modify parameter interventions
            param_interventions = self._generate_param_interventions(i, step_name, step_params, context)
            interventions.extend(param_interventions)

            # Remove action (if not critical)
            if not step.get("critical", False) and not step.get("required", False):
                interventions.append(Intervention(
                    type=InterventionType.REMOVE_ACTION,
                    target_step=i,
                    description=f"Remove {step_name}",
                    params={},
                ))

        # Add action interventions (from knowledge base)
        if focus_areas:
            for area in focus_areas:
                additions = self._get_additional_actions(area, plan, context)
                for add in additions:
                    interventions.append(Intervention(
                        type=InterventionType.ADD_ACTION,
                        target_step=len(plan),  # Append
                        description=f"Add {add['name']} for {area}",
                        params={"addition": add},
                    ))

        # Change order interventions
        if len(plan) > 2:
            for i in range(len(plan) - 1):
                if not plan[i].get("depends_on") and not plan[i+1].get("depends_on"):
                    interventions.append(Intervention(
                        type=InterventionType.CHANGE_ORDER,
                        target_step=i,
                        description=f"Swap steps {i} and {i+1}",
                        params={"swap_with": i+1},
                    ))

        return interventions

    def _get_alternatives(
        self,
        step_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Get alternative actions for a step."""
        # This would query a knowledge base or use heuristics
        # Simplified version with common alternatives
        alternatives_map = {
            "git": [{"name": "gh", "description": "GitHub CLI alternative"}],
            "npm": [{"name": "yarn", "description": "Yarn package manager"}, {"name": "pnpm", "description": "pnpm package manager"}],
            "pytest": [{"name": "vitest", "description": "Vitest for TypeScript"}],
            "docker": [{"name": "podman", "description": "Podman container engine"}],
            "terraform": [{"name": "pulumi", "description": "Pulumi IaC"}],
        }

        return alternatives_map.get(step_name, [])

    def _generate_param_interventions(
        self,
        step_idx: int,
        step_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Intervention]:
        """Generate parameter modification interventions."""
        interventions = []

        # Common parameter modifications
        if "timeout" in params:
            interventions.append(Intervention(
                type=InterventionType.MODIFY_PARAM,
                target_step=step_idx,
                description=f"Increase timeout for {step_name}",
                params={"param": "timeout", "multiplier": 2.0},
            ))

        if "retries" in params:
            interventions.append(Intervention(
                type=InterventionType.MODIFY_PARAM,
                target_step=step_idx,
                description=f"Increase retries for {step_name}",
                params={"param": "retries", "increment": 2},
            ))

        if "model" in params:
            # Suggest different model
            interventions.append(Intervention(
                type=InterventionType.MODIFY_PARAM,
                target_step=step_idx,
                description=f"Try different model for {step_name}",
                params={"param": "model", "alternatives": ["gpt-4o", "claude-3.5-sonnet"]},
            ))

        return interventions

    def _get_additional_actions(
        self,
        focus_area: str,
        plan: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Get additional actions for a focus area."""
        additions_map = {
            "testing": [
                {"name": "run_tests", "params": {"coverage": True}},
                {"name": "run_mutation_tests", "params": {}},
            ],
            "security": [
                {"name": "run_security_scan", "params": {"tool": "semgrep"}},
                {"name": "run_dependency_audit", "params": {}},
            ],
            "performance": [
                {"name": "run_performance_benchmark", "params": {}},
                {"name": "run_visual_regression", "params": {}},
            ],
            "documentation": [
                {"name": "update_docs", "params": {}},
            ],
        }
        return additions_map.get(focus_area, [])

    def _group_interventions(self, interventions: List[Intervention]) -> List[List[Intervention]]:
        """Group interventions into scenario candidates."""
        groups = []

        # Single interventions
        for interv in interventions:
            groups.append([interv])

        # Pairs of compatible interventions
        for i, a in enumerate(interventions):
            for b in interventions[i+1:]:
                if self._compatible(a, b):
                    groups.append([a, b])

        # Triples
        for i, a in enumerate(interventions):
            for j, b in enumerate(interventions[i+1:], i+1):
                for c in interventions[j+1:]:
                    if self._compatible(a, b) and self._compatible(a, c) and self._compatible(b, c):
                        groups.append([a, b, c])

        return groups

    def _compatible(self, a: Intervention, b: Intervention) -> bool:
        """Check if two interventions are compatible."""
        # Same step, different types might conflict
        if a.target_step == b.target_step:
            if a.type == b.type:
                return False
            if a.type == InterventionType.REMOVE_ACTION or b.type == InterventionType.REMOVE_ACTION:
                return False
        return True

    def _apply_interventions(
        self,
        original_plan: List[Dict[str, Any]],
        interventions: List[Intervention],
        context: Dict[str, Any],
    ) -> Optional[CounterfactualScenario]:
        """Apply interventions to create modified plan."""
        modified = copy.deepcopy(original_plan)

        for intervention in sorted(interventions, key=lambda x: -x.target_step):
            if intervention.type == InterventionType.REPLACE_ACTION:
                replacement = intervention.params.get("replacement")
                if replacement and 0 <= intervention.target_step < len(modified):
                    modified[intervention.target_step] = replacement

            elif intervention.type == InterventionType.REMOVE_ACTION:
                if 0 <= intervention.target_step < len(modified):
                    modified.pop(intervention.target_step)

            elif intervention.type == InterventionType.ADD_ACTION:
                addition = intervention.params.get("addition")
                if addition:
                    insert_idx = min(intervention.target_step, len(modified))
                    modified.insert(insert_idx, addition)

            elif intervention.type == InterventionType.MODIFY_PARAM:
                param = intervention.params.get("param")
                if param and 0 <= intervention.target_step < len(modified):
                    step = modified[intervention.target_step]
                    if "multiplier" in intervention.params:
                        current = step.get("params", {}).get(param, 1)
                        step.setdefault("params", {})[param] = current * intervention.params["multiplier"]
                    elif "increment" in intervention.params:
                        current = step.get("params", {}).get(param, 0)
                        step.setdefault("params", {})[param] = current + intervention.params["increment"]
                    elif "alternatives" in intervention.params:
                        step.setdefault("params", {})[param] = intervention.params["alternatives"][0]

            elif intervention.type == InterventionType.CHANGE_ORDER:
                swap_with = intervention.params.get("swap_with")
                if swap_with is not None and swap_with < len(modified):
                    modified[intervention.target_step], modified[swap_with] = modified[swap_with], modified[intervention.target_step]

        # Validate modified plan
        if self.plan_validator and not self.plan_validator(modified, context):
            return None

        # Predict outcome
        predicted_outcome = {}
        if self.predictor:
            predicted_outcome = self.predictor(modified, context)

        # Assess risk
        risk = 0.0
        if self.risk_assessor:
            risk = self.risk_assessor(modified, context)

        # Calculate confidence based on intervention count and types
        confidence = max(0.5, 1.0 - len(interventions) * 0.1)

        return CounterfactualScenario(
            id=str(uuid.uuid4())[:8],
            original_plan=original_plan,
            interventions=interventions,
            modified_plan=modified,
            predicted_outcome=predicted_outcome,
            confidence=confidence,
            metadata={
                "intervention_count": len(interventions),
                "types": [i.type.value for i in interventions],
                "estimated_risk": risk,
            }
        )

    def evaluate_scenario(
        self,
        scenario: CounterfactualScenario,
        context: Dict[str, Any],
    ) -> CounterfactualResult:
        """Evaluate a counterfactual scenario against the original."""
        original_outcome = {}
        if self.predictor:
            original_outcome = self.predictor(scenario.original_plan, context)

        comparison = {}
        for metric in self.config.comparison_metrics:
            orig_val = original_outcome.get(metric)
            new_val = scenario.predicted_outcome.get(metric)
            if orig_val is not None and new_val is not None:
                if isinstance(orig_val, (int, float)) and isinstance(new_val, (int, float)):
                    comparison[metric] = {
                        "original": orig_val,
                        "counterfactual": new_val,
                        "delta": new_val - orig_val,
                        "pct_change": ((new_val - orig_val) / orig_val * 100) if orig_val != 0 else 0,
                    }

        # Risk delta
        orig_risk = scenario.metadata.get("estimated_risk", 0)
        new_risk = scenario.predicted_outcome.get("risk", orig_risk)
        risk_delta = new_risk - orig_risk

        # Generate recommendation
        recommendation = self._generate_recommendation(scenario, comparison, risk_delta)

        return CounterfactualResult(
            scenario=scenario,
            comparison=comparison,
            recommendation=recommendation,
            risk_delta=risk_delta,
        )

    def _generate_recommendation(
        self,
        scenario: CounterfactualScenario,
        comparison: Dict[str, Any],
        risk_delta: float,
    ) -> str:
        """Generate natural language recommendation."""
        interventions_desc = ", ".join(i.description for i in scenario.interventions)

        if risk_delta > 0.2:
            return f"Not recommended: {interventions_desc} increases risk significantly ({risk_delta:.1%})"
        elif risk_delta > 0:
            return f"Caution: {interventions_desc} slightly increases risk ({risk_delta:.1%})"

        improvements = []
        for metric, diff in comparison.items():
            delta = diff.get("delta", 0)
            if delta > 0 and metric in ["success_probability", "quality"]:
                improvements.append(f"{metric} +{delta:.1%}")
            elif delta < 0 and metric in ["cost", "time", "risk"]:
                improvements.append(f"{metric} {delta:.1%}")

        if improvements:
            return f"Recommended: {interventions_desc} — improves {', '.join(improvements)}"
        elif risk_delta < -0.1:
            return f"Recommended: {interventions_desc} — reduces risk by {abs(risk_delta):.1%}"
        else:
            return f"Neutral: {interventions_desc} — minimal impact"

    def ask_what_if(
        self,
        question: str,
        plan: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[CounterfactualResult]:
        """Natural language counterfactual query."""
        # Parse question to extract interventions
        # Simplified: keyword-based
        focus_areas = []
        if "library" in question.lower() or "framework" in question.lower():
            focus_areas.append("dependencies")
        if "test" in question.lower():
            focus_areas.append("testing")
        if "security" in question.lower() or "secure" in question.lower():
            focus_areas.append("security")
        if "performance" in question.lower() or "speed" in question.lower():
            focus_areas.append("performance")
        if "cost" in question.lower() or "cheaper" in question.lower():
            focus_areas.append("cost")

        scenarios = self.generate_scenarios(plan, context, focus_areas)
        results = [self.evaluate_scenario(s, context) for s in scenarios]
        return results


# Global instance
_counterfactual_engine: Optional[CounterfactualEngine] = None


def get_counterfactual_engine(config: Optional[CounterfactualConfig] = None) -> CounterfactualEngine:
    """Get global counterfactual engine instance."""
    global _counterfactual_engine
    if _counterfactual_engine is None:
        _counterfactual_engine = CounterfactualEngine(config)
    return _counterfactual_engine