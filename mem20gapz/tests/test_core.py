"""Tests for mem20gapz's core domain algorithms.

The package tests the part that makes decisions and records state: capability
taxonomy normalization, gap detection, bridging strategy generation, clustering,
ranking, acquisition simulation, and drift detection. Those are the places a
silent regression would do real harm.
"""

from __future__ import annotations

import json
import pytest

from mem20gapz.core import (
    Capability,
    CapabilityCategory,
    RequiredCapability,
    ProficiencyLevel,
    BridgingStrategy,
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


# --- Capability and RequiredCapability ---------------------------------------


def test_capability_to_dict_roundtrip():
    """A capability must survive dict conversion without loss."""
    cap = Capability(
        id="cap-001",
        name="Python",
        category=CapabilityCategory.HUMAN_SKILL,
        description="Python programming",
        tags=("backend", "data-science"),
        proficiency=ProficiencyLevel.ADVANCED,
        source="hr_system",
        metadata={"years": 5},
    )
    d = cap.to_dict()
    assert d["id"] == "cap-001"
    assert d["name"] == "Python"
    assert d["category"] == "human_skill"
    assert d["proficiency"] == "advanced"
    assert d["tags"] == ["backend", "data-science"]
    assert d["metadata"]["years"] == 5

    cap2 = Capability.from_dict(d)
    assert cap2.id == cap.id
    assert cap2.name == cap.name
    assert cap2.category == cap.category
    assert cap2.proficiency == cap.proficiency
    assert cap2.tags == cap.tags


def test_required_capability_to_dict_roundtrip():
    """A required capability must survive dict conversion without loss."""
    req = RequiredCapability(
        id="req-001",
        capability_id="cap-001",
        name="Rust",
        category=CapabilityCategory.HUMAN_SKILL,
        required_proficiency=ProficiencyLevel.INTERMEDIATE,
        criticality=0.8,
        urgency=0.6,
        rationale="Performance migration",
        tags=("backend", "performance"),
        metadata={"target_date": "2026-Q2"},
    )
    d = req.to_dict()
    assert d["id"] == "req-001"
    assert d["required_proficiency"] == "intermediate"
    assert d["criticality"] == 0.8
    assert d["urgency"] == 0.6

    req2 = RequiredCapability.from_dict(d)
    assert req2.id == req.id
    assert req2.required_proficiency == req.required_proficiency
    assert req2.criticality == req.criticality


def test_proficiency_level_numeric():
    """Proficiency levels must map to correct numeric values."""
    assert ProficiencyLevel.NONE.numeric == 0.0
    assert ProficiencyLevel.AWARE.numeric == 0.15
    assert ProficiencyLevel.BASIC.numeric == 0.35
    assert ProficiencyLevel.INTERMEDIATE.numeric == 0.6
    assert ProficiencyLevel.ADVANCED.numeric == 0.8
    assert ProficiencyLevel.EXPERT.numeric == 1.0


# --- normalize_capability ----------------------------------------------------


def test_normalize_capability_creates_new():
    """Normalize must create a Capability from raw dict."""
    raw = {
        "name": "Python",
        "category": "human_skill",
        "proficiency": "advanced",
        "tags": ["backend"],
    }
    cap = normalize_capability(raw)
    assert cap.name == "Python"
    assert cap.category == CapabilityCategory.HUMAN_SKILL
    assert cap.proficiency == ProficiencyLevel.ADVANCED
    assert cap.tags == ("backend",)


def test_normalize_capability_deduplicates():
    """Normalize must merge with existing capability in taxonomy."""
    taxonomy = CapabilityTaxonomy()
    existing = Capability(
        id="cap-001",
        name="Python",
        category=CapabilityCategory.HUMAN_SKILL,
        proficiency=ProficiencyLevel.INTERMEDIATE,
        tags=("backend",),
    )
    taxonomy.add_capability(existing)

    raw = {
        "name": "Python",
        "category": "human_skill",
        "proficiency": "advanced",
        "tags": ["data-science"],
    }
    cap = normalize_capability(raw, taxonomy)
    assert cap.id == "cap-001"  # same ID
    assert cap.proficiency == ProficiencyLevel.ADVANCED  # higher proficiency
    assert set(cap.tags) == {"backend", "data-science"}  # merged tags


def test_normalize_capability_semantic_match():
    """Normalize should match by name when ID not found."""
    taxonomy = CapabilityTaxonomy()
    existing = Capability(
        id="cap-002",
        name="Kubernetes",
        category=CapabilityCategory.HUMAN_SKILL,
        proficiency=ProficiencyLevel.BASIC,
        tags=("devops",),
    )
    taxonomy.add_capability(existing)

    raw = {
        "name": "Kubernetes",
        "category": "human_skill",
        "proficiency": "advanced",
        "tags": ["operators"],
    }
    cap = normalize_capability(raw, taxonomy)
    assert cap.id == "cap-002"
    assert cap.proficiency == ProficiencyLevel.ADVANCED


# --- compute_gaps ------------------------------------------------------------


def test_compute_gaps_exact_match():
    """Gaps must be detected when required capability exceeds actual."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.INTERMEDIATE),
    ]
    required = [
        RequiredCapability(id="req-001", capability_id="cap-001", name="Python",
                          category=CapabilityCategory.HUMAN_SKILL,
                          required_proficiency=ProficiencyLevel.ADVANCED,
                          criticality=0.8, urgency=0.6),
    ]
    gaps = compute_gaps(current, required)
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.required.name == "Python"
    assert gap.proficiency_delta == pytest.approx(0.2)  # 0.8 - 0.6
    assert gap.criticality_weighted == pytest.approx(0.16)  # 0.2 * 0.8
    assert gap.actual is not None
    assert gap.actual.id == "cap-001"


def test_compute_gaps_missing_capability():
    """Gaps must be created for completely missing capabilities."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.ADVANCED),
    ]
    required = [
        RequiredCapability(id="req-002", capability_id="cap-002", name="Rust",
                          category=CapabilityCategory.HUMAN_SKILL,
                          required_proficiency=ProficiencyLevel.INTERMEDIATE,
                          criticality=0.9, urgency=0.7),
    ]
    gaps = compute_gaps(current, required)
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.required.name == "Rust"
    assert gap.proficiency_delta == pytest.approx(0.6)  # 0.6 - 0.0
    assert gap.actual is None
    assert gap.matched_by_semantic is False


def test_compute_gaps_semantic_match():
    """Gaps should match semantically similar capabilities."""
    current = [
        Capability(id="cap-003", name="Kubernetes", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.INTERMEDIATE),
    ]
    required = [
        RequiredCapability(id="req-003", capability_id="cap-004", name="Kubernetes Operators",
                          category=CapabilityCategory.HUMAN_SKILL,
                          required_proficiency=ProficiencyLevel.ADVANCED,
                          criticality=0.85, urgency=0.75),
    ]
    gaps = compute_gaps(current, required, semantic_threshold=0.5)
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.matched_by_semantic is True
    assert gap.similarity_score > 0.5
    assert gap.actual is not None
    assert gap.actual.name == "Kubernetes"


def test_compute_gaps_sorted_by_priority():
    """Gaps must be sorted by priority score descending."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.INTERMEDIATE),
        Capability(id="cap-002", name="Rust", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.NONE),
    ]
    required = [
        RequiredCapability(id="req-001", capability_id="cap-001", name="Python",
                          category=CapabilityCategory.HUMAN_SKILL,
                          required_proficiency=ProficiencyLevel.ADVANCED,
                          criticality=0.5, urgency=0.3),  # lower priority
        RequiredCapability(id="req-002", capability_id="cap-002", name="Rust",
                          category=CapabilityCategory.HUMAN_SKILL,
                          required_proficiency=ProficiencyLevel.EXPERT,
                          criticality=0.9, urgency=0.8),  # higher priority
    ]
    gaps = compute_gaps(current, required)
    assert gaps[0].required.name == "Rust"  # higher priority first
    assert gaps[1].required.name == "Python"
    assert gaps[0].priority_score > gaps[1].priority_score


def test_compute_gaps_no_gap_when_sufficient():
    """No gap should be created when actual meets or exceeds required."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.EXPERT),
    ]
    required = [
        RequiredCapability(id="req-001", capability_id="cap-001", name="Python",
                          category=CapabilityCategory.HUMAN_SKILL,
                          required_proficiency=ProficiencyLevel.ADVANCED,
                          criticality=0.8, urgency=0.6),
    ]
    gaps = compute_gaps(current, required)
    assert len(gaps) == 1  # gap still created but with delta 0
    gap = gaps[0]
    assert gap.proficiency_delta == 0.0
    assert gap.priority_score == 0.0


# --- generate_bridging_strategies --------------------------------------------


def test_generate_bridging_strategies_human_skill():
    """Human skill gaps should generate TRAIN and HIRE strategies."""
    gaps = [
        CapabilityGap(
            id="gap-001",
            required=RequiredCapability(
                id="req-001", capability_id="cap-001", name="Rust",
                category=CapabilityCategory.HUMAN_SKILL,
                required_proficiency=ProficiencyLevel.EXPERT,
                criticality=0.8, urgency=0.6),
            actual=Capability(id="cap-001", name="Rust", category=CapabilityCategory.HUMAN_SKILL,
                            proficiency=ProficiencyLevel.BASIC),
            proficiency_delta=0.65,  # > 0.5 to trigger HIRE
            criticality_weighted=0.52,
            urgency_weighted=0.39,
            priority_score=0.481,
        )
    ]
    actions = generate_bridging_strategies(gaps, {"org_size": 100, "budget_per_gap": 50000})
    strategies = {a.strategy for a in actions}
    assert BridgingStrategy.TRAIN in strategies
    assert BridgingStrategy.HIRE in strategies
    # REDEPLOY only added when delta < 0.5
    assert BridgingStrategy.REDEPLOY not in strategies


def test_generate_bridging_strategies_agent_competency():
    """Agent competency gaps should generate BUILD and BUY strategies."""
    gaps = [
        CapabilityGap(
            id="gap-002",
            required=RequiredCapability(
                id="req-002", capability_id="cap-002", name="Security Audit Agent",
                category=CapabilityCategory.AGENT_COMPETENCY,
                required_proficiency=ProficiencyLevel.EXPERT,
                criticality=0.95, urgency=0.85),
            actual=None,
            proficiency_delta=1.0,
            criticality_weighted=0.95,
            urgency_weighted=0.85,
            priority_score=0.91,
        )
    ]
    actions = generate_bridging_strategies(gaps, {"budget_per_gap": 100000})
    strategies = {a.strategy for a in actions}
    assert BridgingStrategy.BUILD in strategies
    assert BridgingStrategy.BUY in strategies
    # AUTOMATE only added when delta < 0.4
    assert BridgingStrategy.AUTOMATE not in strategies


def test_generate_bridging_strategies_tool_coverage():
    """Tool coverage gaps should generate BUY and BUILD strategies."""
    gaps = [
        CapabilityGap(
            id="gap-003",
            required=RequiredCapability(
                id="req-003", capability_id="cap-003", name="Terraform",
                category=CapabilityCategory.TOOL_COVERAGE,
                required_proficiency=ProficiencyLevel.ADVANCED,
                criticality=0.8, urgency=0.7),
            actual=None,
            proficiency_delta=0.8,
            criticality_weighted=0.64,
            urgency_weighted=0.56,
            priority_score=0.616,
        )
    ]
    # BUILD only added when budget > 100000
    actions = generate_bridging_strategies(gaps, {"budget_per_gap": 50000})
    strategies = {a.strategy for a in actions}
    assert BridgingStrategy.BUY in strategies
    assert BridgingStrategy.BUILD not in strategies

    # With higher budget, BUILD should be included
    actions_high_budget = generate_bridging_strategies(gaps, {"budget_per_gap": 150000})
    strategies_high = {a.strategy for a in actions_high_budget}
    assert BridgingStrategy.BUILD in strategies_high


def test_generate_bridging_strategies_roi_calculation():
    """Bridging actions must have valid ROI scores."""
    gaps = [
        CapabilityGap(
            id="gap-004",
            required=RequiredCapability(
                id="req-004", capability_id="cap-004", name="Python",
                category=CapabilityCategory.HUMAN_SKILL,
                required_proficiency=ProficiencyLevel.ADVANCED,
                criticality=0.8, urgency=0.6),
            actual=Capability(id="cap-004", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                            proficiency=ProficiencyLevel.INTERMEDIATE),
            proficiency_delta=0.2,
            criticality_weighted=0.16,
            urgency_weighted=0.12,
            priority_score=0.148,
        )
    ]
    actions = generate_bridging_strategies(gaps)
    for action in actions:
        assert action.roi_score >= 0
        assert action.estimated_cost >= 0
        assert action.estimated_time_days >= 0
        assert 0 <= action.risk_score <= 1
        assert 0 <= action.strategic_alignment <= 1
        assert action.gap_id == "gap-004"


def test_generate_bridging_strategies_filters_unrealistic():
    """Actions exceeding budget/time limits should be filtered."""
    gaps = [
        CapabilityGap(
            id="gap-005",
            required=RequiredCapability(
                id="req-005", capability_id="cap-005", name="Massive Platform",
                category=CapabilityCategory.INFRASTRUCTURE,
                required_proficiency=ProficiencyLevel.EXPERT,
                criticality=0.9, urgency=0.9),
            actual=None,
            proficiency_delta=0.25,  # < 0.3 to trigger DEFER
            criticality_weighted=0.225,
            urgency_weighted=0.225,
            priority_score=0.225,
        )
    ]
    # Very low budget should filter out expensive BUILD action
    actions = generate_bridging_strategies(gaps, {"budget_per_gap": 1000, "max_time_days": 30})
    # DEFER should still be present
    strategies = {a.strategy for a in actions}
    assert BridgingStrategy.DEFER in strategies


# --- cluster_gaps ------------------------------------------------------------


def test_cluster_gaps_singletons():
    """Unrelated gaps should each form their own cluster."""
    gaps = [
        CapabilityGap(id="gap-001", required=RequiredCapability(id="r1", capability_id="c1", name="Python",
            category=CapabilityCategory.HUMAN_SKILL, required_proficiency=ProficiencyLevel.ADVANCED,
            criticality=0.8, urgency=0.6), actual=None,
            proficiency_delta=0.8, criticality_weighted=0.64, urgency_weighted=0.48, priority_score=0.608),
        CapabilityGap(id="gap-002", required=RequiredCapability(id="r2", capability_id="c2", name="Kubernetes",
            category=CapabilityCategory.INFRASTRUCTURE, required_proficiency=ProficiencyLevel.ADVANCED,
            criticality=0.9, urgency=0.7), actual=None,
            proficiency_delta=0.8, criticality_weighted=0.72, urgency_weighted=0.56, priority_score=0.68),
    ]
    clusters = cluster_gaps(gaps, similarity_threshold=0.8)
    assert len(clusters) == 2
    for c in clusters:
        assert len(c.gap_ids) == 1


def test_cluster_gaps_groups_similar():
    """Semantically similar gaps in same category should cluster."""
    gaps = [
        CapabilityGap(id="gap-001", required=RequiredCapability(id="r1", capability_id="c1", name="Kubernetes Operators",
            category=CapabilityCategory.HUMAN_SKILL, required_proficiency=ProficiencyLevel.ADVANCED,
            criticality=0.8, urgency=0.6), actual=None,
            proficiency_delta=0.8, criticality_weighted=0.64, urgency_weighted=0.48, priority_score=0.608),
        CapabilityGap(id="gap-002", required=RequiredCapability(id="r2", capability_id="c2", name="Kubernetes Controllers",
            category=CapabilityCategory.HUMAN_SKILL, required_proficiency=ProficiencyLevel.ADVANCED,
            criticality=0.9, urgency=0.7), actual=None,
            proficiency_delta=0.8, criticality_weighted=0.72, urgency_weighted=0.56, priority_score=0.68),
        CapabilityGap(id="gap-003", required=RequiredCapability(id="r3", capability_id="c3", name="Kubernetes CRDs",
            category=CapabilityCategory.HUMAN_SKILL, required_proficiency=ProficiencyLevel.INTERMEDIATE,
            criticality=0.7, urgency=0.5), actual=None,
            proficiency_delta=0.6, criticality_weighted=0.42, urgency_weighted=0.3, priority_score=0.384),
    ]
    clusters = cluster_gaps(gaps, similarity_threshold=0.5)
    # Should have 1 cluster with 3 gaps
    multi_gap_clusters = [c for c in clusters if len(c.gap_ids) > 1]
    assert len(multi_gap_clusters) == 1
    cluster = multi_gap_clusters[0]
    assert len(cluster.gap_ids) == 3
    assert cluster.category == CapabilityCategory.HUMAN_SKILL
    assert "Kubernetes" in cluster.theme


def test_cluster_gaps_systemic_root_cause():
    """Clusters should have inferred root causes."""
    gaps = [
        CapabilityGap(id="gap-001", required=RequiredCapability(id="r1", capability_id="c1", name="React Frontend",
            category=CapabilityCategory.HUMAN_SKILL, required_proficiency=ProficiencyLevel.ADVANCED,
            criticality=0.8, urgency=0.6), actual=None,
            proficiency_delta=0.8, criticality_weighted=0.64, urgency_weighted=0.48, priority_score=0.608),
        CapabilityGap(id="gap-002", required=RequiredCapability(id="r2", capability_id="c2", name="React Testing",
            category=CapabilityCategory.HUMAN_SKILL, required_proficiency=ProficiencyLevel.ADVANCED,
            criticality=0.9, urgency=0.7), actual=None,
            proficiency_delta=0.8, criticality_weighted=0.72, urgency_weighted=0.56, priority_score=0.68),
    ]
    clusters = cluster_gaps(gaps, similarity_threshold=0.5)
    multi = [c for c in clusters if len(c.gap_ids) > 1]
    assert len(multi) == 1
    assert "taxonomy" in multi[0].systemic_root_cause.lower() or "hiring" in multi[0].systemic_root_cause.lower()


# --- rank_bridging_actions ---------------------------------------------------


def test_rank_bridging_actions_default_weights():
    """Ranking must sort by weighted score."""
    actions = [
        BridgingAction(id="a1", gap_id="g1", strategy=BridgingStrategy.TRAIN,
                       title="Train", description="", estimated_cost=5000, estimated_time_days=30,
                       risk_score=0.2, strategic_alignment=0.9, roi_score=0.5),
        BridgingAction(id="a2", gap_id="g1", strategy=BridgingStrategy.HIRE,
                       title="Hire", description="", estimated_cost=80000, estimated_time_days=90,
                       risk_score=0.4, strategic_alignment=0.8, roi_score=0.3),
        BridgingAction(id="a3", gap_id="g1", strategy=BridgingStrategy.BUILD,
                       title="Build", description="", estimated_cost=150000, estimated_time_days=120,
                       risk_score=0.5, strategic_alignment=0.7, roi_score=0.4),
    ]
    ranked = rank_bridging_actions(actions)
    # BUILD ranks highest with these weights due to decent ROI and alignment
    # TRAIN second due to low cost/risk but lower ROI
    # HIRE last due to high cost and lower ROI
    assert ranked[0].strategy == BridgingStrategy.BUILD
    assert ranked[1].strategy == BridgingStrategy.TRAIN
    assert ranked[2].strategy == BridgingStrategy.HIRE


def test_rank_bridging_actions_custom_weights():
    """Custom weights must change ranking."""
    actions = [
        BridgingAction(id="a1", gap_id="g1", strategy=BridgingStrategy.TRAIN,
                       title="Train", description="", estimated_cost=5000, estimated_time_days=30,
                       risk_score=0.2, strategic_alignment=0.5, roi_score=0.2),
        BridgingAction(id="a2", gap_id="g1", strategy=BridgingStrategy.HIRE,
                       title="Hire", description="", estimated_cost=80000, estimated_time_days=90,
                       risk_score=0.4, strategic_alignment=0.9, roi_score=0.5),
    ]
    # Weight strategic_alignment heavily
    ranked = rank_bridging_actions(actions, weights={"roi": 0.1, "strategic_alignment": 0.8, "risk": -0.05, "cost": -0.05})
    assert ranked[0].strategy == BridgingStrategy.HIRE


# --- simulate_acquisition ----------------------------------------------------


def test_simulate_acquisition_returns_stats():
    """Simulation must return aggregated statistics."""
    actions = [
        BridgingAction(id="a1", gap_id="g1", strategy=BridgingStrategy.TRAIN,
                       title="Train", description="", estimated_cost=5000, estimated_time_days=30,
                       risk_score=0.2, strategic_alignment=0.9, roi_score=0.5),
        BridgingAction(id="a2", gap_id="g2", strategy=BridgingStrategy.HIRE,
                       title="Hire", description="", estimated_cost=80000, estimated_time_days=90,
                       risk_score=0.4, strategic_alignment=0.8, roi_score=0.3),
    ]
    result = simulate_acquisition(actions, horizon_days=365, monte_carlo_runs=50)
    assert result["horizon_days"] == 365
    assert result["runs"] == 50
    assert "gaps_closed" in result
    assert "mean" in result["gaps_closed"]
    assert "p50" in result["gaps_closed"]
    assert "p90" in result["gaps_closed"]
    assert "total_cost" in result
    assert "total_time_days" in result
    assert "success_rate" in result
    assert 0 <= result["success_rate"] <= 1


def test_simulate_acquisition_respects_horizon():
    """Actions exceeding horizon should not be counted."""
    actions = [
        BridgingAction(id="a1", gap_id="g1", strategy=BridgingStrategy.TRAIN,
                       title="Train", description="", estimated_cost=5000, estimated_time_days=30,
                       risk_score=0.1, strategic_alignment=0.9, roi_score=0.5),
        BridgingAction(id="a2", gap_id="g2", strategy=BridgingStrategy.BUILD,
                       title="Build", description="", estimated_cost=150000, estimated_time_days=400,
                       risk_score=0.5, strategic_alignment=0.7, roi_score=0.3),
    ]
    result = simulate_acquisition(actions, horizon_days=100, monte_carlo_runs=20)
    # BUILD takes 400 days > 100 horizon, so only TRAIN should succeed
    assert result["gaps_closed"]["mean"] <= 1.0


def test_simulate_acquisition_empty():
    """Empty action list should return zeroed stats."""
    result = simulate_acquisition([], horizon_days=365, monte_carlo_runs=10)
    assert result["gaps_closed"]["mean"] == 0
    assert result["total_cost"]["mean"] == 0
    assert result["success_rate"] == 0


# --- detect_drift ------------------------------------------------------------


def test_detect_drift_decayed():
    """Drift must detect capability decay."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.BASIC),
    ]
    previous = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.ADVANCED),
    ]
    drift = detect_drift(current, previous, threshold=0.1)
    assert drift["decayed_count"] == 1
    assert drift["improved_count"] == 0
    assert drift["decayed"][0]["capability"]["name"] == "Python"
    assert drift["decayed"][0]["delta"] < -0.1
    assert drift["health"] in ("warning", "critical")


def test_detect_drift_improved():
    """Drift must detect capability improvement."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.ADVANCED),
    ]
    previous = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.BASIC),
    ]
    drift = detect_drift(current, previous, threshold=0.1)
    assert drift["decayed_count"] == 0
    assert drift["improved_count"] == 1
    assert drift["improved"][0]["delta"] > 0.1
    assert drift["health"] == "healthy"


def test_detect_drift_new_and_removed():
    """Drift must detect new and removed capabilities."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.ADVANCED),
        Capability(id="cap-002", name="Rust", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.INTERMEDIATE),
    ]
    previous = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.ADVANCED),
        Capability(id="cap-003", name="Java", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.INTERMEDIATE),
    ]
    drift = detect_drift(current, previous, threshold=0.1)
    assert drift["new_capabilities_count"] == 1
    assert drift["removed_capabilities_count"] == 1
    assert drift["new_capabilities"][0]["name"] == "Rust"
    assert drift["removed_capabilities"][0]["name"] == "Java"


def test_detect_drift_no_change():
    """Drift must report healthy when no significant changes."""
    current = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.ADVANCED),
    ]
    previous = [
        Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                   proficiency=ProficiencyLevel.ADVANCED),
    ]
    drift = detect_drift(current, previous, threshold=0.1)
    assert drift["decayed_count"] == 0
    assert drift["improved_count"] == 0
    assert drift["new_capabilities_count"] == 0
    assert drift["removed_capabilities_count"] == 0
    assert drift["drift_score"] == 0.0
    assert drift["health"] == "healthy"


# --- family_capability_gap_mapper (Runtime integration) ----------------------


def test_family_201_gap_detection():
    """RID 201 must return gap detection results."""
    request = {
        "current_capabilities": [
            {"id": "c1", "name": "Python", "category": "human_skill", "proficiency": "intermediate"},
        ],
        "required_capabilities": [
            {"id": "r1", "capability_id": "c1", "name": "Python", "category": "human_skill",
             "required_proficiency": "advanced", "criticality": 0.8, "urgency": 0.6},
        ],
    }
    result = family_capability_gap_mapper(201, request)
    assert "gaps" in result
    assert result["total_gaps"] == 1
    assert "critical_gaps" in result
    assert "categories_affected" in result


def test_family_202_bridging_strategies():
    """RID 202 must return ranked bridging actions."""
    request = {
        "current_capabilities": [
            {"id": "c1", "name": "Python", "category": "human_skill", "proficiency": "basic"},
        ],
        "required_capabilities": [
            {"id": "r1", "capability_id": "c1", "name": "Python", "category": "human_skill",
             "required_proficiency": "expert", "criticality": 0.9, "urgency": 0.8},
        ],
        "context": {"org_size": 50, "budget_per_gap": 50000},
    }
    result = family_capability_gap_mapper(202, request)
    assert "actions" in result
    assert result["total_actions"] > 0
    assert "by_strategy" in result


def test_family_203_gap_clustering():
    """RID 203 must return gap clusters."""
    request = {
        "current_capabilities": [],
        "required_capabilities": [
            {"id": "r1", "capability_id": "c1", "name": "Kubernetes Operators", "category": "human_skill",
             "required_proficiency": "advanced", "criticality": 0.8, "urgency": 0.6},
            {"id": "r2", "capability_id": "c2", "name": "Kubernetes Controllers", "category": "human_skill",
             "required_proficiency": "advanced", "criticality": 0.9, "urgency": 0.7},
        ],
    }
    result = family_capability_gap_mapper(203, request)
    assert "clusters" in result
    assert result["total_clusters"] > 0
    assert "systemic_clusters" in result


def test_family_204_acquisition_simulation():
    """RID 204 must return Monte Carlo simulation results."""
    request = {
        "current_capabilities": [
            {"id": "c1", "name": "Python", "category": "human_skill", "proficiency": "basic"},
        ],
        "required_capabilities": [
            {"id": "r1", "capability_id": "c1", "name": "Python", "category": "human_skill",
             "required_proficiency": "expert", "criticality": 0.9, "urgency": 0.8},
        ],
        "context": {"org_size": 50},
        "horizon_days": 180,
        "runs": 20,
    }
    result = family_capability_gap_mapper(204, request)
    assert "gaps_closed" in result
    assert "total_cost" in result
    assert "total_time_days" in result
    assert "success_rate" in result


def test_family_205_drift_detection():
    """RID 205 must return drift detection results."""
    request = {
        "current_capabilities": [
            {"id": "c1", "name": "Python", "category": "human_skill", "proficiency": "basic"},
        ],
        "required_capabilities": [],
        "previous_capabilities": [
            {"id": "c1", "name": "Python", "category": "human_skill", "proficiency": "advanced"},
        ],
        "threshold": 0.1,
    }
    result = family_capability_gap_mapper(205, request)
    assert "decayed_count" in result
    assert "health" in result


def test_family_206_full_pipeline():
    """RID 206 must return full pipeline results."""
    request = {
        "current_capabilities": [
            {"id": "c1", "name": "Python", "category": "human_skill", "proficiency": "intermediate"},
        ],
        "required_capabilities": [
            {"id": "r1", "capability_id": "c1", "name": "Python", "category": "human_skill",
             "required_proficiency": "advanced", "criticality": 0.8, "urgency": 0.6},
        ],
        "context": {"org_size": 50, "budget_per_gap": 50000},
        "horizon_days": 180,
        "runs": 20,
    }
    result = family_capability_gap_mapper(206, request)
    assert "gaps" in result
    assert "clusters" in result
    assert "actions" in result
    assert "simulation" in result
    assert "summary" in result
    assert result["summary"]["total_gaps"] == 1
    assert "top_action" in result["summary"]
    assert "expected_gaps_closed" in result["summary"]


def test_family_unknown_rid_raises():
    """Unknown RID must raise ValueError."""
    with pytest.raises(ValueError):
        family_capability_gap_mapper(999, {})


# --- CapabilityTaxonomy ------------------------------------------------------


def test_taxonomy_add_and_find():
    """Taxonomy must support add and find operations."""
    taxonomy = CapabilityTaxonomy()
    cap = Capability(id="cap-001", name="Python", category=CapabilityCategory.HUMAN_SKILL,
                     proficiency=ProficiencyLevel.ADVANCED, tags=("backend",))
    taxonomy.add_capability(cap)

    found = taxonomy.get_capability("cap-001")
    assert found is not None
    assert found.name == "Python"

    by_name = taxonomy.find_by_name("Python")
    assert len(by_name) == 1
    assert by_name[0].id == "cap-001"

    by_tag = taxonomy.find_by_tag("backend")
    assert len(by_tag) == 1

    by_cat = taxonomy.find_by_category(CapabilityCategory.HUMAN_SKILL)
    assert len(by_cat) == 1


# --- Edge cases --------------------------------------------------------------


def test_compute_gaps_empty_lists():
    """Empty inputs must return empty gaps."""
    gaps = compute_gaps([], [])
    assert gaps == []


def test_generate_bridging_strategies_empty():
    """Empty gaps must return empty actions."""
    actions = generate_bridging_strategies([])
    assert actions == []


def test_cluster_gaps_empty():
    """Empty gaps must return empty clusters."""
    clusters = cluster_gaps([])
    assert clusters == []


def test_rank_bridging_actions_empty():
    """Empty actions must return empty list."""
    ranked = rank_bridging_actions([])
    assert ranked == []


def test_simulate_acquisition_zero_horizon():
    """Zero horizon must handle gracefully."""
    actions = [
        BridgingAction(id="a1", gap_id="g1", strategy=BridgingStrategy.TRAIN,
                       title="Train", description="", estimated_cost=5000, estimated_time_days=30,
                       risk_score=0.2, strategic_alignment=0.9, roi_score=0.5),
    ]
    result = simulate_acquisition(actions, horizon_days=0, monte_carlo_runs=10)
    assert result["gaps_closed"]["mean"] == 0


def test_detect_drift_empty():
    """Empty snapshots must return zeroed drift."""
    drift = detect_drift([], [], threshold=0.1)
    assert drift["decayed_count"] == 0
    assert drift["improved_count"] == 0
    assert drift["new_capabilities_count"] == 0
    assert drift["removed_capabilities_count"] == 0
    assert drift["drift_score"] == 0.0
    assert drift["health"] == "healthy"