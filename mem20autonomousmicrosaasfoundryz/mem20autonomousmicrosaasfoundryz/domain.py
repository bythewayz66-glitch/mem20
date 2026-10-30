"""Autonomous micro-SaaS foundry: idea scoring, MVP spec, launch plan."""
import math


def score_idea(idea):
    market = idea.get("market_size", 0)
    competition = idea.get("competition", 5)
    effort = idea.get("effort", 5)
    score = (market / 100.0) * (1 / max(1, competition)) * (1 / max(1, effort))
    return round(min(1.0,score), 4)


def mvp_spec(idea):
    return {
        "name": idea.get("name"),
        "core_features": idea.get("features", [])[:3],
        "tech_stack": idea.get("stack", "python+react"),
        "timeline_weeks": max(2, idea.get("effort", 4)),
    }


def launch_plan(spec):
    return {
        "phases": ["build", "beta", "launch", "growth"],
        "beta_users": 50,
        "launch_channels": ["producthunt", "twitter", "reddit"],
        "pricing": spec.get("price", 9),
    }


def revenue_projection(users, price, churn=0.05):
    mrr = users * price
    annual = mrr * 12 * (1 - churn)
    return {"mrr": mrr, "arr": round(annual, 2)}


def idea_ranking(ideas):
    scored = [(score_idea(i), i) for i in ideas]
    scored.sort(reverse=True)
    return scored
