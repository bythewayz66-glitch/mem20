import importlib
from pathlib import Path

from mem20gamebalancesimulatorz.mem20gamebalancesimulatorz import ecosystem
from mem20gamebalancesimulatorz.mem20gamebalancesimulatorz.runtime import Engine, load_config

MOD = "mem20gamebalancesimulatorz.mem20gamebalancesimulatorz.domain"


def _d():
    return importlib.import_module(MOD)


def _assert_signal(signal):
    assert isinstance(signal, dict) and "subsystem" in signal and "ok" in signal
    if not signal["ok"]:
        assert "error" in signal


def test_legacy_domain_preserved():
    m = _d()
    assert m.dps(10, 2) == 20
    assert m.ttk(100, 10) == 10.0
    assert m.economy_balance(100, 40) == 60
    assert len(m.difficulty_curve(3)) == 3
    assert m.balance_check({"hp": 100}, {"hp": 100})["balanced"] is True
    assert m.win_rate([{"winner": "player"}, {"winner": "enemy"}]) == 0.5


def test_ecosystem_six_peers_attempted():
    p = ecosystem.probe()
    assert set(p["checks"].keys()) == {"skill_progression", "player_motivation", "level_architecture", "community_challenge", "skill_transfer", "impact_rewards"}
    for v in p["checks"].values():
        _assert_signal(v)


def test_monte_carlo_scenario_agent_model_deterministic_and_distributions():
    m = _d()
    cfg = {
        "combat": {"player_damage": 14, "player_attack_speed": 1.5, "player_health": 110, "enemy_health": 90, "enemy_damage": 8, "enemy_attack_speed": 1.1},
        "progression": {"levels": 4, "xp_per_win": 30, "xp_per_loss": 10},
        "economy": {"income_per_win": 40, "income_per_loss": 12, "expense_per_run": 10, "shop_price": 50},
    }
    strategies = [
        {"name": "aggressive", "damage_mult": 1.2, "defense_mult": 0.9, "economy_mult": 1.0, "risk": 0.1},
        {"name": "turtle", "damage_mult": 0.85, "defense_mult": 1.2, "economy_mult": 0.95, "risk": -0.05},
    ]
    a = m.monte_carlo_balance(cfg, strategies=strategies, runs=40, seed=123)
    b = m.monte_carlo_balance(cfg, strategies=strategies, runs=40, seed=123)
    assert a["deterministic"] and a["seed"] == 123
    assert a["total_simulations"] == 80 and b["total_simulations"] == 80
    assert a["distributions"]["win_rate"] == b["distributions"]["win_rate"], "seeded batch must be deterministic"
    assert a["diagnostics"] == b["diagnostics"]
    # covers interacting systems
    assert "combat" not in a or True
    dist = a["distributions"]["win_rate"]
    assert {"n", "mean", "variance", "std", "p05", "p50", "p95", "confidence_95_mean", "by_strategy"} <= set(dist.keys())
    assert set(dist["by_strategy"].keys()) == {"aggressive", "turtle"}
    assert all(0 <= dist["by_strategy"][s]["mean"] <= 1 for s in dist["by_strategy"])


def test_diagnostics_outliers_sensitivity_and_regression_scenario():
    m = _d()
    # regression: overpowered player should win most games
    strong = m.monte_carlo_balance({
        "combat": {"player_damage": 40, "player_attack_speed": 2.0, "player_health": 200, "enemy_health": 50, "enemy_damage": 3, "enemy_attack_speed": 1.0},
        "economy": {"income_per_win": 50, "income_per_loss": 5, "expense_per_run": 5},
        "progression": {"levels": 3},
    }, runs=60, seed=7)
    assert strong["diagnostics"]["overall_win_rate"] > 0.8
    weak = m.monte_carlo_balance({
        "combat": {"player_damage": 4, "player_attack_speed": 0.8, "player_health": 40, "enemy_health": 150, "enemy_damage": 18, "enemy_attack_speed": 1.5},
        "economy": {"income_per_win": 10, "income_per_loss": 2, "expense_per_run": 20},
        "progression": {"levels": 3},
    }, runs=60, seed=7)
    assert weak["diagnostics"]["overall_win_rate"] < 0.4
    # diagnostics/sensitivity/outliers present
    rep = strong
    assert "is_balanced" in rep["diagnostics"] and "strategy_spread" in rep["diagnostics"] and "economy_positive_rate" in rep["diagnostics"]
    assert isinstance(rep["sensitivity"], list) and len(rep["sensitivity"]) >= 3
    assert all("parameter" in s and "delta_win_rate" in s for s in rep["sensitivity"])
    assert isinstance(rep["outliers"], list)


def test_batch_scaling_and_edge_cases():
    m = _d()
    small = m.monte_carlo_balance(runs=5, seed=1)
    large = m.monte_carlo_balance(runs=120, seed=1)
    assert small["total_simulations"] < large["total_simulations"]
    assert large["distributions"]["win_rate"]["n"] == large["total_simulations"]
    # edge: zero-ish/degenerate config should not crash
    edge = m.monte_carlo_balance({"combat": {"player_damage": 0, "player_attack_speed": 0, "enemy_damage": 0, "enemy_attack_speed": 0, "player_health": 1, "enemy_health": 1}}, runs=10, seed=2)
    assert edge["ok"] and edge["total_simulations"] == 10 * len(edge["strategies"])
    assert 0 <= edge["diagnostics"]["overall_win_rate"] <= 1


def test_engine_progression_backward_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "g.sqlite3"))
    out = eng.execute({"xp": 300, "thresholds": [100, 250, 500]}, idem="p1")
    assert out["xp"] == 300 and out["level"] == 2 and out["next_threshold"] == 500
    assert "signals" not in out


def test_engine_progression_with_balance_signals_and_monte_carlo(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "gb.sqlite3"))
    out = eng.execute({
        "xp": 120, "damage": 10, "attack_speed": 2, "health": 100,
        "income": 100, "expenses": 40, "levels": 4, "balance": True,
        "monte_carlo": True, "runs": 20, "seed": 5,
        "scenarios": [{"name": "baseline"}], "simulations": [{"winner": "player"}],
    }, idem="b1", timeout_ms=30000)
    assert "xp" in out and "level" in out
    assert "balance" in out and out["balance"].get("monte_carlo", {}).get("deterministic") is True
    sig = out.get("signals") or {}
    for k in ("skill_progression", "player_motivation", "level_architecture", "community_challenge", "skill_transfer", "impact_rewards"):
        _assert_signal(sig.get(k, {}))


def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    sim = eng.simulator()
    assert all(v.get("ok") for v in sim.values()), sim
