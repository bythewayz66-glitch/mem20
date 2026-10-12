"""Index corpus chunks into an ISOLATED benchmark store and emit probe queries.

Never touches /root/.mem20/store.
"""
import json, os, re, sys, collections
from pathlib import Path

BENCH = Path("/opt/mem20/bench")
STORE = BENCH / "store"
STORE.mkdir(parents=True, exist_ok=True)
os.environ["MEM20_STORE_PATH"] = str(STORE)
sys.path.insert(0, "/root/.mem20/store")
import memory as M

assert str(M.STORE_DIR) == str(STORE), f"store escape! {M.STORE_DIR}"

STOP = set("""the a an and or but if then else for to of in on at by with from as is are was were be been being
this that these those it its he she they we you i not no yes do does did have has had will would can could
should may might must about into over under again further once here there when where why how all any both
each few more most other some such than too very s t just don now what which who whom whose""".split())

def distinctive(text):
    """Rare-ish tokens: identifiers, paths, code, CamelCase, numbers+units."""
    out = []
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]{2,}", text):
        w = m.group(0)
        if w.lower() in STOP: continue
        if "_" in w or (any(c.isupper() for c in w[1:]) and len(w) > 3):
            out.append(w)
    for m in re.finditer(r"/[\w./-]{3,}", text):
        out.append(m.group(0))
    seen, uniq = set(), []
    for w in out:
        lw = w.lower()
        if lw in seen: continue
        seen.add(lw); uniq.append(w)
    return uniq

def main():
    chunks = [json.loads(l) for l in open(BENCH/"corpus"/"corpus.jsonl")]
    print(f"indexing {len(chunks)} chunks into ISOLATED store {STORE}")
    n = 0
    for c in chunks:
        M.remember(topic=c["role"],
                   content=c["text"],
                   tags=["bench", c["session_id"][:12]],
                   source=f"bench:{c['id']}",
                   epistemic_status="observed")
        n += 1
        if n % 5000 == 0:
            print(f"  {n}...")
    print(f"indexed {n}")
    print("stats:", json.dumps(M.memory_stats(), default=str)[:400])
    with open(BENCH/"corpus"/"store_map.json","w") as f:
        json.dump({c["id"]: {"ts": c["ts"], "sess": c["session_id"]} for c in chunks}, f)


if __name__ == "__main__":
    main()
