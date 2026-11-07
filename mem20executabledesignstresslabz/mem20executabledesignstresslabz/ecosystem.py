"""Six unique peers for Executable Design Stress Lab (#308), different from #300-#307."""
from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# 1) mem20architecturesimulationsandboxz - load/chaos/bottleneck simulation
def architecture_sim(topology: Mapping[str,Any]=None, rps: float=50) -> Dict[str,Any]:
    def run():
        from mem20architecturesimulationsandboxz.domain import simulate_load, scaling_recommendation, topology_cost, bottleneck_node, chaos_test
        topo = dict(topology or {"nodes":[{"id":"api","capacity":100},{"id":"db","capacity":80}], "edges":[{"from":"api","to":"db"}]})
        load = simulate_load(topo, rps=float(rps), duration_s=30)
        metrics = load if isinstance(load, list) else (load.get("nodes") or load.get("metrics") or []) if isinstance(load, dict) else []
        scale = scaling_recommendation(metrics, target_util=0.7) if metrics else []
        cost = topology_cost(topo, cost_per_node=0.05)
        bottleneck = bottleneck_node(metrics) if metrics else None
        chaos = chaos_test(topo, failure_rate=0.1, seed=0)
        return {"simulate_load": load, "scaling": scale, "topology_cost": cost, "bottleneck": bottleneck, "chaos_test": chaos}
    return _safe("mem20architecturesimulationsandboxz", run)

# 2) mem20adversarialqacrewz - adversarial cases/fuzz/mutation
def adversarial_qa(spec: Mapping[str,Any]=None) -> Dict[str,Any]:
    def run():
        from mem20adversarialqacrewz.domain import generate_adversarial_cases, mutation_score, fuzz_input, verdict, hash_case
        s = dict(spec or {"feature":"stress-lab","inputs":["load","capacity"]})
        cases = generate_adversarial_cases(s, count=5)
        score = mutation_score("base", "mutated-base")
        fuzz = fuzz_input({"load":100,"capacity":200}, seed=0)
        v = verdict([{"pass":True},{"pass":True},{"pass":False}])
        h = hash_case(cases[0] if cases else {"x":1})
        return {"cases": cases, "mutation_score": score, "fuzz_input": fuzz, "verdict": v, "hash_sample": h}
    return _safe("mem20adversarialqacrewz", run)

# 3) mem20universalhealthnervoussystemz - health/resilience checks
def health_nervous() -> Dict[str,Any]:
    def run():
        from mem20universalhealthnervoussystemz.domain import register_subsystem, check_all, overall, health_report
        h = {"subsystems": {}, "results": {}}
        register_subsystem(h, "stress", lambda: {"ok": True, "latency_ms": 5})
        register_subsystem(h, "design", lambda: {"ok": True})
        checked = check_all(h)
        ov = overall(h)
        report = health_report(h)
        return {"checked": checked, "overall": ov, "report": report}
    return _safe("mem20universalhealthnervoussystemz", run)

# 4) mem20syntheticevaluatorarenaz - synthetic evaluation/arena
def synthetic_eval(subject: Mapping[str,Any]=None) -> Dict[str,Any]:
    def run():
        from mem20syntheticevaluatorarenaz.domain import create_arena, evaluate, leaderboard, arena_health
        arena = create_arena(["sim-a", "sim-b"])
        subj = dict(subject or {"id":"design"})
        subj_id = str(subj.get("id") or "design")
        evaluate(arena, "resilience", subj_id, 0.8)
        evaluate(arena, "resilience", "design-b", 0.6)
        lb = leaderboard(arena)
        health = arena_health(arena)
        return {"leaderboard": lb, "health": health}
    return _safe("mem20syntheticevaluatorarenaz", run)

# 5) mem20remoteexperimentlabz - experiment runs/compare
def experiment_runs(params: Mapping[str,Any]=None) -> Dict[str,Any]:
    def run():
        from mem20remoteexperimentlabz.domain import create_experiment, run, compare, experiment_health
        e1 = create_experiment("stress-baseline", dict(params or {"load":1.0}))
        e2 = create_experiment("stress-peak", {"load":2.0})
        run(e1, lambda p: {"ok": True, "result": p.get("load",1)*100})
        run(e2, lambda p: {"ok": True, "result": p.get("load",1)*100})
        comp = compare([e1,e2])
        health = experiment_health([e1,e2])
        return {"compare": comp, "health": health}
    return _safe("mem20remoteexperimentlabz", run)

# 6) mem20intentcompilerz - intent/design validation
def intent_validate(text: str = "stress test design graph under 2x load") -> Dict[str,Any]:
    def run():
        from mem20intentcompilerz.domain import parse_intent, classify, compile_to_action, validate, intent_confidence
        intent = parse_intent(text)
        cls = classify(intent)
        action = compile_to_action(intent)
        valid = validate(intent)
        conf = intent_confidence(intent, ["stress","test","design","load"])
        return {"intent": intent, "class": cls, "action": action, "valid": valid, "confidence": conf}
    return _safe("mem20intentcompilerz", run)

def probe() -> Dict[str,Any]:
    checks = {
        "architecture_sim": architecture_sim(),
        "adversarial_qa": adversarial_qa(),
        "health_nervous": health_nervous(),
        "synthetic_eval": synthetic_eval(),
        "experiment_runs": experiment_runs(),
        "intent_validate": intent_validate(),
    }
    reachable=[k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
