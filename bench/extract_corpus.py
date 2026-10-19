"""Extract a retrievable corpus from opencode.db (READ-ONLY).

Writes JSONL of {id, session_id, role, text} then chunks to ~180 words.
"""
import json, sqlite3, re, sys, hashlib
from pathlib import Path

DB = "file:/root/.local/share/opencode/opencode.db?mode=ro"
OUT = Path("/opt/mem20/bench/corpus")
OUT.mkdir(parents=True, exist_ok=True)
TARGET_CHARS = 900  # ~180 words

def main():
    con = sqlite3.connect(DB, uri=True)
    cur = con.cursor()
    n_msg = 0
    turns = []
    q = ("SELECT m.id, m.session_id, m.time_created, m.data, p.data "
         "FROM message m JOIN part p ON p.message_id = m.id "
         "WHERE m.data IS NOT NULL AND p.data IS NOT NULL")
    for mid, sid, tcreated, mdata, pdata in cur.execute(q):
        try:
            md = json.loads(mdata); pd = json.loads(pdata)
        except Exception:
            continue
        if pd.get("type") != "text":
            continue
        text = (pd.get("text") or "").strip()
        if len(text) < 40:          # skip "hi", "ok" etc
            continue
        role = md.get("role") or md.get("agent") or "unknown"
        n_msg += 1
        turns.append((mid, sid, int(tcreated or 0), str(role), text))

    # chunk long turns
    chunks = []
    for mid, sid, ts, role, text in turns:
        if len(text) <= TARGET_CHARS * 1.5:
            pieces = [text]
        else:
            words = text.split()
            pieces = [" ".join(words[i:i+TARGET_CHARS//5])
                      for i in range(0, len(words), TARGET_CHARS//5)]
        for pi, p in enumerate(pieces):
            p = p.strip()
            if len(p) < 60:
                continue
            cid = hashlib.sha1(f"{mid}:{pi}".encode()).hexdigest()[:16]
            chunks.append({"id": cid, "msg_id": mid, "session_id": sid,
                           "ts": ts, "role": role, "text": p})
    chunks.sort(key=lambda c: c["ts"])
    with open(OUT / "corpus.jsonl", "w") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")
    print(f"turns(text,>=40ch): {len(turns)}   chunks: {len(chunks)}")
    roles = {}
    for c in chunks:
        roles[c["role"]] = roles.get(c["role"], 0) + 1
    print("by role:", roles)
    print("sessions:", len({c['session_id'] for c in chunks}))
    ln = [len(c["text"]) for c in chunks]
    print("chars: min %d med %d max %d" % (min(ln), sorted(ln)[len(ln)//2], max(ln)))

if __name__ == "__main__":
    main()
