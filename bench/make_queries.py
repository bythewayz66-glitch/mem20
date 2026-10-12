"""Generate probe queries from corpus chunks.

Query types (each probes a different retrieval capability):
  idf   - rare/distinctive identifier terms (lexical+entity challenge)
  head  - first sentence of the chunk (semantic paraphrase challenge)
  mixed - identifiers + a connective phrase
"""
import json, re, math, random, collections
from pathlib import Path

BENCH = Path("/opt/mem20/bench")
STOP = set("""the a an and or but if then else for to of in on at by with from as is are was were be been being
this that these those it its he she they we you i not no yes do does did have has had will would can could
should may might must about into over under again further once here there when where why how all any both
each few more most other some such than too very s t just don now what which who whom whose also will using
use used like get got make made want need know see look new one two three""".split())

def toks(t):
    return [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_./-]{1,}", t) if w.lower() not in STOP]

def main():
    chunks = [json.loads(l) for l in open(BENCH/"corpus"/"corpus.jsonl")]
    # document frequency for IDF
    df = collections.Counter()
    for c in chunks:
        for w in set(w.lower() for w in toks(c["text"])):
            df[w] += 1
    N = len(chunks)
    idf = {w: math.log(N / (1 + df[w])) for w in df}

    rng = random.Random(20261012)
    sample = rng.sample(chunks, min(1200, len(chunks)))
    out = []
    for c in sample:
        words = toks(c["text"])
        if len(words) < 8:
            continue
        scored = sorted(set(words), key=lambda w: -idf.get(w.lower(), 0))
        ident = [w for w in scored if ("_" in w or "/" in w or
                (any(ch.isupper() for ch in w[1:]) and len(w) > 4))][:4]
        if len(ident) < 2:
            ident = scored[:2]
        first = re.split(r"(?<=[.!?])\s+", c["text"].strip())[0][:220]
        out.append({
            "chunk_id": c["id"], "session_id": c["session_id"], "ts": c["ts"],
            "q_idf": " ".join(ident),
            "q_head": first,
            "q_mixed": " ".join(ident[:2]) + " " + first[:120],
        })
    with open(BENCH/"corpus"/"queries.jsonl", "w") as f:
        for q in out:
            f.write(json.dumps(q) + "\n")
    print(f"generated {len(out)} probe queries x3 types")
    for q in out[:3]:
        print("  idf :", q["q_idf"][:70])
        print("  head:", q["q_head"][:70])

if __name__ == "__main__":
    main()
