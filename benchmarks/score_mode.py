"""Score ONE mode against an existing healthy store and write its slice to JSON.

Split out from the monolithic run-scale because the harness caps at ~2 GB and a
single process that both ingests and scores every mode gets OOM-killed here.
Each invocation prints the wall time and writes its own file, so a partial run
is visible rather than silently truncated.

    python benchmarks/score_mode.py <store> <corpus_dir> <mode> <out.json>
"""
import json
import sys
import time

from mem20api import open_store
from mem20benchmarkz.bench import run
from mem20benchmarkz.scale_corpus import load_jsonl_corpus

store_path, corpus_dir, mode, out = sys.argv[1:5]
corpus = load_jsonl_corpus(corpus_dir)
t0 = time.time()
with open_store(store_path) as store:
    health = store.health()
    assert health["healthy"], health
    report = run(store, modes=(mode,), k=5, corpus=corpus, compare_rerank=False)
d = report.to_dict()
d["_elapsed_s"] = round(time.time() - t0, 1)
unanswerable = [r for r in d["per_query"] if r["kind"] == "unanswerable"]
d["_unanswerable_rows"] = len(unanswerable)
d["_unanswerable_max_hit"] = (
    max(1 if r["hit"] else 0 for r in unanswerable) if unanswerable else None)
with open(out, "w") as fh:
    json.dump(d, fh, indent=2, default=str)
print(json.dumps({"mode": mode, "elapsed_s": d["_elapsed_s"],
                  "kinds": {k: v["n"] for k, v in d["recall"].get(mode, {}).items()}},
                 indent=1))
