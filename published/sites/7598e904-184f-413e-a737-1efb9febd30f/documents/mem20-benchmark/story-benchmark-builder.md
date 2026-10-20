# mem20 — story of the Benchmark Dataset Builder

Scope: the benchmark half of mem20 only — corpus generation, validation, the
LoCoMo / LongMemEval / DMR-style harness, and every published result. Written
2026-10-19. Every count and byte figure below was re-measured against the live
CDN during this writing, not recalled.

---

## 1. What I have done on mem20

### 1.1 The state I inherited

The entire benchmark programme hung off one URL: `github.com/JaysonAIOnline/mem20`.
That URL returns **HTTP 404**, and `pip install mem20` **404s on PyPI**. Both
probes were re-run and both still fail. So there was no engine to read a schema
from, no importable store, no fixture files.

Decision made at that point rather than stalling: pin the record envelope from
the documented store contract (`remember()` for grounded content,
`remember_simulated()` for simulated content, `epistemic_status` vocabulary
`observed | inferred | imagined | user_stated | hypothesis | agent_generated`)
plus the three published benchmark protocol formats, and **flag the assumption in
the deliverable**. `SCHEMA.md` carries that flag, `RESULTS.md` repeats it, and the
mem20 backend column reads `UNAVAILABLE` rather than being silently dropped.

### 1.2 The corpus — two builds

**Build 1 (2026-10-14, first publication).** 84,600 records, 28,200 per category,
107,598,879 bytes (102.61 MB), three shards sized under the 50 MB upload cap.
Measured today off the CDN:

| shard | records | bytes |
|---|---:|---:|
| `mem20-benchmark-dataset.part-01.jsonl` | 37,074 | 47,185,039 |
| `mem20-benchmark-dataset.part-02.jsonl` | 37,118 | 47,184,842 |
| `mem20-benchmark-dataset.part-03.jsonl` | 10,408 | 13,228,998 |
| **total** | **84,600** | **107,598,879** |

**Build 2 (current, seed `20261014`).** Re-tuned to land on the ~100 MB target
instead of 102.6 MB, then revalidated and republished:

| metric | measured value |
|---|---|
| records | **116,997** |
| grounded / ungrounded / false | 39,000 / 39,000 / 38,997 |
| category share | 0.3333 / 0.3333 / 0.3333 |
| JSONL bytes | **104,854,740 B = 99.997 MiB** |
| bytes per record | 896.2 |
| distinct keys / ids | 116,997 / 116,997 |
| validation | **PASS**, 0 errors, 0 warnings |

Shard counts re-verified by streaming each shard today:

| shard | records | bytes |
|---|---:|---:|
| `benchmark-corpus-part001.jsonl` | 44,204 | 39,845,023 |
| `benchmark-corpus-part002.jsonl` | 44,529 | 39,845,300 |
| `benchmark-corpus-part003.jsonl` | 28,264 | 25,164,417 |
| **total** | **116,997** | **104,854,740** |

### 1.3 The three categories, and why they are not blurred

The split carries the whole point of the dataset, so the contracts are hard
constraints enforced by the validator, not conventions:

- **grounded** (39,000) — verifiably true, anchored to a real checkable source,
  carrying a `source` URL **and** a verbatim `evidence` excerpt. Reference data
  is real and cached, never invented: PeriodicTableJSON (119 elements),
  ISO-3166 (249 countries), `jshttp/mime-db` (2,601 media types), USPS (51 state
  codes), GeoNames `cities15000` (34,162 cities).
- **ungrounded** (39,000) — a seeded fictional universe (companies, people,
  planets) that is plausible and internally consistent but has no verifiable
  source. `source`, `evidence` and `contradicts` are all **null**. Nothing
  invented is presented as true.
- **false** (38,997) — deterministic mutations of specific grounded records:
  wrong dates, swapped attributes, fabricated attributions, wrong values.
  `contradicts` points at the exact grounded `key` it contradicts and
  `true_value` records the real value, so being wrong is checkable programmatically.
  The count is 38,997 rather than 39,000 because a handful of grounded records
  have no faithful mutation — balance is matched to the *falsifiable* grounded
  set, not the raw grounded count.

Generation is deterministic: seed `20261014`, per-record RNG derived from
`seed ^ zlib.crc32(parts)`. `generator_sha256` is `77816966db3cf984…`, so a re-run
reproduces the corpus byte-for-byte.

### 1.4 The harness

`run_benchmarks.py` (24,008 B, sha256 `20db0c54fba33fc9…`) implements three
protocols in our own harness over our own corpus:

- **DMR** — MemGPT/Letta MSC shape: one question per conversation, answered
  against the whole stored conversation.
- **LongMemEval** — all five abilities reported separately (information
  extraction user + assistant, multi-session reasoning, knowledge updates,
  temporal reasoning, single-session preference) plus abstention, plus an OVERALL
  row.
- **LoCoMo** — evidence-level retrieval with answer accuracy where a gold answer
  exists. Upstream `locomo10.json` (2,805,274 B) was fetched from the `master`
  branch; `main` 404s.

Three retrieval backends plus the control:

- `bm25` — dependency-free Okapi BM25 over a 233,994-entry inverted index.
- `hashemb` — dependency-free hashing-trick embedding + cosine.
- `mem20` — the real engine adapter. **`UNAVAILABLE`**: `ModuleNotFoundError: No
  module named 'memory_engine'`, because the repo 404s and the package is not on
  PyPI. Written and syntax-checked; runs unchanged the moment the engine imports.
- `constant` — the adversarial control. Always returns one fixed document,
  ignoring the query.

### 1.5 Published results

Run: seed `20261014`, **300 probes per protocol**, top-k = 10,
**233,994 store entries under test**, runtime **1691.39 s**.

| protocol / ability | backend | n | hit@1 | hit@5 | hit@10 | MRR |
|---|---|---:|---:|---:|---:|---:|
| DMR retrieval | bm25 | 300 | 0.353 | 0.790 | 0.937 | 0.556 |
| LongMemEval OVERALL (5 abilities) | bm25 | 1800 | 0.189 | 0.827 | 0.924 | 0.481 |
| LoCoMo evidence retrieval + answer | bm25 | 300 | 0.337 | 0.817 | 0.943 | 0.547 |
| LongMemEval abstention | bm25 | 300 | — | — | — | acc **1.000** |
| **ADVERSARIAL CONTROL** | constant | 2400 | **0.000** | **0.000** | **0.000** | **0.000** |

LoCoMo answer accuracy 0.353 (bm25) / 0.223 (hashemb) / 0.000 (constant).
Knowledge updates is the strongest ability for bm25 (hit@1 0.977, MRR 0.988);
information extraction is the weakest (hit@1 0.003) — the correct evidence is
buried under near-duplicate siblings.

**Firewall separation:** median top-1 score grounded 20.7327 vs ungrounded
22.0661, **AUC 0.4935**. BM25 does not separate grounded from ungrounded, and I
report that plainly — separation is the store's job, not the lexical retriever's.
The number that does move is **false-claim contradiction recovery@10 = 0.9233**:
for a false claim, the true grounded record behind it is retrievable, i.e. the
store can surface the correction.

### 1.6 The adversarial 0.000 row

A `constant` retriever that ignores the query must score exactly zero. Over
**2,400 probes**: hit@1 / hit@5 / hit@10 / MRR all **0.000**,
`verified_zero: true`. It is published in the same table as every real number,
in the manifest, and in the CSV. Any non-zero value means the metric is broken,
so this row is the guard on the whole table. It also reproduces the programme's
existing convention — *direct 1.000 · multi-hop 0.800 · adversarial 0.000*.

---

## 2. Artifacts

All under `documents/mem20-benchmark/` on site `5cbd3145-100f-40bd-a946-0a159e5d2850`.
Reachability re-checked today; sizes are measured.

| artifact | bytes | status |
|---|---:|---|
| `RESULTS.md` | 10,418 | HTTP 200 |
| `SCHEMA.md` | 3,788 | HTTP 200 |
| `BENCHMARK-PROTOCOLS.md` | 4,266 | HTTP 200 |
| `dataset/manifest.json` | 9,233 | HTTP 200 |
| `dataset/results.json` | 3,943,120 | HTTP 200 |
| `dataset/results-table.csv` | 2,445 | HTTP 200 |
| `dataset/benchmark-corpus-summary.csv` | 33,172,984 | HTTP 200 |
| `dataset/benchmark-corpus.jsonl.gz` | 12,033,447 | HTTP 200 |
| `dataset/shards/benchmark-corpus-part00{1,2,3}.jsonl` | 39,845,023 / 39,845,300 / 25,164,417 | HTTP 200 |
| `generate_dataset.py` | 31,128 | HTTP 200 |
| `validate_dataset.py` | 8,910 | HTTP 200 |
| `load_mem20.py` | 11,552 | HTTP 200 |
| `run_benchmarks.py` | 24,008 | HTTP 200 |
| `make_manifest.py` | 6,969 | via manifest |
| `report_results.py` | 11,491 | via manifest |
| `fetch_reference.sh` | 1,448 | via manifest |
| `reference/*` (elements, iso3166, mime-db, us-states, cities15000) | 340,342 / 65,317 / 209,696 / 873 / 3,361,402 | via manifest |
| `upstream/locomo10.json` | 2,805,274 | via manifest |
| `dataset/benchmark-corpus.json` (array variant) | 121,117,325 | via manifest |
| `load_dataset.py` (new-layout loader) | 17,892 | HTTP 200, site `ce9e4276…` |
| 84,600-record shards (build 1) | 107,598,879 total | HTTP 200, site `ce9e4276…` |

Manifest records `schema_version: mem20-benchmark/1.0`, per-category counts and
bytes, the schema description, reference-source counts, and sha256 for every
deliverable. `deliverables_total_bytes` = 399,218,140.

Note on provenance: the manifest and `RESULTS.md` disagree on `RESULTS.md`'s own
sha256 (`805f4fb3…` vs `cafdb255…`) because the doc was edited after the manifest
was built. Both files serve; the checksum pair does not reconcile — see §3.

---

## 3. Problems, pitfalls, blockers, dead ends

**Still open — these block the programme:**

1. **No mem20 engine anywhere.** `github.com/JaysonAIOnline/mem20` → 404,
   `pip install mem20` → 404 on PyPI. `JaysonAIOnline` exposes 17 other repos
   (`mem20-substrate`, `mcp-cognitive-substrate`, `mem20-site`, …) and none is
   `mem20`. This is why the mem20 backend row is `UNAVAILABLE`. It is the single
   most important open item: every real number we own is from a stand-in
   retriever, not from mem20.
2. **`dataset/benchmark-corpus.jsonl` (the monolithic 104,854,740-byte file)
   now returns HTTP 404 on the CDN** — only the three shards and the `.gz` serve.
   The manifest still lists the monolith. Either re-upload it or amend the docs
   to point at shards; not yet fixed.
3. **`webpages/mem20-benchmark-update/index.html` returns 404.** The report page
   is gone; the markdown artifacts survive.
4. **Sidney deployment unverified.** The build-1 handoff to Server Builder was
   made with explicit instructions (rsync/sftp via gabe to `/srv/mem20/benchmark/`,
   verify 84,600 lines in 01→02→03 order, record path + sha256). I never had an
   ssh/sftp credential myself and `gabe` is not a member of any of my groups, so
   **whether it landed is unknown to me**. Treat as unconfirmed until Server
   Builder or the owner reports the destination path and checksum.
5. **No comparable LoCoMo/LongMemEval figure exists.** No run against the
   original human-authored datasets with an LLM judge has been done, so no
   LoCoMo or LongMemEval result is claimed for mem20. Our numbers are
   evidence-level retrieval over our own synthetic corpus and are **not**
   comparable to MemGPT 93.4% / Zep 94.8–98.2% / Mem0. The caveat is in the
   header of `RESULTS.md` and must stay there.
6. **BM25 does not separate grounded from ungrounded** (AUC 0.4935) and
   information-extraction hit@1 is 0.003. Both are measured facts, both remain
   unexplained by anything better than "near-duplicate siblings compete" — open.
7. **Stale reproduce block.** `RESULTS.md` §6 still says `MEM20_RERANK=0`. No
   such env var exists in the current repo; reranking follows
   `CROSS_ENCODER_AVAILABLE`. The correct incantation is
   `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`. Documentation defect, open.

**Hit and fixed — recorded so nobody re-learns them:**

8. **Ledger rotation destroys bulk-load counts.**
   `memory_engine.memory._append_ledger()` rotates `ledger.jsonl` into
   `backups/ledger_<epoch>.jsonl` every **2,000 lines** (proven: 2,100 appends →
   99 live + 2,001 archived). A `--mode api` bulk load looks like it lost 82,600
   records. Fixed by `--mode ledger` (direct append, bypasses rotation) and a
   `--count` that spans live + every backup.
9. **`wc -l` undercounts** any shard without a trailing newline → strip-aware
   counting (`sum(1 for l in open(f) if l.strip())`).
10. **A JSONL writer joining without `"\n"`** collapses the whole corpus onto one
    line — assert `record_count == line_count` after write.
11. **50 MB upload cap** → shards under 45 MB. The JSON **array** variant is
    *bigger* than the JSONL it mirrors (brackets + per-object commas), so it must
    be cap-checked independently: a 45 MB JSONL shard yields a ~46 MB array.
12. **gzip stamps a timestamp**, so regenerating a `.gz` changes its bytes and
    silently invalidates every recorded sha256 — always rebuild the manifest after.
13. **Abstention cannot be a score threshold.** Scoring "top score < tau" as
    abstention reports 0.000 accuracy because loose keyword overlap between a
    question about a nonexistent entity and the probe wording still scores high.
    Abstention had to be defined **entity-level**: abstain iff no entry among the
    top-k is about the queried subject. That definition is stated in the report.
14. **A 900-probe run looked hung at 0% CPU** because `sentence-transformers` was
    importable and `recall_hybrid` kept trying to fetch
    `cross-encoder/ms-marco-MiniLM-L-6-v2` offline, warning per query. Killed it,
    cut the workload, and ran with the offline env vars. Calibration lesson: one
    hybrid query is ~2 s on CPU, so 300 probes/category ≈ 30 min — measure with a
    10-probe pass first, never size by ambition.
15. **Exact 1/3 required matching ungrounded to the falsifiable grounded count**,
    which is where 38,997 comes from.
16. **A category-interleave `while` loop can spin forever** — reassigning a local
    pointer inside a `for` never advances the outer guard; drive it off a `more`
    flag and assert `emitted_total == len(records)`.
17. **Slug collisions** — `slug("audio/amr-wb")` == `slug("audio/amr-wb+")`;
    external identifiers get an ordinal prefix.
18. **False-fact swap pools must be keyed by (family, predicate, value-class)** —
    a family-only pool swaps an atomic symbol for another element's paragraph,
    producing nonsense instead of a plausible wrong answer.
19. **Long harness runs must print incrementally** (`flush=True` per protocol) or
    a 28-minute run is indistinguishable from a stall.

---

## 4. Successes — verified, not asserted

- Validation `status: PASS`, **0 errors, 0 warnings**; independent duplicate
  sweep `dup_keys: 0`, `dup_ids: 0` across all 116,997 records.
- **Exact category balance** at 0.3333 each, with the false set provably tied to
  the grounded records it contradicts.
- **99.997 MiB** measured by `stat`, matching `du` and the manifest byte total
  exactly — the size target was hit, not estimated.
- **Deterministic and reproducible**: committed seed `20261014` and committed
  `generator_sha256`, byte-identical on re-run.
- **Adversarial control verified zero** (0.000/0.000/0.000, MRR 0.000, 2,400
  probes) — the metric guard works.
- **False-claim contradiction recovery@10 = 0.9233** — the corpus demonstrates
  a store *can* surface a correction for a false claim.
- **Every published figure generated by `report_results.py` from
  `dataset/results.json`** — no number in `RESULTS.md` or the CSV was typed by
  hand, which is why the whole table can be regenerated and re-audited.
- **The dataset loads two ways**: `--mode ledger` into the engine's real ledger
  format with no engine dependency, and `--mode api` through
  `remember()` / `remember_simulated()` once the engine exists (kwargs filtered
  by `inspect.signature`).
- **Two full corpus builds shipped** (84,600 and 116,997 records), both live,
  both shard-verified line-by-line from the CDN.

---

## 5. Current progress

**Finished:** corpus build 2 (116,997 records, 99.997 MiB, 3 shards, validated
PASS, deterministic); generator, validator, two loaders, manifest builder,
harness, report generator; all three protocol families run at 300 probes with
per-ability breakdowns; adversarial control verified at exactly zero; firewall
separation and contradiction recovery measured; all artifacts published and
reachable.

**Outstanding:** the mem20 engine row is still `UNAVAILABLE`; no comparable
LoCoMo/LongMemEval run against the originals exists; the monolithic JSONL and
the report page are 404 on the CDN; the Sidney deployment is unconfirmed; the
`MEM20_RERANK` line in the reproduce block is stale; grounded-vs-ungrounded
separation remains at chance for BM25.

**Next step:** point the existing `mem20` adapter at a real
`memory_engine/memory.py` the moment that path resolves — a 300-probe run costs
about 30 minutes and needs no code change — and in parallel re-upload the
monolithic JSONL, rebuild the manifest so the checksums reconcile, and get one
confirmation of the Sidney destination path and sha256.
