"""R@k evaluation across mem20 retrieval methods, on the ISOLATED bench store.

Usage: python eval_rerank.py [--limit N] [--k 5]
"""
import argparse, json, os, sys, time
from pathlib import Path

BENCH = Path("/opt/mem20/bench")
os.environ["MEM20_STORE_PATH"] = str(BENCH / "store")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.path.insert(0, "/root/.mem20/store")
import memory as M

def indexed_sources():
    """chunk ids actually present in the bench store."""
    out = set()
    led = BENCH / "store" / "ledger.jsonl"
    if not led.exists():
        return out
    for line in led.open():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        s = d.get("source") or ""
        if isinstance(s, str) and s.startswith("bench:"):
            out.add(s.split(":", 1)[1])
    return out

def score(results, gold, k):
    if not results:
        return 0.0, None
    for i, r in enumerate(results[:k]):
        rid = None
        if isinstance(r, dict):
            rid = (r.get("source") or "")
            if isinstance(rid, str) and rid.startswith("bench:"):
                rid = rid.split(":", 1)[1]
        if rid == gold:
            return 1.0, i + 1
    return 0.0, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    gold_pool = indexed_sources()
    qs = [json.loads(l) for l in open(BENCH / "corpus" / "queries.jsonl")]
    qs = [q for q in qs if q["chunk_id"] in gold_pool]
    qs = qs[:args.limit]
    print(f"indexed chunks: {len(gold_pool)}   scorable queries: {len(qs)}   k={args.k}")
    if not qs:
        print("no scorable queries yet - indexing still running")
        return

    methods = [
        ("semantic", lambda q: M.recall_semantic(q, k=args.k)),
        ("hybrid",   lambda q: M.recall_hybrid(q, k=args.k)),
    ]
    summary = {}
    for name, fn in methods:
        t0 = time.time()
        hits = 0
        ranks = []
        errs = 0
        for q in qs:
            for qtype in ("q_idf", "q_head", "q_mixed"):
                try:
                    res = fn(q[qtype])
                except Exception:
                    errs += 1
                    continue
                h, rk = score(res, q["chunk_id"], args.k)
                hits += h
                if rk:
                    ranks.append(rk)
        total = len(qs) * 3
        dt = time.time() - t0
        rec = hits / total if total else 0.0
        mrr = (sum(1 / r for r in ranks) / total) if total else 0.0
        summary[name] = {"recall@k": round(rec, 4), "mrr": round(mrr, 4),
                         "latency_ms": round(dt / total * 1000, 1),
                         "errors": errs, "n": total}
        print(f"  {name:9s} R@{args.k}={rec:.3f}  MRR={mrr:.3f}  "
              f"{dt/total*1000:.1f}ms/q  errors={errs}")
    json.dump(summary, open(BENCH / "results" / "rerank.json", "w")
              if (BENCH / "results").exists() else open("/tmp/opencode/rerank.json", "w"), indent=1)

if __name__ == "__main__":
    main()
