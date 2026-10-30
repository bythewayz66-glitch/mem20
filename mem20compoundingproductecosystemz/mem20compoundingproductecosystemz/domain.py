"""Compounding product ecosystem: synergies, network effects, growth."""
import math


def synergy(a, b):
    shared = set(a.get("users", [])) & set(b.get("users", []))
    return round(len(shared) * 0.1 + a.get("value", 0) * b.get("value", 0) * 0.01, 4)


def network_value(n_users, connections_per_user=3):
    # Metcalfe's law: V = n * (n-1) / 2 * density
    return round(n_users * (n_users - 1) / 2 * 0.01, 2)


def compound_growth(initial, rate, periods):
    out = [initial]
    cur = initial
    for _ in range(periods - 1):
        cur = cur * (1 + rate)
        out.append(round(cur, 2))
    return out


def ecosystem_health(products):
    if not products:
        return 0.0
    avg_synergy = sum(synergy(products[i], products[j]) for i in range(len(products)) for j in range(i + 1, len(products))) / max(1, len(products) * (len(products) - 1) / 2)
    return round(min(1.0, avg_synergy + 0.3), 4)


def cross_sell_matrix(products):
    matrix = {}
    for a in products:
        for b in products:
            if a.get("id") != b.get("id"):
                matrix.setdefault(a.get("id"), {})[b.get("id")] = synergy(a, b)
    return matrix
