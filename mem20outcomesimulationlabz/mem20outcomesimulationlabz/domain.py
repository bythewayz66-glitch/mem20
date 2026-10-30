"""Outcome simulation lab: Monte Carlo, scenarios, risk."""
import random, statistics


def simulate_once(params, seed=0):
    rng = random.Random(seed)
    base = params.get("base", 100)
    noise = rng.gauss(0, params.get("std", 10))
    return base + noise


def monte_carlo(params, n=100, seed=0):
    rng = random.Random(seed)
    results = []
    for i in range(n):
        results.append(simulate_once(params, seed=rng.randint(0, 10**6)))
    return results


def summarize(results):
    return {"mean": round(statistics.mean(results),4), "std": round(statistics.pstdev(results),4),
            "min": round(min(results),4), "max": round(max(results),4), "p5": round(sorted(results)[int(len(results)*0.05)],4)}


def scenario_compare(scenarios):
    out = []
    for s in scenarios:
        res = monte_carlo(s["params"], n=50, seed=s.get("seed",0))
        out.append({"name": s["name"], **summarize(res)})
    return out


def risk_of_loss(results, threshold=0):
    return sum(1 for r in results if r < threshold) / max(1, len(results))
