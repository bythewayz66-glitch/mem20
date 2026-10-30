"""Spatial command universe: 3D commands, regions, navigation."""
import math


def create_region(name, bounds):
    return {"name": name, "bounds": bounds, "entities": []}


def add_entity(region, entity, pos):
    region["entities"].append({"entity": entity, "pos": pos})
    return region


def distance(a, b):
    return math.sqrt(sum((a[i]-b[i])**2 for i in range(len(a))))


def in_region(region, pos):
    b = region["bounds"]
    return all(b[i][0] <= pos[i] <= b[i][1] for i in range(len(pos)))


def spatial_health(regions):
    return {"regions": len(regions), "entities": sum(len(r["entities"]) for r in regions)}
