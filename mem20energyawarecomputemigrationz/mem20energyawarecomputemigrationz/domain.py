"""Energy-aware compute migration: energy cost, migration decisions."""
import math


def energy_cost(node, workload_size):
    power = node.get("power_watts", 100)
    time_s = workload_size / max(0.1, node.get("speed", 1.0))
    kwh = power * time_s / 3600000.0
    rate = node.get("energy_rate", 0.12)
    return round(kwh * rate, 6)


def migrate_decision(src, dst, workload):
    src_cost = energy_cost(src, workload.get("size", 1))
    dst_cost = energy_cost(dst, workload.get("size", 1))
    if dst_cost < src_cost * 0.8:
        return {"migrate": True, "savings": round(src_cost - dst_cost, 4)}
    return {"migrate": False, "savings": 0.0}


def carbon_footprint(node, workload_size):
    kwh = node.get("power_watts", 100) * (workload_size / max(0.1, node.get("speed", 1.0))) / 3600000.0
    carbon_intensity = node.get("carbon_g_per_kwh", 400)
    return round(kwh * carbon_intensity, 4)


def greenest_node(nodes, workload):
    scored = [(energy_cost(n, workload.get("size", 1)) + carbon_footprint(n, workload.get("size", 1)) * 0.001, n) for n in nodes]
    scored.sort()
    return scored[0][1] if scored else None


def migration_plan(workloads, nodes):
    plan = []
    for w in workloads:
        n = greenest_node(nodes, w)
        if n:
            plan.append({"workload": w.get("id"), "target": n.get("id")})
    return plan
