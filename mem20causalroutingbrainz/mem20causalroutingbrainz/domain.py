"""Causal routing brain: causal inference for routing decisions."""
import math, random


def causal_effect(treatment_outcomes, control_outcomes):
    """Average treatment effect."""
    if not treatment_outcomes or not control_outcomes:
        return 0.0
    return round(sum(treatment_outcomes) / len(treatment_outcomes) - sum(control_outcomes) / len(control_outcomes), 4)


def route_by_cause(features, causal_weights):
    """Route based on causal weights."""
    score = 0.0
    for k, w in causal_weights.items():
        score += features.get(k, 0) * w
    return score


def confounder_adjust(raw_effect, confounder_strength):
    return round(raw_effect * (1 - confounder_strength), 4)


def intervention_value(baseline, intervention_outcome):
    return round(intervention_outcome - baseline, 4)


def causal_graph(edges):
    """Build adjacency for causal graph."""
    graph = {}
    for src, dst in edges:
        graph.setdefault(src, []).append(dst)
    return graph
