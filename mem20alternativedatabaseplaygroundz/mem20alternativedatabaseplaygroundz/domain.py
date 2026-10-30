"""Alternative database playground: query plans, index suggestions, benchmarks."""
import math, random


def query_plan(query, tables):
    """Generate a simple query plan."""
    return {
        "query": query,
        "steps": [{"op": "scan", "table": t} for t in tables],
        "estimated_cost": len(tables) * 10,
    }


def suggest_index(columns, cardinality):
    """Suggest index on high-cardinality columns."""
    suggestions = []
    for c, card in zip(columns, cardinality):
        if card > 100:
            suggestions.append({"column": c, "reason": "high cardinality", "cardinality": card})
    return suggestions


def benchmark_query(plan, rows):
    """Estimate query execution time (ms)."""
    base = plan.get("estimated_cost", 10)
    return round(base * math.log10(max(10, rows)) / 10.0, 3)


def compare_engines(results):
    """Compare multiple engine benchmark results."""
    if not results:
        return {}
    best = min(results, key=lambda r: r.get("time_ms", float("inf")))
    return {"fastest": best.get("engine"), "best_time": best.get("time_ms"), "all": results}


def index_efficiency(indexed_cols, total_cols):
    """Compute index coverage ratio."""
    if total_cols == 0:
        return 0.0
    return round(len(indexed_cols) / total_cols, 4)
