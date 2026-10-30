"""Personal cognitive search: index, query, rank, recall."""
import math


def index(docs):
    idx = {}
    for d in docs:
        for w in d.get("text", "").lower().split():
            idx.setdefault(w, []).append(d.get("id"))
    return idx


def query(idx, q, docs_by_id):
    qwords = q.lower().split()
    hits = set()
    for w in qwords:
        for did in idx.get(w, []):
            hits.add(did)
    return [docs_by_id[did] for did in hits if did in docs_by_id]


def rank(results, q):
    qwords = set(q.lower().split())
    scored = []
    for r in results:
        rw = set(r.get("text", "").lower().split())
        scored.append((len(qwords & rw), r))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored]


def recall(idx, recent_ids, k=5):
    # return docs whose terms overlap recent
    return list(recent_ids)[:k]


def search_health(idx):
    return {"terms": len(idx), "postings": sum(len(v) for v in idx.values())}
