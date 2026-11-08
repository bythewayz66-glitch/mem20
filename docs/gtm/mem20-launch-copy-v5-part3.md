## 4.6 Canonical benchmark table

Every asset above quotes from this table. It is the transcription source of record; `python3 docs/gtm/audit-launch-copy.py` verifies it cell-by-cell against `benchmarks/results/latest.json`.

| mode | direct | multi-hop | adversarial | adv-hard | contradiction | unanswerable |
|---|---|---|---|---|---|---|
| `bm25` | **1.000** (60) | **0.800** (30) | **0.767** (60) | **0.025** (40) | **0.050** (40) | **0.000** (20) |
| `vector` | **0.900** (60) | **1.000** (30) | **0.667** (60) | **0.750** (40) | **1.000** (40) | **0.000** (20) |
| `hybrid` | **1.000** (60) | **0.533** (30) | **0.167** (60) | **0.050** (40) | **1.000** (40) | **0.000** (20) |
| `hybrid-rerank-off` | **1.000** (60) | **1.000** (30) | **0.650** (60) | **0.625** (40) | **1.000** (40) | **0.000** (20) |
| `keyword` | **1.000** (60) | **0.467** (30) | **0.167** (60) | **0.025** (40) | **0.125** (40) | **0.000** (20) |
| `graph` | — | **0.033** (30) | — | — | — | — |

Corpus `mem20-scale-corpus-v2`: 700 grounded / 1,300 simulated / 250 queries. Trust properties: `contamination_rate` **0.0** over 700 ledger records, **0** degraded queries of 250, **654** graph entities / **3,601** edges.

**The row that matters:** `unanswerable` is **0.000 in every mode**, n=20. Abstention is unsolved and no asset may imply otherwise.

---

## 4.7 Where the rest of the pack lives

Sections 5–9 (long-form article, README/install block, claim ledger index, guardrails, hand-off and open defects) are in [`mem20-launch-copy-v5-part2.md`](./mem20-launch-copy-v5-part2.md). They are split out only because the GitHub contents API rejects a single payload above ~15 KB; the two files are one pack and ship together.
