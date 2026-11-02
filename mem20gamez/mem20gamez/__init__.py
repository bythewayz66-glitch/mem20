"""mem20gamez — native OpenGame absorption.

Real implementations: game agents (DQN / REINFORCE / PPO / SAC), environments
(TinyGridWorld-v0, gymnasium wrappers), reward shaping (Ng potential-based),
adaptive curriculum, prioritized replay, single- and multi-agent trainers.
"""

from .agent import (
    AgentConfig,
    AgentType,
    GameAgent,
    RandomAgent,
    RuleBasedAgent,
    create_agent,
)
from .config import DEFAULT_CONFIG, GameConfig
from .curriculum import (
    AdaptiveCurriculum,
    Curriculum,
    CurriculumConfig,
    CurriculumType,
    ExponentialCurriculum,
    LinearCurriculum,
    SelfPacedCurriculum,
    StepCurriculum,
    create_curriculum,
)
from .environment import (
    EnvConfig,
    Environment,
    GymnasiumEnvironment,
    StepResult,
    TinyGridWorld,
    create_environment,
)
from .replay_buffer import (
    EpisodeBuffer,
    Experience,
    ReplayBuffer,
    stack_batch,
)
from .reward_shaper import (
    CurriculumShaper,
    IntrinsicRewardShaper,
    PotentialBasedShaper,
    RewardConfig,
    RewardShaper,
    ShapedRewardShaper,
    create_shaper,
)
# torch is an OPTIONAL extra, not a hard requirement of the package.
#
# `agents`, `networks` and `trainer` all import torch at module scope, so a
# top-level import of them made the ENTIRE package unimportable on a machine
# without torch - including `mem20gamez.build_harness`, which needs no torch at
# all and whose tests therefore could not even be collected (issue #176).
#
# The learning classes are still exported when torch is present; when it is
# absent the package imports cleanly and the names are simply not bound, which
# is what an optional extra should look like. Tests that genuinely need torch
# declare it with `pytest.importorskip("torch")`.
try:
    from .agents import DQNAgent, PPOAgent, REINFORCEAgent, SACAgent
    from .networks import (
        DuelingQNetwork,
        PolicyNetwork,
        QNetwork,
        ValueNetwork,
        build_mlp,
    )
    from .trainer import (
        DQNTrainer,
        MultiAgentTrainer,
        default_adaptive_curriculum,
        default_reward_shaper,
        normalize_grid_size,
    )
except ImportError as _exc:  # torch (or a torch-dependent sibling) is absent
    _TORCH_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _TORCH_ERROR = ""

__title__ = "mem20gamez"
__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CONFIG",
    "AdaptiveCurriculum",
    "AgentConfig",
    "AgentType",
    "Curriculum",
    "CurriculumConfig",
    "CurriculumShaper",
    "CurriculumType",
    "DQNAgent",
    "DQNTrainer",
    "DuelingQNetwork",
    "EnvConfig",
    "Environment",
    "EpisodeBuffer",
    "Experience",
    "ExponentialCurriculum",
    "GameAgent",
    "GameConfig",
    "GymnasiumEnvironment",
    "IntrinsicRewardShaper",
    "LinearCurriculum",
    "MultiAgentTrainer",
    "PPOAgent",
    "PolicyNetwork",
    "PotentialBasedShaper",
    "QNetwork",
    "REINFORCEAgent",
    "RandomAgent",
    "ReplayBuffer",
    "RewardConfig",
    "RewardShaper",
    "RuleBasedAgent",
    "SACAgent",
    "SelfPacedCurriculum",
    "ShapedRewardShaper",
    "StepCurriculum",
    "StepResult",
    "TinyGridWorld",
    "ValueNetwork",
    "build_mlp",
    "create_agent",
    "create_curriculum",
    "create_environment",
    "create_shaper",
    "default_adaptive_curriculum",
    "default_reward_shaper",
    "normalize_grid_size",
    "stack_batch",
]