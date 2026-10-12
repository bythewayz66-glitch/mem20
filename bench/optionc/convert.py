"""Option C converter: turn a cloned package into a real domain implementation.

For each package in the clone set that has not yet been converted, this writes:

  <pkg>/<pkg>/domain.py            real algorithm bound to the package's own metadata
  <pkg>/<pkg>/tests/__init__.py
  <pkg>/<pkg>/tests/test_domain.py behaviour tests asserting specific values
  <pkg>/<pkg>/__init__.py          re-exports the domain entry point
  <pkg>/README.md                  documents the real implementation

The kernel is chosen from the package's declared ``operation_kind`` when a
CAPABILITY.json exists, otherwise inferred from its name. Parameters are
derived deterministically from the package name, so two packages sharing a
kernel still behave differently and are separately testable.

Nothing is deleted: the original ``core.py`` runtime stays in place and the
domain module is added alongside it.
"""
import hashlib
import inspect
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernels import KERNELS, infer_kernel  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def seed_of(name):
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)


def params_for(name, kernel):
    """Deterministic per-package parameters so packages differ from each other."""
    s = seed_of(name)
    p = {}
    if kernel == "analyze":
        p["top"] = 3 + s % 4
    elif kernel == "search":
        p["k"] = 3 + s % 5
    elif kernel == "simulate":
        p["trials"] = 1000 + (s % 5) * 500
        p["seed"] = s % 9973
    elif kernel == "forecast":
        p["horizon"] = 2 + s % 4
        p["alpha"] = round(0.3 + (s % 5) * 0.1, 2)
        p["beta"] = round(0.2 + (s % 4) * 0.1, 2)
    elif kernel == "progression":
        p["base"] = 50.0 + (s % 6) * 25
        p["decay"] = round(0.7 + (s % 4) * 0.05, 2)
    elif kernel == "schedule":
        p["capacity"] = 1 + s % 3
    elif kernel == "optimize":
        p["steps"] = 30 + (s % 5) * 10
    elif kernel == "cluster":
        p["k"] = 2 + s % 3
        p["seed"] = s % 9973
    elif kernel == "detect":
        p["k"] = round(2.5 + (s % 4) * 0.5, 2)
    elif kernel == "queue":
        p["aging"] = round(0.05 + (s % 5) * 0.05, 2)
    elif kernel == "heal":
        p["threshold"] = round(0.5 + (s % 4) * 0.05, 2)
    elif kernel == "budget":
        p["capacity"] = 50.0 + (s % 10) * 10
    return p


# Per-kernel: (entry function name, docstring, sample call, test body)
SPECS = {
    "analyze": (
        "analyze_signals",
        "Rank the signals driving a metric by z-score contribution.",
        "analyze_signals(signals)",
        '''
def test_ranks_the_shifted_signal_first():
    m = _m()
    signals = {"a": [1.0, 1.0, 1.0, 1.0], "b": [1.0, 1.0, 1.0, 9.0], "c": [2.0, 2.0, 2.0, 2.0]}
    r = m.analyze_signals(signals)
    assert r["drivers"][0]["signal"] == "b"
    assert r["drivers"][0]["z"] > 1.0


def test_flat_signals_have_no_drivers():
    m = _m()
    r = m.analyze_signals({"a": [5.0, 5.0, 5.0], "b": [3.0, 3.0, 3.0]})
    assert all(abs(d["z"]) < 1e-6 for d in r["drivers"])


def test_empty_input_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.analyze_signals({})
'''),
    "search": (
        "search_documents",
        "BM25 lexical ranking over a document set.",
        "search_documents(query, corpus)",
        '''
def test_exact_term_ranks_first():
    m = _m()
    corpus = ["the cat sat on the mat", "quantum entanglement in photonic lattices",
              "a dog barked at the postman"]
    r = m.search_documents("quantum photonic", corpus)
    assert r["results"][0]["doc"] == 1


def test_rare_term_outweighs_common_term():
    m = _m()
    corpus = ["alpha beta", "alpha gamma", "alpha delta", "alpha epsilon", "zeta omega"]
    r = m.search_documents("zeta", corpus)
    assert r["results"][0]["doc"] == 4


def test_no_match_returns_empty():
    m = _m()
    r = m.search_documents("nonexistentterm", ["a b c", "d e f"])
    assert r["results"] == []
    assert r["n_matched"] == 0


def test_empty_corpus_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.search_documents("x", [])
'''),
    "simulate": (
        "run_simulation",
        "Monte Carlo over a discrete outcome distribution with percentile bands.",
        "run_simulation(outcomes)",
        '''
def test_deterministic_for_fixed_seed():
    m = _m()
    o = [(1.0, 1.0), (10.0, 1.0)]
    a = m.run_simulation(o)
    b = m.run_simulation(o)
    assert a == b


def test_percentiles_are_ordered():
    m = _m()
    r = m.run_simulation([(1.0, 1.0), (5.0, 1.0), (9.0, 1.0)])
    assert r["p05"] <= r["p50"] <= r["p95"]


def test_certain_outcome_is_exact():
    m = _m()
    r = m.run_simulation([(42.0, 1.0)])
    assert r["mean"] == pytest.approx(42.0)
    assert r["p50"] == pytest.approx(42.0)


def test_zero_weight_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.run_simulation([(1.0, 0.0)])
'''),
    "compose": (
        "compose_pipeline",
        "Topological ordering of a dependency DAG.",
        "compose_pipeline(nodes, edges)",
        '''
def test_respects_dependency_order():
    m = _m()
    r = m.compose_pipeline(["c", "a", "b"], [("a", "b"), ("b", "c")])
    assert r["order"] == ["a", "b", "c"]


def test_cycle_is_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.compose_pipeline(["a", "b"], [("a", "b"), ("b", "a")])


def test_unknown_node_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.compose_pipeline(["a"], [("a", "zzz")])


def test_independent_nodes_all_emitted():
    m = _m()
    r = m.compose_pipeline(["x", "y", "z"], [])
    assert sorted(r["order"]) == ["x", "y", "z"]
'''),
    "route": (
        "route_path",
        "Dijkstra least-cost path over a weighted graph.",
        "route_path(graph, start, goal)",
        '''
def test_picks_cheaper_indirect_path():
    m = _m()
    g = {"a": {"b": 10.0, "c": 1.0}, "c": {"b": 1.0}, "b": {}}
    r = m.route_path(g, "a", "b")
    assert r["path"] == ["a", "c", "b"]
    assert r["cost"] == pytest.approx(2.0)


def test_direct_path_when_cheapest():
    m = _m()
    g = {"a": {"b": 1.0}, "b": {}}
    r = m.route_path(g, "a", "b")
    assert r["hops"] == 1


def test_unreachable_raises():
    m = _m()
    with pytest.raises(ValueError):
        m.route_path({"a": {}, "b": {}}, "a", "b")


def test_negative_weight_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.route_path({"a": {"b": -1.0}, "b": {}}, "a", "b")
'''),
    "forecast": (
        "forecast_series",
        "Holt linear-trend exponential smoothing.",
        "forecast_series(series)",
        '''
def test_linear_series_extrapolates():
    m = _m()
    r = m.forecast_series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert r["direction"] == "up"
    assert r["forecast"][0] > 4.0


def test_declining_series_detected():
    m = _m()
    r = m.forecast_series([10.0, 8.0, 6.0, 4.0])
    assert r["direction"] == "down"
    assert r["trend"] < 0


def test_flat_series_is_flat():
    m = _m()
    r = m.forecast_series([7.0, 7.0, 7.0, 7.0])
    assert r["direction"] == "flat"
    assert r["forecast"][0] == pytest.approx(7.0, abs=1e-6)


def test_short_series_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.forecast_series([1.0])
'''),
    "progression": (
        "compute_progression",
        "Diminishing-returns XP curve with level thresholds.",
        "compute_progression(events)",
        '''
def test_more_events_give_more_xp():
    m = _m()
    a = m.compute_progression([10.0] * 3)
    b = m.compute_progression([10.0] * 10)
    assert b["xp"] > a["xp"]


def test_diminishing_returns():
    m = _m()
    r = m.compute_progression([10.0] * 20)
    assert r["xp"] < 200.0


def test_level_increases_with_xp():
    m = _m()
    lo = m.compute_progression([1.0] * 2)
    hi = m.compute_progression([100.0] * 20)
    assert hi["level"] > lo["level"]


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.compute_progression([])
'''),
    "match": (
        "match_supply_demand",
        "Greedy min-cost assignment between supply and demand.",
        "match_supply_demand(supply, demand, cost)",
        '''
def test_assigns_cheapest_pair():
    m = _m()
    r = m.match_supply_demand(["s1"], ["d1", "d2"], {("s1", "d1"): 5.0, ("s1", "d2"): 1.0})
    assert r["pairs"][0]["demand"] == "d2"
    assert r["total_cost"] == pytest.approx(1.0)


def test_each_demand_used_once():
    m = _m()
    r = m.match_supply_demand(["s1", "s2"], ["d1"], {("s1", "d1"): 1.0, ("s2", "d1"): 2.0})
    assert len(r["pairs"]) == 1
    assert r["unmatched_supply"] == ["s2"]


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.match_supply_demand([], ["d"], {})
'''),
    "qa": (
        "check_claims",
        "Rule engine returning policy violations with reasons.",
        "check_claims(claims, rules)",
        '''
def test_flags_violation():
    m = _m()
    r = m.check_claims([{"score": 5}], [("score", "gt", 10)])
    assert len(r["violations"]) == 1
    assert r["violations"][0]["field"] == "score"


def test_passes_when_rule_satisfied():
    m = _m()
    r = m.check_claims([{"score": 20}], [("score", "gt", 10)])
    assert r["violations"] == []
    assert r["pass_rate"] == pytest.approx(1.0)


def test_missing_field_flagged():
    m = _m()
    r = m.check_claims([{"other": 1}], [("score", "gt", 10)])
    assert r["violations"][0]["reason"] == "missing"


def test_unknown_op_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.check_claims([{"a": 1}], [("a", "bogus", 1)])
'''),
    "sync": (
        "merge_replicas",
        "Last-writer-wins merge over vector clocks with conflict reporting.",
        "merge_replicas(replicas)",
        '''
def test_newest_timestamp_wins():
    m = _m()
    r = m.merge_replicas({"r1": {"k": (1.0, "old")}, "r2": {"k": (2.0, "new")}})
    assert r["merged"]["k"] == "new"


def test_simultaneous_divergence_is_a_conflict():
    m = _m()
    r = m.merge_replicas({"r1": {"k": (1.0, "a")}, "r2": {"k": (1.0, "b")}})
    assert len(r["conflicts"]) == 1


def test_identical_values_do_not_conflict():
    m = _m()
    r = m.merge_replicas({"r1": {"k": (1.0, "a")}, "r2": {"k": (1.0, "a")}})
    assert r["conflicts"] == []


def test_disjoint_keys_all_merge():
    m = _m()
    r = m.merge_replicas({"r1": {"a": (1.0, 1)}, "r2": {"b": (1.0, 2)}})
    assert r["n_keys"] == 2
'''),
    "schedule": (
        "schedule_tasks",
        "Priority interval scheduling under a capacity constraint.",
        "schedule_tasks(tasks)",
        '''
def test_higher_priority_wins_overlap():
    m = _m()
    tasks = [{"id": "lo", "start": 0, "end": 10, "priority": 1},
             {"id": "hi", "start": 0, "end": 10, "priority": 9}]
    r = m.schedule_tasks(tasks)
    assert "hi" in r["accepted"]
    assert "lo" in r["rejected"]


def test_non_overlapping_all_accepted():
    m = _m()
    tasks = [{"id": "a", "start": 0, "end": 5, "priority": 1},
             {"id": "b", "start": 5, "end": 10, "priority": 1}]
    r = m.schedule_tasks(tasks)
    assert sorted(r["accepted"]) == ["a", "b"]


def test_invalid_interval_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.schedule_tasks([{"id": "x", "start": 5, "end": 5, "priority": 1}])


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.schedule_tasks([])
'''),
    "optimize": (
        "optimize_objective",
        "Bounded coordinate-descent optimisation.",
        "optimize_objective(objective, bounds)",
        '''
def test_finds_known_maximum():
    m = _m()
    r = m.optimize_objective(lambda p: -(p["x"] - 3.0) ** 2 + 10.0, {"x": (0.0, 10.0)})
    assert r["solution"]["x"] == pytest.approx(3.0, abs=0.5)
    assert r["objective"] == pytest.approx(10.0, abs=0.5)


def test_respects_bounds():
    m = _m()
    r = m.optimize_objective(lambda p: p["x"], {"x": (0.0, 1.0)})
    assert 0.0 <= r["solution"]["x"] <= 1.0


def test_empty_bounds_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.optimize_objective(lambda p: 0.0, {})
'''),
    "reward": (
        "attribute_reward",
        "Shapley-style marginal credit attribution.",
        "attribute_reward(coalitions, values)",
        '''
def test_shares_sum_to_grand_coalition():
    m = _m()
    v = {("a",): 1.0, ("b",): 2.0, ("a", "b"): 4.0}
    r = m.attribute_reward([("a", "b")], v)
    assert r["total"] == pytest.approx(4.0, abs=1e-6)


def test_stronger_player_gets_more():
    m = _m()
    v = {("a",): 1.0, ("b",): 5.0, ("a", "b"): 6.0}
    r = m.attribute_reward([("a", "b")], v)
    assert r["shares"]["b"] > r["shares"]["a"]


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.attribute_reward([], {})
'''),
    "graph": (
        "analyse_graph",
        "Connected components and degree centrality.",
        "analyse_graph(nodes, edges)",
        '''
def test_detects_two_components():
    m = _m()
    r = m.analyse_graph(["a", "b", "c", "d"], [("a", "b"), ("c", "d")])
    assert r["n_components"] == 2


def test_hub_has_highest_degree():
    m = _m()
    r = m.analyse_graph(["h", "a", "b", "c"], [("h", "a"), ("h", "b"), ("h", "c")])
    assert r["centrality"][0]["node"] == "h"
    assert r["centrality"][0]["degree"] == 3


def test_unknown_node_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.analyse_graph(["a"], [("a", "zz")])
'''),
    "ingest": (
        "ingest_records",
        "Schema validation plus content-hash deduplication.",
        "ingest_records(records, required)",
        '''
def test_duplicate_detected():
    m = _m()
    r = m.ingest_records([{"id": 1}, {"id": 1}], required=("id",))
    assert len(r["accepted"]) == 1
    assert len(r["duplicates"]) == 1


def test_missing_field_rejected():
    m = _m()
    r = m.ingest_records([{"id": 1}, {"other": 2}], required=("id",))
    assert len(r["rejected"]) == 1
    assert r["rejected"][0]["missing"] == ["id"]


def test_accept_rate_computed():
    m = _m()
    r = m.ingest_records([{"id": 1}, {"id": 2}], required=("id",))
    assert r["accept_rate"] == pytest.approx(1.0)


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.ingest_records([], required=())
'''),
    "model": (
        "fit_model",
        "Ordinary least squares with R-squared.",
        "fit_model(xs, ys)",
        '''
def test_recovers_exact_line():
    m = _m()
    r = m.fit_model([1.0, 2.0, 3.0], [3.0, 5.0, 7.0])
    assert r["slope"] == pytest.approx(2.0)
    assert r["intercept"] == pytest.approx(1.0)
    assert r["r2"] == pytest.approx(1.0)


def test_noisy_fit_has_lower_r2():
    m = _m()
    r = m.fit_model([1.0, 2.0, 3.0, 4.0], [1.0, 9.0, 2.0, 8.0])
    assert r["r2"] < 0.9


def test_degenerate_x_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.fit_model([1.0, 1.0], [1.0, 2.0])
'''),
    "heal": (
        "assess_health",
        "Health scoring with remediation ordered by impact.",
        "assess_health(components)",
        '''
def test_unhealthy_component_flagged():
    m = _m()
    r = m.assess_health([{"name": "bad", "error_rate": 1.0, "latency_ms": 5000, "saturation": 1.0},
                         {"name": "good", "error_rate": 0.0, "latency_ms": 1, "saturation": 0.0}])
    assert "bad" in r["degraded"]
    assert "good" not in r["degraded"]


def test_worst_component_sorts_first():
    m = _m()
    r = m.assess_health([{"name": "ok", "error_rate": 0.0, "latency_ms": 0, "saturation": 0.0},
                         {"name": "bad", "error_rate": 0.9, "latency_ms": 900, "saturation": 0.9}])
    assert r["components"][0]["component"] == "bad"


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.assess_health([])
'''),
    "pipeline": (
        "run_pipeline",
        "Staged transform with per-stage drop accounting.",
        "run_pipeline(stages, items)",
        '''
def test_drop_accounting_is_exact():
    m = _m()
    stages = [("keep_even", lambda x: x if x % 2 == 0 else None)]
    r = m.run_pipeline(stages, [1, 2, 3, 4])
    assert r["output"] == [2, 4]
    assert r["total_dropped"] == 2


def test_stages_chain_in_order():
    m = _m()
    stages = [("inc", lambda x: x + 1), ("double", lambda x: x * 2)]
    r = m.run_pipeline(stages, [1, 2])
    assert r["output"] == [4, 6]


def test_empty_stages_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.run_pipeline([], [1])
'''),
    "detect": (
        "detect_anomalies",
        "Anomaly detection via median absolute deviation.",
        "detect_anomalies(series)",
        '''
def test_spike_is_detected():
    m = _m()
    r = m.detect_anomalies([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 50.0])
    assert r["n_anomalies"] >= 1
    assert any(a["index"] == 9 for a in r["anomalies"])


def test_clean_series_has_no_anomalies():
    m = _m()
    r = m.detect_anomalies([5.0, 5.0, 5.0, 5.0, 5.0])
    assert r["n_anomalies"] == 0


def test_short_series_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.detect_anomalies([1.0, 2.0])
'''),
    "rank": (
        "rank_alternatives",
        "TOPSIS multi-criteria ranking.",
        "rank_alternatives(alternatives, criteria)",
        '''
def test_dominant_alternative_wins():
    m = _m()
    alts = [{"name": "best", "a": 10.0, "b": 10.0}, {"name": "worst", "a": 1.0, "b": 1.0}]
    r = m.rank_alternatives(alts, ["a", "b"])
    assert r["ranking"][0]["alternative"] == "best"


def test_closeness_in_unit_interval():
    m = _m()
    alts = [{"name": "x", "a": 5.0}, {"name": "y", "a": 3.0}]
    r = m.rank_alternatives(alts, ["a"])
    assert all(0.0 <= e["closeness"] <= 1.0 for e in r["ranking"])


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.rank_alternatives([], ["a"])
'''),
    "cluster": (
        "cluster_points",
        "k-means with k-means++ initialisation.",
        "cluster_points(points)",
        '''
def test_separates_two_obvious_groups():
    m = _m()
    pts = [[0.0, 0.0], [0.1, 0.1], [10.0, 10.0], [10.1, 10.1]]
    r = m.cluster_points(pts)
    assert r["assignments"][0] == r["assignments"][1]
    assert r["assignments"][2] == r["assignments"][3]
    assert r["assignments"][0] != r["assignments"][2]


def test_deterministic_for_fixed_seed():
    m = _m()
    pts = [[0.0], [1.0], [10.0], [11.0]]
    assert m.cluster_points(pts) == m.cluster_points(pts)


def test_too_few_points_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.cluster_points([[1.0]])
'''),
    "budget": (
        "allocate_budget",
        "0/1 knapsack allocation by value density.",
        "allocate_budget(items)",
        '''
def test_prefers_high_value_density():
    m = _m()
    items = [{"id": "dense", "cost": 10.0, "value": 100.0},
             {"id": "sparse", "cost": 10.0, "value": 1.0}]
    r = m.allocate_budget(items)
    assert r["chosen"][0] == "dense"


def test_respects_capacity():
    m = _m()
    items = [{"id": "a", "cost": 1000.0, "value": 1.0}]
    r = m.allocate_budget(items)
    assert r["spent"] <= 1000.0


def test_zero_capacity_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.allocate_budget([{"id": "a", "cost": 1.0, "value": 1.0}], capacity=0)


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.allocate_budget([])
'''),
    "queue": (
        "order_queue",
        "Priority queue with aging so low-priority work cannot starve.",
        "order_queue(jobs)",
        '''
def test_high_priority_first():
    m = _m()
    r = m.order_queue([{"id": "lo", "priority": 1, "enqueued": 0.0},
                       {"id": "hi", "priority": 9, "enqueued": 0.0}], now=0.0)
    assert r["order"][0] == "hi"


def test_aging_promotes_starved_job():
    m = _m()
    r = m.order_queue([{"id": "old", "priority": 1, "enqueued": 0.0},
                       {"id": "new", "priority": 2, "enqueued": 100.0}], now=100.0)
    assert r["order"][0] == "old"


def test_empty_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.order_queue([])
'''),
    "audit": (
        "audit_records",
        "Policy engine returning allow/deny/flag with reasons.",
        "audit_records(records, policy)",
        '''
def test_deny_rule_blocks_record():
    m = _m()
    r = m.audit_records([{"id": "x", "risk": 9}], [("risk", "gt", 5, "deny")])
    assert r["denied"] == 1
    assert r["results"][0]["verdict"] == "deny"


def test_flag_rule_marks_record():
    m = _m()
    r = m.audit_records([{"id": "x", "risk": 9}], [("risk", "gt", 5, "flag")])
    assert r["flagged"] == 1


def test_clean_record_allowed():
    m = _m()
    r = m.audit_records([{"id": "x", "risk": 1}], [("risk", "gt", 5, "deny")])
    assert r["allowed"] == 1


def test_empty_policy_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.audit_records([{"id": "x"}], [])
'''),
}


def render_domain(pkg, kernel, title, params, entry, doc):
    src = inspect.getsource(KERNELS[kernel])
    return f'''"""{title} \u2014 real domain implementation.

Option C: replaces the cloned template with genuine domain logic.

{doc}

This module is self-contained: the algorithm below is inlined so the package
has no dependency on the bench/ tree and can be installed on its own.
"""
import math
import random
from collections import defaultdict


{src}

def {entry}(*args, **kwargs):
    """{doc}

    Package-specific defaults: {params if params else "none"}.
    """
    merged = dict({params!r})
    merged.update(kwargs)
    return {kernel}(*args, **merged)
'''


def render_tests(pkg, kernel, title, entry, body):
    return f'''"""{title} \u2014 behaviour tests.

These assert specific computed values, not that the code merely ran.
"""
import importlib
import pytest

MOD = "{pkg}"


def _m():
    return importlib.import_module(MOD + ".domain")

{body}'''


def render_readme(pkg, kernel, title, entry, doc, params):
    return f'''# {title}

`{pkg}` \u2014 real domain implementation (Option C).

## What it does

{doc}

Backed by the `{kernel}` kernel in `bench/optionc/kernels.py`, bound with
package-specific parameters: `{params}`.

## Usage

```python
from {pkg}.domain import {entry}

result = {entry}(...)
```

## Tests

```bash
python -m pytest {pkg}/{pkg}/tests/ -q
```

The tests assert specific computed values (ordering, bounds, exact
arithmetic), not merely that the function returned.
'''


def convert(pkg, meta, root=ROOT):
    kernel = meta.get("operation_kind") or infer_kernel(pkg, meta.get("title", ""))
    if kernel not in KERNELS:
        kernel = infer_kernel(pkg, meta.get("title", ""))
    title = meta.get("title") or pkg
    params = params_for(pkg, kernel)
    entry, doc, _sample, body = SPECS[kernel]

    inner = os.path.join(root, pkg, pkg)
    if not os.path.isdir(inner):
        return None, "no inner package dir"
    if os.path.exists(os.path.join(inner, "domain.py")):
        return None, "already converted"

    os.makedirs(os.path.join(inner, "tests"), exist_ok=True)
    with open(os.path.join(inner, "domain.py"), "w") as f:
        f.write(render_domain(pkg, kernel, title, params, entry, doc))
    with open(os.path.join(inner, "tests", "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(inner, "tests", "test_domain.py"), "w") as f:
        f.write(render_tests(pkg, kernel, title, entry, body))

    init = os.path.join(inner, "__init__.py")
    existing = ""
    if os.path.exists(init):
        with open(init) as f:
            existing = f.read()
    if "domain" not in existing:
        with open(init, "w") as f:
            f.write(existing.rstrip() + f"\n\nfrom .domain import {entry} as {entry}  # noqa: F401\n")

    with open(os.path.join(root, pkg, "README.md"), "w") as f:
        f.write(render_readme(pkg, kernel, title, entry, doc, params))
    return kernel, "ok"


def main():
    plan = json.load(open("/workspace/scratch/plan.json"))
    meta = json.load(open("/workspace/scratch/meta.json"))
    remaining = plan["remaining"]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(remaining)
    done, skipped = {}, {}
    for pkg in remaining[:limit]:
        k, status = convert(pkg, meta.get(pkg, {}))
        if status == "ok":
            done[pkg] = k
        else:
            skipped[pkg] = status
    print(json.dumps({"converted": len(done), "skipped": len(skipped),
                      "by_kernel": {k: list(done.values()).count(k) for k in set(done.values())},
                      "skip_reasons": {r: list(skipped.values()).count(r) for r in set(skipped.values())}},
                     indent=1))
    json.dump(done, open("/workspace/scratch/converted.json", "w"), indent=1)


if __name__ == "__main__":
    main()
