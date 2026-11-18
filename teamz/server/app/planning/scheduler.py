"""Time-boxed steps with deadline-aware scheduling."""

from __future__ import annotations

import heapq
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ScheduleStatus(str, Enum):
    """Schedule execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PREEMPTED = "preempted"
    TIMED_OUT = "timed_out"


@dataclass
class ScheduledStep:
    """A step in the schedule."""
    id: str
    name: str
    estimated_duration: float  # seconds
    deadline: Optional[float] = None  # Unix timestamp
    priority: int = 0  # Higher = more important
    dependencies: List[str] = field(default_factory=list)  # Step IDs
    resources: List[str] = field(default_factory=list)  # Required resources
    timeout_seconds: float = 300.0
    max_retries: int = 2
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Runtime fields
    status: ScheduleStatus = ScheduleStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    actual_duration: float = 0.0
    retry_count: int = 0
    assigned_worker: Optional[str] = None

    @property
    def is_ready(self) -> bool:
        return self.status == ScheduleStatus.PENDING

    @property
    def is_overdue(self) -> bool:
        if self.deadline is None:
            return False
        return time.time() > self.deadline

    @property
    def slack_time(self) -> float:
        """Time until deadline minus estimated duration."""
        if self.deadline is None:
            return float('inf')
        return self.deadline - time.time() - self.estimated_duration

    @property
    def urgency(self) -> float:
        """Urgency score based on deadline and priority."""
        if self.deadline is None:
            return float(self.priority)
        time_left = max(0.1, self.deadline - time.time())
        return (self.priority + 1) * (1.0 / time_left) * 1000


@dataclass
class Schedule:
    """A complete schedule."""
    id: str
    steps: Dict[str, ScheduledStep] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: ScheduleStatus = ScheduleStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_estimated_duration(self) -> float:
        return sum(s.estimated_duration for s in self.steps.values())

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps.values() if s.status == ScheduleStatus.COMPLETED)

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.steps.values() if s.status == ScheduleStatus.FAILED)


class SchedulerConfig(BaseModel):
    """Configuration for plan scheduler."""
    max_parallel_steps: int = 4
    default_timeout_seconds: float = 300.0
    preemption_enabled: bool = True
    deadline_aware: bool = True
    resource_aware: bool = True
    checkpoint_interval_seconds: float = 60.0
    slack_buffer_seconds: float = 30.0
    priority_weight: float = 1.0
    urgency_weight: float = 2.0


class PlanScheduler:
    """Schedules and executes plan steps with deadline awareness."""

    def __init__(
        self,
        config: Optional[SchedulerConfig] = None,
        resource_manager: Optional[Callable[[List[str]], bool]] = None,
        step_executor: Optional[Callable[[ScheduledStep], Tuple[bool, Any]]] = None,
    ) -> None:
        self.config = config or SchedulerConfig()
        self.resource_manager = resource_manager or self._default_resource_manager
        self.step_executor = step_executor or self._default_executor
        self._schedules: Dict[str, Schedule] = {}
        self._running = False
        self._current_schedule: Optional[Schedule] = None

    def _default_resource_manager(self, resources: List[str]) -> bool:
        """Default resource check (always available)."""
        return True

    def _default_executor(self, step: ScheduledStep) -> Tuple[bool, Any]:
        """Default step executor (simulated)."""
        # Simulate work
        time.sleep(min(step.estimated_duration, 0.1))
        return True, {"completed": True}

    def create_schedule(
        self,
        steps: List[Dict[str, Any]],
        plan_id: Optional[str] = None,
    ) -> Schedule:
        """Create a schedule from plan steps."""
        schedule = Schedule(id=plan_id or str(uuid.uuid4())[:8])

        for i, step_data in enumerate(steps):
            step = ScheduledStep(
                id=step_data.get("id", f"step_{i}"),
                name=step_data.get("name", step_data.get("tool", f"step_{i}")),
                estimated_duration=step_data.get("estimated_duration", 60.0),
                deadline=step_data.get("deadline"),
                priority=step_data.get("priority", 0),
                dependencies=step_data.get("dependencies", []),
                resources=step_data.get("resources", []),
                timeout_seconds=step_data.get("timeout_seconds", self.config.default_timeout_seconds),
                max_retries=step_data.get("max_retries", 2),
                metadata=step_data.get("metadata", {}),
            )
            schedule.steps[step.id] = step

        # Validate dependencies
        self._validate_dependencies(schedule)

        return schedule

    def _validate_dependencies(self, schedule: Schedule) -> None:
        """Validate step dependencies."""
        step_ids = set(schedule.steps.keys())
        for step in schedule.steps.values():
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(f"Step {step.id} depends on unknown step: {dep}")

    async def execute_schedule(
        self,
        schedule: Schedule,
        progress_callback: Optional[Callable[[ScheduledStep, ScheduleStatus], None]] = None,
    ) -> Schedule:
        """Execute a schedule."""
        self._running = True
        self._current_schedule = schedule
        schedule.status = ScheduleStatus.RUNNING
        schedule.started_at = time.time()

        try:
            while self._running and not self._is_complete(schedule):
                # Get ready steps
                ready_steps = self._get_ready_steps(schedule)

                # Select steps to run (up to max_parallel)
                selected = self._select_steps(ready_steps, schedule)

                # Execute selected steps
                if selected:
                    await self._execute_steps(selected, schedule, progress_callback)
                else:
                    # No ready steps - wait or check for deadlock
                    if self._check_deadlock(schedule):
                        break
                    await asyncio.sleep(1.0)

            # Finalize
            schedule.completed_at = time.time()
            if self._has_failures(schedule):
                schedule.status = ScheduleStatus.FAILED
            else:
                schedule.status = ScheduleStatus.COMPLETED

        finally:
            self._running = False
            self._current_schedule = None

        return schedule

    def _is_complete(self, schedule: Schedule) -> bool:
        """Check if all steps are done."""
        return all(
            s.status in (ScheduleStatus.COMPLETED, ScheduleStatus.FAILED, ScheduleStatus.TIMED_OUT)
            for s in schedule.steps.values()
        )

    def _has_failures(self, schedule: Schedule) -> bool:
        """Check if any required steps failed."""
        return any(
            s.status == ScheduleStatus.FAILED and not s.metadata.get("optional", False)
            for s in schedule.steps.values()
        )

    def _get_ready_steps(self, schedule: Schedule) -> List[ScheduledStep]:
        """Get steps ready to execute."""
        ready = []
        for step in schedule.steps.values():
            if step.status != ScheduleStatus.PENDING:
                continue

            # Check dependencies
            deps_met = all(
                schedule.steps[dep].status == ScheduleStatus.COMPLETED
                for dep in step.dependencies
            )
            if not deps_met:
                continue

            # Check resources
            if self.config.resource_aware and step.resources:
                if not self.resource_manager(step.resources):
                    continue

            # Check deadline
            if step.is_overdue:
                step.status = ScheduleStatus.TIMED_OUT
                continue

            ready.append(step)

        return ready

    def _select_steps(
        self,
        ready_steps: List[ScheduledStep],
        schedule: Schedule,
    ) -> List[ScheduledStep]:
        """Select steps to execute based on priority/urgency."""
        if not ready_steps:
            return []

        # Sort by urgency (deadline-aware) then priority
        if self.config.deadline_aware:
            ready_steps.sort(
                key=lambda s: (s.urgency * self.config.urgency_weight + s.priority * self.config.priority_weight),
                reverse=True,
            )
        else:
            ready_steps.sort(key=lambda s: s.priority, reverse=True)

        # Take up to max_parallel
        return ready_steps[:self.config.max_parallel_steps]

    async def _execute_steps(
        self,
        steps: List[ScheduledStep],
        schedule: Schedule,
        progress_callback: Optional[Callable[[ScheduledStep, ScheduleStatus], None]] = None,
    ) -> None:
        """Execute multiple steps in parallel."""
        tasks = []
        for step in steps:
            step.status = ScheduleStatus.RUNNING
            step.start_time = time.time()
            if progress_callback:
                progress_callback(step, ScheduleStatus.RUNNING)
            tasks.append(self._execute_step(step, schedule))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for step, result in zip(steps, results):
            step.end_time = time.time()
            step.actual_duration = step.end_time - step.start_time

            if isinstance(result, Exception):
                step.status = ScheduleStatus.FAILED
                step.metadata["error"] = str(result)
            elif isinstance(result, tuple) and len(result) == 2:
                success, output = result
                step.status = ScheduleStatus.COMPLETED if success else ScheduleStatus.FAILED
                step.metadata["output"] = output
                if not success:
                    step.metadata["error"] = output.get("error", "Unknown error")
            else:
                step.status = ScheduleStatus.COMPLETED
                step.metadata["output"] = result

            if progress_callback:
                progress_callback(step, step.status)

            # Handle retry
            if step.status == ScheduleStatus.FAILED and step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = ScheduleStatus.PENDING
                step.start_time = None
                step.end_time = None

    async def _execute_step(
        self,
        step: ScheduledStep,
        schedule: Schedule,
    ) -> Tuple[bool, Any]:
        """Execute a single step with timeout."""
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self.step_executor, step),
                timeout=step.timeout_seconds,
            )
        except asyncio.TimeoutError:
            step.status = ScheduleStatus.TIMED_OUT
            return False, {"error": f"Timeout after {step.timeout_seconds}s"}
        except Exception as e:
            return False, {"error": str(e)}

    def _check_deadlock(self, schedule: Schedule) -> bool:
        """Check for deadlock (no progress possible)."""
        pending = [s for s in schedule.steps.values() if s.status == ScheduleStatus.PENDING]
        if not pending:
            return True

        # Check if any pending step can proceed
        for step in pending:
            deps_met = all(
                schedule.steps[dep].status == ScheduleStatus.COMPLETED
                for dep in step.dependencies
            )
            if deps_met and (not self.config.resource_aware or not step.resources or self.resource_manager(step.resources)):
                return False

        return True  # Deadlock detected

    def preempt_step(
        self,
        schedule: Schedule,
        step_id: str,
        reason: str = "preempted",
    ) -> bool:
        """Preempt a running step."""
        if not self.config.preemption_enabled:
            return False

        step = schedule.steps.get(step_id)
        if not step or step.status != ScheduleStatus.RUNNING:
            return False

        step.status = ScheduleStatus.PREEMPTED
        step.metadata["preemption_reason"] = reason
        step.end_time = time.time()
        step.actual_duration = step.end_time - step.start_time if step.start_time else 0
        return True

    def reschedule_step(
        self,
        schedule: Schedule,
        step_id: str,
        new_deadline: Optional[float] = None,
        new_priority: Optional[int] = None,
    ) -> bool:
        """Reschedule a step."""
        step = schedule.steps.get(step_id)
        if not step:
            return False

        if new_deadline is not None:
            step.deadline = new_deadline
        if new_priority is not None:
            step.priority = new_priority

        return True

    def get_schedule_status(self, schedule: Schedule) -> Dict[str, Any]:
        """Get detailed schedule status."""
        status_counts = {}
        for status in ScheduleStatus:
            status_counts[status.value] = sum(
                1 for s in schedule.steps.values() if s.status == status
            )

        return {
            "schedule_id": schedule.id,
            "status": schedule.status.value,
            "progress": f"{schedule.completed_steps}/{len(schedule.steps)}",
            "step_counts": status_counts,
            "started_at": schedule.started_at,
            "elapsed_seconds": time.time() - schedule.started_at if schedule.started_at else 0,
            "estimated_remaining": sum(
                s.estimated_duration for s in schedule.steps.values()
                if s.status == ScheduleStatus.PENDING
            ),
            "overdue_steps": [
                s.id for s in schedule.steps.values()
                if s.is_overdue and s.status == ScheduleStatus.PENDING
            ],
        }


# Global instance
_plan_scheduler: Optional[PlanScheduler] = None


def get_plan_scheduler(config: Optional[SchedulerConfig] = None) -> PlanScheduler:
    """Get global plan scheduler instance."""
    global _plan_scheduler
    if _plan_scheduler is None:
        _plan_scheduler = PlanScheduler(config)
    return _plan_scheduler