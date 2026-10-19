"""Build the mem20 master todo artifact: exactly 100 plans, each 20-30 roadmap items.

Validates the spec hard and exits non-zero on any violation.
"""
import json
import sys
from collections import OrderedDict

HERE = "/opt/mem20/plans/master"
sys.path.insert(0, HERE)

ns = {}
for f, n in [
    ("plans_data_a.py", "PLANS_A"),
    ("plans_data_b.py", "PLANS_B"),
    ("plans_data_c.py", "PLANS_C"),
    ("plans_data_d.py", "PLANS_D"),
    ("plans_extra.py", "NEW_PLANS"),
    ("plans_extra2.py", "COMPLETION"),
    ("plans_extra3.py", "ROUND3"),
    ("plans_extra4.py", "ROUND4"),
    ("plans_extra5.py", "ROUND5"),
    ("plans_extra6.py", "ROUND6"),
    ("plans_extra7.py", "ROUND7"),
]:
    exec(open(f"{HERE}/{f}").read(), ns)

plans = []
for n in ["PLANS_A", "PLANS_B", "PLANS_C", "PLANS_D"]:
    plans += ns[n]
plans += ns["NEW_PLANS"]

# Apply plan-specific expansions (keyed by current id)
for p in plans:
    extra = ns["EXPANSIONS"].get(p["id"])
    if extra:
        have = set(p["items"])
        for it in extra:
            if it not in have:
                p["items"].append(it)

# Resolve duplicate ids deterministically
seen = {}
for p in plans:
    base = p["id"]
    if base in seen:
        n = 2
        while f"{base}-{n}" in seen:
            n += 1
        p["id"] = f"{base}-{n}"
    seen[p["id"]] = True

# Fill in done_when for the new plans
for p in plans:
    if not p.get("done_when"):
        p["done_when"] = ns["DONE_WHEN"].get(p["id"], "")

# Trim over-length plans
byid = {p["id"]: p for p in plans}
for pid, drop in ns["TRIM"].items():
    p = byid.get(pid)
    if p:
        for d in drop:
            if d in p["items"] and len(p["items"]) > 30:
                p["items"].remove(d)

# Second expansion round (post-dedup ids)
for p in plans:
    for it in ns["EXPAND2"].get(p["id"], []):
        if it not in set(p["items"]):
            p["items"].append(it)

# Third expansion round (post-dedup ids)
for p in plans:
    for it in ns["EXPAND3"].get(p["id"], []):
        if it not in set(p["items"]):
            p["items"].append(it)

# Fourth expansion round (post-dedup ids)
for p in plans:
    for it in ns["EXPAND4"].get(p["id"], []):
        if it not in set(p["items"]):
            p["items"].append(it)

# Fifth expansion round (post-dedup ids)
for p in plans:
    for it in ns["EXPAND5"].get(p["id"], []):
        if it not in set(p["items"]):
            p["items"].append(it)

# Sixth expansion round (post-dedup ids)
for p in plans:
    for it in ns["EXPAND6"].get(p["id"], []):
        if it not in set(p["items"]):
            p["items"].append(it)

# Seventh expansion round (post-dedup ids)
byid7 = {p["id"]: p for p in plans}
for pid, items in ns["EXPAND7"].items():
    p = byid7.get(pid)
    if p is None:
        continue
    for it in items:
        if it not in set(p["items"]):
            p["items"].append(it)

# Final trim: enforce the 30-item ceiling after every expansion
for p in plans:
    while len(p["items"]) > 30:
        p["items"].pop()

# Enforce unique, stable ordering and renumber for the artifact
plans.sort(key=lambda p: (p["domain"], p["id"]))

# ---- Validate the spec hard ----
errors = []
if len(plans) != 100:
    errors.append(f"expected exactly 100 plans, got {len(plans)}")
for p in plans:
    n = len(p["items"])
    if n < 20 or n > 30:
        errors.append(f"{p['id']}: {n} items (need 20-30) — {p['title'][:50]}")
    for k in ("id", "domain", "title", "problem", "done_when", "items"):
        if not p.get(k):
            errors.append(f"{p['id']}: missing field {k}")
titles = [p["title"].lower().strip() for p in plans]
dupes = {t for t in titles if titles.count(t) > 1}
if dupes:
    errors.append(f"duplicate titles: {dupes}")

if errors:
    print("SPEC VIOLATIONS:")
    for e in errors:
        print("  -", e)
    sys.exit(1)

# ---- Emit markdown ----
by_domain = OrderedDict()
for p in plans:
    by_domain.setdefault(p["domain"], []).append(p)

total_items = sum(len(p["items"]) for p in plans)

md = []
md.append("# mem20 Master Todo — 100 Plans")
md.append("")
md.append(f"**Generated:** 2026-10-11 · **Plans:** {len(plans)} · **Roadmap items:** {total_items}")
md.append("")
md.append("Every plan below is grounded in a measurement taken from this system on 2026-10-11.")
md.append("The `problem` field states the verified defect or gap, not a guess. The")
md.append("`done_when` field is a verifiable condition, not a judgement.")
md.append("")
md.append("## Verified baseline (2026-10-11)")
md.append("")
md.append("| Measurement | Value | Source |")
md.append("|---|---|---|")
md.append("| Git sync vs origin/master | 0 ahead / 0 behind (already up to date) | `git fetch --all --prune` |")
md.append("| Sitemap | 329 subsystems, 302 organs, 9,181 files, 472,027 code lines | `mem20sitemapz build` |")
md.append("| Benchmark corpus | 14 grounded facts, 3 simulated, 13 queries | `benchmarks/results/latest.json` |")
md.append("| Adversarial hit rate | 0.000 across all four modes | same |")
md.append("| Graph mode | 1.000 hit rate on **n=2** queries only | same |")
md.append("| Rerank ON vs OFF | 101.4ms / MRR 1.000 direct, 0.640 multi-hop vs 15.7ms / 0.900 / 0.800 | same |")
md.append("| Hybrid p50 | 103.5 ms (semantic 12.2 ms) | same |")
md.append("| Live ledger | 449 records, 41 topics | `/root/.mem20/store/ledger.jsonl` |")
md.append("| Index drift | ledger 449 vs vector_meta 448 vs bm25 448 | file line counts |")
md.append("| Simulated ledger | 85 records | `simulated_ledger.jsonl` |")
md.append("| `index_health` | **MISSING** — MCP tool raises AttributeError | `hasattr(memory,'index_health')` → False |")
md.append("| MEMORY.md / USER.md | **ABSENT** but status reports \"0/2200 OK\" | `ls` failed, `memory_status` reports OK |")
md.append("| Bi-temporal suite | **11 of 14 FAIL**, 3 pass — see P0 below | `pytest`, 64s |")
md.append("| Bi-temporal root cause | `remember()` now REQUIRES `epistemic_status`; tests pass it 0 times | `memory.py:541` ValueError |")
md.append("| Tests calling `remember()` | 15 calls, 0 supply `epistemic_status` | grep on test file |")
md.append("| Regression introduced by | `ca7c1e76` Repair retrieval, add a stable API | `git log` |")
md.append("| `mem20temporaldatabasefabricz` | 54 passed in 0.56s | `pytest -q` |")
md.append("| Cold model download | one-time `sentence_transformers` hub fetch, no timeout | pytest-timeout dump |")
md.append("| Organs with no README | 10 missing + 2 zero-byte | disk audit |")
md.append("| Organs with 0 tests | 241 of 300 | disk audit |")
md.append("| Packaged organs not wiring README | 111 of 158 | pyproject audit |")
md.append("| opencode.db | 200 sessions, 40,847 messages, 5,304 user turns | sqlite3 |")
md.append("| 5,000-QA corpus | **does not exist anywhere on the box** | content sweep, 1,522 JSON files |")
md.append("| Roadmap duplicates | 13 md5-identical step files in 2.0_roadmap | md5sum |")
md.append("")

md.append("## The three P0 findings that block everything else")
md.append("")
md.append("1. **`remember()` contract break — 11 of 14 bi-temporal tests fail.**")
md.append("   `remember()` now raises unless `epistemic_status` is passed")
md.append("   (`memory.py:541`). The test file makes 15 `remember()` calls and supplies")
md.append("   the field **zero** times. Introduced by `ca7c1e76` and never repaired.")
md.append("   The suite's own README claims the bi-temporal bug is fixed and locked by")
md.append("   these tests — the tests do not currently pass, so that claim is unverified.")
md.append("2. **`index_health()` does not exist.** `mem20_memory_index_health` raises")
md.append("   `AttributeError`, yet drift is real (ledger 449 vs vector_meta 448 vs")
md.append("   bm25 448). The trust differentiator's primary diagnostic cannot run.")
md.append("3. **False-green status.** `memory_status` reports `MEMORY.md 0/2200 OK`")
md.append("   for a file that does not exist. A status that lies is worse than no status.")
md.append("")
md.append("> **Correction to an earlier reading of this session.** A first pass concluded")
md.append("> the suite *hangs* on a `huggingface_hub` connect with no timeout. That was a")
md.append("> one-time cold model download, not a persistent defect: with weights cached the")
md.append("> suite completes in 64s and shows the real failures above. The offline hardening")
md.append("> work is still worth doing (plans `R01`, `L01`, `B03`) but it is **not** the")
md.append("> blocker. The blocker is the `epistemic_status` contract break.")
md.append("")

md.append("## Critical path")
md.append("")
md.append("```")
md.append("R01  remember() contract break .. unblocks 11 failing tests")
md.append("C01  index_health() ........... unblocks the trust claim")
md.append("S01  false-green status ....... stop the status lying")
md.append("R01  offline hardening ........ makes benchmarks hermetic")
md.append("B01  corpus 14 -> 1500 ........ needs the above green")
md.append("B02  5000-pair QA benchmark ... needs B01")
md.append("T01  one verify command ....... needs C01")
md.append("```")
md.append("")

md.append("---")
md.append("")
md.append("## Index")
md.append("")
md.append("| # | ID | Domain | Title | Items |")
md.append("|---:|---|---|---|---:|")
n = 0
for dom, ps in by_domain.items():
    for p in ps:
        n += 1
        md.append(f"| {n} | `{p['id']}` | {dom} | {p['title']} | {len(p['items'])} |")
md.append("")

md.append("---")
md.append("")
md.append("## Plans")
md.append("")
for dom, ps in by_domain.items():
    md.append(f"## Domain {dom}")
    md.append("")
    for p in ps:
        md.append(f"### `{p['id']}` — {p['title']}")
        md.append("")
        md.append(f"**Problem (verified):** {p['problem']}")
        md.append("")
        md.append(f"**Done when:** {p['done_when']}")
        md.append("")
        md.append("**Roadmap:**")
        md.append("")
        for i, it in enumerate(p["items"], 1):
            md.append(f"{i}. {it}")
        md.append("")

open(f"{HERE}/MASTER_TODO.md", "w").write("\n".join(md))

json.dump(
    {"generated": "2026-10-11", "plan_count": len(plans), "item_count": total_items,
     "plans": plans},
    open(f"{HERE}/master_todo.json", "w"), indent=2,
)

print(f"OK  plans={len(plans)}  items={total_items}  domains={len(by_domain)}")
print(f"wrote {HERE}/MASTER_TODO.md")
print(f"wrote {HERE}/master_todo.json")