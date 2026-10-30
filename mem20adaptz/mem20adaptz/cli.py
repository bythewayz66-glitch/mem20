"""mem20adaptz CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from . import __version__, MEMBERS, FORMER_PACKAGES
from .runtime import AdaptiveRuntime


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mem20adaptz", description="mem20 adaptive systems runtime")
    p.add_argument("--version", action="store_true")
    p.add_argument("--members", action="store_true")
    p.add_argument("--health", action="store_true")
    p.add_argument("--demo", action="store_true")
    return p


def _demo() -> int:
    rt = AdaptiveRuntime()
    print("=== mem20adaptz unified adaptive runtime demo ===\n")
    rt.forgetting.add("cap-paris", "Paris is the capital of France", stability_days=2.0)
    rt.forgetting.add("cap-tokyo", "Tokyo is the capital of Japan", stability_days=0.3)
    q = rt.forgetting.queue()
    print(f"[forgetting] due={q['due_count']} scheduled={q['scheduled']}")
    for price, qty in [(9.0, 140), (11.0, 110), (13.0, 85), (15.0, 60)]:
        rt.pricing.observe(price, qty)
    rec = rt.pricing.recommend()
    print(f"[pricing] recommended={rec['recommended_price']} elasticity={rec['elasticity']}")
    rt.inference.bid(0.02, 10, agent="buyer-1")
    rt.inference.ask(0.015, 8, agent="seller-1")
    fills = rt.inference.clear()
    print(f"[inference] fills={fills['fill_count']} clearing={fills['clearing_price']}")
    from .dispatch import Agent, Mission
    rt.dispatch.register(Agent(id="a1", capabilities={"code", "review"}, load=0.2, trust=0.9, location="us-east"))
    asg = rt.dispatch.assign(Mission(id="m1", required_capabilities={"code", "review"}, urgency=0.8))
    print(f"[dispatch] best_agent={asg['best']['agent_id'] if asg['best'] else None}")
    style = rt.personality.style_for(task_type="support", urgency=0.8, emotional_valence=-0.4)
    print(f"[personality] tone={style.tone_label}")
    rt.achievement.add_goal("ship", "Ship features", target=10)
    res = rt.achievement.record("ship", 3)
    print(f"[achievement] progress={res['progress']} points={res['total_points']}")
    from .interface import Capability, UserIntent
    rt.interface.register(Capability(id="search", name="Semantic Search", tags=["search"]))
    plan = rt.interface.compose(UserIntent(text="search deployment notes", preferred_tags=["search"]))
    print(f"[interface] plan={plan.plan_id} steps={len(plan.steps)}")
    print("\n=== health ===")
    print(json.dumps(rt.health(), indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"mem20adaptz {__version__}")
        return 0
    if args.members:
        for short, former in MEMBERS.items():
            print(f"{short}\t{former}")
        return 0
    if args.health:
        print(json.dumps(AdaptiveRuntime().health(), indent=2))
        return 0
    if args.demo:
        return _demo()
    print(f"mem20adaptz {__version__} — use --members | --health | --demo | --version")
    return 0


if __name__ == "__main__":
    sys.exit(main())
