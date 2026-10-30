"""Revenue leak hunter: detect billing leaks, anomalies."""
import statistics


def detect_leaks(transactions, expected):
    leaks = []
    for t in transactions:
        exp = expected.get(t.get("id"))
        if exp is not None and t.get("amount") != exp:
            leaks.append({"id": t.get("id"), "actual": t.get("amount"), "expected": exp, "delta": t.get("amount",0)-exp})
    return leaks


def anomaly_score(values):
    if len(values) < 2:
        return 0.0
    m = statistics.mean(values)
    sd = statistics.pstdev(values) or 1
    return round(max(abs((v-m)/sd) for v in values), 4)


def recoverable(leaks):
    return round(sum(abs(l["delta"]) for l in leaks), 4)


def hunter_health(leaks):
    return {"leaks": len(leaks), "recoverable": recoverable(leaks)}
