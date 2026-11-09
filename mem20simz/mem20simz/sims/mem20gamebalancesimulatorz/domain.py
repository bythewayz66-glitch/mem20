"""Game balance simulator: stats, DPS, TTK, economy, and large-scale
scenario/agent Monte Carlo simulation.

Legacy API preserved:
  dps(damage, attack_speed), ttk(health, dps_val), economy_balance(income, expenses),
  difficulty_curve(levels, base, growth), balance_check(stats, targets), win_rate(simulations)
"""
from __future__ import annotations

import math
import random
import statistics
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


# ---- legacy API ----

def dps(damage, attack_speed):
    return round(float(damage) * float(attack_speed), 2)


def ttk(health, dps_val):
    if float(dps_val) <= 0:
        return float("inf")
    return round(float(health) / float(dps_val), 3)


def economy_balance(income, expenses):
    return round(float(income) - float(expenses), 2)


def difficulty_curve(levels, base=1.0, growth=1.12):
    return [round(float(base) * (float(growth) ** i), 3) for i in range(int(levels))]


def balance_check(stats, targets):
    issues = []
    for k, target in (targets or {}).items():
        actual = (stats or {}).get(k, 0)
        t = float(target)
        if abs(float(actual) - t) > abs(t) * 0.2:
            issues.append({"stat": k, "actual": actual, "target": target})
    return {"balanced": not issues, "issues": issues}


def win_rate(simulations):
    sims = list(simulations or [])
    if not sims:
        return 0.0
    wins = sum(1 for s in sims if (s or {}).get("winner") == "player")
    return round(wins / len(sims), 4)


# ---- scenario/agent Monte Carlo simulator ----

DEFAULT_CONFIG = {
    "combat": {"player_damage": 12.0, "player_attack_speed": 1.4, "player_health": 100.0, "enemy_health": 90.0, "enemy_damage": 9.0, "enemy_attack_speed": 1.2, "armor_mitigation": 0.1, "crit_chance": 0.1, "crit_mult": 1.5},
    "progression": {"levels": 5, "xp_per_win": 30.0, "xp_per_loss": 10.0, "xp_curve_base": 50.0, "xp_curve_growth": 1.25, "skill_growth": 0.03},
    "economy": {"income_per_win": 40.0, "income_per_loss": 12.0, "expense_per_run": 15.0, "shop_price": 60.0, "upgrade_power": 2.0, "inflation": 0.0},
    "player_strategies": [
        {"name": "aggressive", "damage_mult": 1.15, "defense_mult": 0.9, "economy_mult": 0.95, "risk": 0.1},
        {"name": "balanced", "damage_mult": 1.0, "defense_mult": 1.0, "economy_mult": 1.0, "risk": 0.0},
        {"name": "greedy", "damage_mult": 0.95, "defense_mult": 0.95, "economy_mult": 1.2, "risk": 0.05},
        {"name": "turtle", "damage_mult": 0.85, "defense_mult": 1.2, "economy_mult": 0.9, "risk": -0.05},
    ],
}


def _merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _percentile(vals: Sequence[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    if len(s) == 1:
        return float(s[0])
    k = (len(s) - 1) * p
    f = math.floor(k); c = math.ceil(k)
    if f == c:
        return float(s[int(k)])
    return float(s[f] * (c - k) + s[c] * (k - f))


def _dist(vals: Sequence[float]) -> Dict[str, Any]:
    vals = [float(v) for v in vals]
    if not vals:
        return {"n": 0}
    mean = statistics.fmean(vals)
    var = statistics.pvariance(vals) if len(vals) > 1 else 0.0
    std = math.sqrt(var)
    return {
        "n": len(vals),
        "mean": round(mean, 6),
        "variance": round(var, 6),
        "std": round(std, 6),
        "min": round(min(vals), 6),
        "max": round(max(vals), 6),
        "p05": round(_percentile(vals, 0.05), 6),
        "p50": round(_percentile(vals, 0.50), 6),
        "p95": round(_percentile(vals, 0.95), 6),
        "confidence_95_mean": round(1.96 * std / math.sqrt(len(vals)), 6) if len(vals) > 1 else 0.0,
    }


def run_scenario(config: Mapping[str, Any], strategy: Mapping[str, Any], seed: int, runs_per_scenario: int = 1) -> List[Dict[str, Any]]:
    rng = random.Random(int(seed))
    combat = dict(config.get("combat") or {})
    prog = dict(config.get("progression") or {})
    econ = dict(config.get("economy") or {})
    results = []
    xp_needed = difficulty_curve(int(prog.get("levels", 5)), base=float(prog.get("xp_curve_base", 50)), growth=float(prog.get("xp_curve_growth", 1.25)))
    for i in range(max(1, int(runs_per_scenario))):
        player_hp = float(combat.get("player_health", 100)) * float(strategy.get("defense_mult", 1.0))
        enemy_hp = float(combat.get("enemy_health", 90))
        # progression/economy interactions: starting resources affect upgrades
        gold = 0.0
        xp = 0.0
        level = 0
        upgrades = 0
        rounds = 0
        while rounds < 50 and player_hp > 0 and enemy_hp > 0:
            rounds += 1
            pd = float(combat.get("player_damage", 12)) * float(strategy.get("damage_mult", 1.0)) * (1.0 + upgrades * float(econ.get("upgrade_power", 2.0)) / 100.0)
            pd *= float(combat.get("player_attack_speed", 1.4))
            if rng.random() < float(combat.get("crit_chance", 0.1)):
                pd *= float(combat.get("crit_mult", 1.5))
            ed = float(combat.get("enemy_damage", 9)) * float(combat.get("enemy_attack_speed", 1.2))
            ed *= max(0.1, 1.0 - float(combat.get("armor_mitigation", 0.1)) * float(strategy.get("defense_mult", 1.0)) + float(strategy.get("risk", 0.0)))
            # simultaneous exchange approximation
            enemy_hp -= max(0.0, pd + rng.uniform(-pd * 0.1, pd * 0.1))
            if enemy_hp <= 0:
                break
            player_hp -= max(0.0, ed + rng.uniform(-ed * 0.1, ed * 0.1))
            # economy during combat: can buy upgrade if enough gold and below level cap
            if gold >= float(econ.get("shop_price", 60)) and level < len(xp_needed):
                gold -= float(econ.get("shop_price", 60))
                upgrades += 1
        win = enemy_hp <= 0 and player_hp > 0
        gold += (float(econ.get("income_per_win", 40)) if win else float(econ.get("income_per_loss", 12))) * float(strategy.get("economy_mult", 1.0))
        gold -= float(econ.get("expense_per_run", 15))
        xp += float(prog.get("xp_per_win", 30) if win else prog.get("xp_per_loss", 10))
        for threshold in xp_needed:
            if xp >= threshold:
                level += 1
        results.append({
            "winner": "player" if win else "enemy",
            "rounds": rounds,
            "remaining_player_hp": round(max(0.0, player_hp), 4),
            "remaining_enemy_hp": round(max(0.0, enemy_hp), 4),
            "gold": round(gold, 4),
            "xp": round(xp, 4),
            "level": level,
            "upgrades": upgrades,
            "strategy": strategy.get("name"),
            "seed": int(seed),
            "run": i,
        })
    return results


def monte_carlo_balance(config: Optional[Mapping[str, Any]] = None, strategies: Optional[Sequence[Mapping[str, Any]]] = None, runs: int = 100, seed: int = 0) -> Dict[str, Any]:
    cfg = _merge(DEFAULT_CONFIG, config or {})
    strats = list(strategies or cfg.get("player_strategies") or DEFAULT_CONFIG["player_strategies"])
    runs = max(1, int(runs))
    seed = int(seed)
    all_results = []
    by_strategy = {}
    for si, strat in enumerate(strats):
        sname = str(strat.get("name") or f"strategy-{si}")
        sres = []
        for i in range(runs):
            sres.extend(run_scenario(cfg, strat, seed=seed * 100000 + si * 1000 + i, runs_per_scenario=1))
        by_strategy[sname] = sres
        all_results.extend(sres)
    # distributions
    metrics = {}
    for mkey, getter in [
        ("win_rate", lambda r: 1.0 if r["winner"] == "player" else 0.0),
        ("rounds", lambda r: r["rounds"]),
        ("gold", lambda r: r["gold"]),
        ("xp", lambda r: r["xp"]),
        ("remaining_player_hp", lambda r: r["remaining_player_hp"]),
    ]:
        vals = [getter(r) for r in all_results]
        metrics[mkey] = _dist(vals)
        metrics[mkey]["by_strategy"] = {s: _dist([getter(r) for r in rs]) for s, rs in by_strategy.items()}
    # outliers (z-score on rounds)
    rounds_vals = [r["rounds"] for r in all_results]
    mu = statistics.fmean(rounds_vals) if rounds_vals else 0
    sigma = statistics.pstdev(rounds_vals) if len(rounds_vals) > 1 else 1
    outliers = [r for r in all_results if sigma > 0 and abs((r["rounds"] - mu) / sigma) > 2.5][:20]
    # sensitivity: vary one parameter (player_damage +/- 20%)
    base_wr = win_rate(all_results)
    sensitivities = []
    for param, path in [("player_damage", ("combat", "player_damage")), ("enemy_health", ("combat", "enemy_health")), ("income_per_win", ("economy", "income_per_win"))]:
        deltas = {}
        for label, mult in [("down", 0.8), ("up", 1.2)]:
            c2 = _merge(cfg, {})
            sect, key = path
            c2.setdefault(sect, {})[key] = float((cfg.get(sect) or {}).get(key, 1)) * mult
            r2 = []
            for si, strat in enumerate(strats):
                for i in range(min(runs, 30)):
                    r2.extend(run_scenario(c2, strat, seed=seed * 777 + si * 1000 + i + (1 if label == "up" else 0)))
            deltas[label] = round(win_rate(r2) - base_wr, 6)
        sensitivities.append({"parameter": param, "base_win_rate": base_wr, "delta_win_rate": deltas})
    # balance diagnostics / regression guardrails
    wr = metrics["win_rate"]["mean"]
    diagnostics = {
        "overall_win_rate": round(wr, 6),
        "balanced_band": [0.35, 0.65],
        "is_balanced": 0.35 <= wr <= 0.65,
        "strategy_spread": round(max((metrics["win_rate"]["by_strategy"][s]["mean"] for s in metrics["win_rate"]["by_strategy"]), default=0) - min((metrics["win_rate"]["by_strategy"][s]["mean"] for s in metrics["win_rate"]["by_strategy"]), default=0), 6),
        "economy_positive_rate": round(sum(1 for r in all_results if r["gold"] >= 0) / max(1, len(all_results)), 6),
    }
    return {
        "ok": True,
        "seed": seed,
        "deterministic": True,
        "runs_per_strategy": runs,
        "strategies": [str(s.get("name")) for s in strats],
        "total_simulations": len(all_results),
        "distributions": metrics,
        "outliers": outliers,
        "sensitivity": sensitivities,
        "diagnostics": diagnostics,
        "sample_results": all_results[:5],
    }
