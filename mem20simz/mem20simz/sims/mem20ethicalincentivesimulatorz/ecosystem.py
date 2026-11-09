"""Six unique peers for Ethical Incentive Simulator (#307), different from #300-#306."""
from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# 1) mem20simz - simulate/monte-carlo outcomes and risk
def outcome_simulation(params: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20simz.domain import simulate_once, monte_carlo, summarize, risk_of_loss, scenario_compare
        p = dict(params or {"base": 1.0, "std": 0.2})
        once = simulate_once(p, seed=0)
        mc = monte_carlo(p, n=20, seed=1)
        summ = summarize(mc)
        risk = risk_of_loss(mc, threshold=float(p.get("loss_threshold", 0)))
        comp = scenario_compare([{"name": "baseline", "params": p, "seed": 0}, {"name": "stress", "params": dict(p, std=float(p.get("std", 0.2))*2), "seed": 1}])
        return {"simulate_once": once, "summary": summ, "risk_of_loss": risk, "scenario_compare": comp, "runs": 20}
    return _safe("mem20simz", run)

# 2) mem20simz - incentive/balance dynamics
def balance_dynamics(stats: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20simz.domain import dps, ttk, economy_balance, difficulty_curve, balance_check, win_rate
        s = dict(stats or {"damage": 10, "attack_speed": 1.5, "health": 100, "income": 50, "expenses": 40})
        d = dps(float(s.get("damage",10)), float(s.get("attack_speed",1)))
        t = ttk(float(s.get("health",100)), float(d) if isinstance(d,(int,float)) else 15.0)
        econ = economy_balance(float(s.get("income",50)), float(s.get("expenses",40)))
        curve = difficulty_curve(5, base=1.0, growth=1.12)
        bal = balance_check(s, {"health": 100, "income": 50})
        wr = win_rate([{"winner": "player"}, {"winner": "opponent"}, {"winner": "player"}])
        return {"dps": d, "ttk": t, "economy": econ, "difficulty_curve": curve, "balance_check": bal, "win_rate": wr}
    return _safe("mem20simz", run)

# 3) mem20twinz - twin/simulate incentive process outcomes
def incentive_twin(process: Mapping[str, Any] = None, action: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20twinz.domain import create_twin, sync_twin, simulate, predict_outcome, drift
        proc = dict(process or {"id": "incentive-flow", "state": {"reward": 10, "fairness": 0.8}})
        twin = create_twin(proc)
        twin = sync_twin(twin, dict(proc.get("state") or {}))
        act = dict(action or {"type": "adjust_reward", "delta": 2})
        sim = simulate(twin, [act])
        pred = predict_outcome(twin, act)
        dr = drift(twin, {"reward": 12, "fairness": 0.7})
        return {"twin_id": (twin.get("id") if isinstance(twin, dict) else None), "simulate": sim, "predict_outcome": pred, "drift": dr}
    return _safe("mem20twinz", run)

# 4) mem20dynamicquestrewardcomposerz - reward composition/balance
def reward_composition(level: int = 1, quests: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20dynamicquestrewardcomposerz.domain import generate_quest, reward_for_quest, balance_quests, quest_chain, completion_rate
        q = generate_quest(difficulty=1, seed=0)
        rew = reward_for_quest(q, player_level=max(1, int(level)))
        qs = [dict(x) for x in (quests or [q, generate_quest(difficulty=2, seed=1)])]
        bal = balance_quests(qs)
        chain = quest_chain(qs)
        rate = completion_rate(2, 3)
        return {"quest": q, "reward": rew, "balance": bal, "chain": chain, "completion_rate": rate}
    return _safe("mem20dynamicquestrewardcomposerz", run)

# 5) mem20rewardforgez - shaped/normalized rewards
def reward_forge(state: Mapping[str, Any] = None, rewards: Sequence[float] = None) -> Dict[str, Any]:
    def run():
        from mem20rewardforgez.domain import linear_reward, shaped_reward, normalize, reward_health
        st = dict(state or {"effort": 1.0, "fairness": 0.8, "harm_risk": 0.1})
        weights = {"effort": 0.5, "fairness": 0.4, "harm_risk": -0.3}
        lin = linear_reward(st, weights)
        shaped = shaped_reward(lin if isinstance(lin,(int,float)) else 0.5, 0.1)
        rw = list(rewards or [0.2, 0.5, 0.8, 0.3])
        norm = normalize(rw)
        health = reward_health(rw)
        return {"linear": lin, "shaped": shaped, "normalized": norm, "health": health}
    return _safe("mem20rewardforgez", run)

# 6) mem20pipez - risk/feasibility assessment
def risk_feasibility(concept: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20pipez.domain import concept_score, scope_estimate, feasibility_check, risk_assessment, pipeline_stage
        c = dict(concept or {"name": "ethical-incentive", "complexity": 3, "harm_risk": 0.2, "manipulation_risk": 0.1, "budget_weeks": 8})
        score = concept_score(c)
        scope = scope_estimate(c)
        feas = feasibility_check(c, budget_weeks=int(c.get("budget_weeks", 24)))
        risk = risk_assessment(c)
        stage = pipeline_stage(c)
        return {"concept_score": score, "scope": scope, "feasibility": feas, "risk_assessment": risk, "stage": stage}
    return _safe("mem20pipez", run)

def probe() -> Dict[str, Any]:
    checks = {
        "outcome_simulation": outcome_simulation(),
        "balance_dynamics": balance_dynamics(),
        "incentive_twin": incentive_twin(),
        "reward_composition": reward_composition(),
        "reward_forge": reward_forge(),
        "risk_feasibility": risk_feasibility(),
    }
    reachable = [k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
