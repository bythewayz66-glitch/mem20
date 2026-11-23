"""Core domain algorithms for Capability Gap Mapper.

Implements capability taxonomy, gap detection, bridging strategy generation,
clustering, ranking, acquisition simulation, and drift detection.
"""

from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal

from mem20core.core import canonical, stable_hash, topo


class CapabilityCategory(str, Enum):
    """High-level capability categories."""

    HUMAN_SKILL = "human_skill"
    AGENT_COMPETENCY = "agent_competency"
    TOOL_COVERAGE = "tool_coverage"
    INFRASTRUCTURE = "infrastructure"
    DATA_ASSET = "data_asset"
    API_INTEGRATION = "api_integration"
    PROCESS_KNOWLEDGE = "process_knowledge"
    DOMAIN_EXPERTISE = "domain_expertise"


class BridgingStrategy(str, Enum):
    """Strategies for closing capability gaps."""

    HIRE = "hire"
    TRAIN = "train"
    BUILD = "build"
    BUY = "buy"
    PARTNER = "partner"
    AUTOMATE = "automate"
    DEFER = "defer"
    REDEPLOY = "redeploy"


class ProficiencyLevel(str, Enum):
    """Proficiency levels for capabilities."""

    NONE = "none"
    AWARE = "aware"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

    @property
    def numeric(self) -> float:
        mapping = {
            ProficiencyLevel.NONE: 0.0,
            ProficiencyLevel.AWARE: 0.15,
            ProficiencyLevel.BASIC: 0.35,
            ProficiencyLevel.INTERMEDIATE: 0.6,
            ProficiencyLevel.ADVANCED: 0.8,
            ProficiencyLevel.EXPERT: 1.0,
        }
        return mapping[self]


@dataclass(frozen=True)
class Capability:
    """A single capability with metadata."""

    id: str
    name: str
    category: CapabilityCategory
    description: str = ""
    tags: tuple[str, ...] = ()
    proficiency: ProficiencyLevel = ProficiencyLevel.NONE
    source: str = "manual"  # manual, hr_system, code_analysis, agent_registry, cmdb
    last_verified: float | None = None  # unix timestamp
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "tags": list(self.tags),
            "proficiency": self.proficiency.value,
            "source": self.source,
            "last_verified": self.last_verified,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Capability:
        return cls(
            id=data["id"],
            name=data["name"],
            category=CapabilityCategory(data["category"]),
            description=data.get("description", ""),
            tags=tuple(data.get("tags", [])),
            proficiency=ProficiencyLevel(data.get("proficiency", "none")),
            source=data.get("source", "manual"),
            last_verified=data.get("last_verified"),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class RequiredCapability:
    """A capability requirement with business context."""

    id: str
    capability_id: str  # references Capability.id
    name: str
    category: CapabilityCategory
    required_proficiency: ProficiencyLevel
    criticality: float  # 0-1: business impact * frequency * blast radius
    urgency: float  # 0-1: how soon this is needed
    rationale: str = ""
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "capability_id": self.capability_id,
            "name": self.name,
            "category": self.category.value,
            "required_proficiency": self.required_proficiency.value,
            "criticality": self.criticality,
            "urgency": self.urgency,
            "rationale": self.rationale,
            "tags": list(self.tags),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RequiredCapability:
        return cls(
            id=data["id"],
            capability_id=data["capability_id"],
            name=data["name"],
            category=CapabilityCategory(data["category"]),
            required_proficiency=ProficiencyLevel(data["required_proficiency"]),
            criticality=float(data["criticality"]),
            urgency=float(data["urgency"]),
            rationale=data.get("rationale", ""),
            tags=tuple(data.get("tags", [])),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class CapabilityGap:
    """A detected gap between required and actual capability."""

    id: str
    required: RequiredCapability
    actual: Capability | None
    proficiency_delta: float  # required - actual (0-1)
    criticality_weighted: float  # proficiency_delta * criticality
    urgency_weighted: float  # proficiency_delta * urgency
    priority_score: float  # combined priority for ranking
    matched_by_semantic: bool = False  # true if matched via semantic similarity
    similarity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "required": self.required.to_dict(),
            "actual": self.actual.to_dict() if self.actual else None,
            "proficiency_delta": self.proficiency_delta,
            "criticality_weighted": self.criticality_weighted,
            "urgency_weighted": self.urgency_weighted,
            "priority_score": self.priority_score,
            "matched_by_semantic": self.matched_by_semantic,
            "similarity_score": self.similarity_score,
        }


@dataclass(frozen=True)
class BridgingAction:
    """A recommended action to close a capability gap."""

    id: str
    gap_id: str
    strategy: BridgingStrategy
    title: str
    description: str
    estimated_cost: float  # USD
    estimated_time_days: int
    risk_score: float  # 0-1
    strategic_alignment: float  # 0-1
    roi_score: float  # computed: (criticality_weighted * strategic_alignment) / (cost_factor * time_factor * risk_factor)
    prerequisites: tuple[str, ...] = ()
    success_metrics: tuple[str, ...] = ()
    owner: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "gap_id": self.gap_id,
            "strategy": self.strategy.value,
            "title": self.title,
            "description": self.description,
            "estimated_cost": self.estimated_cost,
            "estimated_time_days": self.estimated_time_days,
            "risk_score": self.risk_score,
            "strategic_alignment": self.strategic_alignment,
            "roi_score": self.roi_score,
            "prerequisites": list(self.prerequisites),
            "success_metrics": list(self.success_metrics),
            "owner": self.owner,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class GapCluster:
    """A cluster of related gaps sharing a systemic theme."""

    id: str
    name: str
    theme: str
    gap_ids: tuple[str, ...]
    category: CapabilityCategory
    combined_priority: float
    recommended_strategy: BridgingStrategy
    systemic_root_cause: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "theme": self.theme,
            "gap_ids": list(self.gap_ids),
            "category": self.category.value,
            "combined_priority": self.combined_priority,
            "recommended_strategy": self.recommended_strategy.value,
            "systemic_root_cause": self.systemic_root_cause,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CapabilityTaxonomy:
    """Unified capability taxonomy with hierarchy and relationships."""

    capabilities: dict[str, Capability] = field(default_factory=dict)
    relationships: dict[str, list[str]] = field(default_factory=dict)  # parent -> children
    synonyms: dict[str, str] = field(default_factory=dict)  # alias -> canonical_id

    def add_capability(self, cap: Capability) -> None:
        self.capabilities[cap.id] = cap

    def get_capability(self, cap_id: str) -> Capability | None:
        return self.capabilities.get(cap_id)

    def find_by_name(self, name: str) -> list[Capability]:
        name_lower = name.lower()
        return [
            c for c in self.capabilities.values()
            if c.name.lower() == name_lower or name_lower in c.name.lower()
        ]

    def find_by_tag(self, tag: str) -> list[Capability]:
        return [c for c in self.capabilities.values() if tag in c.tags]

    def find_by_category(self, category: CapabilityCategory) -> list[Capability]:
        return [c for c in self.capabilities.values() if c.category == category]


# --- Utility functions ---

_SIMILARITY_CACHE: dict[tuple[str, str], float] = {}


def _semantic_similarity(a: str, b: str) -> float:
    """Compute semantic similarity between two capability names/descriptions."""
    key = tuple(sorted((a.lower(), b.lower())))
    if key in _SIMILARITY_CACHE:
        return _SIMILARITY_CACHE[key]

    # Use word overlap + substring matching as proxy for semantic similarity
    words_a = set(re.findall(r"[a-z0-9]+", a.lower()))
    words_b = set(re.findall(r"[a-z0-9]+", b.lower()))

    if not words_a or not words_b:
        return 0.0

    # Jaccard similarity
    intersection = words_a & words_b
    union = words_a | words_b
    jaccard = len(intersection) / len(union)

    # Substring bonus
    substring_bonus = 0.0
    if a.lower() in b.lower() or b.lower() in a.lower():
        substring_bonus = 0.2

    # Common prefix bonus - for things like "Kubernetes X" vs "Kubernetes Y"
    prefix_bonus = 0.0
    a_words = a.lower().split()
    b_words = b.lower().split()
    if a_words and b_words and a_words[0] == b_words[0] and len(a_words[0]) > 3:
        prefix_bonus = 0.25

    result = min(1.0, jaccard + substring_bonus + prefix_bonus)
    _SIMILARITY_CACHE[key] = result
    return result


def normalize_capability(raw: dict[str, Any], taxonomy: CapabilityTaxonomy | None = None) -> Capability:
    """Normalize a raw capability dict into a Capability object with deduplication."""
    cap_id = raw.get("id") or stable_hash({"name": raw["name"], "category": raw["category"]})[:12]

    # Check for existing capability with same name/category
    if taxonomy:
        existing = taxonomy.find_by_name(raw["name"])
        if existing:
            # Merge: keep higher proficiency, merge tags
            best = max(existing, key=lambda c: c.proficiency.numeric)
            merged_tags = tuple(set(best.tags) | set(raw.get("tags", [])))
            return Capability(
                id=best.id,
                name=best.name,
                category=best.category,
                description=best.description or raw.get("description", ""),
                tags=merged_tags,
                proficiency=max(best.proficiency, ProficiencyLevel(raw.get("proficiency", "none")), key=lambda p: p.numeric),
                source=raw.get("source", best.source),
                last_verified=raw.get("last_verified", best.last_verified),
                metadata={**best.metadata, **raw.get("metadata", {})},
            )

    return Capability(
        id=cap_id,
        name=raw["name"],
        category=CapabilityCategory(raw["category"]),
        description=raw.get("description", ""),
        tags=tuple(raw.get("tags", [])),
        proficiency=ProficiencyLevel(raw.get("proficiency", "none")),
        source=raw.get("source", "manual"),
        last_verified=raw.get("last_verified"),
        metadata=raw.get("metadata", {}),
    )


def compute_gaps(
    current: list[Capability],
    required: list[RequiredCapability],
    semantic_threshold: float = 0.7,
) -> list[CapabilityGap]:
    """Compute gaps between current capabilities and requirements."""
    current_by_id = {c.id: c for c in current}
    current_by_name = defaultdict(list)
    for c in current:
        current_by_name[c.name.lower()].append(c)

    gaps = []
    for req in required:
        actual = current_by_id.get(req.capability_id)

        # Try exact ID match first
        if not actual:
            # Try name match
            matches = current_by_name.get(req.name.lower(), [])
            if matches:
                actual = max(matches, key=lambda c: c.proficiency.numeric)

        # Try semantic match
        matched_by_semantic = False
        similarity_score = 0.0
        if not actual:
            best_match = None
            best_score = 0.0
            for cap in current:
                if cap.category != req.category:
                    continue
                score = _semantic_similarity(cap.name, req.name)
                if score > best_score and score >= semantic_threshold:
                    best_score = score
                    best_match = cap
            if best_match:
                actual = best_match
                matched_by_semantic = True
                similarity_score = best_score

        actual_proficiency = actual.proficiency.numeric if actual else 0.0
        required_proficiency = req.required_proficiency.numeric
        proficiency_delta = max(0.0, required_proficiency - actual_proficiency)

        criticality_weighted = proficiency_delta * req.criticality
        urgency_weighted = proficiency_delta * req.urgency
        priority_score = (criticality_weighted * 0.7) + (urgency_weighted * 0.3)

        gap = CapabilityGap(
            id=stable_hash({"req": req.id, "actual": actual.id if actual else "none"})[:12],
            required=req,
            actual=actual,
            proficiency_delta=proficiency_delta,
            criticality_weighted=criticality_weighted,
            urgency_weighted=urgency_weighted,
            priority_score=priority_score,
            matched_by_semantic=matched_by_semantic,
            similarity_score=similarity_score,
        )
        gaps.append(gap)

    # Sort by priority descending
    return sorted(gaps, key=lambda g: -g.priority_score)


def generate_bridging_strategies(
    gaps: list[CapabilityGap],
    context: dict[str, Any] | None = None,
) -> list[BridgingAction]:
    """Generate bridging actions for each gap."""
    context = context or {}
    budget_per_gap = context.get("budget_per_gap", 50000)
    max_time_days = context.get("max_time_days", 180)
    org_size = context.get("org_size", 100)
    strategic_priorities = context.get("strategic_priorities", [])

    actions = []

    for gap in gaps:
        req = gap.required
        delta = gap.proficiency_delta

        if delta <= 0:
            continue

        # Determine applicable strategies based on category, delta, and context
        applicable_strategies = _select_strategies(req.category, delta, org_size, budget_per_gap)

        for strategy in applicable_strategies:
            action = _create_bridging_action(gap, strategy, context)
            if action:
                actions.append(action)

    return actions


def _select_strategies(
    category: CapabilityCategory,
    delta: float,
    org_size: int,
    budget: float,
) -> list[BridgingStrategy]:
    """Select applicable bridging strategies for a gap."""
    strategies = []

    # Always consider training for skill gaps
    if category in (CapabilityCategory.HUMAN_SKILL, CapabilityCategory.DOMAIN_EXPERTISE, CapabilityCategory.PROCESS_KNOWLEDGE):
        strategies.append(BridgingStrategy.TRAIN)
        if delta > 0.5 and org_size > 50:
            strategies.append(BridgingStrategy.HIRE)

    # Agent competencies: build or buy
    if category == CapabilityCategory.AGENT_COMPETENCY:
        strategies.append(BridgingStrategy.BUILD)
        strategies.append(BridgingStrategy.BUY)
        if delta < 0.4:
            strategies.append(BridgingStrategy.AUTOMATE)

    # Tools: buy or build
    if category == CapabilityCategory.TOOL_COVERAGE:
        strategies.append(BridgingStrategy.BUY)
        if budget > 100000:
            strategies.append(BridgingStrategy.BUILD)

    # Infrastructure: build, buy, or partner
    if category == CapabilityCategory.INFRASTRUCTURE:
        strategies.append(BridgingStrategy.BUILD)
        strategies.append(BridgingStrategy.BUY)
        strategies.append(BridgingStrategy.PARTNER)

    # Data assets: build, buy, partner
    if category == CapabilityCategory.DATA_ASSET:
        strategies.append(BridgingStrategy.BUILD)
        strategies.append(BridgingStrategy.BUY)
        strategies.append(BridgingStrategy.PARTNER)

    # APIs: build, buy, partner
    if category == CapabilityCategory.API_INTEGRATION:
        strategies.append(BridgingStrategy.BUILD)
        strategies.append(BridgingStrategy.BUY)
        strategies.append(BridgingStrategy.PARTNER)

    # Defer is always an option for low priority
    if delta < 0.3:
        strategies.append(BridgingStrategy.DEFER)

    # Redeploy for human skills when similar capability exists
    if category == CapabilityCategory.HUMAN_SKILL and delta < 0.5:
        strategies.append(BridgingStrategy.REDEPLOY)

    return list(dict.fromkeys(strategies))  # deduplicate preserving order


def _create_bridging_action(
    gap: CapabilityGap,
    strategy: BridgingStrategy,
    context: dict[str, Any],
) -> BridgingAction | None:
    """Create a specific bridging action for a gap and strategy."""
    req = gap.required
    delta = gap.proficiency_delta
    criticality = req.criticality

    # Base estimates by strategy
    estimates = {
        BridgingStrategy.HIRE: {"cost": 80000, "time": 90, "risk": 0.4, "alignment": 0.8},
        BridgingStrategy.TRAIN: {"cost": 5000, "time": 30, "risk": 0.2, "alignment": 0.9},
        BridgingStrategy.BUILD: {"cost": 150000, "time": 120, "risk": 0.5, "alignment": 0.7},
        BridgingStrategy.BUY: {"cost": 50000, "time": 30, "risk": 0.3, "alignment": 0.6},
        BridgingStrategy.PARTNER: {"cost": 30000, "time": 60, "risk": 0.35, "alignment": 0.65},
        BridgingStrategy.AUTOMATE: {"cost": 100000, "time": 90, "risk": 0.45, "alignment": 0.75},
        BridgingStrategy.REDEPLOY: {"cost": 2000, "time": 14, "risk": 0.15, "alignment": 0.85},
        BridgingStrategy.DEFER: {"cost": 0, "time": 0, "risk": 0.1, "alignment": 0.2},
    }

    base = estimates.get(strategy, {"cost": 50000, "time": 60, "risk": 0.3, "alignment": 0.5})

    # Adjust for gap severity
    severity_multiplier = 1 + delta
    cost = base["cost"] * severity_multiplier
    time_days = int(base["time"] * severity_multiplier)
    risk = min(1.0, base["risk"] * (1 + delta * 0.5))

    # Strategic alignment boost if matches org priorities
    alignment = base["alignment"]
    if any(p in req.tags for p in context.get("strategic_priorities", [])):
        alignment = min(1.0, alignment * 1.2)

    # ROI calculation
    # Higher criticality and alignment = higher ROI
    # Higher cost, time, risk = lower ROI
    cost_factor = max(1.0, cost / 10000)
    time_factor = max(1.0, time_days / 30)
    risk_factor = max(0.5, 1 + risk)

    roi = (criticality * alignment) / (cost_factor * time_factor * risk_factor)

    # Filter out unrealistic options
    max_budget = context.get("budget_per_gap", 50000)
    max_time = context.get("max_time_days", 180)
    if cost > max_budget * 3 or time_days > max_time * 2:
        return None

    action_id = stable_hash({"gap": gap.id, "strategy": strategy.value})[:12]

    titles = {
        BridgingStrategy.HIRE: f"Hire {req.name} specialist",
        BridgingStrategy.TRAIN: f"Train team on {req.name}",
        BridgingStrategy.BUILD: f"Build {req.name} capability internally",
        BridgingStrategy.BUY: f"Purchase {req.name} solution",
        BridgingStrategy.PARTNER: f"Partner for {req.name} capability",
        BridgingStrategy.AUTOMATE: f"Automate {req.name} via agent/tool",
        BridgingStrategy.REDEPLOY: f"Redeploy existing talent to {req.name}",
        BridgingStrategy.DEFER: f"Defer {req.name} investment",
    }

    # Map delta to current proficiency level for description
    delta_to_proficiency = {
        (0.0, 0.15): ProficiencyLevel.NONE,
        (0.15, 0.35): ProficiencyLevel.AWARE,
        (0.35, 0.6): ProficiencyLevel.BASIC,
        (0.6, 0.8): ProficiencyLevel.INTERMEDIATE,
        (0.8, 1.0): ProficiencyLevel.ADVANCED,
    }
    current_prof = ProficiencyLevel.NONE
    for (lo, hi), prof in delta_to_proficiency.items():
        if lo <= delta < hi:
            current_prof = prof
            break
    else:
        if delta >= 1.0:
            current_prof = ProficiencyLevel.EXPERT

    descriptions = {
        BridgingStrategy.HIRE: f"Recruit a {req.required_proficiency.value}+ {req.name} expert to close the {delta:.0%} proficiency gap",
        BridgingStrategy.TRAIN: f"Upskill existing team members from {current_prof.value} to {req.required_proficiency.value} in {req.name}",
        BridgingStrategy.BUILD: f"Develop custom {req.name} capability with internal engineering resources",
        BridgingStrategy.BUY: f"Procure commercial {req.name} solution with {req.required_proficiency.value} coverage",
        BridgingStrategy.PARTNER: f"Establish strategic partnership for {req.name} capability delivery",
        BridgingStrategy.AUTOMATE: f"Build/deploy agent to automate {req.name} tasks at {req.required_proficiency.value} level",
        BridgingStrategy.REDEPLOY: f"Reassign adjacent-skilled team member to {req.name} with focused upskilling",
        BridgingStrategy.DEFER: f"Monitor {req.name} gap ({delta:.0%}) and reassess next planning cycle",
    }

    success_metrics = {
        BridgingStrategy.HIRE: ("time_to_productivity", "retention_1yr", "peer_review_score"),
        BridgingStrategy.TRAIN: ("certification_rate", "skill_assessment_delta", "project_application"),
        BridgingStrategy.BUILD: ("feature_completeness", "adoption_rate", "incident_rate"),
        BridgingStrategy.BUY: ("vendor_SLA_compliance", "user_satisfaction", "cost_vs_budget"),
        BridgingStrategy.PARTNER: ("delivery_on_time", "quality_score", "knowledge_transfer"),
        BridgingStrategy.AUTOMATE: ("automation_coverage", "error_rate_reduction", "human_hours_saved"),
        BridgingStrategy.REDEPLOY: ("ramp_time", "output_quality", "employee_satisfaction"),
        BridgingStrategy.DEFER: ("gap_stability", "business_impact_monitoring", ""),
    }

    return BridgingAction(
        id=action_id,
        gap_id=gap.id,
        strategy=strategy,
        title=titles[strategy],
        description=descriptions[strategy],
        estimated_cost=round(cost, 2),
        estimated_time_days=time_days,
        risk_score=round(risk, 3),
        strategic_alignment=round(alignment, 3),
        roi_score=round(roi, 4),
        prerequisites=(),
        success_metrics=success_metrics[strategy],
        owner=context.get("default_owner", ""),
        metadata={"gap_priority": gap.priority_score, "category": req.category.value},
    )


def cluster_gaps(
    gaps: list[CapabilityGap],
    similarity_threshold: float = 0.6,
) -> list[GapCluster]:
    """Cluster gaps by semantic similarity to identify systemic themes."""
    if not gaps:
        return []

    # Build similarity graph
    n = len(gaps)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            # Compare required capability names and categories
            if gaps[i].required.category != gaps[j].required.category:
                continue
            sim = _semantic_similarity(gaps[i].required.name, gaps[j].required.name)
            if sim >= similarity_threshold:
                edges.append((i, j))

    # Find connected components (clusters)
    visited = [False] * n
    clusters = []

    for i in range(n):
        if visited[i]:
            continue

        # BFS to find cluster
        component = []
        queue = [i]
        visited[i] = True

        while queue:
            idx = queue.pop(0)
            component.append(idx)
            for a, b in edges:
                if a == idx and not visited[b]:
                    visited[b] = True
                    queue.append(b)
                elif b == idx and not visited[a]:
                    visited[a] = True
                    queue.append(a)

        if len(component) > 1:
            # Multi-gap cluster
            gap_ids = tuple(gaps[idx].id for idx in component)
            category = gaps[component[0]].required.category
            combined_priority = sum(gaps[idx].priority_score for idx in component)

            # Determine theme from common words
            names = [gaps[idx].required.name for idx in component]
            theme = _extract_theme(names)

            # Recommend strategy based on category and cluster size
            strategy = _recommend_cluster_strategy(category, len(component))

            root_cause = _infer_root_cause(component, gaps, category)

            cluster = GapCluster(
                id=stable_hash({"cluster": theme, "category": category.value})[:12],
                name=f"{theme} Cluster",
                theme=theme,
                gap_ids=gap_ids,
                category=category,
                combined_priority=combined_priority,
                recommended_strategy=strategy,
                systemic_root_cause=root_cause,
                metadata={"gap_count": len(component), "avg_priority": combined_priority / len(component)},
            )
            clusters.append(cluster)
        else:
            # Singleton - still create a cluster for uniform handling
            idx = component[0]
            gap = gaps[idx]
            cluster = GapCluster(
                id=gap.id,
                name=f"Single: {gap.required.name}",
                theme=gap.required.name,
                gap_ids=(gap.id,),
                category=gap.required.category,
                combined_priority=gap.priority_score,
                recommended_strategy=_recommend_single_strategy(gap),
                systemic_root_cause="Isolated capability gap",
                metadata={"gap_count": 1},
            )
            clusters.append(cluster)

    return sorted(clusters, key=lambda c: -c.combined_priority)


def _extract_theme(names: list[str]) -> str:
    """Extract common theme from capability names."""
    if not names:
        return "Unknown"

    # Find common words
    word_counts: dict[str, int] = defaultdict(int)
    for name in names:
        words = set(re.findall(r"[a-z]{3,}", name.lower()))
        for w in words:
            word_counts[w] += 1

    common = [w for w, c in word_counts.items() if c >= len(names) * 0.5]
    if common:
        return " ".join(sorted(common, key=lambda w: -word_counts[w])[:3]).title()

    # Fallback: longest common substring-ish
    return names[0]


def _recommend_cluster_strategy(category: CapabilityCategory, count: int) -> BridgingStrategy:
    """Recommend strategy for a cluster."""
    if category == CapabilityCategory.HUMAN_SKILL:
        return BridgingStrategy.TRAIN if count < 5 else BridgingStrategy.HIRE
    if category == CapabilityCategory.AGENT_COMPETENCY:
        return BridgingStrategy.BUILD
    if category == CapabilityCategory.TOOL_COVERAGE:
        return BridgingStrategy.BUY
    if category == CapabilityCategory.INFRASTRUCTURE:
        return BridgingStrategy.BUILD
    if category == CapabilityCategory.DATA_ASSET:
        return BridgingStrategy.PARTNER
    return BridgingStrategy.BUILD


def _recommend_single_strategy(gap: CapabilityGap) -> BridgingStrategy:
    """Recommend strategy for a single gap."""
    delta = gap.proficiency_delta
    cat = gap.required.category

    if cat == CapabilityCategory.HUMAN_SKILL:
        return BridgingStrategy.TRAIN if delta < 0.5 else BridgingStrategy.HIRE
    if cat == CapabilityCategory.AGENT_COMPETENCY:
        return BridgingStrategy.BUILD
    if cat == CapabilityCategory.TOOL_COVERAGE:
        return BridgingStrategy.BUY
    if cat == CapabilityCategory.INFRASTRUCTURE:
        return BridgingStrategy.BUILD
    return BridgingStrategy.BUILD


def _infer_root_cause(
    indices: list[int],
    gaps: list[CapabilityGap],
    category: CapabilityCategory,
) -> str:
    """Infer systemic root cause for a cluster."""
    causes = {
        CapabilityCategory.HUMAN_SKILL: "Skills taxonomy outdated; hiring not aligned with project needs",
        CapabilityCategory.AGENT_COMPETENCY: "Agent capability registry incomplete; no automated discovery",
        CapabilityCategory.TOOL_COVERAGE: "Tool evaluation process lacks capability mapping",
        CapabilityCategory.INFRASTRUCTURE: "Infrastructure provisioning not capability-driven",
        CapabilityCategory.DATA_ASSET: "Data catalog missing capability annotations",
        CapabilityCategory.API_INTEGRATION: "Integration strategy reactive rather than capability-planned",
    }
    return causes.get(category, "Systemic capability planning gap")


def rank_bridging_actions(
    actions: list[BridgingAction],
    weights: dict[str, float] | None = None,
) -> list[BridgingAction]:
    """Rank bridging actions by weighted score."""
    weights = weights or {
        "roi": 0.4,
        "strategic_alignment": 0.25,
        "risk": -0.15,  # negative weight
        "cost": -0.1,
        "time": -0.1,
    }

    def score(action: BridgingAction) -> float:
        # Normalize cost and time to 0-1 range (assuming max 500k cost, 365 days)
        cost_norm = min(1.0, action.estimated_cost / 500000)
        time_norm = min(1.0, action.estimated_time_days / 365)
        return (
            weights.get("roi", 0) * action.roi_score
            + weights.get("strategic_alignment", 0) * action.strategic_alignment
            + weights.get("risk", 0) * (1 - action.risk_score)
            + weights.get("cost", 0) * (1 - cost_norm)
            + weights.get("time", 0) * (1 - time_norm)
        )

    return sorted(actions, key=score, reverse=True)


def simulate_acquisition(
    actions: list[BridgingAction],
    horizon_days: int = 365,
    monte_carlo_runs: int = 100,
) -> dict[str, Any]:
    """Monte Carlo simulation of capability acquisition outcomes."""
    if not actions:
        return {
            "horizon_days": horizon_days,
            "runs": 0,
            "results": [],
            "gaps_closed": {"mean": 0.0, "p50": 0, "p90": 0},
            "total_cost": {"mean": 0.0, "p50": 0.0, "p90": 0.0},
            "total_time_days": {"mean": 0.0, "p50": 0, "p90": 0},
            "success_rate": 0.0,
        }

    results = []
    rng = random.Random(42)

    for _ in range(monte_carlo_runs):
        acquired = 0
        total_cost = 0
        total_time = 0
        gaps_closed = []

        for action in actions:
            # Success probability based on risk score
            success_prob = 1 - action.risk_score
            if rng.random() < success_prob:
                # Time variance: +/- 30%
                actual_time = int(action.estimated_time_days * rng.uniform(0.7, 1.3))
                # Cost variance: +/- 25%
                actual_cost = action.estimated_cost * rng.uniform(0.75, 1.25)

                if total_time + actual_time <= horizon_days:
                    acquired += 1
                    total_cost += actual_cost
                    total_time += actual_time
                    gaps_closed.append(action.gap_id)

        results.append({
            "gaps_closed": acquired,
            "total_cost": round(total_cost, 2),
            "total_time_days": total_time,
            "gap_ids": gaps_closed,
        })

    # Aggregate statistics
    gaps_closed_vals = [r["gaps_closed"] for r in results]
    cost_vals = [r["total_cost"] for r in results]
    time_vals = [r["total_time_days"] for r in results]

    return {
        "horizon_days": horizon_days,
        "runs": monte_carlo_runs,
        "gaps_closed": {
            "mean": round(sum(gaps_closed_vals) / len(gaps_closed_vals), 2),
            "p50": sorted(gaps_closed_vals)[len(gaps_closed_vals) // 2],
            "p90": sorted(gaps_closed_vals)[int(0.9 * len(gaps_closed_vals))],
        },
        "total_cost": {
            "mean": round(sum(cost_vals) / len(cost_vals), 2),
            "p50": sorted(cost_vals)[len(cost_vals) // 2],
            "p90": sorted(cost_vals)[int(0.9 * len(cost_vals))],
        },
        "total_time_days": {
            "mean": round(sum(time_vals) / len(time_vals), 2),
            "p50": sorted(time_vals)[len(time_vals) // 2],
            "p90": sorted(time_vals)[int(0.9 * len(time_vals))],
        },
        "success_rate": round(sum(1 for r in results if r["gaps_closed"] > 0) / len(results), 3),
    }


def detect_drift(
    current_snapshot: list[Capability],
    previous_snapshot: list[Capability],
    threshold: float = 0.1,
) -> dict[str, Any]:
    """Detect capability drift between two snapshots."""
    current_by_id = {c.id: c for c in current_snapshot}
    previous_by_id = {c.id: c for c in previous_snapshot}

    all_ids = set(current_by_id.keys()) | set(previous_by_id.keys())

    decayed = []
    improved = []
    new_capabilities = []
    removed_capabilities = []

    for cap_id in all_ids:
        curr = current_by_id.get(cap_id)
        prev = previous_by_id.get(cap_id)

        if curr and not prev:
            new_capabilities.append(curr.to_dict())
        elif prev and not curr:
            removed_capabilities.append(prev.to_dict())
        elif curr and prev:
            delta = curr.proficiency.numeric - prev.proficiency.numeric
            if delta <= -threshold:
                decayed.append({
                    "capability": curr.to_dict(),
                    "previous_proficiency": prev.proficiency.value,
                    "current_proficiency": curr.proficiency.value,
                    "delta": round(delta, 3),
                })
            elif delta >= threshold:
                improved.append({
                    "capability": curr.to_dict(),
                    "previous_proficiency": prev.proficiency.value,
                    "current_proficiency": curr.proficiency.value,
                    "delta": round(delta, 3),
                })

    # Scope creep: new required capabilities without corresponding actuals
    return {
        "timestamp": datetime.now().isoformat(),
        "decayed_count": len(decayed),
        "improved_count": len(improved),
        "new_capabilities_count": len(new_capabilities),
        "removed_capabilities_count": len(removed_capabilities),
        "decayed": decayed,
        "improved": improved,
        "new_capabilities": new_capabilities,
        "removed_capabilities": removed_capabilities,
        "drift_score": round(len(decayed) / max(1, len(all_ids)), 3),
        "health": "healthy" if len(decayed) == 0 else ("warning" if len(decayed) < 5 else "critical"),
    }


# --- Family function for mem20core Runtime integration ---

def family_capability_gap_mapper(rid: int, p: dict[str, Any]) -> dict[str, Any]:
    """Domain algorithm entry points for Capability Gap Mapper (RM-201)."""

    # Parse input capabilities
    current_raw = p.get("current_capabilities", [])
    required_raw = p.get("required_capabilities", [])

    taxonomy = CapabilityTaxonomy()
    current = [normalize_capability(c, taxonomy) for c in current_raw]
    for c in current:
        taxonomy.add_capability(c)

    required = [RequiredCapability.from_dict(r) for r in required_raw]

    if rid == 201:
        # Gap detection
        gaps = compute_gaps(current, required)
        return {
            "gaps": [g.to_dict() for g in gaps],
            "total_gaps": len(gaps),
            "critical_gaps": len([g for g in gaps if g.priority_score > 0.5]),
            "categories_affected": list(set(g.required.category.value for g in gaps)),
        }

    if rid == 202:
        # Bridging strategy generation
        gaps = compute_gaps(current, required)
        actions = generate_bridging_strategies(gaps, p.get("context", {}))
        ranked = rank_bridging_actions(actions)
        return {
            "actions": [a.to_dict() for a in ranked],
            "total_actions": len(ranked),
            "by_strategy": {s.value: len([a for a in ranked if a.strategy == s]) for s in BridgingStrategy},
        }

    if rid == 203:
        # Gap clustering
        gaps = compute_gaps(current, required)
        clusters = cluster_gaps(gaps)
        return {
            "clusters": [c.to_dict() for c in clusters],
            "total_clusters": len(clusters),
            "systemic_clusters": len([c for c in clusters if len(c.gap_ids) > 1]),
        }

    if rid == 204:
        # Acquisition simulation
        gaps = compute_gaps(current, required)
        actions = generate_bridging_strategies(gaps, p.get("context", {}))
        ranked = rank_bridging_actions(actions)
        simulation = simulate_acquisition(
            ranked,
            horizon_days=p.get("horizon_days", 365),
            monte_carlo_runs=p.get("runs", 100),
        )
        return simulation

    if rid == 205:
        # Drift detection
        previous_raw = p.get("previous_capabilities", [])
        previous = [normalize_capability(c) for c in previous_raw]
        drift = detect_drift(current, previous, p.get("threshold", 0.1))
        return drift

    if rid == 206:
        # Full pipeline: gaps -> clusters -> strategies -> simulation
        gaps = compute_gaps(current, required)
        clusters = cluster_gaps(gaps)
        actions = generate_bridging_strategies(gaps, p.get("context", {}))
        ranked = rank_bridging_actions(actions)
        simulation = simulate_acquisition(ranked, p.get("horizon_days", 365), p.get("runs", 100))

        return {
            "gaps": [g.to_dict() for g in gaps],
            "clusters": [c.to_dict() for c in clusters],
            "actions": [a.to_dict() for a in ranked],
            "simulation": simulation,
            "summary": {
                "total_gaps": len(gaps),
                "critical_gaps": len([g for g in gaps if g.priority_score > 0.5]),
                "total_clusters": len(clusters),
                "systemic_clusters": len([c for c in clusters if len(c.gap_ids) > 1]),
                "total_actions": len(ranked),
                "top_action": ranked[0].to_dict() if ranked else None,
                "expected_gaps_closed": simulation["gaps_closed"]["mean"],
                "expected_cost": simulation["total_cost"]["mean"],
            },
        }

    raise ValueError(f"Unknown rid {rid} for CapabilityGapMapper")


# Register with mem20core's FAMILY_FUNCS
# This will be picked up by the Runtime when owner="CapabilityGapMapper"
FAMILY_FUNCS = {
    "CapabilityGapMapper": family_capability_gap_mapper,
}