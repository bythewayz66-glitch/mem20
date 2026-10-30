"""Cross-product loyalty graph: edges, centrality, recommendations."""
import math


def add_edge(graph, a, b, weight=1.0):
    graph.setdefault(a, {})[b] = graph.get(a, {}).get(b, 0) + weight
    graph.setdefault(b, {})[a] = graph.get(b, {}).get(a, 0) + weight
    return graph


def degree(graph, node):
    return len(graph.get(node, {}))


def centrality(graph):
    # simple degree centrality
    n = len(graph)
    if n <= 1:
        return {}
    return {node: round(deg / (n - 1), 4) for node, deg in ((n, degree(graph, n)) for n in graph)}


def recommend_products(graph, user_products, top=3):
    scores = {}
    for p in user_products:
        for neighbor, w in graph.get(p, {}).items():
            if neighbor not in user_products:
                scores[neighbor] = scores.get(neighbor, 0) + w
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [p for p, _ in ranked[:top]]


def loyalty_score(user_products, graph):
    if not user_products:
        return 0.0
    total_edges = sum(degree(graph, p) for p in user_products)
    return round(total_edges / max(1, len(user_products)), 4)
