import importlib
from pathlib import Path
from mem20gamebalancesimulatorz.mem20gamebalancesimulatorz import ecosystem
from mem20gamebalancesimulatorz.mem20gamebalancesimulatorz.runtime import Engine, load_config

MOD = "mem20gamebalancesimulatorz.mem20gamebalancesimulatorz.domain"

def _d(): return importlib.import_module(MOD)

def test_legacy_domain_preserved():
    m = _d()
    assert m.dps(10, 2) == 20
    assert m.ttk(100, 10) == 10.0
    assert m.economy_balance(100, 40) == 60
    assert len(m.difficulty_curve(3)) == 3
    assert m.balance_check({"hp": 100}, {"hp": 100})["balanced"] is True
    assert m.win_rate([{"winner": "player"}, {"winner": "enemy"}]) == 0.5

def test_ecosystem_six_peers():
    p = ecosystem.probe()
    assert p["ok"] and p["count"] == 6
    assert ecosystem.skill_progression({"xp": 100})["ok"]
    assert ecosystem.player_motivation({"player": "p1"})["ok"]
    assert ecosystem.level_architecture({"levels": 3})["ok"]
    assert ecosystem.community_challenge({"goal": 50})["ok"]
    assert ecosystem.skill_transfer({})["ok"]
    assert ecosystem.impact_rewards({})["ok"]

def test_engine_progression_backward_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "g.sqlite3"))
    out = eng.execute({"xp": 300, "thresholds": [100, 250, 500]}, idem="p1")
    assert out["xp"] == 300 and out["level"] == 2 and out["next_threshold"] == 500
    # not enriched
    assert "signals" not in out

def test_engine_progression_with_balance_signals(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "gb.sqlite3"))
    out = eng.execute({
        "xp": 120, "damage": 10, "attack_speed": 2, "health": 100,
        "income": 100, "expenses": 40, "levels": 4, "balance": True,
        "scenarios": [{"name": "baseline"}], "simulations": [{"winner": "player"}],
    }, idem="b1", timeout_ms=30000)
    assert "xp" in out and "level" in out
    assert "balance" in out
    sig = out.get("signals") or {}
    for k in ("skill_progression", "player_motivation", "level_architecture", "community_challenge", "skill_transfer", "impact_rewards"):
        assert sig.get(k, {}).get("ok") is True, (k, sig.get(k))

def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    sim = eng.simulator()
    assert all(v.get("ok") for v in sim.values()), sim
