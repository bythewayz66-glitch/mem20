"""Executable game concept & scope pipeline: concept, scope, feasibility."""
import math


def concept_score(concept):
    innovation = concept.get("innovation", 5)
    market = concept.get("market_fit", 5)
    feasibility = concept.get("feasibility", 5)
    return round(min(1.0,(innovation + market + feasibility) / 15.0), 4)


def scope_estimate(concept):
    features = concept.get("features", [])
    base_weeks = len(features) * 2
    complexity = concept.get("complexity", "medium")
    mult = {"low": 0.8, "medium": 1.0, "high": 1.5}.get(complexity, 1.0)
    return {"weeks": round(base_weeks * mult), "features": len(features), "complexity": complexity}


def feasibility_check(concept, budget_weeks=24):
    scope = scope_estimate(concept)
    return {"feasible": scope["weeks"] <= budget_weeks, "needed": scope["weeks"], "budget": budget_weeks}


def risk_assessment(concept):
    risks = []
    if concept.get("complexity") == "high":
        risks.append("high complexity")
    if concept.get("market_fit", 5) < 4:
        risks.append("low market fit")
    if concept.get("team_size", 5) < 3:
        risks.append("small team")
    return risks


def pipeline_stage(concept):
    score = concept_score(concept)
    if score >= 0.8:
        return "greenlit"
    if score >= 0.5:
        return "prototype"
    return "concept"
