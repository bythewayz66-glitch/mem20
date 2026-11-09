"""Model genome lab: model lineage, mutation, fitness, evolution."""
import random


def create_genome(params):
    return {"id": params.get("id"), "genes": dict(params.get("genes", {})), "fitness": 0.0, "generation": 0}


def mutate(genome, rate=0.1, seed=0):
    rng = random.Random(seed)
    g = {"id": genome["id"], "genes": dict(genome["genes"]), "fitness": genome["fitness"], "generation": genome["generation"]+1}
    for k in list(g["genes"].keys()):
        if rng.random() < rate:
            g["genes"][k] = g["genes"][k] + (rng.random()-0.5)*0.1
    return g


def crossover(a, b, seed=0):
    rng = random.Random(seed)
    genes = {}
    for k in set(a["genes"]) | set(b["genes"]):
        genes[k] = a["genes"].get(k, 0) if rng.random() < 0.5 else b["genes"].get(k, 0)
    return {"id": f"{a['id']}x{b['id']}", "genes": genes, "fitness": 0.0, "generation": max(a["generation"], b["generation"])+1}


def fitness(genome, objective):
    # objective: dict of target gene values
    score = 0.0
    for k, v in objective.items():
        score += 1.0 - abs(genome["genes"].get(k, 0) - v)
    genome["fitness"] = round(score / max(1, len(objective)), 4)
    return genome["fitness"]


def evolve(population, objective, generations=3, seed=0):
    rng = random.Random(seed)
    pop = list(population)
    for _ in range(generations):
        for g in pop:
            fitness(g, objective)
        pop.sort(key=lambda g: -g["fitness"])
        # keep top half, mutate
        survivors = pop[:max(1, len(pop)//2)]
        new = []
        for g in survivors:
            new.append(mutate(g, seed=rng.randint(0, 1000)))
        pop = survivors + new
    for g in pop:
        fitness(g, objective)
    pop.sort(key=lambda g: -g["fitness"])
    return pop

# 1st-class extensions (#335)
def genome_record(genome, ancestry=None, adapters=None, limits=None):
    return {"genome": genome, "ancestry": list(ancestry or []), "adapters": list(adapters or []), "limits": dict(limits or {}), "traits": dict(genome.get("genes") or {}), "fitness": genome.get("fitness", 0.0)}

def simulate_genome_lab(spec=None):
    spec=dict(spec or {})
    objective=spec.get("objective") or {"quality":1.0,"latency":0.2}
    pop=[create_genome({"id":f"g{i}","genes":{"quality":0.3+i*0.1,"latency":0.5-i*0.05}}) for i in range(int(spec.get("population",4)))]
    evolved=evolve(pop, objective, generations=int(spec.get("generations",2)), seed=int(spec.get("seed",0)))
    best=evolved[0] if evolved else None
    record=genome_record(best, ancestry=[g.get("id") for g in pop], adapters=spec.get("adapters") or ["default"], limits=spec.get("limits") or {"max_tokens":4096}) if best else None
    return {"ok": bool(best), "best": best, "population_size": len(evolved), "objective": objective, "record": record, "top": evolved[:3]}
