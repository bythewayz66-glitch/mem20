"""Tests for unified mem20adapz runtime."""

from __future__ import annotations
import time
from mem20adapz import AdaptiveRuntime, MEMBERS
from mem20adapz.forgetting import retention, reinforce, review_queue
from mem20adapz.pricing import recommend_price
from mem20adapz.inference import Order, match
from mem20adapz.dispatch import Agent, Mission, assign
from mem20adapz.personality import derive_style
from mem20adapz.achievement import AchievementEngine
from mem20adapz.interface import Capability, UserIntent, InterfaceComposer


def test_members_complete():
    assert set(MEMBERS) == {"achievement", "dispatch", "forgetting", "inference", "interface", "personality", "pricing"}


def test_forgetting_retention_math():
    assert abs(retention(0, 1.0) - 1.0) < 1e-9
    assert retention(100, 1.0) < 0.01
    assert reinforce(1.0, success=True) > 1.0


def test_forgetting_queue_orders_by_lapse():
    now = time.time()
    items = [{"id": "fresh", "last_review_ts": now, "stability_days": 10.0}, {"id": "stale", "last_review_ts": now - 30 * 86400, "stability_days": 2.0}]
    q = review_queue(items, now_ts=now, threshold=0.5)
    assert q["due_count"] >= 1
    assert q["queue"][0]["id"] == "stale"


def test_pricing_elasticity():
    rec = recommend_price([(10, 100), (12, 80), (14, 60), (16, 45)], objective="revenue")
    assert rec["elasticity"] < 0
    assert rec["recommended_price"] > 0


def test_inference_match():
    result = match([Order(price=0.02, ts=1.0, side="buy", qty=5, oid="b1"), Order(price=0.015, ts=1.0, side="sell", qty=3, oid="s1")])
    assert result["fill_count"] == 1
    assert result["matched_volume"] == 3


def test_dispatch_prefers_capable_idle_trusted():
    agents = [Agent(id="good", capabilities={"code", "review"}, load=0.1, trust=0.95, location="us"), Agent(id="busy", capabilities={"code", "review"}, load=0.9, trust=0.95, location="us"), Agent(id="unskilled", capabilities={"code"}, load=0.0, trust=0.95, location="us")]
    result = assign(Mission(id="m", required_capabilities={"code", "review"}, urgency=0.7, preferred_location="us"), agents)
    assert result["best"]["agent_id"] == "good"


def test_personality_crisis_is_direct():
    style = derive_style(task_type="crisis", urgency=0.9)
    assert style.directness > 0.8


def test_achievement_tiers():
    eng = AchievementEngine()
    eng.add_goal("g1", "Ship it", target=100)
    r1 = eng.record("g1", 30)
    assert "g1:bronze" in r1["newly_unlocked"]


def test_interface_compose():
    comp = InterfaceComposer()
    comp.register(Capability(id="s", name="Search memory", tags=["search", "memory"]))
    plan = comp.compose(UserIntent(text="search memory notes", preferred_tags=["search"]))
    assert plan.steps and plan.steps[0]["capability_id"] == "s"


def test_runtime_health_and_integration():
    rt = AdaptiveRuntime()
    rt.forgetting.add("k", "v")
    rt.pricing.observe(5, 50)
    rt.pricing.observe(7, 30)
    h = rt.health()
    assert h["runtime"] == "mem20adapz"
    assert set(h["organs"]) == set(MEMBERS)
