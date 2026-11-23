"""mem20gapz — Capability Gap Mapper.

Maps current vs required capabilities across human skills, agent competencies,
tool coverage, and infrastructure. Identifies gaps and recommends bridging
strategies with ROI ranking.
"""

from .core import (
    Capability,
    CapabilityGap,
    BridgingAction,
    GapCluster,
    CapabilityTaxonomy,
    normalize_capability,
    compute_gaps,
    generate_bridging_strategies,
    cluster_gaps,
    rank_bridging_actions,
    simulate_acquisition,
    detect_drift,
    family_capability_gap_mapper,
)

__all__ = [
    "Capability",
    "CapabilityGap",
    "BridgingAction",
    "GapCluster",
    "CapabilityTaxonomy",
    "normalize_capability",
    "compute_gaps",
    "generate_bridging_strategies",
    "cluster_gaps",
    "rank_bridging_actions",
    "simulate_acquisition",
    "detect_drift",
    "family_capability_gap_mapper",
]

__version__ = "0.1.0"