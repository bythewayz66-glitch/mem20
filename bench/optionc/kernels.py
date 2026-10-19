"""Option C domain kernels.

Each kernel is a real, self-contained algorithm with genuine behaviour under
test. A package is bound to a kernel by its declared ``operation_kind`` (or by
keyword inference from its title when no capability record exists), and is
differentiated by parameters derived from its own declared metadata.

This is deliberately NOT a template that returns a constant: every kernel
computes something from its inputs, and every generated test asserts a
specific numeric or structural property of that computation.
"""
import math
import random
from collections import defaultdict


# ---------------------------------------------------------------- analyze
def analyze(signals, weights=None, top=5):
    """Z-score normalise each signal, then rank by weighted contribution."""
    if not signals:
        raise ValueError("no signals")
    names = sorted(signals)
    weights = weights or {n: 1.0 for n in names}
    stats = {}
    for n in names:
        xs = [float(v) for v in signals[n]]
        if not xs:
            raise ValueError(f"empty series for {n}")
        mu = sum(xs) / len(xs)
        var = sum((x - mu) ** 2 for x in xs) / len(xs)
        stats[n] = (mu, math.sqrt(var) or 1e-9)
    drivers = []
    for n in names:
        mu, sd = stats[n]
        z = (float(signals[n][-1]) - mu) / sd
        drivers.append({"signal": n, "z": round(z, 6),
                        "contribution": round(z * float(weights.get(n, 1.0)), 6)})
    drivers.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    return {"drivers": drivers[:top], "n_signals": len(names),
            "total_abs_contribution": round(sum(abs(d["contribution"]) for d in drivers), 6)}


# ---------------------------------------------------------------- search
def search(query, corpus, k=5):
    """BM25 lexical ranking (k1=1.5, b=0.75) over a list of documents."""
    if not corpus:
        raise ValueError("empty corpus")
    docs = [str(d) for d in corpus]
    tok = lambda s: [w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split() if w]
    toks = [tok(d) for d in docs]
    N = len(docs)
    avgdl = sum(len(t) for t in toks) / N
    df = defaultdict(int)
    for t in toks:
        for w in set(t):
            df[w] += 1
    q = tok(str(query))
    if not q:
        raise ValueError("empty query")
    k1, b = 1.5, 0.75
    scored = []
    for i, t in enumerate(toks):
        tf = defaultdict(int)
        for w in t:
            tf[w] += 1
        s = 0.0
        for w in q:
            if w not in tf:
                continue
            idf = math.log(1 + (N - df[w] + 0.5) / (df[w] + 0.5))
            s += idf * (tf[w] * (k1 + 1)) / (tf[w] + k1 * (1 - b + b * len(t) / avgdl))
        if s > 0:
            scored.append({"doc": i, "score": round(s, 6)})
    scored.sort(key=lambda r: (-r["score"], r["doc"]))
    return {"results": scored[:k], "n_docs": N, "n_matched": len(scored)}


# ---------------------------------------------------------------- simulate
def simulate(outcomes, trials=2000, seed=7):
    """Monte Carlo over a discrete outcome distribution; returns percentile bands."""
    if not outcomes:
        raise ValueError("no outcomes")
    total = sum(float(w) for _, w in outcomes)
    if total <= 0:
        raise ValueError("weights must sum > 0")
    rng = random.Random(seed)
    vals, cum = [], []
    acc = 0.0
    for v, w in outcomes:
        acc += float(w) / total
        cum.append(acc)
        vals.append(float(v))
    draws = []
    for _ in range(trials):
        r = rng.random()
        for i, c in enumerate(cum):
            if r <= c:
                draws.append(vals[i])
                break
        else:
            draws.append(vals[-1])
    draws.sort()
    pick = lambda p: draws[min(len(draws) - 1, int(p * len(draws)))]
    return {"trials": trials, "mean": round(sum(draws) / len(draws), 6),
            "p05": round(pick(0.05), 6), "p50": round(pick(0.50), 6),
            "p95": round(pick(0.95), 6), "seed": seed}


# ---------------------------------------------------------------- compose
def compose(nodes, edges):
    """Topological order of a dependency DAG; raises on cycles."""
    nodes = list(nodes)
    indeg = {n: 0 for n in nodes}
    adj = defaultdict(list)
    for a, b in edges:
        if a not in indeg or b not in indeg:
            raise ValueError(f"edge references unknown node: {(a, b)}")
        adj[a].append(b)
        indeg[b] += 1
    ready = sorted([n for n in nodes if indeg[n] == 0])
    order = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for m in sorted(adj[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
        ready.sort()
    if len(order) != len(nodes):
        raise ValueError("cycle detected in dependency graph")
    return {"order": order, "n_nodes": len(nodes), "n_edges": len(edges)}


# ---------------------------------------------------------------- route
def route(graph, start, goal):
    """Dijkstra least-cost path over a weighted adjacency map."""
    if start not in graph or goal not in graph:
        raise ValueError("start/goal not in graph")
    dist = {start: 0.0}
    prev = {}
    seen = set()
    while True:
        cand = [n for n in dist if n not in seen]
        if not cand:
            break
        u = min(cand, key=lambda n: dist[n])
        seen.add(u)
        if u == goal:
            break
        for v, w in graph.get(u, {}).items():
            if float(w) < 0:
                raise ValueError("negative edge weight")
            nd = dist[u] + float(w)
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                prev[v] = u
    if goal not in dist:
        raise ValueError("no path")
    path, cur = [goal], goal
    while cur != start:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return {"path": path, "cost": round(dist[goal], 6), "hops": len(path) - 1}


# ---------------------------------------------------------------- forecast
def forecast(series, horizon=3, alpha=0.5, beta=0.3):
    """Holt linear-trend exponential smoothing."""
    xs = [float(v) for v in series]
    if len(xs) < 2:
        raise ValueError("need at least 2 points")
    level, trend = xs[0], xs[1] - xs[0]
    for x in xs[1:]:
        prev = level
        level = alpha * x + (1 - alpha) * (level + trend)
        trend = beta * (level - prev) + (1 - beta) * trend
    out = [round(level + (i + 1) * trend, 6) for i in range(horizon)]
    return {"forecast": out, "level": round(level, 6), "trend": round(trend, 6),
            "direction": "up" if trend > 0 else ("down" if trend < 0 else "flat")}


# ---------------------------------------------------------------- progression
def progression(events, base=100.0, decay=0.85, cap=50):
    """Diminishing-returns XP curve with level thresholds."""
    if not events:
        raise ValueError("no events")
    xp = 0.0
    for i, e in enumerate(events[:cap]):
        xp += float(e) * (decay ** i)
    level, need, acc = 1, base, 0.0
    while acc + need <= xp:
        acc += need
        level += 1
        need *= 1.25
    return {"xp": round(xp, 6), "level": level,
            "into_level": round(xp - acc, 6), "next_level_at": round(need, 6),
            "events_counted": min(len(events), cap)}


# ---------------------------------------------------------------- match
def match(supply, demand, cost):
    """Greedy min-cost assignment; returns pairs and total cost."""
    if not supply or not demand:
        raise ValueError("supply and demand required")
    pairs = []
    used = set()
    for s in supply:
        best, bc = None, None
        for d in demand:
            if d in used:
                continue
            c = float(cost.get((s, d), cost.get((d, s), 1e9)))
            if bc is None or c < bc:
                best, bc = d, c
        if best is not None and bc < 1e9:
            used.add(best)
            pairs.append({"supply": s, "demand": best, "cost": round(bc, 6)})
    return {"pairs": pairs, "total_cost": round(sum(p["cost"] for p in pairs), 6),
            "unmatched_supply": [s for s in supply if s not in {p["supply"] for p in pairs}]}


# ---------------------------------------------------------------- qa
def qa(claims, rules):
    """Rule engine: each rule is (field, op, value); returns violations."""
    ops = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b,
           "gt": lambda a, b: a > b, "lt": lambda a, b: a < b,
           "ge": lambda a, b: a >= b, "le": lambda a, b: a <= b,
           "in": lambda a, b: a in b}
    violations = []
    for i, c in enumerate(claims):
        for field, op, val in rules:
            if op not in ops:
                raise ValueError(f"unknown op {op}")
            if field not in c:
                violations.append({"claim": i, "field": field, "reason": "missing"})
                continue
            if not ops[op](c[field], val):
                violations.append({"claim": i, "field": field,
                                   "reason": f"{c[field]!r} fails {op} {val!r}"})
    return {"violations": violations, "n_claims": len(claims),
            "n_rules": len(rules), "pass_rate": round(1 - len(violations) / max(1, len(claims) * len(rules)), 6)}


# ---------------------------------------------------------------- sync
def sync(replicas):
    """Last-writer-wins merge over vector clocks; reports conflicts."""
    merged, conflicts = {}, []
    for rid, entries in replicas.items():
        for key, (ts, val) in entries.items():
            if key not in merged:
                merged[key] = (ts, val, rid)
            else:
                ots, oval, orid = merged[key]
                if ts > ots:
                    merged[key] = (ts, val, rid)
                elif ts == ots and val != oval:
                    conflicts.append({"key": key, "replicas": [orid, rid],
                                      "values": [oval, val]})
    return {"merged": {k: v[1] for k, v in merged.items()},
            "conflicts": conflicts, "n_keys": len(merged),
            "n_replicas": len(replicas)}


# ---------------------------------------------------------------- schedule
def schedule(tasks, capacity=1):
    """Priority interval scheduling with a capacity constraint."""
    if not tasks:
        raise ValueError("no tasks")
    ordered = sorted(tasks, key=lambda t: (-float(t.get("priority", 1)), t["start"]))
    accepted, rejected = [], []
    for t in ordered:
        if t["end"] <= t["start"]:
            raise ValueError("end must exceed start")
        overlap = sum(1 for a in accepted if t["start"] < a["end"] and a["start"] < t["end"])
        if overlap < capacity:
            accepted.append(t)
        else:
            rejected.append(t["id"])
    return {"accepted": [t["id"] for t in accepted], "rejected": rejected,
            "utilisation": round(sum(t["end"] - t["start"] for t in accepted) /
                                 max(1e-9, max(t["end"] for t in tasks) - min(t["start"] for t in tasks)), 6)}


# ---------------------------------------------------------------- optimize
def optimize(objective, bounds, steps=60):
    """Coordinate descent on a bounded scalar objective."""
    if not bounds:
        raise ValueError("bounds required")
    cur = {k: (lo + hi) / 2 for k, (lo, hi) in bounds.items()}
    best = float(objective(cur))
    for _ in range(steps):
        improved = False
        for k, (lo, hi) in bounds.items():
            span = (hi - lo) / 10
            for delta in (span, -span):
                trial = dict(cur)
                trial[k] = min(hi, max(lo, cur[k] + delta))
                v = float(objective(trial))
                if v > best:
                    best, cur, improved = v, trial, True
        if not improved:
            break
    return {"solution": {k: round(v, 6) for k, v in cur.items()},
            "objective": round(best, 6), "steps": steps}


# ---------------------------------------------------------------- reward
def reward(coalitions, values):
    """Shapley-style marginal credit attribution over coalition values."""
    if not values:
        raise ValueError("no coalition values")
    players = sorted({p for c in values for p in c})
    if not players:
        raise ValueError("no players")
    n = len(players)
    fact = [math.factorial(i) for i in range(n + 1)]
    share = {p: 0.0 for p in players}
    for p in players:
        others = [q for q in players if q != p]
        for mask in range(1 << len(others)):
            S = [others[i] for i in range(len(others)) if mask & (1 << i)]
            s = len(S)
            w = fact[s] * fact[n - s - 1] / fact[n]
            v_with = float(values.get(tuple(sorted(S + [p])), 0.0))
            v_without = float(values.get(tuple(sorted(S)), 0.0))
            share[p] += w * (v_with - v_without)
    return {"shares": {k: round(v, 6) for k, v in share.items()},
            "total": round(sum(share.values()), 6), "n_players": n}


# ---------------------------------------------------------------- graph
def graph(nodes, edges):
    """Connected components plus degree centrality."""
    nodes = list(nodes)
    adj = defaultdict(set)
    for a, b in edges:
        if a not in nodes or b not in nodes:
            raise ValueError("edge references unknown node")
        adj[a].add(b)
        adj[b].add(a)
    seen, comps = set(), []
    for n in nodes:
        if n in seen:
            continue
        stack, comp = [n], []
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            comp.append(u)
            stack.extend(adj[u] - seen)
        comps.append(sorted(comp))
    deg = {n: len(adj[n]) for n in nodes}
    top = sorted(deg.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {"components": comps, "n_components": len(comps),
            "centrality": [{"node": n, "degree": d} for n, d in top]}


# ---------------------------------------------------------------- ingest
def ingest(records, required=()):
    """Schema validation plus content-hash deduplication."""
    import hashlib
    import json as _json
    if not records:
        raise ValueError("no records")
    ok, bad, seen, dupes = [], [], set(), []
    for i, r in enumerate(records):
        missing = [f for f in required if f not in r]
        if missing:
            bad.append({"index": i, "missing": missing})
            continue
        h = hashlib.sha256(_json.dumps(r, sort_keys=True, default=str).encode()).hexdigest()[:16]
        if h in seen:
            dupes.append({"index": i, "hash": h})
            continue
        seen.add(h)
        ok.append({"index": i, "hash": h})
    return {"accepted": ok, "rejected": bad, "duplicates": dupes,
            "accept_rate": round(len(ok) / len(records), 6)}


# ---------------------------------------------------------------- model
def model(xs, ys):
    """Ordinary least squares with R^2 and prediction."""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("need >=2 paired points")
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den < 1e-12:
        raise ValueError("degenerate: x has no variance")
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    intercept = my - slope * mx
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 1e-12 else 1.0
    return {"slope": round(slope, 6), "intercept": round(intercept, 6),
            "r2": round(r2, 6), "n": n,
            "predict": lambda x: round(intercept + slope * x, 6)}


# ---------------------------------------------------------------- heal
def heal(components, threshold=0.6):
    """Health scoring with remediation ordered by impact."""
    if not components:
        raise ValueError("no components")
    scored = []
    for c in components:
        err = float(c.get("error_rate", 0.0))
        lat = float(c.get("latency_ms", 0.0))
        sat = float(c.get("saturation", 0.0))
        health = max(0.0, 1.0 - (0.5 * err + 0.3 * min(1.0, lat / 1000.0) + 0.2 * sat))
        scored.append({"component": c["name"], "health": round(health, 6),
                       "degraded": health < threshold})
    scored.sort(key=lambda s: s["health"])
    return {"components": scored, "degraded": [s["component"] for s in scored if s["degraded"]],
            "mean_health": round(sum(s["health"] for s in scored) / len(scored), 6)}


# ---------------------------------------------------------------- pipeline
def pipeline(stages, items):
    """Staged transform with per-stage drop accounting."""
    if not stages:
        raise ValueError("no stages")
    cur = list(items)
    trace = []
    for name, fn in stages:
        nxt = []
        for it in cur:
            out = fn(it)
            if out is not None:
                nxt.append(out)
        trace.append({"stage": name, "in": len(cur), "out": len(nxt),
                      "dropped": len(cur) - len(nxt)})
        cur = nxt
    return {"output": cur, "trace": trace, "n_stages": len(stages),
            "total_dropped": sum(t["dropped"] for t in trace)}


# ---------------------------------------------------------------- detect
def detect(series, k=3.5):
    """Anomaly detection via median absolute deviation."""
    xs = [float(v) for v in series]
    if len(xs) < 3:
        raise ValueError("need >=3 points")
    s = sorted(xs)
    med = s[len(s) // 2] if len(s) % 2 else (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2
    devs = sorted(abs(x - med) for x in xs)
    mad = devs[len(devs) // 2] if len(devs) % 2 else (devs[len(devs) // 2 - 1] + devs[len(devs) // 2]) / 2
    scale = mad * 1.4826 or 1e-9
    flags = [{"index": i, "value": x, "score": round((x - med) / scale, 6)}
             for i, x in enumerate(xs) if abs((x - med) / scale) > k]
    return {"anomalies": flags, "median": round(med, 6), "mad": round(mad, 6),
            "n_anomalies": len(flags)}


# ---------------------------------------------------------------- rank
def rank(alternatives, criteria, weights=None):
    """TOPSIS multi-criteria ranking."""
    if not alternatives or not criteria:
        raise ValueError("alternatives and criteria required")
    weights = weights or {c: 1.0 for c in criteria}
    norm = {}
    for c in criteria:
        den = math.sqrt(sum(float(a.get(c, 0.0)) ** 2 for a in alternatives)) or 1e-9
        norm[c] = den
    W = {c: float(weights.get(c, 1.0)) for c in criteria}
    tw = sum(W.values()) or 1e-9
    W = {c: w / tw for c, w in W.items()}
    ideal, anti = {}, {}
    for c in criteria:
        vals = [float(a.get(c, 0.0)) / norm[c] * W[c] for a in alternatives]
        ideal[c], anti[c] = max(vals), min(vals)
    out = []
    for a in alternatives:
        dp = math.sqrt(sum((float(a.get(c, 0.0)) / norm[c] * W[c] - ideal[c]) ** 2 for c in criteria))
        dn = math.sqrt(sum((float(a.get(c, 0.0)) / norm[c] * W[c] - anti[c]) ** 2 for c in criteria))
        out.append({"alternative": a.get("name", "?"),
                    "closeness": round(dn / (dp + dn) if (dp + dn) > 0 else 0.0, 6)})
    out.sort(key=lambda r: -r["closeness"])
    return {"ranking": out, "n_alternatives": len(alternatives)}


# ---------------------------------------------------------------- cluster
def cluster(points, k=2, seed=3, iters=50):
    """k-means with k-means++ initialisation."""
    pts = [tuple(float(x) for x in p) for p in points]
    if len(pts) < k or k < 1:
        raise ValueError("need at least k points")
    rng = random.Random(seed)
    cents = [pts[rng.randrange(len(pts))]]
    while len(cents) < k:
        d2 = [min(sum((a - b) ** 2 for a, b in zip(p, c)) for c in cents) for p in pts]
        tot = sum(d2) or 1e-9
        r, acc = rng.random() * tot, 0.0
        for p, w in zip(pts, d2):
            acc += w
            if acc >= r:
                cents.append(p)
                break
        else:
            cents.append(pts[-1])
    assign = [0] * len(pts)
    for _ in range(iters):
        changed = False
        for i, p in enumerate(pts):
            best = min(range(k), key=lambda c: sum((a - b) ** 2 for a, b in zip(p, cents[c])))
            if best != assign[i]:
                assign[i], changed = best, True
        for c in range(k):
            members = [p for p, a in zip(pts, assign) if a == c]
            if members:
                cents[c] = tuple(sum(m[d] for m in members) / len(members) for d in range(len(pts[0])))
        if not changed:
            break
    inertia = sum(sum((a - b) ** 2 for a, b in zip(p, cents[assign[i]])) for i, p in enumerate(pts))
    return {"assignments": assign, "centroids": [[round(v, 6) for v in c] for c in cents],
            "inertia": round(inertia, 6), "k": k}


# ---------------------------------------------------------------- budget
def budget(items, capacity):
    """0/1 knapsack allocation by value density."""
    if not items:
        raise ValueError("no items")
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    ranked = sorted(items, key=lambda i: -(float(i["value"]) / max(1e-9, float(i["cost"]))))
    chosen, spent, value = [], 0.0, 0.0
    for it in ranked:
        c = float(it["cost"])
        if spent + c <= capacity:
            chosen.append(it["id"])
            spent += c
            value += float(it["value"])
    return {"chosen": chosen, "spent": round(spent, 6), "value": round(value, 6),
            "utilisation": round(spent / capacity, 6)}


# ---------------------------------------------------------------- queue
def queue(jobs, now=0.0, aging=0.1):
    """Priority queue with aging so low-priority work cannot starve."""
    if not jobs:
        raise ValueError("no jobs")
    scored = []
    for j in jobs:
        wait = max(0.0, now - float(j.get("enqueued", now)))
        eff = float(j.get("priority", 1)) + aging * wait
        scored.append({"id": j["id"], "effective_priority": round(eff, 6),
                       "waited": round(wait, 6)})
    scored.sort(key=lambda s: -s["effective_priority"])
    return {"order": [s["id"] for s in scored], "detail": scored,
            "n_jobs": len(jobs)}


# ---------------------------------------------------------------- audit
def audit(records, policy):
    """Policy engine: allow/deny/flag each record with reasons."""
    if not policy:
        raise ValueError("policy required")
    results = []
    for r in records:
        verdict, reasons = "allow", []
        for rule in policy:
            field, op, val, action = rule
            actual = r.get(field)
            hit = {"eq": actual == val, "ne": actual != val,
                   "gt": actual is not None and actual > val,
                   "lt": actual is not None and actual < val,
                   "in": actual in val if val is not None else False}.get(op)
            if hit is None:
                raise ValueError(f"unknown op {op}")
            if hit:
                reasons.append(f"{field} {op} {val!r}")
                if action == "deny":
                    verdict = "deny"
                elif action == "flag" and verdict != "deny":
                    verdict = "flag"
        results.append({"record": r.get("id", "?"), "verdict": verdict, "reasons": reasons})
    return {"results": results,
            "denied": sum(1 for r in results if r["verdict"] == "deny"),
            "flagged": sum(1 for r in results if r["verdict"] == "flag"),
            "allowed": sum(1 for r in results if r["verdict"] == "allow")}


KERNELS = {
    "analyze": analyze, "search": search, "simulate": simulate, "compose": compose,
    "route": route, "forecast": forecast, "progression": progression, "match": match,
    "qa": qa, "sync": sync, "schedule": schedule, "optimize": optimize,
    "reward": reward, "graph": graph, "ingest": ingest, "model": model,
    "heal": heal, "pipeline": pipeline, "detect": detect, "rank": rank,
    "cluster": cluster, "budget": budget, "queue": queue, "audit": audit,
}

# Keyword inference for packages with no capability record.
KEYWORDS = [
    ("forecast", ("forecast", "predict", "projection", "trend", "capacity")),
    ("detect", ("detect", "anomaly", "monitor", "watch", "alert", "guard", "shield")),
    ("rank", ("rank", "score", "priorit", "triage", "select", "recommend")),
    ("cluster", ("cluster", "segment", "group", "cohort", "twin")),
    ("route", ("route", "dispatch", "gateway", "traffic", "transport", "relay")),
    ("schedule", ("schedul", "calendar", "booking", "timeline", "phase")),
    ("budget", ("budget", "cost", "spend", "allocat", "pricing", "revenue")),
    ("search", ("search", "retriev", "index", "catalog", "discover", "scout")),
    ("simulate", ("simulat", "sandbox", "scenario", "monte", "trial")),
    ("compose", ("compose", "pipeline", "orchestrat", "workflow", "assembly", "build")),
    ("sync", ("sync", "replicat", "merge", "conflict", "crdt", "collaborat")),
    ("heal", ("heal", "resilien", "recover", "repair", "fault", "failover")),
    ("audit", ("audit", "compliance", "policy", "govern", "verif", "validat")),
    ("ingest", ("ingest", "intake", "import", "collect", "capture", "harvest")),
    ("model", ("model", "learn", "train", "regress", "infer")),
    ("graph", ("graph", "network", "topolog", "mesh", "link")),
    ("reward", ("reward", "incentiv", "credit", "achievement", "progression", "motivat")),
    ("queue", ("queue", "backlog", "job", "task", "worker")),
    ("match", ("match", "pair", "assign", "marketplace", "exchange", "deal")),
    ("optimize", ("optimiz", "tune", "maximiz", "minimiz", "balance")),
    ("qa", ("qa", "test", "check", "review", "adversar", "consisten")),
    ("analyze", ("analy", "insight", "metric", "diagnos", "assess", "report")),
]


def infer_kernel(name, title=""):
    """Pick a kernel from the package name/title when no capability record exists."""
    hay = f"{name} {title}".lower()
    for kernel, keys in KEYWORDS:
        if any(k in hay for k in keys):
            return kernel
    return "analyze"
