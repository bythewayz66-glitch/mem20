"""Monte Carlo Tree Search (MCTS) for step selection and outcome simulation."""

from __future__ import annotations

import math
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


@dataclass
class MCTSState:
    """State for MCTS simulation."""
    data: Dict[str, Any] = field(default_factory=dict)
    step: int = 0
    is_terminal: bool = False
    reward: float = 0.0

    def copy(self) -> "MCTSState":
        new_state = MCTSState()
        new_state.data = dict(self.data)
        new_state.step = self.step
        new_state.is_terminal = self.is_terminal
        new_state.reward = self.reward
        return new_state

    def get_hash(self) -> str:
        """Get a hash for transposition table."""
        import hashlib
        content = str(sorted(self.data.items())) + str(self.step)
        return hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class MCTSAction:
    """An action in the MCTS."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    cost: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.name, tuple(sorted(self.params.items()))))


@dataclass
class MCTSNode:
    """A node in the MCTS tree."""
    state: MCTSState
    parent: Optional["MCTSNode"] = None
    action: Optional[MCTSAction] = None
    children: Dict[str, "MCTSNode"] = field(default_factory=dict)
    visits: int = 0
    total_reward: float = 0.0
    untried_actions: List[MCTSAction] = field(default_factory=list)
    depth: int = 0

    @property
    def average_reward(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.total_reward / self.visits

    @property
    def uct_value(self) -> float:
        if self.visits == 0:
            return float('inf')
        if self.parent is None:
            return self.average_reward
        exploration = math.sqrt(2 * math.log(self.parent.visits) / self.visits)
        return self.average_reward + exploration

    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def add_child(self, action: MCTSAction, state: MCTSState) -> "MCTSNode":
        child = MCTSNode(
            state=state,
            parent=self,
            action=action,
            depth=self.depth + 1,
        )
        self.children[action.name] = child
        return child


class MCTSConfig(BaseModel):
    """Configuration for MCTS planner."""
    max_iterations: int = 1000
    max_depth: int = 50
    max_time_seconds: float = 10.0
    exploration_constant: float = 1.414  # sqrt(2)
    discount_factor: float = 0.95
    rollout_policy: str = "random"  # random, heuristic, greedy
    num_rollouts: int = 1
    parallel_rollouts: bool = False
    transposition_table: bool = True
    progressive_widening: bool = False
    widening_factor: float = 0.5


class MCTSPlanner:
    """Monte Carlo Tree Search planner for step selection."""

    def __init__(
        self,
        config: Optional[MCTSConfig] = None,
        get_actions_fn: Optional[Callable[[MCTSState], List[MCTSAction]]] = None,
        apply_action_fn: Optional[Callable[[MCTSState, MCTSAction], MCTSState]] = None,
        is_terminal_fn: Optional[Callable[[MCTSState], bool]] = None,
        reward_fn: Optional[Callable[[MCTSState], float]] = None,
        heuristic_fn: Optional[Callable[[MCTSState], float]] = None,
    ) -> None:
        self.config = config or MCTSConfig()
        self.get_actions = get_actions_fn or self._default_get_actions
        self.apply_action = apply_action_fn or self._default_apply_action
        self.is_terminal = is_terminal_fn or self._default_is_terminal
        self.reward_fn = reward_fn or self._default_reward
        self.heuristic_fn = heuristic_fn
        self._transposition_table: Dict[str, MCTSNode] = {}

    def _default_get_actions(self, state: MCTSState) -> List[MCTSAction]:
        """Default: return available actions from state metadata."""
        return state.data.get("available_actions", [])

    def _default_apply_action(self, state: MCTSState, action: MCTSAction) -> MCTSState:
        """Default: apply action and return new state."""
        new_state = state.copy()
        new_state.step += 1
        # Apply action effects from metadata
        effects = action.metadata.get("effects", {})
        new_state.data.update(effects)
        return new_state

    def _default_is_terminal(self, state: MCTSState) -> bool:
        """Default: terminal if marked or max depth reached."""
        return state.is_terminal or state.step >= self.config.max_depth

    def _default_reward(self, state: MCTSState) -> float:
        """Default reward function."""
        return state.reward

    def search(self, initial_state: MCTSState) -> Tuple[MCTSAction, MCTSNode]:
        """
        Run MCTS search from initial state.
        Returns best action and root node.
        """
        root = MCTSNode(state=initial_state)
        root.untried_actions = self.get_actions(initial_state)

        start_time = time.time()
        iteration = 0

        while (iteration < self.config.max_iterations and
               time.time() - start_time < self.config.max_time_seconds):

            # Selection
            node = self._select(root)

            # Expansion
            if not node.state.is_terminal and node.untried_actions:
                node = self._expand(node)

            # Simulation (Rollout)
            reward = self._simulate(node.state)

            # Backpropagation
            self._backpropagate(node, reward)

            iteration += 1

        # Select best action
        if not root.children:
            # No valid actions found
            return MCTSAction(name="no_op"), root

        best_child = max(root.children.values(), key=lambda c: c.visits)
        return best_child.action, root

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select node using UCT."""
        while not node.is_leaf() and node.is_fully_expanded():
            # Select child with highest UCT
            node = max(node.children.values(), key=lambda c: c.uct_value)
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """Expand node by trying an untried action."""
        if not node.untried_actions:
            return node

        action = node.untried_actions.pop()
        new_state = self.apply_action(node.state, action)
        child = node.add_child(action, new_state)
        child.untried_actions = self.get_actions(new_state)
        return child

    def _simulate(self, state: MCTSState) -> float:
        """Run rollout simulation from state."""
        total_reward = 0.0
        current_state = state.copy()
        discount = 1.0

        for _ in range(self.config.num_rollouts):
            sim_state = current_state.copy()
            sim_discount = 1.0
            rollout_reward = 0.0

            for _ in range(self.config.max_depth):
                if self.is_terminal(sim_state):
                    break

                actions = self.get_actions(sim_state)
                if not actions:
                    break

                # Select action based on rollout policy
                action = self._select_rollout_action(sim_state, actions)
                sim_state = self.apply_action(sim_state, action)
                step_reward = self.reward_fn(sim_state)
                rollout_reward += sim_discount * step_reward
                sim_discount *= self.config.discount_factor

            total_reward += rollout_reward

        return total_reward / max(self.config.num_rollouts, 1)

    def _select_rollout_action(self, state: MCTSState, actions: List[MCTSAction]) -> MCTSAction:
        """Select action during rollout based on policy."""
        if self.config.rollout_policy == "random":
            return random.choice(actions)
        elif self.config.rollout_policy == "greedy":
            if self.heuristic_fn:
                return max(actions, key=lambda a: self.heuristic_fn(self.apply_action(state, a)))
            return random.choice(actions)
        elif self.config.rollout_policy == "heuristic":
            if self.heuristic_fn:
                # Weighted random by heuristic
                weights = [self.heuristic_fn(self.apply_action(state, a)) + 1e-6 for a in actions]
                return random.choices(actions, weights=weights)[0]
            return random.choice(actions)
        return random.choice(actions)

    def _backpropagate(self, node: MCTSNode, reward: float) -> None:
        """Backpropagate reward up the tree."""
        current = node
        while current is not None:
            current.visits += 1
            current.total_reward += reward
            current = current.parent

    def get_best_action(self, root: MCTSNode) -> Optional[MCTSAction]:
        """Get best action from root (most visited)."""
        if not root.children:
            return None
        return max(root.children.values(), key=lambda c: c.visits).action

    def get_action_probabilities(self, root: MCTSNode, temperature: float = 1.0) -> Dict[str, float]:
        """Get action probabilities from visit counts."""
        if not root.children:
            return {}

        visits = {name: child.visits for name, child in root.children.items()}
        total = sum(visits.values())
        if total == 0:
            return {name: 1.0 / len(visits) for name in visits}

        if temperature == 0:
            best = max(visits, key=visits.get)
            return {name: 1.0 if name == best else 0.0 for name in visits}

        # Temperature scaling
        probs = {}
        for name, count in visits.items():
            probs[name] = (count / total) ** (1.0 / temperature)

        # Normalize
        total_prob = sum(probs.values())
        return {name: p / total_prob for name, p in probs.items()}


class MCTSStepSelector:
    """MCTS-based step selector for agent planning."""

    def __init__(
        self,
        planner: MCTSPlanner,
        state_encoder: Callable[[Dict[str, Any]], MCTSState],
        action_decoder: Callable[[MCTSAction], Dict[str, Any]],
    ) -> None:
        self.planner = planner
        self.state_encoder = state_encoder
        self.action_decoder = action_decoder

    def select_step(
        self,
        context: Dict[str, Any],
        available_actions: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], MCTSNode]:
        """Select best step using MCTS."""
        # Encode context to MCTS state
        initial_state = self.state_encoder(context)
        initial_state.data["available_actions"] = [
            MCTSAction(name=a["name"], params=a.get("params", {}), metadata=a.get("metadata", {}))
            for a in available_actions
        ]

        # Run search
        best_action, root = self.planner.search(initial_state)

        # Decode action
        selected_step = self.action_decoder(best_action)
        selected_step["mcts_stats"] = {
            "visits": root.visits,
            "children": {name: child.visits for name, child in root.children.items()},
            "probabilities": self.planner.get_action_probabilities(root),
        }

        return selected_step, root


# Global instance
_mcts_planner: Optional[MCTSPlanner] = None


def get_mcts_planner(config: Optional[MCTSConfig] = None) -> MCTSPlanner:
    """Get global MCTS planner instance."""
    global _mcts_planner
    if _mcts_planner is None:
        _mcts_planner = MCTSPlanner(config)
    return _mcts_planner