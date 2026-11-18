"""Hierarchical Task Network (HTN) planner for complex goal decomposition."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


class PredicateType(str, Enum):
    """Types of state predicates."""
    FACT = "fact"           # Simple boolean fact
    NUMERIC = "numeric"     # Numeric comparison
    SET = "set"             # Set membership
    FUNCTION = "function"   # Custom predicate function


@dataclass
class Predicate:
    """A state predicate that can be true or false."""
    name: str
    type: PredicateType = PredicateType.FACT
    args: Tuple = field(default_factory=tuple)
    value: Any = None  # For numeric/set types
    func: Optional[Callable] = None  # For function type

    def evaluate(self, state: "HTNState") -> bool:
        """Evaluate predicate against state."""
        if self.type == PredicateType.FACT:
            return state.has_fact(self.name, self.args)
        elif self.type == PredicateType.NUMERIC:
            return state.check_numeric(self.name, self.args, self.value)
        elif self.type == PredicateType.SET:
            return state.check_set(self.name, self.args, self.value)
        elif self.type == PredicateType.FUNCTION and self.func:
            return self.func(state, *self.args)
        return False

    def __hash__(self) -> int:
        return hash((self.name, self.type, self.args, self.value))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Predicate):
            return False
        return (self.name == other.name and
                self.type == other.type and
                self.args == other.args and
                self.value == other.value)

    def __str__(self) -> str:
        if self.type == PredicateType.FACT:
            return f"{self.name}{self.args}"
        elif self.type == PredicateType.NUMERIC:
            return f"{self.name}{self.args} == {self.value}"
        elif self.type == PredicateType.SET:
            return f"{self.value} in {self.name}{self.args}"
        return f"{self.name}{self.args}"


@dataclass
class HTNState:
    """World state for HTN planning."""
    facts: Dict[str, Set[Tuple]] = field(default_factory=dict)  # fact_name -> set of arg tuples
    numeric: Dict[str, Dict[Tuple, float]] = field(default_factory=dict)  # name -> {args: value}
    sets: Dict[str, Dict[Tuple, Set]] = field(default_factory=dict)  # name -> {args: set}
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_fact(self, name: str, args: Tuple = ()) -> bool:
        return name in self.facts and args in self.facts[name]

    def add_fact(self, name: str, args: Tuple = ()) -> None:
        if name not in self.facts:
            self.facts[name] = set()
        self.facts[name].add(args)

    def remove_fact(self, name: str, args: Tuple = ()) -> None:
        if name in self.facts:
            self.facts[name].discard(args)

    def check_numeric(self, name: str, args: Tuple, expected: float) -> bool:
        if name in self.numeric and args in self.numeric[name]:
            return self.numeric[name][args] == expected
        return False

    def set_numeric(self, name: str, args: Tuple, value: float) -> None:
        if name not in self.numeric:
            self.numeric[name] = {}
        self.numeric[name][args] = value

    def check_set(self, name: str, args: Tuple, expected: Set) -> bool:
        if name in self.sets and args in self.sets[name]:
            return expected.issubset(self.sets[name][args])
        return False

    def set_set(self, name: str, args: Tuple, value: Set) -> None:
        if name not in self.sets:
            self.sets[name] = {}
        self.sets[name][args] = value

    def copy(self) -> "HTNState":
        """Create a deep copy of the state."""
        new_state = HTNState()
        new_state.facts = {k: set(v) for k, v in self.facts.items()}
        new_state.numeric = {k: dict(v) for k, v in self.numeric.items()}
        new_state.sets = {k: {k2: set(v2) for k2, v2 in v.items()} for k, v in self.sets.items()}
        new_state.metadata = dict(self.metadata)
        return new_state

    def apply_effects(self, effects: List[Tuple[str, Any]]) -> None:
        """Apply a list of effects to the state."""
        for effect in effects:
            if isinstance(effect, tuple) and len(effect) >= 2:
                op, *params = effect
                if op == "add_fact":
                    self.add_fact(params[0], tuple(params[1:]) if len(params) > 1 else ())
                elif op == "remove_fact":
                    self.remove_fact(params[0], tuple(params[1:]) if len(params) > 1 else ())
                elif op == "set_numeric":
                    self.set_numeric(params[0], tuple(params[1:-1]), params[-1])
                elif op == "set_set":
                    self.set_set(params[0], tuple(params[1:-1]), params[-1])


@dataclass
class HTNOperator:
    """A primitive operator (executable action)."""
    name: str
    preconditions: List[Predicate] = field(default_factory=list)
    effects: List[Tuple] = field(default_factory=list)  # ("add_fact", "name", args...)
    cost: float = 1.0
    executor: Optional[Callable] = None  # Async function to execute
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_applicable(self, state: HTNState) -> bool:
        """Check if all preconditions are satisfied."""
        return all(p.evaluate(state) for p in self.preconditions)

    def apply(self, state: HTNState) -> HTNState:
        """Apply effects to create new state."""
        new_state = state.copy()
        new_state.apply_effects(self.effects)
        return new_state

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the operator."""
        if self.executor:
            return await self.executor(*args, **kwargs)
        return None


@dataclass
class HTNMethod:
    """A method for decomposing a compound task."""
    name: str
    task_name: str  # The compound task this method decomposes
    preconditions: List[Predicate] = field(default_factory=list)
    subtasks: List["HTNTask"] = field(default_factory=list)  # Ordered subtasks
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_applicable(self, state: HTNState) -> bool:
        """Check if all preconditions are satisfied."""
        return all(p.evaluate(state) for p in self.preconditions)


@dataclass
class HTNTask:
    """A task (primitive or compound)."""
    name: str
    args: Tuple = field(default_factory=tuple)
    is_primitive: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"


@dataclass
class HTNGoal:
    """A goal to achieve."""
    name: str
    conditions: List[Predicate] = field(default_factory=list)
    priority: int = 0
    deadline: Optional[float] = None  # Unix timestamp

    def is_satisfied(self, state: HTNState) -> bool:
        """Check if goal conditions are satisfied."""
        return all(c.evaluate(state) for c in self.conditions)


@dataclass
class HTNPlan:
    """A complete HTN plan."""
    id: str
    tasks: List[HTNTask]
    goal: HTNGoal
    initial_state: HTNState
    final_state: HTNState
    total_cost: float = 0.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_primitive_sequence(self) -> List[HTNOperator]:
        """Extract primitive operators in execution order."""
        # This would be populated during planning
        return []


class HTNConfig(BaseModel):
    """Configuration for HTN planner."""
    max_depth: int = 20
    max_nodes: int = 10000
    heuristic_weight: float = 1.0
    use_heuristic: bool = True
    timeout_seconds: float = 30.0
    allow_partial_plans: bool = False


class HTNPlanner:
    """HTN planner using forward decomposition."""

    def __init__(self, config: Optional[HTNConfig] = None) -> None:
        self.config = config or HTNConfig()
        self._operators: Dict[str, HTNOperator] = {}
        self._methods: Dict[str, List[HTNMethod]] = {}  # task_name -> methods
        self._task_cache: Dict[str, List[HTNTask]] = {}

    def register_operator(self, operator: HTNOperator) -> None:
        """Register a primitive operator."""
        self._operators[operator.name] = operator

    def register_method(self, method: HTNMethod) -> None:
        """Register a decomposition method."""
        if method.task_name not in self._methods:
            self._methods[method.task_name] = []
        self._methods[method.task_name].append(method)

    def get_operators(self) -> List[HTNOperator]:
        """Get all registered operators."""
        return list(self._operators.values())

    def get_methods(self, task_name: str) -> List[HTNMethod]:
        """Get methods for a compound task."""
        return self._methods.get(task_name, [])

    def plan(
        self,
        initial_state: HTNState,
        goal: HTNGoal,
        start_tasks: Optional[List[HTNTask]] = None,
    ) -> Optional[HTNPlan]:
        """
        Find a plan to achieve the goal from initial state.
        Returns HTNPlan or None if no plan found.
        """
        start_time = time.time()
        nodes_expanded = 0

        # Initial task network
        if start_tasks is None:
            # Create a top-level task from goal
            start_tasks = [HTNTask(name=goal.name, args=(), is_primitive=False)]

        # Search queue: (state, task_network, plan_so_far, cost)
        from collections import deque
        queue = deque()
        queue.append((initial_state, start_tasks, [], 0.0))

        visited = set()

        while queue and nodes_expanded < self.config.max_nodes:
            if time.time() - start_time > self.config.timeout_seconds:
                break

            state, tasks, plan, cost = queue.popleft()
            nodes_expanded += 1

            # Check if goal satisfied
            if goal.is_satisfied(state):
                return HTNPlan(
                    id=str(uuid.uuid4()),
                    tasks=plan,
                    goal=goal,
                    initial_state=initial_state,
                    final_state=state,
                    total_cost=cost,
                )

            if not tasks:
                continue

            # Get next task
            current_task = tasks[0]
            remaining_tasks = tasks[1:]

            # If primitive, try to apply operator
            if current_task.is_primitive:
                operator = self._operators.get(current_task.name)
                if operator and operator.is_applicable(state):
                    new_state = operator.apply(state)
                    new_plan = plan + [current_task]
                    new_cost = cost + operator.cost
                    queue.append((new_state, remaining_tasks, new_plan, new_cost))
                continue

            # Compound task - try methods
            methods = self._methods.get(current_task.name, [])
            for method in methods:
                if method.is_applicable(state):
                    # Create new task network: method subtasks + remaining
                    new_tasks = list(method.subtasks) + remaining_tasks
                    queue.append((state, new_tasks, plan, cost))

        return None

    def plan_with_heuristic(
        self,
        initial_state: HTNState,
        goal: HTNGoal,
        start_tasks: Optional[List[HTNTask]] = None,
        heuristic: Optional[Callable[[HTNState, HTNGoal], float]] = None,
    ) -> Optional[HTNPlan]:
        """A* search with heuristic."""
        if not self.config.use_heuristic or heuristic is None:
            return self.plan(initial_state, goal, start_tasks)

        import heapq

        start_time = time.time()
        nodes_expanded = 0

        if start_tasks is None:
            start_tasks = [HTNTask(name=goal.name, args=(), is_primitive=False)]

        # Priority queue: (f_score, g_score, counter, state, tasks, plan)
        counter = 0
        queue = []
        h = heuristic(initial_state, goal)
        heapq.heappush(queue, (h, 0.0, counter, initial_state, start_tasks, []))
        counter += 1

        visited = set()

        while queue and nodes_expanded < self.config.max_nodes:
            if time.time() - start_time > self.config.timeout_seconds:
                break

            f_score, g_score, _, state, tasks, plan = heapq.heappop(queue)
            nodes_expanded += 1

            if goal.is_satisfied(state):
                return HTNPlan(
                    id=str(uuid.uuid4()),
                    tasks=plan,
                    goal=goal,
                    initial_state=initial_state,
                    final_state=state,
                    total_cost=g_score,
                )

            if not tasks:
                continue

            current_task = tasks[0]
            remaining_tasks = tasks[1:]

            if current_task.is_primitive:
                operator = self._operators.get(current_task.name)
                if operator and operator.is_applicable(state):
                    new_state = operator.apply(state)
                    new_plan = plan + [current_task]
                    new_g = g_score + operator.cost
                    new_h = heuristic(new_state, goal)
                    heapq.heappush(queue, (new_g + new_h, new_g, counter, new_state, remaining_tasks, new_plan))
                    counter += 1
                continue

            methods = self._methods.get(current_task.name, [])
            for method in methods:
                if method.is_applicable(state):
                    new_tasks = list(method.subtasks) + remaining_tasks
                    new_h = heuristic(state, goal)
                    heapq.heappush(queue, (g_score + new_h, g_score, counter, state, new_tasks, plan))
                    counter += 1

        return None


# --- Built-in operators for common operations ---

def create_operator(
    name: str,
    preconditions: List[Predicate],
    effects: List[Tuple],
    cost: float = 1.0,
    executor: Optional[Callable] = None,
) -> HTNOperator:
    """Factory for creating operators."""
    return HTNOperator(
        name=name,
        preconditions=preconditions,
        effects=effects,
        cost=cost,
        executor=executor,
    )


def create_method(
    name: str,
    task_name: str,
    preconditions: List[Predicate],
    subtasks: List[HTNTask],
) -> HTNMethod:
    """Factory for creating methods."""
    return HTNMethod(
        name=name,
        task_name=task_name,
        preconditions=preconditions,
        subtasks=subtasks,
    )


# --- Heuristic functions ---

def goal_distance_heuristic(state: HTNState, goal: HTNGoal) -> float:
    """Simple heuristic: count unsatisfied goal conditions."""
    unsatisfied = sum(1 for c in goal.conditions if not c.evaluate(state))
    return float(unsatisfied)


def relaxed_plan_heuristic(state: HTNState, goal: HTNGoal) -> float:
    """Relaxed plan heuristic (ignore delete effects)."""
    # Simplified: just count missing preconditions
    return goal_distance_heuristic(state, goal)


# Global instance
_htn_planner: Optional[HTNPlanner] = None


def get_htn_planner(config: Optional[HTNConfig] = None) -> HTNPlanner:
    """Get global HTN planner instance."""
    global _htn_planner
    if _htn_planner is None:
        _htn_planner = HTNPlanner(config)
    return _htn_planner