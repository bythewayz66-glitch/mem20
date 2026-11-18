"""Contingency planning: auto-generate fallback steps."""

from __future__ import annotations

import copy
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class FailureMode(str, Enum):
    """Types of failure modes."""
    TIMEOUT = "timeout"
    ERROR = "error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    PERMISSION_DENIED = "permission_denied"
    DEPENDENCY_FAILED = "dependency_failed"
    NETWORK_ERROR = "network_error"
    VALIDATION_FAILED = "validation_failed"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


class FallbackStrategy(str, Enum):
    """Fallback strategies."""
    RETRY = "retry"                    # Retry with same parameters
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry with exponential backoff
    ALTERNATIVE_TOOL = "alternative_tool"      # Use different tool
    SKIP_STEP = "skip_step"            # Skip this step
    ROLLBACK = "rollback"              # Rollback previous steps
    MANUAL_INTERVENTION = "manual_intervention"  # Require human
    DEGRADED_MODE = "degraded_mode"    # Continue with reduced functionality
    COMPENSATING_ACTION = "compensating_action"  # Run compensating transaction


@dataclass
class FallbackStep:
    """A fallback step."""
    id: str
    strategy: FallbackStrategy
    description: str
    trigger_conditions: List[FailureMode] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 1
    timeout_seconds: float = 60.0
    prerequisite_step_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackPlan:
    """A complete fallback plan for a step."""
    step_id: str
    step_name: str
    primary_fallback: FallbackStep
    alternative_fallbacks: List[FallbackStep] = field(default_factory=list)
    escalation_fallback: Optional[FallbackStep] = None
    risk_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContingencyPlan:
    """Full contingency plan for entire plan."""
    plan_id: str
    fallback_plans: Dict[str, FallbackPlan] = field(default_factory=dict)
    global_fallbacks: List[FallbackStep] = field(default_factory=list)
    rollback_points: List[str] = field(default_factory=list)  # Step IDs where rollback possible
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContingencyConfig(BaseModel):
    """Configuration for contingency planner."""
    max_fallbacks_per_step: int = 3
    default_retry_attempts: int = 2
    default_backoff_base: float = 2.0
    default_backoff_max: float = 60.0
    enable_rollbacks: bool = True
    rollback_checkpoint_interval: int = 3  # Every N steps
    auto_generate: bool = True
    fallback_timeout_multiplier: float = 1.5


class ContingencyPlanner:
    """Generates contingency plans with fallback steps."""

    def __init__(
        self,
        config: Optional[ContingencyConfig] = None,
        tool_alternatives: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        self.config = config or ContingencyConfig()
        self.tool_alternatives = tool_alternatives or self._default_alternatives()

    def _default_alternatives(self) -> Dict[str, List[str]]:
        """Default tool alternatives."""
        return {
            "git": ["gh", "manual"],
            "npm": ["yarn", "pnpm", "manual"],
            "pip": ["uv", "pipx", "manual"],
            "pytest": ["vitest", "jest", "unittest"],
            "ruff": ["flake8", "pylint", "black"],
            "mypy": ["pyright", "pytype"],
            "docker": ["podman", "buildah"],
            "kubectl": ["helm", "kustomize"],
            "terraform": ["pulumi", "crossplane"],
            "curl": ["wget", "httpie"],
            "ssh": ["scp", "rsync"],
        }

    def generate_contingency_plan(
        self,
        plan: List[Dict[str, Any]],
        risk_assessments: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ContingencyPlan:
        """Generate full contingency plan."""
        plan_id = str(uuid.uuid4())[:8]
        contingency = ContingencyPlan(plan_id=plan_id)

        # Determine rollback points
        contingency.rollback_points = self._identify_rollback_points(plan)

        # Generate fallback for each step
        for i, step in enumerate(plan):
            step_id = step.get("id", f"step_{i}")
            fallback_plan = self._generate_step_fallback(
                step, i, plan, risk_assessments, context
            )
            contingency.fallback_plans[step_id] = fallback_plan

        # Add global fallbacks
        contingency.global_fallbacks = self._generate_global_fallbacks(plan, context)

        return contingency

    def _identify_rollback_points(self, plan: List[Dict[str, Any]]) -> List[str]:
        """Identify steps where rollback checkpoints should be created."""
        rollback_points = []

        for i, step in enumerate(plan):
            # Create checkpoint before irreversible steps
            if self._is_irreversible(step):
                if i > 0:
                    rollback_points.append(plan[i-1].get("id", f"step_{i-1}"))

            # Also checkpoint at intervals
            if i > 0 and i % self.config.rollback_checkpoint_interval == 0:
                rollback_points.append(step.get("id", f"step_{i}"))

        return rollback_points

    def _is_irreversible(self, step: Dict[str, Any]) -> bool:
        """Check if a step is irreversible."""
        irreversible_tools = {
            "terraform", "kubectl", "docker", "database",
            "git", "npm", "pip", "kubectl",
        }
        tool = step.get("name", step.get("tool", ""))
        return tool in irreversible_tools or step.get("destructive", False)

    def _generate_step_fallback(
        self,
        step: Dict[str, Any],
        index: int,
        plan: List[Dict[str, Any]],
        risk_assessments: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> FallbackPlan:
        """Generate fallback plan for a single step."""
        step_id = step.get("id", f"step_{index}")
        step_name = step.get("name", step.get("tool", "unknown"))
        tool = step.get("name", step.get("tool", ""))

        fallbacks = []

        # 1. Retry with backoff (always available)
        fallbacks.append(FallbackStep(
            id=f"{step_id}_retry",
            strategy=FallbackStrategy.RETRY_WITH_BACKOFF,
            description=f"Retry {step_name} with exponential backoff",
            trigger_conditions=[FailureMode.TIMEOUT, FailureMode.ERROR, FailureMode.NETWORK_ERROR],
            params={
                "max_attempts": self.config.default_retry_attempts,
                "backoff_base": self.config.default_backoff_base,
                "backoff_max": self.config.default_backoff_max,
            },
            max_attempts=self.config.default_retry_attempts,
        ))

        # 2. Alternative tool
        alternatives = self.tool_alternatives.get(tool, [])
        if alternatives:
            alt_tool = alternatives[0]
            fallbacks.append(FallbackStep(
                id=f"{step_id}_alt",
                strategy=FallbackStrategy.ALTERNATIVE_TOOL,
                description=f"Use {alt_tool} instead of {tool}",
                trigger_conditions=[FailureMode.ERROR, FailureMode.PERMISSION_DENIED],
                params={
                    "tool": alt_tool,
                    "original_args": step.get("params", step.get("args", {})),
                },
            ))

        # 3. Skip step (if not critical)
        if not step.get("critical", False) and not step.get("required", False):
            fallbacks.append(FallbackStep(
                id=f"{step_id}_skip",
                strategy=FallbackStrategy.SKIP_STEP,
                description=f"Skip {step_name} and continue",
                trigger_conditions=[FailureMode.ERROR, FailureMode.RESOURCE_EXHAUSTED],
                params={},
            ))

        # 4. Rollback (if enabled and rollback point exists)
        if self.config.enable_rollbacks:
            rollback_point = self._find_rollback_point(step_id, plan)
            if rollback_point:
                fallbacks.append(FallbackStep(
                    id=f"{step_id}_rollback",
                    strategy=FallbackStrategy.ROLLBACK,
                    description=f"Rollback to {rollback_point}",
                    trigger_conditions=[FailureMode.ERROR, FailureMode.DATA_LOSS],
                    params={"rollback_to": rollback_point},
                ))

        # 5. Degraded mode
        fallbacks.append(FallbackStep(
            id=f"{step_id}_degraded",
            strategy=FallbackStrategy.DEGRADED_MODE,
            description=f"Continue with reduced functionality for {step_name}",
            trigger_conditions=[FailureMode.VALIDATION_FAILED, FailureMode.RATE_LIMITED],
            params={"degraded": True},
        ))

        # 6. Compensating action (for destructive operations)
        if self._is_destructive(step):
            fallbacks.append(FallbackStep(
                id=f"{step_id}_compensate",
                strategy=FallbackStrategy.COMPENSATING_ACTION,
                description=f"Run compensating action for {step_name}",
                trigger_conditions=[FailureMode.ERROR],
                params={
                    "compensating_action": self._get_compensating_action(step),
                },
            ))

        # Select primary fallback (first viable)
        primary = fallbacks[0] if fallbacks else FallbackStep(
            id=f"{step_id}_manual",
            strategy=FallbackStrategy.MANUAL_INTERVENTION,
            description=f"Manual intervention required for {step_name}",
            trigger_conditions=[FailureMode.UNKNOWN],
            params={},
        )

        # Alternative fallbacks (excluding primary)
        alternatives = fallbacks[1:self.config.max_fallbacks_per_step]

        # Escalation fallback (last resort)
        escalation = FallbackStep(
            id=f"{step_id}_escalate",
            strategy=FallbackStrategy.MANUAL_INTERVENTION,
            description=f"Escalate to human for {step_name}",
            trigger_conditions=[FailureMode.UNKNOWN],
            params={"notify": context.get("stakeholders", []) if context else []},
        ) if fallbacks else None

        return FallbackPlan(
            step_id=step_id,
            step_name=step_name,
            primary_fallback=primary,
            alternative_fallbacks=alternatives,
            escalation_fallback=escalation,
        )

    def _find_rollback_point(
        self,
        step_id: str,
        plan: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Find nearest rollback point before this step."""
        for i, step in enumerate(plan):
            if step.get("id") == step_id:
                # Look backwards for checkpoint
                for j in range(i - 1, -1, -1):
                    if not self._is_irreversible(plan[j]):
                        return plan[j].get("id", f"step_{j}")
        return None

    def _is_destructive(self, step: Dict[str, Any]) -> bool:
        """Check if step is destructive."""
        destructive_tools = {"terraform", "kubectl", "git", "database", "docker"}
        tool = step.get("name", step.get("tool", ""))
        return tool in destructive_tools or step.get("destructive", False)

    def _get_compensating_action(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Get compensating action for a destructive step."""
        tool = step.get("name", step.get("tool", ""))

        compensations = {
            "terraform": {"action": "terraform destroy", "args": ["-auto-approve"]},
            "kubectl": {"action": "kubectl rollback", "args": []},
            "git": {"action": "git reset --hard HEAD~1", "args": []},
            "docker": {"action": "docker stop && docker rm", "args": []},
            "database": {"action": "restore from backup", "args": []},
        }

        return compensations.get(tool, {"action": "manual", "args": []})

    def _generate_global_fallbacks(
        self,
        plan: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> List[FallbackStep]:
        """Generate global fallback strategies."""
        return [
            FallbackStep(
                id="global_abort",
                strategy=FallbackStrategy.MANUAL_INTERVENTION,
                description="Abort entire plan and notify stakeholders",
                trigger_conditions=[FailureMode.UNKNOWN],
                params={"notify": context.get("stakeholders", []) if context else []},
            ),
            FallbackStep(
                id="global_rollback",
                strategy=FallbackStrategy.ROLLBACK,
                description="Rollback all completed steps",
                trigger_conditions=[FailureMode.ERROR, FailureMode.UNKNOWN],
                params={"full_rollback": True},
            ),
        ]

    def execute_fallback(
        self,
        fallback: FallbackStep,
        context: Dict[str, Any],
    ) -> Tuple[bool, Any]:
        """Execute a fallback step."""
        # This would be implemented to actually run the fallback
        # Returns (success, result)
        strategy = fallback.strategy

        if strategy == FallbackStrategy.RETRY_WITH_BACKOFF:
            return self._execute_retry(fallback, context)
        elif strategy == FallbackStrategy.ALTERNATIVE_TOOL:
            return self._execute_alternative(fallback, context)
        elif strategy == FallbackStrategy.SKIP_STEP:
            return True, {"skipped": True}
        elif strategy == FallbackStrategy.ROLLBACK:
            return self._execute_rollback(fallback, context)
        elif strategy == FallbackStrategy.DEGRADED_MODE:
            return True, {"degraded": True}
        elif strategy == FallbackStrategy.COMPENSATING_ACTION:
            return self._execute_compensation(fallback, context)
        else:
            return False, {"error": "Manual intervention required"}

    def _execute_retry(self, fallback: FallbackStep, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute retry with backoff."""
        params = fallback.params
        max_attempts = params.get("max_attempts", 3)
        backoff_base = params.get("backoff_base", 2.0)
        backoff_max = params.get("backoff_max", 60.0)

        for attempt in range(max_attempts):
            # Would execute the original step here
            # For now, simulate
            if attempt > 0:
                wait_time = min(backoff_base ** attempt, backoff_max)
                time.sleep(wait_time)

        return True, {"retried": True, "attempts": max_attempts}

    def _execute_alternative(self, fallback: FallbackStep, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute alternative tool."""
        params = fallback.params
        alt_tool = params.get("tool")
        original_args = params.get("original_args", {})

        # Would execute alternative tool here
        return True, {"alternative_tool": alt_tool, "args": original_args}

    def _execute_rollback(self, fallback: FallbackStep, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute rollback."""
        params = fallback.params
        rollback_to = params.get("rollback_to")

        return True, {"rolled_back_to": rollback_to}

    def _execute_compensation(self, fallback: FallbackStep, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute compensating action."""
        params = fallback.params
        action = params.get("compensating_action", {})

        return True, {"compensated": True, "action": action}


# Global instance
_contingency_planner: Optional[ContingencyPlanner] = None


def get_contingency_planner(config: Optional[ContingencyConfig] = None) -> ContingencyPlanner:
    """Get global contingency planner instance."""
    global _contingency_planner
    if _contingency_planner is None:
        _contingency_planner = ContingencyPlanner(config)
    return _contingency_planner