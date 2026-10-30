"""Offer genome engine: genetic optimization of offers."""
import random


def create_genome(offer):
    return {"offer": offer, "genes": {"price": offer.get("price", 0), "discount": 0.0, "bundle_size": len(offer.get("components", []))}, "fitness": 0.0}


def mutate(genome, rate=0.2, seed=0):
    rng = random.Random(seed)
    g = {"offer": genome["offer"], "genes": dict(genome["genes"]), "fitness": genome["fitness"]}
    for k in g["genes"]:
        if rng.random() < rate:
            if isinstance(g["genes"][k], (int, float)):
                g["genes"][k] = g["genes"][k] * (0.8 + rng.random()*0.4)
    return g


def fitness(genome, target_conversion=0.1):
    # higher discount -> higher conversion proxy
    conv = min(1.0, genome["genes"].get("discount", 0)*2 + 0.05)
    genome["fitness"] = round(conv, 4)
    return genome["fitness"]


def evolve(population, generations=5, seed=0):
    rng = random.Random(seed)
    pop = list(population)
    for _ in range(generations):
        for g in pop:
            fitness(g)
        pop.sort(key=lambda g: -g["fitness"])
        survivors = pop[:max(1, len(pop)//2)]
        pop = survivors + [mutate(g, seed=rng.randint(0,999)) for g in survivors]
    for g in pop:
        fitness(g)
    pop.sort(key=lambda g: -g["fitness"])
    return pop
