# mem20 Master Todo — 100 Plans

**Generated:** 2026-10-11 · **Plans:** 100 · **Roadmap items:** 2305

Every plan below is grounded in a measurement taken from this system on 2026-10-11.
The `problem` field states the verified defect or gap, not a guess. The
`done_when` field is a verifiable condition, not a judgement.

## Verified baseline (2026-10-11)

| Measurement | Value | Source |
|---|---|---|
| Git sync vs origin/master | 0 ahead / 0 behind (already up to date) | `git fetch --all --prune` |
| Sitemap | 329 subsystems, 302 organs, 9,181 files, 472,027 code lines | `mem20sitemapz build` |
| Benchmark corpus | 14 grounded facts, 3 simulated, 13 queries | `benchmarks/results/latest.json` |
| Adversarial hit rate | 0.000 across all four modes | same |
| Graph mode | 1.000 hit rate on **n=2** queries only | same |
| Rerank ON vs OFF | 101.4ms / MRR 1.000 direct, 0.640 multi-hop vs 15.7ms / 0.900 / 0.800 | same |
| Hybrid p50 | 103.5 ms (semantic 12.2 ms) | same |
| Live ledger | 449 records, 41 topics | `/root/.mem20/store/ledger.jsonl` |
| Index drift | ledger 449 vs vector_meta 448 vs bm25 448 | file line counts |
| Simulated ledger | 85 records | `simulated_ledger.jsonl` |
| `index_health` | **MISSING** — MCP tool raises AttributeError | `hasattr(memory,'index_health')` → False |
| MEMORY.md / USER.md | **ABSENT** but status reports "0/2200 OK" | `ls` failed, `memory_status` reports OK |
| Bi-temporal suite | **11 of 14 FAIL**, 3 pass — see P0 below | `pytest`, 64s |
| Bi-temporal root cause | `remember()` now REQUIRES `epistemic_status`; tests pass it 0 times | `memory.py:541` ValueError |
| Tests calling `remember()` | 15 calls, 0 supply `epistemic_status` | grep on test file |
| Regression introduced by | `ca7c1e76` Repair retrieval, add a stable API | `git log` |
| `mem20temporaldatabasefabricz` | 54 passed in 0.56s | `pytest -q` |
| Cold model download | one-time `sentence_transformers` hub fetch, no timeout | pytest-timeout dump |
| Organs with no README | 10 missing + 2 zero-byte | disk audit |
| Organs with 0 tests | 241 of 300 | disk audit |
| Packaged organs not wiring README | 111 of 158 | pyproject audit |
| opencode.db | 200 sessions, 40,847 messages, 5,304 user turns | sqlite3 |
| 5,000-QA corpus | **does not exist anywhere on the box** | content sweep, 1,522 JSON files |
| Roadmap duplicates | 13 md5-identical step files in 2.0_roadmap | md5sum |

## The three P0 findings that block everything else

1. **`remember()` contract break — 11 of 14 bi-temporal tests fail.**
   `remember()` now raises unless `epistemic_status` is passed
   (`memory.py:541`). The test file makes 15 `remember()` calls and supplies
   the field **zero** times. Introduced by `ca7c1e76` and never repaired.
   The suite's own README claims the bi-temporal bug is fixed and locked by
   these tests — the tests do not currently pass, so that claim is unverified.
2. **`index_health()` does not exist.** `mem20_memory_index_health` raises
   `AttributeError`, yet drift is real (ledger 449 vs vector_meta 448 vs
   bm25 448). The trust differentiator's primary diagnostic cannot run.
3. **False-green status.** `memory_status` reports `MEMORY.md 0/2200 OK`
   for a file that does not exist. A status that lies is worse than no status.

> **Correction to an earlier reading of this session.** A first pass concluded
> the suite *hangs* on a `huggingface_hub` connect with no timeout. That was a
> one-time cold model download, not a persistent defect: with weights cached the
> suite completes in 64s and shows the real failures above. The offline hardening
> work is still worth doing (plans `R01`, `L01`, `B03`) but it is **not** the
> blocker. The blocker is the `epistemic_status` contract break.

## Critical path

```
R01  remember() contract break .. unblocks 11 failing tests
C01  index_health() ........... unblocks the trust claim
S01  false-green status ....... stop the status lying
R01  offline hardening ........ makes benchmarks hermetic
B01  corpus 14 -> 1500 ........ needs the above green
B02  5000-pair QA benchmark ... needs B01
T01  one verify command ....... needs C01
```

---

## Index

| # | ID | Domain | Title | Items |
|---:|---|---|---|---:|
| 1 | `I01` | A. Retrieval Core & Ranking | Advanced retrievers: sparse, late-interaction and lexical variants | 25 |
| 2 | `I02` | A. Retrieval Core & Ranking | Query expansion, decomposition, rewriting and mode selection | 22 |
| 3 | `I03` | A. Retrieval Core & Ranking | Caching, deduplication, result diversity and context packing | 24 |
| 4 | `I04` | A. Retrieval Core & Ranking | Learned ranking, long documents, chunking and graceful degradation | 24 |
| 5 | `I05` | A. Retrieval Core & Ranking | Namespace-scoped retrieval and multi-tenancy isolation | 20 |
| 6 | `R01` | A. Retrieval Core & Ranking | Embedding model selection, upgrade and offline-safety | 30 |
| 7 | `R02` | A. Retrieval Core & Ranking | Lexical (BM25) retrieval hardening and tuning | 30 |
| 8 | `R03` | A. Retrieval Core & Ranking | Hybrid fusion re-engineering (RRF and beyond) | 28 |
| 9 | `R04` | A. Retrieval Core & Ranking | Cross-encoder reranking policy engine | 27 |
| 10 | `R05` | A. Retrieval Core & Ranking | Graph multi-hop retrieval: depth, decay and path scoring | 28 |
| 11 | `R06` | A. Retrieval Core & Ranking | Query understanding: intent, decomposition and rewriting | 28 |
| 12 | `R07` | A. Retrieval Core & Ranking | Context packing, token budget and result diversity | 26 |
| 13 | `K01` | B. Temporal & Bi-temporal | Timeline reconstruction, history replay and change feeds | 20 |
| 14 | `K02` | B. Temporal & Bi-temporal | Interval algebra, timezone correctness and clock-skew handling | 22 |
| 15 | `K03` | B. Temporal & Bi-temporal | Temporal ranking signals and retention policy | 21 |
| 16 | `T01` | B. Temporal & Bi-temporal | True bidirectional temporal retrieval (both axes) | 30 |
| 17 | `T02` | B. Temporal & Bi-temporal | Temporal index, versioning and conflict resolution | 30 |
| 18 | `C01` | C. Trust & Provenance | Index health, drift detection and the missing health API | 29 |
| 19 | `C02` | C. Trust & Provenance | Provenance chain: every result carries its evidence | 28 |
| 20 | `C03` | C. Trust & Provenance | Abstention: knowing when not to answer | 27 |
| 21 | `J01` | C. Trust & Provenance | Confidence calibration, trust decay and staleness signals | 20 |
| 22 | `J02` | C. Trust & Provenance | Adversarial fact injection and poisoning resistance | 20 |
| 23 | `J03` | C. Trust & Provenance | Attribution chains, right-to-explanation and contradiction surfacing | 21 |
| 24 | `J04` | C. Trust & Provenance | Audit logging, epistemic status and knowledge-layer separation | 21 |
| 25 | `J05` | C. Trust & Provenance | PII and secret handling, and the detector-must-not-mutate contract | 20 |
| 26 | `B01` | D. Benchmark Suite | Scale the benchmark corpus from 14 facts to 1500 | 29 |
| 27 | `B02` | D. Benchmark Suite | The 5000-pair QA conversation benchmark | 30 |
| 28 | `B03` | D. Benchmark Suite | Fix the benchmark network hang and make the runner hermetic | 28 |
| 29 | `B04` | D. Benchmark Suite | Trustworthiness benchmark as the primary axis | 28 |
| 30 | `B05` | D. Benchmark Suite | Benchmark statistics, confidence intervals and honest reporting | 27 |
| 31 | `B06` | D. Benchmark Suite | Long-horizon and conversation-scoped benchmarks | 28 |
| 32 | `B07` | D. Benchmark Suite | Fair comparison and competitor-comparable tracks | 27 |
| 33 | `B08` | D. Benchmark Suite | Adversarial and failure-mode benchmark track | 27 |
| 34 | `B09` | D. Benchmark Suite | Multi-hop and compositional benchmark track | 27 |
| 35 | `B10` | D. Benchmark Suite | Latency, throughput and cost benchmarking | 27 |
| 36 | `B11` | D. Benchmark Suite | Graph-specific and temporal-specific benchmark tracks | 26 |
| 37 | `B12` | D. Benchmark Suite | Benchmark reproducibility, versioning and publication | 27 |
| 38 | `B13` | D. Benchmark Suite | Benchmark CI gate and regression protection | 27 |
| 39 | `B14` | D. Benchmark Suite | Realistic agent-workload retrieval benchmark | 26 |
| 40 | `B15` | D. Benchmark Suite | Multilingual and cross-lingual retrieval benchmark | 26 |
| 41 | `B16` | D. Benchmark Suite | Failure analysis and diagnostic tooling | 26 |
| 42 | `B17` | D. Benchmark Suite | Benchmark for the trust firewall and promotion path | 26 |
| 43 | `B18` | D. Benchmark Suite | Index-health and drift benchmarking | 26 |
| 44 | `D01` | E. Corpus & Dataset Production | Conversation mining pipeline from opencode.db | 29 |
| 45 | `D02` | E. Corpus & Dataset Production | Distil conversations into grounded facts with provenance | 20 |
| 46 | `D03` | E. Corpus & Dataset Production | Fact schema, typing and quality control | 25 |
| 47 | `D04` | E. Corpus & Dataset Production | Temporal corpus for bi-temporal evaluation | 20 |
| 48 | `D05` | E. Corpus & Dataset Production | Adversarial and trap corpus construction | 20 |
| 49 | `D06` | E. Corpus & Dataset Production | Corpus versioning, diffing and lineage | 20 |
| 50 | `D07` | E. Corpus & Dataset Production | Corpus quality assurance and human validation | 25 |
| 51 | `F01` | F. Index & Storage | Atomic index rebuild and crash safety | 20 |
| 52 | `F02` | F. Index & Storage | Storage growth, compaction and the deep-entries store | 20 |
| 53 | `F03` | F. Index & Storage | Index/ledger consistency enforcement | 20 |
| 54 | `G01` | G. API, MCP & Interfaces | Repair and complete the MCP tool surface | 20 |
| 55 | `G02` | G. API, MCP & Interfaces | Stable public API with trust metadata in every result | 20 |
| 56 | `E01` | H. Documentation Systemwide | Restore the 12 missing or empty READMEs | 22 |
| 57 | `E02` | H. Documentation Systemwide | Wire READMEs into packaging metadata (111 unwired) | 22 |
| 58 | `E03` | H. Documentation Systemwide | Make documentation claims verifiable and test-backed | 22 |
| 59 | `E04` | H. Documentation Systemwide | Root README accuracy and the generated SITEMAP appendix | 20 |
| 60 | `E05` | H. Documentation Systemwide | Quickstart and architecture documentation that matches reality | 20 |
| 61 | `E06` | I. Packaging & Distribution | Packaging consistency across 300 organs | 20 |
| 62 | `E07` | I. Packaging & Distribution | Install, import and CI smoke tests estate-wide | 20 |
| 63 | `H01` | J. Operations, Ecosystem & Product | Systemd, health and operational readiness | 20 |
| 64 | `H02` | J. Operations, Ecosystem & Product | Sales and information websites | 20 |
| 65 | `H03` | J. Operations, Ecosystem & Product | Documentation and roadmap deduplication | 20 |
| 66 | `H04` | J. Operations, Ecosystem & Product | Toolchest registration and discoverability for the whole estate | 20 |
| 67 | `H05` | J. Operations, Ecosystem & Product | Cross-subsystem quality gate and honest reporting | 20 |
| 68 | `L01` | K. Testing & Quality Culture | Network isolation and deterministic clocks in the test suite | 21 |
| 69 | `L02` | K. Testing & Quality Culture | Property-based, mutation and contract testing | 20 |
| 70 | `L03` | K. Testing & Quality Culture | Test the 241 untested organs | 20 |
| 71 | `M01` | N. Scale & Performance | Retrieval performance and quality at 10k, 50k and 100k facts | 20 |
| 72 | `M02` | N. Scale & Performance | Concurrency safety, background index maintenance and write latency | 20 |
| 73 | `M03` | N. Scale & Performance | Memory footprint and cold-start optimisation | 20 |
| 74 | `N01` | O. Agent Ecosystem & Integration | Agent-platform retrieval integration and tool surface | 20 |
| 75 | `N02` | O. Agent Ecosystem & Integration | Usage guidance, namespace-per-agent isolation and decision durability | 22 |
| 76 | `O01` | P. Governance, Process & Growth | Single source of truth and regression discipline | 20 |
| 77 | `O02` | P. Governance, Process & Growth | Honest gap reporting, release engineering and contribution model | 23 |
| 78 | `O03` | P. Governance, Process & Growth | Roadmap execution and roadmap deduplication | 20 |
| 79 | `P01` | Q. Advanced Retrieval Research | Adaptive routing, graph structure and attribution-weighted fusion | 22 |
| 80 | `P02` | Q. Advanced Retrieval Research | Diverse ensembles, answer faithfulness and perturbation robustness | 22 |
| 81 | `P03` | Q. Advanced Retrieval Research | Index format evolution, multilingual and code corpora, and dense subjects | 22 |
| 82 | `Q01` | R. Communication & Enablement | Honest positioning, reproducible demo and troubleshooting documentation | 21 |
| 83 | `Q02` | R. Communication & Enablement | Benchmark report as the primary artifact and lessons made queryable | 21 |
| 84 | `R01-2` | S. Multi-Agent & Fleet | Fleet load testing and shared-versus-isolated store strategy | 24 |
| 85 | `R02-2` | S. Multi-Agent & Fleet | Agent knowledge transfer, write conflict resolution and per-agent policy | 22 |
| 86 | `S01` | T. Data Governance | MEMORY.md and USER.md, and the false-green detection pattern | 20 |
| 87 | `S02` | T. Data Governance | Ledger separation audit, retention, export and schema migration | 24 |
| 88 | `T01-2` | U. Quality Gates & Verification | One verification command and the definition of done | 23 |
| 89 | `T02-2` | U. Quality Gates & Verification | Continuous verification, adversarial review and honest self-audit | 23 |
| 90 | `T03` | U. Quality Gates & Verification | Estate-wide quality gate and honest reporting | 20 |
| 91 | `U01` | V. Long-Term Architecture | Consolidate duplicate temporal implementations and the orphaned entries mirror | 20 |
| 92 | `U02` | V. Long-Term Architecture | Single retrieval engine, registry accuracy and dependency hygiene | 20 |
| 93 | `U03` | V. Long-Term Architecture | Interface stability and the roadmap to 10,000 facts | 20 |
| 94 | `X01` | W. Advanced Retrieval Quality | Query-level cache warming and index warm-start on cold boot | 20 |
| 95 | `X02` | W. Advanced Retrieval Quality | Negative-result analysis: why queries return nothing | 21 |
| 96 | `X03` | W. Advanced Retrieval Quality | Ranking stability: reproducible results under equivalent queries | 20 |
| 97 | `X04` | W. Advanced Retrieval Quality | Retrieval budget enforcement: bounded work per query | 20 |
| 98 | `X05` | W. Advanced Retrieval Quality | Schema and field weighting: topic, tags, content and actor | 20 |
| 99 | `X06` | W. Advanced Retrieval Quality | Bench harness honesty: no metric that cannot detect a real failure | 20 |
| 100 | `X07` | W. Advanced Retrieval Quality | Honest 0-to-1 roadmap: measurable retrieval improvement targets | 20 |

---

## Plans

## Domain A. Retrieval Core & Ranking

### `I01` — Advanced retrievers: sparse, late-interaction and lexical variants

**Problem (verified):** BM25 is the only lexical arm and cannot match a rare token to a differently-worded equivalent fact; measured keyword multi_hop MRR is 0.640, identical to hybrid, so the lexical arm adds no ranking power. Single-vector retrieval also compresses each document into one 384-dim vector, discarding token-level detail that MaxSim late interaction is designed to keep.

**Done when:** Sparse and late-interaction arms are implemented, measured against the current baseline on the 1500-fact corpus, and the index-size and latency tradeoff is published honestly.

**Roadmap:**

1. Evaluate BM25+ with a delta term capturing term dependence
2. Evaluate SPLADE as a learned sparse representation
3. Measure SPLADE recall against BM25 on the labelled probe set
4. Evaluate a ColBERT-style late-interaction model
5. Measure MaxSim quality over single-vector on the labelled set
6. Measure the index size cost of adopting SPLADE
7. Measure the index size growth of late interaction, which is substantial
8. Measure encoding and storage cost per fact for each arm
9. Add the sparse arm to hybrid fusion
10. Add the late-interaction arm to the retrieval pipeline
11. Add cheap candidate generation that late interaction can rerank
12. Measure whether sparse improves multi_hop beyond 0.640
13. Measure the late-interaction gain on multi-hop queries specifically
14. Measure the late-interaction gain on direct queries
15. Add a routing rule selecting sparse where it beats dense
16. Make both arms optional through configuration
17. Keep BM25 as the dependency-light fallback when models are absent
18. Ensure each arm degrades gracefully when unavailable
19. Add a test that each arm returns identical results for identical queries
20. Verify every arm's results carry full provenance
21. Add a rebuild command for each new index type
22. Report each arm as a distinct benchmark row
23. Publish the quality-per-megabyte tradeoff
24. Publish the recommendation for corpus sizes where each arm helps
25. Make a documented decision on whether each arm is worth its cost

### `I02` — Query expansion, decomposition, rewriting and mode selection

**Problem (verified):** Query understanding is unimplemented beyond classification, so multi-hop queries are answered by brute retrieval; measured multi_hop MRR is 0.640. Separately, an agent cannot know which mode to pick: hybrid costs 103.5ms against semantic at 12.2ms, and reranking helps direct queries while hurting multi-hop.

**Done when:** Queries are decomposed and rewritten where beneficial, and a measured recommendation table tells an agent which mode to use per query characteristics.

**Roadmap:**

1. Implement multi-hop query decomposition
2. Execute sub-queries with per-sub-query retrieval
3. Implement result join across sub-queries
4. Implement entity-anchored query expansion
5. Implement pronoun resolution against conversation context
6. Add a decomposition depth ceiling
7. Ensure decomposition preserves conjunctions
8. Test that decomposition never drops query constraints
9. Measure the gain over brute-force multi-hop retrieval
10. Measure the latency cost of decomposition
11. Measure whether decomposition or graph traversal performs better
12. Measure quality and latency per mode on the 1500-fact corpus
13. Measure quality per query kind for each mode
14. Build a recommendation table by query characteristics
15. Measure the cost of always using the single best mode
16. Measure the saving from routing by query kind
17. Expose the table as a routing helper in the API
18. Add a test that the routing helper always returns a valid enabled mode
19. Add a decision table by query kind to the documentation
20. Report decomposition and routing results as benchmark rows
21. Add regression gates on decomposition gain and routing accuracy
22. Verify the guidance is regenerated whenever the benchmark re-runs

### `I03` — Caching, deduplication, result diversity and context packing

**Problem (verified):** Agents repeat queries heavily and hybrid costs 103.5ms p50. The same fact also appears from vector, BM25 and graph arms at once, consuming result slots and crowding out distinct facts. No packing strategy exists, so results are returned flat with no budget awareness or diversity control.

**Done when:** Repeated queries are served from a correctly-invalidated cache, duplicates are merged without losing provenance, and packing preserves the gold answer at every budget.

**Roadmap:**

1. Define cache keys including store version and index generation
2. Include corpus generation so stale entries can never be served
3. Exclude temporal queries, whose answers legitimately change
4. Include namespace in the cache key so caching cannot leak
5. Implement semantic matching within a similarity threshold
6. Add invalidation on every write
7. Add a test proving a write invalidates affected entries
8. Add a test proving temporal queries are never served stale
9. Measure hit rate on a realistic query stream
10. Measure the latency saving from cache hits
11. Bound the cache with an LRU policy
12. Detect exact duplicate content across retrieval arms
13. Detect near-duplicates above a similarity threshold
14. Merge duplicates while preserving every provenance reference
15. Enforce per-entity diversity caps
16. Measure how many result slots duplicates were wasting
17. Measure the recall gain from freed slots
18. Define a context budget in tokens with a default and override
19. Implement a greedy packer maximising value within budget
20. Ensure the gold answer is retained at every budget and assert it
21. Add a dropped-result count so callers know what they did not see
22. Measure gold-answer retention across budgets 512/1024/2048/4096
23. Verify provenance survives packing and truncation
24. Report hit rate, duplicate rate and retention as benchmark metrics

### `I04` — Learned ranking, long documents, chunking and graceful degradation

**Problem (verified):** Fusion weights are hand-set despite a labelled query set now making learned ranking feasible. Chunking strategy is undocumented, so what the embedder ever sees is undefined. And if BM25 or the embedder fails, retrieval returns nothing, making a transient dependency failure indistinguishable from data loss.

**Done when:** A learned ranker is evaluated against hand-tuning, chunking is documented and measured, and every arm failure degrades to a working reduced mode.

**Roadmap:**

1. Build ranking training data from labelled queries only, never test
2. Train a lightweight learning-to-rank model
3. Evaluate strictly on the held-out split
4. Compare against hand-tuned fusion on the same split
5. Report the gain with a confidence interval
6. Report honestly if learned ranking does not beat hand-tuning
7. Keep hand-tuning as the fallback path
8. Document the current chunking strategy or its absence
9. Implement chunking for long input if absent
10. Measure retrieval quality across chunk sizes
11. Measure the effect of chunk overlap
12. Ensure facts spanning a chunk boundary remain retrievable
13. Add a test for boundary-spanning facts
14. Verify chunks never duplicate content
15. Ensure chunk provenance points back to the source
16. Implement a fallback chain across retrieval arms
17. Fail soft rather than returning empty when an arm fails
18. Report which arms were available in each result
19. Report degraded mode explicitly to callers
20. Test each arm failing individually
21. Test all arms failing and confirm a clear error rather than a hang
22. Verify degraded results still carry full provenance
23. Add degradation to the health report
24. Document the fallback behaviour and the chunking recommendation

### `I05` — Namespace-scoped retrieval and multi-tenancy isolation

**Problem (verified):** 17 namespaces exist in memory.db and every one is a test fixture created 2026-09-04, so there is no verified multi-tenancy isolation guarantee on any retrieval path. A leak between tenants would be the single most damaging retrieval defect possible.

**Done when:** Namespace isolation is enforced in every mode and verified by adversarial cross-namespace tests on each path.

**Roadmap:**

1. Enforce namespace filtering in every retrieval mode
2. Add an ACL check on every read
3. Test that a fact from another namespace never surfaces
4. Test that a query cannot leak across namespaces via graph traversal
5. Test that fusion cannot mix namespaces from different actors
6. Test that temporal queries respect namespace boundaries
7. Test that the semantic cache never serves across namespaces
8. Test that an ACL denial returns empty rather than an error
9. Test that the API surface cannot bypass namespace filtering
10. Measure the isolation overhead on latency
11. Document the isolation model precisely
12. Add namespace support to the benchmark corpus
13. Report isolation results as a trust metric
14. Add a CI gate that fails on any cross-namespace leak
15. Test that graph traversal cannot leak across a namespace boundary
16. Add a CI gate failing on any cross-namespace leak
17. Measure and publish the isolation overhead on latency
18. Verify ACL changes take effect without a restart
19. Test that a revoked ACL immediately stops returning facts
20. Publish isolation coverage as a trust number

### `R01` — Embedding model selection, upgrade and offline-safety

**Problem (verified):** Every retrieval path calls sentence-transformers/all-MiniLM-L6-v2. Verified defect: a cold-cache model load performs an unauthenticated HuggingFace Hub download with no timeout, which stalled the bi-temporal suite on first run. Once weights are cached the suite completes in 64s. Offline hardening is still required for hermetic CI, and the more urgent sibling defect is that remember() now requires epistemic_status while 11 of 14 bi-temporal tests never pass it (see U01).

**Done when:** Every embedding call either resolves from local cache or fails fast with a typed error inside 5s. Zero test runs exceed 60s. Full benchmark suite runs green offline.

**Roadmap:**

1. Pin HF_HUB_OFFLINE=1 and HF_HUB_DISABLE_TELEMETRY=1 as defaults in the memory engine import path, overridable by env
2. Add an explicit connect+read timeout to every huggingface_hub call site; no call may use the library default
3. Add a local model cache resolution probe at engine import that reports hit/miss without downloading
4. Cache the resolved model path in the store so warm starts never touch the hub
5. Fail with EmbeddingUnavailableError (typed, catchable) instead of hanging or bare OSError
6. Add MEM20_EMBEDDING_BACKEND selector: local-cache | stub | remote, defaulting to local-cache
7. Implement a deterministic hashing embedder backend so CI and benchmarks run with zero network
8. Make the benchmark suite default to the stub backend so it is hermetic and fast by construction
9. Add a test asserting engine import completes offline with the network namespace blocked
10. Add a test asserting a cold-cache embedding call raises within 5s rather than hanging
11. Re-run the bi-temporal suite with --timeout and prove 14/14 pass offline
12. Re-run the full benchmark suite with --timeout and prove it terminates
13. Evaluate upgrade candidates: bge-small-en-v1.5, gte-small, e5-small-v2 on a fixed labelled probe set
14. Benchmark candidate models on recall@10 and p50 latency against the current MiniLM baseline
15. Record the model decision in a README section with measured numbers, not adjectives
16. Add dimension-mismatch detection that refuses to mix embeddings from two models in one index
17. Store model name + dimension + hash in the vector index metadata header for provenance
18. Add a rebuild command that re-embeds an index after a model change without losing provenance
19. Add per-model accuracy deltas to the benchmark report so a model change is never silent
20. Guard against index corruption if a rebuild is interrupted; rebuilds must be atomic
21. Add corpus-size scaling curve: latency and recall at 150/500/1500/5000 facts
22. Publish embedding latency and recall in benchmarks/results/latest.md as a first-class table
23. Add a cache-eviction policy so the HF cache cannot grow unbounded on this box
24. Document the offline contract in the root README and in mem20benchmarkz README
25. Add a regression test that fails if a new huggingface_hub call site lacks a timeout
26. Record measured numbers in the sitemap keyword index so future agents can find this decision
27. Add MEM20_OFFLINE=1 mode covering hub, telemetry and any other outbound call
28. Verify the whole estate test suite terminates under a hard 300s ceiling
29. Model concurrency from observed usage rather than an invented number
30. Verify no corruption appears under sustained load

### `R02` — Lexical (BM25) retrieval hardening and tuning

**Problem (verified):** keyword mode measured 103.3ms p50 and multi_hop MRR 0.640, identical to hybrid. BM25Corpus is 448 lines against a 449-record ledger, so the index is already one record behind. BM25 is the only mode that survives exact-token and rare-token queries, and it is the fallback when the embedding path is degraded.

**Done when:** BM25 index is provably in sync with the ledger, tokenization is tuned against a labelled set, and p50 latency is under 20ms at 1500 facts.

**Roadmap:**

1. Reconcile BM25Corpus to the ledger and add a drift assertion that fails when counts differ
2. Add an index rebuild subcommand to mem20benchmarkz for offline corpus experiments
3. Tune k1 and b on a labelled probe set rather than shipping library defaults
4. Add field-weighted scoring for topic, tags and content rather than flat concatenation
5. Add a tag-exact-match boost ahead of the BM25 score
6. Add phrase and proximity scoring for multi-word entity names
7. Add a stopword policy tuned for agent vocabulary rather than generic English
8. Add stemming and lemmatisation behind a flag; measure whether it helps or hurts agent queries
9. Add synonym expansion from the organ's own vocabulary, not a generic thesaurus
10. Handle hyphenation and camelCase token splitting for identifiers like mem20temporaldatabasefabricz
11. Add numeric and version tokenisation so build-4200 style queries match
12. Add an exact-substring pass that runs before BM25 scoring for quoted phrases
13. Measure and publish the recall contribution of lexical mode alone against vector mode alone
14. Add per-query-kind BM25 score curves to the benchmark report
15. Add a rare-token IDF diagnostic that flags queries where BM25 should beat vector
16. Implement BM25 saturation visibility so a term appearing in every doc scores zero
17. Add a corpus-stats cache to avoid recomputing DF on every query
18. Serialize the BM25 index with a version header and a checksum
19. Refuse to load a BM25 index whose checksum does not match its corpus
20. Add atomic index write via temp-file-plus-rename
21. Add a p50/p95/p99 latency target and fail the benchmark gate above it
22. Add a concurrency test: 32 parallel BM25 queries produce identical results to serial
23. Add index size reporting in MB so regressions are visible
24. Add a BM25 rebuild benchmark to the latency suite
25. Add a poor-man's check that BM25 answers a query the vector index cannot
26. Document the k1/b decision with the measured sweep in the README
27. Add the tuning harness as a CLI subcommand so it is reproducible
28. Verify keyword multi_hop MRR improves from the measured 0.640 baseline
29. Verify no concurrent write is silently lost
30. Verify one agent's retrieval policy cannot affect another's

### `R03` — Hybrid fusion re-engineering (RRF and beyond)

**Problem (verified):** hybrid is 103.5ms p50 against semantic 12.2ms and scores identically to keyword on multi_hop (0.640 vs 0.640). The fusion is adding cost without adding measurable ranking power, which is the weakest possible result for a mode that exists to be better than both halves.

**Done when:** Hybrid beats BOTH its halves on every query kind at a p50 under 60ms, and the gain is demonstrated on a labelled set of at least 200 queries.

**Roadmap:**

1. Instrument current RRF weights and record the measured contribution of each arm
2. Rebuild the fusion on a 200+ query labelled set instead of a 13-query corpus
3. Sweep RRF k across 10/20/60/100 and record hit rate and MRR at each value
4. Add per-query-kind weights so direct and multi_hop queries fuse differently
5. Add a score-normalisation step before fusion; raw BM25 and cosine scores are not comparable
6. Add a learned combiner that maps arm scores to fused rank with a tiny logistic model
7. Keep a deterministic rule-based combiner as the fallback when training data is absent
8. Add a confidence-aware fusion that downweights an arm when its index is stale
9. Measure fusion gain over the best single arm; require a positive delta to ship
10. Add a guard that disables fusion when the gain is within noise on a given corpus
11. Cut hybrid latency by running the reranker on a shortlist rather than the full candidate set
12. Target p50 under 60ms, down from the measured 103.5ms
13. Add an adaptive k that grows with query specificity
14. Add negative-result handling: fusion should not invent relevance from one noisy arm
15. Add a tie-break policy that is total and deterministic
16. Add fusion behaviour tests with hand-computed expected rankings
17. Add a golden-file test that fails loudly when fusion output changes for a fixed corpus
18. Expose fusion weights as configuration so they can be tuned without code changes
19. Document the weight choice and the measured delta in the README
20. Add a fusion ablation report to the benchmark suite
21. Add duplicate suppression across arms so one fact does not occupy three slots
22. Add arm-coverage stats showing which arm supplied each returned result
23. Add a fallback chain: hybrid fails to direct fails to lexical fails to empty
24. Measure and publish the quality-latency Pareto front, not just one operating point
25. Add a per-query-kind recommendation table for agents choosing retrieval mode
26. Verify direct MRR holds at or above the current 1.000
27. Verify multi_hop MRR exceeds the current 0.640
28. Add the fusion change to the benchmark results history so regressions are visible

### `R04` — Cross-encoder reranking policy engine

**Problem (verified):** Measured tradeoff on this corpus: rerank ON is 101.4ms p50 with direct MRR 1.000 and multi_hop 0.640; OFF is 15.7ms p50 with direct MRR 0.900 and multi_hop 0.800. Reranking helps direct queries and HURTS multi-hop. MEM20_RERANK=0 exists as a blunt global switch with no per-query guidance.

**Done when:** Reranking is selected per query kind by measured policy, defaulting to the cheaper option where quality does not degrade.

**Roadmap:**

1. Confirm the measured 101.4ms/15.7ms split reproduces on the 1500-fact corpus
2. Build a rerank decision table keyed by query kind from measured data
3. Default reranking OFF for multi_hop where it measurably hurts
4. Default reranking ON only for direct queries where it measurably helps
5. Add a latency budget parameter that disables reranking automatically when exceeded
6. Rerank only the top-N shortlist rather than every candidate
7. Batch rerank calls so one request amortises model overhead
8. Cache rerank scores keyed by (query hash, doc id) with a bounded LRU
9. Add a rerank cache hit-rate metric to the benchmark report
10. Fail open: if the cross-encoder is unavailable, return the fused ranking unchanged
11. Add a test proving rerank failure never loses a document that fusion found
12. Measure rerank benefit on adversarial queries, currently hit_rate 0.000
13. Publish both operating points as first-class rows in the results table
14. Add a command-line flag to force rerank on or off for A/B runs
15. Add model warm-up so the first query does not pay load cost
16. Add a reranker memory-footprint measurement
17. Document the exact conditions under which each setting wins
18. Add a guard preventing a config that enables both slow rerank and slow hybrid
19. Add a test that MEM20_RERANK=0 yields exactly the pre-rerank ordering
20. Add a canary metric: rerank quality delta per corpus size
21. Track rerank benefit as corpus grows to 1500 facts; it may invert
22. Add rerank parity tests against a stored reference output
23. Add per-stage timing breakdown: retrieve, fuse, rerank, pack
24. Alert if rerank exceeds 25% of total retrieval budget
25. Make the policy table data-driven and reloadable without a code change
26. Verify p50 hybrid latency drops below 60ms with the policy applied
27. Record the decision and numbers in the mem20benchmarkz README

### `R05` — Graph multi-hop retrieval: depth, decay and path scoring

**Problem (verified):** graph mode measured 0.6ms p50 with 1.000 hit rate and 1.000 MRR, but on only 2 queries out of 13. That is the fastest and nominally the best mode in the suite, on the thinnest evidence. The memory_graph.json is 3.19 MB with 38 entities and 70 edges on the benchmark corpus.

**Done when:** Graph mode is measured on at least 100 multi-hop queries at production graph scale, with depth and decay chosen from measurement.

**Roadmap:**

1. Build a labelled multi-hop query set of at least 100 questions against the live graph
2. Measure the current live graph entity and edge counts and record them as the baseline
3. Sweep hop depth 1 to 4 and record hit rate, MRR and latency at each depth
4. Add edge-weight decay so a 3-hop path does not outrank a direct 1-hop edge without evidence
5. Add path scoring that prefers fewer hops at equal evidence
6. Add a shortest-path-aware ranking component
7. Detect and report hub nodes that dominate traversal and distort ranking
8. Add a hub-damping factor and measure its effect
9. Add cycle detection so cyclic entity graphs cannot cause unbounded traversal
10. Add a hard hop ceiling enforced in code, not only by configuration
11. Add a traversal budget in edges examined per query
12. Measure graph-only vs hybrid-on-graph so the value of combining them is known
13. Merge graph scores into hybrid fusion as a first-class arm
14. Add provenance so a graph result cites the exact edge path that produced it
15. Add a graph-result explanation string for agent consumption
16. Add a graph index health check for orphaned entities and dangling edges
17. Add incremental graph maintenance on ledger write rather than full rebuild
18. Add a rebuild benchmark for the 3.19 MB graph
19. Add entity resolution so duplicate entities do not fragment traversal
20. Add canonical entity ids with alias mapping
21. Add graph statistics to the sitemap so agents can see scale before querying
22. Verify graph p95 latency stays under 20ms at production graph size
23. Add a test proving hop ceiling is enforced on a synthetic dense graph
24. Add a test proving traversal terminates on a cyclic graph
25. Add a graph quality report: coverage, orphan rate, hub concentration
26. Publish graph mode results as a separate table, not folded into hybrid
27. Increase graph query count in the benchmark from 2 to at least 100 and re-report
28. Document measured hop depth and decay values in the README

### `R06` — Query understanding: intent, decomposition and rewriting

**Problem (verified):** adversarial queries score hit_rate 0.000 across all four modes on a 13-query corpus. A 13-query corpus cannot distinguish a genuine quality failure from an ambiguous query, so query understanding is currently untested and unmeasured.

**Done when:** Every benchmark query carries a machine-readable intent label and a decomposition where multi-hop, and measured results are reported per intent.

**Roadmap:**

1. Define a query intent taxonomy: direct, multi_hop, temporal, adversarial, procedural, factual, summary
2. Label all 13 existing benchmark queries with an intent
3. Build a labelled set of at least 50 queries per intent for the 1500-fact corpus
4. Implement intent classification over the query string
5. Implement question-type detection: who, what, when, where, how, why
6. Implement temporal cue detection for words like latest, before, after, during
7. Implement multi-hop detection via compound question structure
8. Implement decomposition of a multi-hop query into an ordered sub-query chain
9. Execute decomposition as a real fan-out/join over the retrieval modes
10. Implement query rewriting for pronoun and anaphora resolution against conversation context
11. Implement spelling and tokenisation normalisation for agent vocabulary
12. Implement abbreviation expansion from a maintained agent glossary
13. Add a query-intent column to the benchmark report
14. Add per-intent hit rate and MRR as first-class tables
15. Add a confusion matrix for the intent classifier
16. Measure intent classification accuracy against the labelled set
17. Add a test that a temporal-cue query routes to a temporal path
18. Add a test that an adversarial query routes to the abstention path
19. Add query-classification latency to the performance budget; it must be under 2ms
20. Add a query normalisation cache keyed by normalised form
21. Add a feedback loop: queries that returned no result feed intent tuning
22. Build a no-result query log for analysis
23. Add a test that decomposition preserves conjunctions and does not drop constraints
24. Add a decomposition depth ceiling
25. Add a sub-query result merge policy that preserves provenance
26. Expose detected intent and decomposition in the result envelope
27. Verify every benchmark query resolves to exactly one intent
28. Update the README with the taxonomy and per-intent results

### `R07` — Context packing, token budget and result diversity

**Problem (verified):** No measured packing strategy exists. Results are returned as a flat list with no budget awareness, no diversity control, and no guarantee that the highest-value fact is not crowded out by near-duplicates from one entity.

**Done when:** A packing stage fits results into a token budget, enforces diversity, and demonstrably preserves the gold answer at every budget tested.

**Roadmap:**

1. Define a context budget in tokens with a default and a per-call override
2. Implement a greedy packer that maximises value within budget
3. Add near-duplicate suppression using content similarity above a threshold
4. Add per-entity diversity caps so one entity cannot fill the context
5. Add source diversity so all results do not come from one subsystem
6. Ensure the gold answer is always retained at every budget; measure and assert
7. Add a token estimator that does not require loading a full tokenizer
8. Add per-result token cost to the result envelope
9. Add a dropped-result count so the agent knows what it did not see
10. Add an overflow policy: truncate, summarise, or expand budget
11. Add a packing benchmark across budgets 512/1024/2048/4096
12. Measure gold-answer retention rate at each budget
13. Add a test proving diversity caps are enforced
14. Add a test proving the packer is deterministic for a fixed input
15. Add a packing latency measurement; target under 5ms
16. Add provenance preservation through packing so citations survive
17. Add a mode that returns summaries instead of raw text for overflow results
18. Add a test proving provenance is never lost when results are dropped
19. Add a contextual compression stage that removes boilerplate from long facts
20. Measure compression ratio and retention together, never compression alone
21. Add a packing mode that interleaves temporal results in chronological order
22. Add a test proving chronological ordering is stable under equal timestamps
23. Expose the packing strategy used in each result for reproducibility
24. Add packing statistics to the benchmark report
25. Add a CLI flag to run the packing sweep as a standalone benchmark
26. Document the budget defaults and the measured retention curve in the README

## Domain B. Temporal & Bi-temporal

### `K01` — Timeline reconstruction, history replay and change feeds

**Problem (verified):** There is no way to ask what the store believed as a whole at any past instant. Bi-temporal retrieval is per-fact; a timeline view needs reconstruction across all facts, which is what an auditor or a debugging session actually requires.

**Done when:** The full store can be reconstructed as it was at any instant on either axis, with diffs and change feeds between instants.

**Roadmap:**

1. Implement a full-store snapshot at a given valid instant
2. Implement a full-store snapshot at a given known instant
3. Implement a diff between two instants
4. Implement a change feed between two instants
5. Ensure reconstruction never mutates the store
6. Test reconstruction determinism across repeated calls
7. Measure reconstruction cost at 1500 facts
8. Expose reconstruction through the API
9. Add reconstruction to the benchmark suite
10. Document the reconstruction semantics precisely
11. Verify reconstruction never mutates the store
12. Test reconstruction determinism across repeated identical calls
13. Measure reconstruction cost at 1500 facts and publish it
14. Expose reconstruction through the stable API
15. Add a reconstruction correctness test against a hand-built store
16. Add reconstruction tests against a hand-built correction chain
17. Verify a reconstructed view never includes retracted content
18. Expose the change feed through the stable API
19. Measure reconstruction cost and publish it as a benchmark
20. Ensure reconstruction respects namespace boundaries

### `K02` — Interval algebra, timezone correctness and clock-skew handling

**Problem (verified):** Temporal filtering uses string comparison on timestamps, which is fragile across timezones and formats, and there is no interval algebra for overlap or containment. Facts learned late have known time after valid time, and nothing documents how out-of-order arrival behaves.

**Done when:** Timestamps are normalized canonically, interval operations are explicit and tested, and out-of-order arrival is handled and measured.

**Roadmap:**

1. Normalize all timestamps to UTC with an explicit canonical format
2. Add timezone handling so offsets cannot break comparisons
3. Implement interval overlap
4. Implement interval containment
5. Implement interval adjacency
6. Implement interval difference
7. Use these operators consistently in every temporal path
8. Test each operator on boundary cases
9. Test mixed-timezone input explicitly
10. Reject malformed timestamps at write time
11. Document the ordering guarantee precisely
12. Handle records arriving with valid time earlier than known time
13. Handle a correction arriving before its original due to skew
14. Measure how many records have valid time before known time
15. Define and enforce a maximum tolerated skew
16. Verify skew never corrupts the hash chain
17. Publish the measured late-arrival rate
18. Publish the measured late-arrival rate from the live 449 records
19. Verify skew never corrupts the hash-chained event log
20. Document the interval model and the ordering guarantee
21. Test interval operators against hand-computed expectations
22. Reject malformed timestamps at write time rather than silently defaulting

### `K03` — Temporal ranking signals and retention policy

**Problem (verified):** Recency is not a ranking signal in semantic, BM25 or hybrid, so a current fact can be outranked by a stale one with identical textual relevance. Separately, corrections never delete, which is correct for correctness but means unbounded growth with no way to honour a legitimate deletion request.

**Done when:** Recency is a first-class measured ranking signal in every mode, and retention policy is configurable with auditable deletion.

**Roadmap:**

1. Add a recency term to semantic scoring
2. Add a recency term to BM25 scoring
3. Add a recency term to graph traversal
4. Add a recency term to hybrid fusion
5. Measure the effect on temporal queries
6. Measure the effect on non-temporal queries
7. Verify non-temporal accuracy does not degrade
8. Make the recency weight configurable
9. Add a regression test on recency ordering
10. Define a retention policy
11. Support policy-driven archival
12. Support a deletion request path with an audit trail
13. Ensure deletion removes content while preserving the chain
14. Ensure deleted content is not retrievable after deletion
15. Test that deletion is effective
16. Test that the chain stays verifiable after deletion
17. Verify deletion never removes retained history
18. Verify deletion is effective and content is genuinely unretrievable
19. Verify the hash chain stays verifiable after a deletion
20. Verify deletion never removes retained pre-correction history
21. Publish the measured effect of recency on every quality metric

### `T01` — True bidirectional temporal retrieval (both axes)

**Problem (verified):** The single highest-value retrieval defect found on 2026-10-11: remember() now raises ValueError unless epistemic_status is supplied (memory.py:541), and test_recall_at_bitemporal.py makes 15 remember() calls while supplying the field zero times. Result: 11 of 14 tests fail, 3 pass. Introduced by ca7c1e76 and never repaired. The organ README claims the bi-temporal bug is fixed and locked down by these tests; the tests do not pass, so that claim is currently unverified. recall_at() is documented as a bi-temporal query; the organ documents that it was not, and the fix cannot be trusted while its own regression suite is red.

**Done when:** Both axes are independently queryable, the four-slice model (valid_now_known_now, valid_then_known_now, valid_now_known_then, valid_then_known_then) is reachable from the main API, and all 14 bi-temporal tests pass without network.

**Roadmap:**

1. Define the four-slice query model precisely and document it in one place
2. Expose known-time filtering in recall_at alongside valid-time filtering
3. Add slice parameters valid_as_of and known_as_of to recall_at
4. Wire mem20temporaldatabasefabricz into the main memory path rather than running beside it
5. Remove the duplicate temporal implementation once one is authoritative
6. Fix the hugingface_hub hang blocking memory_engine/tests/test_recall_at_bitemporal.py
7. Get all 14 tests in test_recall_at_bitemporal.py passing
8. Add tests for each of the four slices explicitly
9. Add a test that known_then never returns a fact learned after that instant
10. Add a test that valid_then can differ from known_then for a late-learned fact
11. Add backward temporal traversal: walk the known-time axis backwards
12. Add forward temporal traversal: walk the known-time axis forwards
13. Add a since/until DSL covering both axes
14. Add a timeline reconstruction function returning the full version history of a subject
15. Add a change-feed returning what changed between two instants on either axis
16. Add a contradiction detector flagging facts that conflict in valid time
17. Add temporal decay weighting so recent valid facts outrank stale ones, tunable
18. Add recency as an explicit ranking signal in all four modes, not just temporal
19. Add a bitemporal vector index so semantic recall respects both axes
20. Add a bitemporal BM25 index for the lexical path
21. Add temporal filters to the hybrid fusion path
22. Add an as-of index health check so a stale temporal index is detected
23. Add temporal query latency to the benchmark suite as its own mode
24. Build a temporal benchmark set of at least 100 queries across all four slices
25. Add a test proving half-open interval semantics hold at exact boundaries
26. Add a test proving a correction never edits valid time
27. Verify pre-correction truth is reachable through EVERY query path, not one
28. Publish temporal mode results as a first-class benchmark table
29. Update the mem20temporaldatabasefabricz README to state what is wired and what is not
30. Include documentation coverage in the single verification command

### `T02` — Temporal index, versioning and conflict resolution

**Problem (verified):** /root/.mem20/temporal/temporal.db holds 752 events and 376 versions, separate from the 449-record main ledger. Two temporal stores exist with no reconciliation, and the main ledger has no recorded-time axis of its own.

**Done when:** One authoritative temporal store with both axes, a documented migration path, and a reconciliation check that fails loudly on divergence.

**Roadmap:**

1. Decide and document which temporal store is authoritative
2. Write a migration that folds temporal.db versions into the main ledger
3. Preserve every existing version during migration; corrections never delete
4. Add a reconciliation check comparing both stores and reporting divergence
5. Add recorded_time to every main-ledger record
6. Backfill recorded_time for the 449 existing records from an available timestamp
7. Mark backfilled records explicitly rather than presenting them as observed
8. Add interval validation rejecting invalid or overlapping intervals at write time
9. Enforce at most one open belief per (subject, attribute) at write time
10. Add a repair command for existing data violating that invariant
11. Add a temporal compaction that merges adjacent identical intervals safely
12. Add a hash-chained event log over temporal writes and a verify command
13. Make verify exit non-zero on any tamper, and test that it does
14. Add idempotent ingest so replaying a ledger adds nothing; test it
15. Add a temporal index rebuild command with atomic swap
16. Add drift detection between temporal.db and the ledger
17. Add a temporal store size metric to the sitemap
18. Add tests for retract, correct and supersede semantics
19. Add a test that retraction closes the interval rather than deleting the record
20. Add a test that superseded content is still retrievable via history
21. Add a migration dry-run mode that reports without writing
22. Add a migration verification step comparing before and after counts
23. Document the migration in the organ README with measured before/after counts
24. Add a repair log recording every automatic repair applied
25. Add an alert when the two stores disagree by more than a threshold
26. Verify the temporal suite passes 54/54 plus the new tests with no network
27. Add temporal store backup to the backup routine
28. Add a restore drill that restores temporal.db and verifies the chain
29. Update the root README temporal section to match measured reality
30. Withdraw published figures that cannot be reproduced

## Domain C. Trust & Provenance

### `C01` — Index health, drift detection and the missing health API

**Problem (verified):** mem20_memory_index_health is BROKEN. memory.py has no index_health attribute (verified: hasattr returned False, and no health/drift/stale attributes exist). The MCP tool raises AttributeError. Measured drift is real: ledger 449, vector_meta 448, bm25_corpus 448. The trustworthiness story is the differentiator and its primary diagnostic does not run.

**Done when:** index_health() exists, returns exact counts for every index, flags every mismatch, the MCP tool stops raising, and a drift test proves the detection fires.

**Roadmap:**

1. Implement memory.index_health() returning a structured report
2. Report exact counts: ledger, vector_meta, bm25_corpus, graph nodes, simulated ledger
3. Report missing-in-index and orphan-in-index record IDs, not just counts
4. Fix the MCP tool so mem20_memory_index_health stops raising AttributeError
5. Return a boolean healthy flag with an explicit required-vs-actual table
6. Exit non-zero when unhealthy so it can gate CI
7. Add a drift injection test proving detection fires on induced failure
8. Add the existing mem20benchmarkz drift subcommand as the CLI surface
9. Reconcile the live 449 vs 448 vs 448 mismatch and document the cause
10. Add a rebuild command that repairs index drift without data loss
11. Detect and report index entries whose record no longer exists
12. Detect and report records missing from an index entirely
13. Detect schema version mismatch between index and engine
14. Detect a model-dimension change that invalidates a vector index
15. Add health to the mem20api health() surface
16. Add health output to mem20-api-health
17. Add a health badge in SITEMAP.md generated from live probe
18. Add a scheduled health check that logs drift over time
19. Add a drift history file so a slowly growing skew is visible
20. Add an alert threshold for drift percentage
21. Add a test that a stale-pointer scenario is detected and reported
22. Add a test that a healthy store reports healthy
23. Make health read-only; it must never mutate the store
24. Add a test asserting health does not modify any file
25. Document what health checks and what it explicitly does not
26. Add health to the benchmark trustworthiness table already in the report
27. Publish health numbers in benchmarks/results/latest.md
28. Fix the report so Queries reporting a diagnostic of 41 is explained, not left dangling
29. Add health coverage of pinned_blocks and procedural_memory

### `C02` — Provenance chain: every result carries its evidence

**Problem (verified):** The retrieval envelope carries content, score and topic. It does not carry where the fact came from, who asserted it, when it was recorded, or what chain of reasoning reached it. The ledger records actor (agent, gateway, researcher, fountain, writer) and that data is not surfaced.

**Done when:** Every returned fact carries actor, recorded_time, valid interval, source subsystem and ledger id, and the chain is verifiable back to the writing event.

**Roadmap:**

1. Define a Provenance schema with required and optional fields
2. Attach ledger id to every result in every retrieval mode
3. Attach actor to every result so assertion source is visible
4. Attach recorded_time and the valid interval to every result
5. Attach the source subsystem or namespace that stored the fact
6. Add a verification function that re-derives a fact from its ledger entry
7. Add a tamper test proving an edited fact fails verification
8. Expose provenance in the mem20api result envelope
9. Expose provenance through the MCP retrieval tools
10. Add a provenance display in benchmark results
11. Propagate provenance through fusion so it survives ranking
12. Propagate provenance through packing so it survives truncation
13. Propagate provenance through graph traversal, citing the exact edge path
14. Add a chain hash per fact at write time for later verification
15. Add a batch verify command for the whole ledger
16. Report verification pass/fail counts in the health check
17. Add a test that provenance survives every stage of the retrieval pipeline
18. Add a test that a fact with no ledger id is flagged rather than silently returned
19. Add provenance to temporal results including both interval axes
20. Add a policy decision on whether unprovenanced facts are returned by default
21. Add a strict mode that returns only fully provenanced facts
22. Measure provenance coverage across the 449 live records
23. Report coverage percentage in the trust benchmark
24. Add a citation string generator for agent consumption
25. Add a test that citation strings round-trip to the right ledger id
26. Document the provenance contract in the mem20api README
27. Add provenance fields to the benchmark JSON schema
28. Make unprovenanced results visually distinct in every CLI output

### `C03` — Abstention: knowing when not to answer

**Problem (verified):** adversarial queries score hit_rate 0.000 on all four modes, but the benchmark cannot distinguish correct abstention from retrieval failure because hit_rate has no abstention concept. A system that returns nothing correctly and a system that fails identically are scored the same. This is the single most important metric defect in the suite.

**Done when:** Abstention is a first-class outcome. The benchmark reports correct-abstention separately from failure, and measured abstention is competitive with the best systems.

**Roadmap:**

1. Define abstention formally: when should the system return nothing
2. Add a correct_abstention metric distinct from hit_rate
3. Add a false_abstention metric for wrongly refusing an answerable query
4. Add an answerable-but-missed metric distinct from abstention
5. Fix the adversarial scoring so correct refusal scores 1.0 and failure scores 0.0
6. Re-run and publish the corrected adversarial numbers
7. Add a confidence threshold below which the system abstains
8. Make the threshold tunable and sweep it on a labelled set
9. Add a test that an unanswerable query returns empty rather than a plausible guess
10. Add a test that an answerable query is not wrongly refused
11. Add abstention rate to the health and trust reports
12. Publish abstention quality as a headline trustworthiness number
13. Add an explicit UNKNOWN response type distinct from empty results
14. Add an UNKNOWN response with a reason code
15. Make reason codes enumerable and documented
16. Add a partial-answer mode with explicit uncertainty markers
17. Add a test that partial answers are marked as partial
18. Add abstention threshold to the mem20api surface as configuration
19. Add per-intent abstention thresholds; adversarial and direct need different levels
20. Measure and publish the abstention quality/recall tradeoff curve
21. Add a test that abstention never returns a fact from the simulated partition
22. Ensure abstention is enforced identically across all four retrieval modes
23. Add an abstention benchmark track with at least 100 unanswerable queries
24. Build 100 unanswerable queries as a distinct labelled set
25. Add confidence calibration: predicted confidence vs actual correctness
26. Publish a calibration curve in the trust report
27. Document the abstention contract in the benchmark README

### `J01` — Confidence calibration, trust decay and staleness signals

**Problem (verified):** Similarity scores are not confidence; nothing measures whether a score of 0.9 corresponds to 90% correctness, so every trust claim is unquantified. Facts also do not lose truth with age but relevance does, and a two-year-old fact is weighted identically to one from an hour ago.

**Done when:** Confidence is calibrated against observed correctness and recency is a measured, configurable ranking signal in every mode.

**Roadmap:**

1. Collect predicted scores alongside observed correctness on the benchmark
2. Build a calibration curve
3. Measure expected calibration error
4. Add a temperature or isotonic calibrator
5. Apply calibration per mode since score scales differ
6. Report calibration error per mode
7. Test that calibration measurably improves the error metric
8. Verify calibration never changes retrieval ordering
9. Publish the calibration curve
10. Define a decay function with a documented half-life
11. Add recency as a ranking signal in every retrieval mode
12. Measure the effect on temporal queries
13. Measure the effect on non-temporal queries
14. Verify non-temporal accuracy does not degrade
15. Detect facts contradicted by newer facts
16. Add a staleness signal distinguishing old from wrong
17. Verify recency never promotes a retracted or superseded fact
18. Make the half-life configurable
19. Publish the measured effect of recency on every quality metric
20. Re-measure calibration whenever the corpus changes

### `J02` — Adversarial fact injection and poisoning resistance

**Problem (verified):** Nothing measures whether a false fact written into the store propagates through the indexes and graph into confident wrong answers. This is the most damaging attack on a memory system and the one least likely to be noticed without deliberate measurement.

**Done when:** Poisoning resistance is measured end to end, defended where possible, and reported honestly including any residual vulnerability.

**Roadmap:**

1. Define an injection attack model with explicit attacker capabilities
2. Inject false facts at write time
3. Measure propagation into the vector index
4. Measure propagation into the BM25 index
5. Measure propagation into the graph
6. Measure how readily a poisoned fact is returned
7. Measure whether provenance makes a poisoned fact detectable
8. Design a defence such as requiring corroboration for a claim
9. Measure the defence's effect on attack success rate
10. Measure the defence's cost to legitimate recall
11. Verify the defence does not break the grounded firewall
12. Publish the result including any residual vulnerability honestly
13. Add injection scenarios to the regression suite
14. Add a CI gate on poisoning detection rate
15. Measure the defence's cost to legitimate recall on the held-out split
16. Verify the defence cannot itself be poisoned by an attacker
17. Publish the attack success rate before and after the defence
18. Add injection scenarios to the trust regression suite
19. Verify the firewall still blocks promotion of a poisoned fact
20. Test injection through the graph path specifically

### `J03` — Attribution chains, right-to-explanation and contradiction surfacing

**Problem (verified):** Provenance stops at a ledger id with no chain showing how a fact connects to its source or how an answer was assembled. An agent receiving a fact cannot tell why it was returned. And if two facts conflict, returning both unflagged is worse than flagging them.

**Done when:** Every result carries an accurate attribution chain and an explanation, and contradictions are detected and surfaced at retrieval time.

**Roadmap:**

1. Define an attribution chain format
2. Record which facts contributed to a fused answer
3. Record which graph edges a traversal used
4. Record which sub-queries a decomposition produced
5. Ensure the chain survives packing and truncation
6. Bound chain depth for pathological graphs
7. Render the chain for agent consumption
8. Test that the chain round-trips
9. Expose the chain through the API
10. Generate a match explanation per result
11. Explain lexical matches by the matched terms
12. Explain semantic matches by similarity and content
13. Explain graph matches by the traversed path
14. Explain temporal matches by interval satisfaction
15. Test that explanations correspond to real match reasons, not decoration
16. Verify explanations never leak unrelated content
17. Detect contradiction between top results
18. Attach a contradiction flag to the result envelope
19. Prefer the temporally later valid fact on conflict
20. Return both with an explicit conflict note when unresolvable
21. Measure and report the contradiction rate in retrieval

### `J04` — Audit logging, epistemic status and knowledge-layer separation

**Problem (verified):** Writes are logged but reads are not, so there is no way to answer who saw what. mem20 also separates grounded from simulated but does not separate observed from inferred from agent-generated, so a model guess is stored alongside an observation with no distinction.

**Done when:** Reads and writes are both auditable, and every fact carries an epistemic status that retrieval can filter and report on.

**Roadmap:**

1. Log every retrieval with actor, query and result ids
2. Keep the read log separate from the fact ledger
3. Make the read log bounded with rotation
4. Ensure the read log never stores sensitive result content
5. Add a query for who has read a given fact
6. Add a query for what a given actor has read
7. Include namespace in audit records for isolation
8. Add a test proving the read log never mutates the store
9. Define the epistemic status taxonomy
10. Stamp status at write time
11. Make status visible in every result
12. Allow filtering retrieval by status
13. Measure status distribution across the 449 records
14. Classify existing records by status
15. Report inferred facts separately from observed ones
16. Add promotion rules between status levels
17. Test that promotion requires evidence and cannot be forged
18. Ensure audit records include namespace so isolation is auditable
19. Verify epistemic status cannot be forged or downgraded on read
20. Measure the status distribution after classification
21. Report inferred versus observed counts separately in the trust table

### `J05` — PII and secret handling, and the detector-must-not-mutate contract

**Problem (verified):** A PII scanner exists and commit 3c83c64c stopped a test writing index rows into the live store. Detection and redaction must remain distinct operations, and stored data must never be rewritten by a detector, or the store silently diverges from what the user authored.

**Done when:** PII is detected without mutation, redaction is proven to be an explicit output-layer operation only, and the exact regression is guarded by a test.

**Roadmap:**

1. Verify detection never mutates stored content
2. Verify redaction is an explicit output-layer operation only
3. Test that stored bytes are identical after a detection scan
4. Add a test for the exact regression fixed in 3c83c64c
5. Add a test that no detector writes to the live store
6. Scan the 449 live records and report findings without mutating
7. Scan benchmark corpora for secrets before publication
8. Ensure per-query benchmark output carries no PII or secrets
9. Verify the exported QA dataset contains no live secrets
10. Document the detect-versus-redact contract precisely
11. Run the full test suite and confirm no live-store writes
12. Scan the benchmark per-query output for PII before publishing
13. Verify no detector writes to the live store during a full suite run
14. Confirm stored bytes are byte-identical after a detection scan
15. Run the full suite and prove no live-store index rows were written
16. Add a test that a scan leaves ledger bytes byte-identical
17. Verify redaction output is clearly marked as redacted
18. Ensure benchmark corpora are scanned before every publication
19. Verify no test writes index rows to the live store
20. Publish a detection-rate metric separate from a redaction metric

## Domain D. Benchmark Suite

### `B01` — Scale the benchmark corpus from 14 facts to 1500

**Problem (verified):** mem20benchmarkz runs on corpus mem20-agent-kb-v1 with 14 grounded facts, 3 simulated facts, 13 queries. Four retrieval modes, three query kinds, thirteen data points. Every number in latest.md carries a 13-query sample. No claim about quality can survive that, and the user has directed the corpus go to roughly 1500 facts.

**Done when:** A 1500-fact benchmark corpus exists with at least 300 labelled queries across four query kinds, all results re-published, and every reported figure carrying its sample size.

**Roadmap:**

1. Design the corpus schema: id, text, topic, tags, recorded_time, valid interval, actor, kind
2. Author 1500 grounded facts across at least 12 distinct domains, not one synthetic topic
3. Include realistic agent-operational vocabulary, not generic English filler
4. Author at least 300 labelled queries split across direct, multi_hop, temporal and adversarial
5. Ensure every fact is referenced by at least one query so recall is measurable per fact
6. Add distractor facts that are topically adjacent but not answers
7. Add near-miss facts that differ from a query answer in exactly one token
8. Add at least 50 adversarial unanswerable queries
9. Add at least 50 temporal queries spanning valid-time and known-time axes
10. Add at least 50 multi-hop queries requiring two or more joins
11. Seed through the real remember() path so provenance is genuine
12. Verify no fact is reachable only through one index
13. Publish per-fact recall so weak areas are visible, not just aggregate hit rate
14. Report confidence intervals on every rate; 13 queries cannot support a point estimate
15. Report sample size in every table row
16. Re-run all four modes and publish the corrected results
17. Add corpus difficulty tiers so easy and hard are not averaged together
18. Add a held-out split so tuning cannot silently overfit the benchmark
19. Document the corpus construction method so it is reproducible
20. Add a corpus statistics report: topics, tags, length distribution, density
21. Add a leakage check proving held-out facts are absent from tuning runs
22. Make corpus generation a reproducible command, not a committed blob only
23. Version the corpus and record which version produced which published numbers
24. Add a corpus diff tool showing what changed between versions
25. Measure and publish latency at 150/500/1500 facts as a scaling curve
26. Measure and publish recall at each corpus size to show degradation or improvement
27. Replace the 14-fact corpus name in all documentation
28. Keep a small 14-fact smoke corpus for fast CI runs alongside the full corpus
29. Announce the corpus size change with before/after numbers so the delta is honest

### `B02` — The 5000-pair QA conversation benchmark

**Problem (verified):** Verified: no 5000-question conversation corpus exists anywhere on this box. Content sweeps over 1522 JSON/JSONL files found exactly one question/answer hit, and it was a benchmark result record, not a corpus. The real asset is /root/.local/share/opencode/opencode.db at 5.37 GB with 200 sessions, 40,847 messages, 5,304 user turns, 156,054 parts. This is the corpus to build from and it is entirely unmined.

**Done when:** A 5000-pair QA benchmark exists, derived from real conversation, with gold answers, graded relevance, provenance back to session and message ids, and published results.

**Roadmap:**

1. Open opencode.db read-only and build an extract of user turns with message ids
2. Extract 5304 user turns as the candidate pool for question selection
3. Filter turns into genuine questions rather than commands or statements
4. Select 5000 pairs stratified across sessions so no single session dominates
5. Attach the assistant reply as the reference answer for each question
6. Attach session id, message id and timestamp to every pair for provenance
7. Store the source db path and extraction timestamp in the corpus manifest
8. Build a distractor set for every question from real facts in the same session
9. Grade relevance on a graded scale, not binary, to allow partial credit
10. Define the grading rubric explicitly in the corpus documentation
11. Implement a deterministic retriever baseline for comparison
12. Split 5000 into train/dev/test so tuning never touches test
13. Keep a frozen test split that is re-evaluated only on release
14. Add retrieval of the answer even when it was never stored as a fact
15. Measure how many questions are answerable from the memory store at all
16. Separate answerable from unanswerable questions and report both
17. Add temporal questions derived from real conversation ordering
18. Add multi-turn context questions requiring conversation history
19. Add pronoun and anaphora questions requiring context resolution
20. Add a relevance judge; validate it against a human-labelled sample
21. Report judge agreement rate honestly, not as ground truth
22. Add a retrieval-quality metric over 5000 pairs with confidence intervals
23. Add a per-category breakdown so weak categories are visible
24. Publish results as a first-class benchmark table
25. Publish MRR and nDCG at k=5, 10 and 20
26. Measure and publish recall@k across all four retrieval modes
27. Add latency measured across 5000 queries, not 13
28. Add a sample of 50 hand-verified pairs as a gold anchor set
29. Compare against a BM25-only baseline and an embed-only baseline
30. Keep the 14-fact smoke corpus for CI so the fast gate stays fast

### `B03` — Fix the benchmark network hang and make the runner hermetic

**Problem (verified):** mem20benchmarkz tests were observed stalling on an ssl recv during this session. Root cause was a cold sentence-transformers HuggingFace download with no timeout, not a code hang: once weights are cached the suite proceeds. The runner still has no network policy, so any cold-cache CI run can stall indefinitely, and an unbounded stall is itself a defect. The suite must be hermetic and bounded before it can be scaled.

**Done when:** mem20benchmarkz tests terminate under a 60s ceiling, require no network, and are reproducible on a box with no outbound access.

**Roadmap:**

1. Reproduce the hang with a recorded traceback before changing anything
2. Identify every outbound call in the benchmark path
3. Set HF_HUB_OFFLINE for the benchmark process by default
4. Select the stub embedding backend for benchmarks
5. Add a hermetic mode that forbids all network by patching socket
6. Add a test that fails if any socket connect is attempted during a benchmark run
7. Add a hard per-query timeout inside the benchmark harness
8. Add a hard per-run timeout with a clear non-zero exit
9. Add pytest-timeout to the benchmark test configuration
10. Verify the suite passes with the network namespace blocked
11. Make the run command deterministic: fixed seed, fixed corpus version
12. Record the wall-clock time of a full run and publish it
13. Add a fast smoke mode that runs in under 30s for CI
14. Add a full mode for release validation
15. Document the difference between smoke and full in the README
16. Add a check that the isolated temp store is always used, never the live store
17. Verify no run ever writes to /root/.mem20/store
18. Add a test asserting live store mtimes are unchanged after a run
19. Add structured logging so a slow query is identifiable
20. Add a --seed flag and record the seed in the output JSON
21. Make results reproducible: same seed and corpus produce identical JSON
22. Add a test asserting byte-identical output across two runs
23. Clean up the temp store after every run, including on failure
24. Add a disk-space guard so a runaway run cannot fill the box
25. Report peak memory used during a run
26. Add a CI job that runs the smoke benchmark on every change
27. Fix the 41 Queries reporting a diagnostic figure so it is explained or removed
28. Verify every published number in latest.md is reproducible by a documented command

### `B04` — Trustworthiness benchmark as the primary axis

**Problem (verified):** The README states trustworthiness is the axis mem20 claims as its differentiator and the one no competitor publishes, yet the suite is organised quality-first. The current trust numbers are a checklist of zeros: contamination 0.0, stale pointers 0.0, healthy True. Zeros prove nothing is broken, not that the system is trustworthy under pressure.

**Done when:** Trustworthiness is measured under induced adversarial conditions, not only on a clean store, and published as the headline result.

**Roadmap:**

1. Reorganise the report so trust metrics appear before quality metrics
2. Add a contamination injection test and measure detection rate
3. Add a stale-index injection test and measure detection rate
4. Add a tampered-ledger test and measure detection rate
5. Add a simulated-fact leakage test on every retrieval path
6. Add a poisoned-fact test: an attacker writes a false fact and we measure how readily it is returned
7. Measure false-fact propagation through the graph and indexes
8. Add a trust score per query based on provenance completeness
9. Publish a trust-weighted quality metric alongside raw quality
10. Add a refusal-accuracy metric on unanswerable queries
11. Add a confidence calibration curve: predicted confidence vs observed correctness
12. Publish calibration error as a single number
13. Add an adversarial suite where the correct answer is to return nothing
14. Measure abstention quality as a headline number
15. Add a provenance coverage metric across the corpus
16. Verify the grounded firewall cannot be bypassed by any of the four modes
17. Add a test proving simulated facts never appear in default results
18. Add a test proving promotion requires real evidence
19. Add a test that audit_contamination returns 0.0 after injection attempts
20. Report trust numbers for each retrieval mode separately
21. Add a trust regression gate that fails CI on any trust metric regression
22. Document what trust means operationally, not just as a list of checks
23. Add a comparison table showing which trust metrics competitors publish
24. Be explicit in the README about which trust claims are and are not verified
25. Add a hostile-reviewer track where the benchmark audits its own claims
26. Publish the trust report with sample sizes like every other metric
27. Make trust regression a hard gate separate from quality regression
28. Re-measure every trust metric after the corpus grows to 1500 facts

### `B05` — Benchmark statistics, confidence intervals and honest reporting

**Problem (verified):** Thirteen queries produce hit rates of 1.000, 0.800 and 0.000. Those are presented as measurements. A 0.800 hit rate on 5 queries is 4 of 5 successes; the 95% interval spans roughly 0.30 to 0.97. No current number carries an uncertainty.

**Done when:** Every published rate carries a confidence interval and a sample size, and no point estimate is presented without its uncertainty.

**Roadmap:**

1. Compute Wilson score intervals for all binary rates
2. Compute bootstrap intervals for MRR and nDCG
3. Attach an interval to every number in the published table
4. Show sample size alongside every rate
5. Mark rates computed on fewer than 30 samples as indicative only
6. Add a significance test comparing retrieval modes pairwise
7. Report the multiple-comparison correction applied
8. Add a bootstrap seed so intervals are reproducible
9. Add a percentile and a BCa interval option
10. Add a power analysis showing how many queries each claim needs
11. Add a minimum-sample gate that refuses to publish an underpowered number
12. Distinguish statistically significant from practically important
13. Publish the difference between raw and corrected adversarial numbers side by side
14. Remove any claim that cannot survive its own interval
15. Add a trend line across corpus versions so improvement is visible
16. Add a regression detector that flags statistically significant drops
17. Report latency percentiles with intervals too
18. Add a note to every table stating the corpus version that produced it
19. Document the statistical method in the README
20. Add tests that the interval calculation is correct on known inputs
21. Add a test that an underpowered result is flagged
22. Add a seed sweep to confirm stability of the conclusions
23. Report the number of ties in MRR so ties are not hidden
24. Add a histogram of per-query scores, not just the mean
25. Remove the 1.000 values or explain why they are exactly 1.000 on 5 queries
26. Audit every currently published number and mark which survive scrutiny
27. Re-publish the report with intervals on every figure

### `B06` — Long-horizon and conversation-scoped benchmarks

**Problem (verified):** The current corpus is a flat 14 facts with no session, no conversation, no ordering, and no growth over time. A memory system's advantage is that it accumulates; the benchmark never tests accumulation because there is nothing accumulated.

**Done when:** The suite measures retrieval quality as a corpus grows across sessions and time, showing whether quality improves, degrades, or drifts.

**Roadmap:**

1. Model the corpus as sessions rather than a flat fact list
2. Simulate a long-horizon stream of at least 5000 fact writes
3. Measure retrieval quality at 100/500/1500/5000 facts
4. Measure latency growth at the same sizes
5. Measure index build and rebuild time as the corpus grows
6. Measure memory footprint at each corpus size
7. Measure how much of the gain is real and how much is corpus memorisation
8. Add a forgetting test: delete facts and verify they stop being returned
9. Add a stale-fact test: supersede a fact and verify the old one is not returned as current
10. Add a retraction test and verify retracted facts never surface
11. Add temporal decay measurement over simulated months
12. Add a session-boundary test measuring cross-session leakage
13. Add a namespace isolation test proving one namespace cannot read another
14. Add a test that indexing cost does not grow superlinearly without warning
15. Publish the scaling curve as a headline figure
16. Add memory footprint reporting to the benchmark JSON
17. Measure and publish rebuild time at 1500 facts
18. Add a concurrent-write benchmark during retrieval
19. Measure degradation when writes and reads interleave
20. Add a durability test that survives a crash mid-write
21. Add a test that a partially written record is never indexed
22. Publish corpus growth cost so scaling decisions are informed
23. Compare the scaling curve against a published baseline honestly
24. Add an SLO proposal derived from measured percentiles
25. Add alerting thresholds derived from measured variance
26. Document the long-horizon methodology in the README
27. Re-run the 13-query baseline under the new harness to prove comparability
28. Publish before and after numbers for the same measurement

### `B07` — Fair comparison and competitor-comparable tracks

**Problem (verified):** The README correctly refuses to compare against Mem0 LoCoMo 92.5, LongMemEval 94.4 and Zep DMR 94.8% because corpora and metrics differ. That honesty is right and it is also a marketing problem: a reader cannot tell how mem20 would do.

**Done when:** The suite runs at least one public benchmark under its original metric and reports the result with an explicit statement of what is and is not comparable.

**Roadmap:**

1. Identify one public benchmark whose corpus and metric are fully reproducible
2. Verify the public corpus licence permits use and redistribution
3. Build an adapter for that benchmark's loader
4. Reproduce the published baseline number to validate the adapter
5. Run mem20 through the adapter under the original metric
6. Report the mem20 number beside the published baseline with full method disclosure
7. State precisely which parts are comparable and which are not
8. Do not claim to beat or match any published figure without a like-for-like run
9. Add a second public benchmark if licence and metric permit
10. Publish the adapter code so the comparison is auditable
11. Document every deviation from the original protocol
12. Add a protocol-deviation section to the report
13. Add a reproducibility check that re-runs the published baseline
14. Keep the mem20-agent-kb-v1 results clearly separate from public comparisons
15. Add a section explaining why a single corpus cannot represent a whole class of systems
16. Publish our own numbers first and comparables second
17. Add a glossary so non-specialists can read the metrics
18. Add an interactive results page for the comparison
19. Have the comparison reviewed for overclaiming before publishing
20. State plainly where mem20 is behind, not only where it leads
21. Add a tracking plan for when a better public benchmark appears
22. Measure the adapter overhead and exclude it from latency claims
23. Add a test that the adapter reproduces the published baseline within tolerance
24. Keep the refusal-to-compare disclaimer where it belongs: in the comparison section
25. Let the internal corpus results speak for themselves without borrowed numbers
26. Record the comparison date and the versions of both systems
27. Update the root README with the honest comparison summary

### `B08` — Adversarial and failure-mode benchmark track

**Problem (verified):** Three adversarial queries scoring 0.000 on a 13-query corpus prove almost nothing. If the metric is misdefined then a correct abstention is scored as a failure, and the track is measuring the wrong thing while appearing to expose a weakness.

**Done when:** An adversarial track of at least 100 queries with a scoring model that distinguishes correct abstention from retrieval failure.

**Roadmap:**

1. Author at least 100 adversarial queries across six failure modes
2. Failure mode 1: the fact does not exist anywhere in the corpus
3. Failure mode 2: the fact exists but was superseded, and the old value is asked for
4. Failure mode 3: the fact exists only in the simulated partition
5. Failure mode 4: the question presupposes something false
6. Failure mode 5: the question is ambiguous and needs clarification
7. Failure mode 6: the question is answerable only with external knowledge
8. Define the expected correct behaviour for each failure mode
9. Score correct abstention as 1.0 and retrieval failure as 0.0
10. Score a wrong-but-confident answer as a distinct, worse category
11. Publish abstention rate, false-abstention rate and wrong-answer rate
12. Measure over-answering: returning something when nothing should be returned
13. Measure false confidence: answering when it should have abstained
14. Add a jailbreak track testing whether stored content can override the firewall
15. Test whether a fact written by an untrusted actor is returned as trusted
16. Add a prompt-injection variant: a fact whose text contains an instruction
17. Verify instruction text in a stored fact is never executed or followed
18. Publish the jailbreak results even where they are unflattering
19. Add an abstain confidence threshold sweep on adversarial queries
20. Measure how confidence tracks with adversarial difficulty
21. Add a regression test for each failure mode
22. Add per-failure-mode hit rates, not one aggregate
23. Add a track for questions whose answers span multiple facts
24. Add a track for questions requiring numeric reasoning over stored facts
25. Add a track for temporal traps such as before versus after a correction
26. Publish the adversarial results as the most important table in the report
27. Make adversarial regressions a hard CI gate

### `B09` — Multi-hop and compositional benchmark track

**Problem (verified):** multi_hop MRR is 0.640 for both keyword and hybrid, and 0.800 for semantic, on 5 multi_hop queries. That is a 3-of-5 and a 4-of-5 result presented as a measurement. Multi-hop is where a graph memory system should show its advantage and it currently does not.

**Done when:** At least 100 multi-hop queries measured with hop counts recorded, and measured multi_hop MRR improving over the current 0.640.

**Roadmap:**

1. Author at least 100 multi-hop queries with a recorded hop count per query
2. Include 2-hop, 3-hop and 4-hop queries
3. Build the gold evidence set per query listing every required fact
4. Score partial credit when some but not all hops resolve
5. Measure MRR by hop count to see where degradation starts
6. Compare graph, hybrid, keyword and semantic on the same queries
7. Measure whether graph mode wins on 3-hop and above
8. Measure hop budget sensitivity from 1 to 4
9. Measure edge-weight decay sensitivity
10. Add chain-join queries requiring an ordered sequence of facts
11. Add aggregation queries such as counting or summing over stored facts
12. Add set queries requiring all matching facts, not one
13. Add contradiction queries where two facts conflict
14. Measure how contradictions are surfaced rather than silently resolved
15. Add a test that a 4-hop query does not blow the traversal budget
16. Measure latency growth with hop count
17. Publish MRR by hop count as a primary table
18. Add a decomposition success metric for multi-hop queries
19. Measure whether decomposition or brute traversal performs better
20. Add a compositional chain benchmark: chains of two multi-hop queries
21. Add a failure analysis for every multi-hop query that misses
22. Classify misses: wrong hop, wrong fact, wrong join, budget exhausted
23. Publish the miss taxonomy so improvement targets are clear
24. Add a confidence metric for multi-hop answers
25. Verify multi_hop MRR exceeds 0.640 with the new harness
26. Compare against the pre-change 13-query result honestly
27. Update the README with the hop-count table

### `B10` — Latency, throughput and cost benchmarking

**Problem (verified):** Latency is reported as p50 and p95 only, on 13 queries. Hybrid p50 of 103.5ms with a p99 of 123.1ms is a 13-sample measurement. There is no throughput measurement, no concurrency data, and no token or dollar cost, which matters for an agent system that calls retrieval constantly.

**Done when:** Latency is measured over thousands of queries with full percentiles, under concurrency, with cost, and against an SLO.

**Roadmap:**

1. Run latency over at least 1000 queries per mode
2. Report p50, p95, p99 and max with confidence intervals
3. Add a warm-up phase excluded from measurement
4. Add a cold-start measurement as a separate figure
5. Measure throughput under 1, 8, 32 and 128 concurrent clients
6. Report throughput in queries per second at each concurrency level
7. Measure latency degradation under concurrency
8. Find the concurrency knee where latency degrades sharply
9. Report cold-start time per process
10. Add a memory footprint measurement per retrieval mode
11. Measure index load time at startup
12. Measure warm index load time separately from cold
13. Add token cost accounting per query for the reranker
14. Add estimated dollar cost per query and per thousand queries
15. Compare rerank on versus off for cost as well as latency
16. Publish the quality-latency-cost Pareto front
17. Publish the quality-latency-cost operating points agents should choose from
18. Define an SLO per mode grounded in measured percentiles
19. Add alerting thresholds from measured variance not from guesswork
20. Measure tail latency specifically: the slowest 1% of queries
21. Identify what causes tail latency and fix the worst contributor
22. Add a latency budget per pipeline stage
23. Report per-stage timing so regressions localise
24. Add a benchmark mode measuring first-query versus steady-state
25. Publish latency on the 1500-fact corpus as the headline figure
26. Compare against the 14-fact baseline to show corpus-size sensitivity
27. Document the measurement methodology in the README

### `B11` — Graph-specific and temporal-specific benchmark tracks

**Problem (verified):** graph mode has 2 queries and temporal recall has no track at all. graph reports 1.000 hit rate on n=2, which is the single most misleading number in the report. Temporal retrieval, which is mem20's differentiator, is entirely unbenchmarked.

**Done when:** Graph and temporal modes each have at least 100 queries and published results with sample sizes.

**Roadmap:**

1. Build a graph benchmark set of at least 100 entity-traversal queries
2. Measure graph hit rate, MRR and latency at production graph scale
3. Measure the live graph's entity and edge counts as the baseline
4. Report graph results on the current 38-entity, 70-edge benchmark graph AND a larger graph
5. Remove or heavily caveat the n=2 graph result until replaced
6. Build a temporal benchmark set of at least 100 queries
7. Cover valid-time queries: what was true at instant T
8. Cover known-time queries: what did we believe at instant T
9. Cover all four bi-temporal slices
10. Measure temporal recall separately from ordinary recall
11. Measure correctness of historical answers after corrections
12. Measure whether pre-correction truth is reachable through every path
13. Add temporal boundary queries at exact interval edges
14. Add queries spanning multiple corrections to the same subject
15. Measure temporal abstention on questions with no valid answer at that instant
16. Publish a temporal results table as a primary benchmark
17. Report temporal latency separately; it is a different cost class
18. Add a temporal correctness metric distinct from retrieval hit rate
19. Compare temporal mode against non-temporal retrieval on the same facts
20. Measure the improvement temporal mode provides on temporal queries
21. Add a regression test for each of the four slices
22. Verify the suite terminates with temporal mode included
23. Add temporal mode to the drift subcommand
24. Publish temporal results in the main report, not an appendix
25. Add the graph entity count to the report header for context
26. Update the README to remove the n=2 graph claim until replaced

### `B12` — Benchmark reproducibility, versioning and publication

**Problem (verified):** latest.json and latest.md exist with no version stamp visible in the report, no seed recorded, and no link between a published number and the code version that produced it. A number nobody can reproduce is not evidence.

**Done when:** Every published result carries a corpus version, code commit, seed and environment stamp, and is reproducible by one documented command.

**Roadmap:**

1. Add a corpus version identifier to every result
2. Add the git commit sha to every result
3. Add the seed to every result
4. Add the Python version and platform to every result
5. Add the embedding model name and dimension to every result
6. Add a result manifest listing every input file with its checksum
7. Publish a results history rather than overwriting latest
8. Add a date and sequence number to every published result
9. Add a diff tool comparing two results and highlighting regressions
10. Make re-running with the same inputs produce byte-identical output
11. Add a test asserting result reproducibility
12. Add a reproducibility script that regenerates a published number
13. Archive results under versioned directories
14. Publish the command that produced every published figure
15. Add a results index page listing every run
16. Add a trend view showing each metric over runs
17. Flag statistically significant regressions automatically
18. Add a stamp showing whether a run used the smoke or full corpus
19. Prevent publishing a smoke run as if it were a full run
20. Add a content hash of the report so silent edits are detectable
21. Add a changelog for benchmark methodology changes
22. Record methodology changes so old numbers are not compared to new ones naively
23. Publish a machine-readable results feed
24. Add a subscriber mechanism for downstream dashboards
25. Verify every currently published number can be reproduced
26. Mark any number that cannot be reproduced as withdrawn
27. Update the README with the exact reproduce command

### `B13` — Benchmark CI gate and regression protection

**Problem (verified):** There is no reported gate. drift exists as a subcommand proving diagnostics fire, but nothing prevents a quality or trust regression from landing. The suite runs manually and the last run predates the current commit.

**Done when:** A CI gate runs the smoke benchmark on every change and blocks on quality, trust or latency regression.

**Roadmap:**

1. Add a fast smoke benchmark that completes in under 30 seconds
2. Wire it into CI on every pull request
3. Define regression thresholds for hit rate, MRR and nDCG
4. Define regression thresholds for every trust metric
5. Define latency thresholds per mode
6. Fail the build on a statistically significant quality regression
7. Fail the build on ANY trust regression with no tolerance
8. Fail the build on a latency regression beyond 20 percent
9. Publish the baseline the gate compares against
10. Add an allowlist mechanism for deliberate metric changes
11. Require an explicit justification to use the allowlist
12. Report the gate result as a clear pass or fail with the delta
13. Add a full benchmark run on release branches
14. Add trend tracking across releases
15. Add a nightly full run with results archived
16. Verify CI runs hermetically with no network
17. Add a test that the gate correctly detects an induced regression
18. Add a test that the gate correctly passes an unchanged codebase
19. Publish gate status in the README and in SITEMAP.md
20. Alert on gate failures through the existing notification path
21. Add the benchmark result as a CI artifact
22. Make the baseline version explicit in every gate run
23. Rebaseline deliberately and visibly, never automatically
24. Add a dry-run mode to preview whether the gate would pass
25. Document the gate policy in the README
26. Run the gate against the current code to establish the baseline
27. Record the baseline numbers as the new reference point

### `B14` — Realistic agent-workload retrieval benchmark

**Problem (verified):** The benchmark asks factoid questions. Agents do not work that way. The real usage recorded in the ledger is actors like agent, gateway, researcher, fountain and writer retrieving in the context of an ongoing task with partial knowledge and time pressure.

**Done when:** A workload benchmark reproduces real agent retrieval patterns and is the primary quality gate.

**Roadmap:**

1. Model agent retrieval as task-driven rather than question-driven
2. Simulate a multi-step task requiring 20 to 50 retrievals
3. Include context accumulation where earlier retrievals shape later ones
4. Simulate partial knowledge: the agent knows some facts already
5. Simulate time pressure with a per-retrieval budget
6. Simulate failure: the agent must notice a retrieval returned nothing useful
7. Simulate contradiction encountered mid-task
8. Simulate superseded facts encountered mid-task
9. Measure task success rate given retrieval quality
10. Measure how many retrievals a task needs before success
11. Measure wasted retrievals returning irrelevant results
12. Measure whether earlier good retrievals help or hurt later ones
13. Simulate an agent with a context window limit
14. Measure degradation as the context window fills
15. Simulate multi-agent retrieval sharing one store
16. Measure cross-agent interference in a shared store
17. Test namespace isolation under concurrent multi-agent load
18. Publish a task-success metric alongside hit rate
19. Compare modes on task success, not just query hit rate
20. Add a workload trace from real sessions if available
21. Use the real actor distribution from the ledger as weighting
22. Publish the workload methodology in the README
23. Add a task-success regression gate
24. Verify task success improves over the naive baseline
25. Report which mode wins on task success versus query hit rate
26. Make task success the headline number in the report

### `B15` — Multilingual and cross-lingual retrieval benchmark

**Problem (verified):** The embedding model is all-MiniLM-L6-v2, an English model, and the corpus is English. BM25 tokenisation has no multilingual handling. Any non-English fact is effectively unretrievable by the vector path.

**Done when:** A multilingual benchmark measures retrieval across at least 5 languages and the embedding model is upgraded or the limitation is documented and measured.

**Roadmap:**

1. Author corpus facts in at least 5 languages including one non-Latin script
2. Author queries in each language
3. Measure vector retrieval per language to expose the English bias
4. Measure BM25 retrieval per language
5. Measure hybrid retrieval per language
6. Measure cross-lingual retrieval: query in A, fact in B
7. Evaluate a multilingual embedding model against the current one
8. Measure the quality and latency cost of the multilingual upgrade
9. Add language detection so queries route correctly
10. Add script-aware tokenisation for BM25
11. Measure retrieval on mixed-language documents
12. Measure retrieval on transliterated queries
13. Add a language column to every benchmark table
14. Publish per-language results even where they are poor
15. Document the current English-only limitation explicitly
16. Add per-language regression gates
17. Add a test that a non-Latin query returns the right fact
18. Measure performance degradation by script
19. Add a translation-based cross-lingual baseline for comparison
20. Measure whether the multilingual model beats translation
21. Keep the fast English CI path while adding slower multilingual nightly runs
22. Publish the language coverage of the corpus
23. Add a language-coverage warning if a script is unrepresented
24. Verify BM25 tokenisation handles non-Latin scripts correctly
25. Add multilingual facts to the 1500-fact corpus
26. Update the README with per-language numbers

### `B16` — Failure analysis and diagnostic tooling

**Problem (verified):** The suite reports aggregate numbers with no mechanism to ask why a specific query failed. Improving an aggregate without knowing its failure modes is guesswork, and the current 0.000 adversarial result cannot be diagnosed at all.

**Done when:** Every failing query can be inspected with a diagnosis of which stage failed and why.

**Roadmap:**

1. Record a per-query result file for every benchmark run
2. Store the candidate set the query actually produced
3. Store the score of the gold answer even when it is not in the top k
4. Store the rank of the gold answer
5. Implement a stage-attribution: retrieval, fusion, rerank, packing
6. Classify each miss: not indexed, indexed but not retrieved, retrieved but outranked, outranked but dropped
7. Publish a failure taxonomy with counts
8. Build a CLI tool to inspect a single query failure end to end
9. Show the candidate list for any query
10. Show why the gold answer was excluded at each stage
11. Add a diff mode comparing a query result before and after a change
12. Automatically flag queries whose result changed after a code change
13. Add a regression-diff report per change
14. Build a golden-file store of expected results for regression tracking
15. Add a tool to find queries that became worse
16. Add a tool to find queries that became better
17. Measure the fraction of misses attributable to each stage
18. Publish stage attribution as a primary diagnostic table
19. Add a test that failure classification is correct on synthetic cases
20. Use failure attribution to drive the next improvement cycle
21. Add an interactive results browser
22. Add export to CSV for external analysis
23. Make per-query results part of the published artifact
24. Ensure per-query data contains no secrets or PII
25. Add a size guard so per-query data does not bloat the repo
26. Document the diagnostic workflow in the README

### `B17` — Benchmark for the trust firewall and promotion path

**Problem (verified):** Promotion from simulated to grounded memory requires explicit evidence: a confirmation, or resolution via prediction error. Nothing measures how well that gate works, so a failure there would be invisible. The simulated ledger already holds 85 records and the contamination rate is currently 0.0.

**Done when:** The benchmark measures contamination under injection, promotion gate correctness, and audit accuracy on a store with known injected faults.

**Roadmap:**

1. Inject known simulated facts into a benchmark corpus
2. Verify none appear in default grounded retrieval
3. Verify they appear when include_simulated is explicitly true
4. Measure contamination rate after injection; currently 0.0 on a clean store
5. Test promotion with a valid confirmation succeeds
6. Test promotion without confirmation is refused
7. Test promotion via prediction-error resolution succeeds
8. Test promotion via a fabricated resolution note is refused
9. Verify the promotion gate cannot be bypassed by any retrieval mode
10. Verify audit_contamination detects injected contamination
11. Verify audit_contamination returns 0.0 on a clean store
12. Test that quarantined simulated facts never surface
13. Test that expired simulated facts never surface
14. Add a test that simulated facts cannot be written directly to the grounded ledger
15. Measure the false-positive rate of contamination detection
16. Measure the false-negative rate on injected facts
17. Add a benchmark track that specifically attacks the firewall
18. Verify the PII scanner never mutates stored data
19. Test that detection and redaction are distinct operations
20. Verify detection leaves stored content byte-identical
21. Add a benchmark of the PII scanner's precision and recall
22. Publish contamination numbers after injection as the honest figure
23. Make a contamination regression a hard CI failure
24. Add the promotion-gate tests to the trust benchmark
25. Publish promotion-gate correctness in the trust table
26. Document the firewall contract and its measured enforcement

### `B18` — Index-health and drift benchmarking

**Problem (verified):** mem20_memory_index_health raises AttributeError because memory.py has no index_health. Measured drift exists: ledger 449, vector_meta 448, bm25_corpus 448. The drift subcommand exists to prove diagnostics fire, but the underlying health function is missing, so the primary diagnostic cannot run.

**Done when:** index_health() exists, drift is detected automatically, and a benchmark proves detection fires on induced drift.

**Roadmap:**

1. Implement memory.index_health() returning a structured report
2. Report exact per-index counts and the mismatches between them
3. Fix the MCP tool so mem20_memory_index_health stops raising
4. Reconcile the live 449/448/448 mismatch and document the cause
5. Induce drift by removing an index entry and verify it is detected
6. Induce drift by adding an orphan entry and verify it is detected
7. Induce a schema version mismatch and verify detection
8. Induce a model-dimension change and verify detection
9. Add drift injection to the existing drift subcommand
10. Make the drift subcommand the CLI entry to index_health
11. Make health exit non-zero when unhealthy
12. Add health to the mem20api surface
13. Add health to mem20-api-health
14. Measure time-to-detect drift
15. Add a scheduled health check logging drift over time
16. Add a drift history file to catch slow skew
17. Add an alert threshold for drift percentage
18. Publish health numbers in the trust table
19. Replace the unexplained Queries reporting a diagnostic of 41 with real health data
20. Add a test asserting health does not mutate the store
21. Add a test asserting a healthy store reports healthy
22. Add a rebuild command that repairs drift without data loss
23. Verify rebuild preserves provenance
24. Add health to the benchmark JSON schema
25. Make health a required field in the published report
26. Update the README so the trust claim is backed by a function that runs

## Domain E. Corpus & Dataset Production

### `D01` — Conversation mining pipeline from opencode.db

**Problem (verified):** opencode.db holds 40,847 messages, 5,304 user turns and 156,054 parts across 200 sessions and is 5.37 GB. It is the only real conversational corpus on this box and nothing reads it for memory purposes. mem20ocaskz already mines it read-only, so the safe extraction pattern exists and can be reused.

**Done when:** A repeatable, read-only pipeline extracts structured facts and QA pairs from opencode.db into a versioned, provenance-carrying dataset, proven not to write to the live store.

**Roadmap:**

1. Open opencode.db strictly read-only; never write to the live session store
2. Snapshot the source db before extraction so the run is reproducible
3. Record a checksum of the source db snapshot in the manifest
4. Extract the session table with id, directory, time_created and title
5. Extract the message table with id, session id, role and timestamp
6. Extract the part table and reassemble multi-part text messages
7. Filter to sessions whose directory touches /opt/mem20 for domain relevance
8. Extract all 5,304 user turns with their session and message ids
9. Classify each user turn as question, command, statement or feedback
10. Distil multi-turn context into self-contained facts
11. Attach the assistant reply as a reference answer per question
12. Attach provenance to every extracted fact
13. Deduplicate near-identical turns across sessions
14. Run the PII scanner in detect mode; never redact stored data
15. Filter out secrets before any output is written
16. Version the extracted dataset
17. Make the pipeline a reproducible command with documented arguments
18. Add a dry-run mode that reports counts without writing
19. Measure extraction throughput in records per second
20. Measure how many of the 5,304 turns become usable facts
21. Publish extraction statistics honestly including what was dropped and why
22. Add a test asserting the pipeline never writes to opencode.db
23. Add a test asserting two runs over one snapshot produce identical output
24. Add resume capability so an interrupted long run continues
25. Add a bounded mode so CI can run a small slice in seconds
26. Document the output schema so consumers can depend on it
27. Add a quality review step on a human-sampled subset
28. Ensure the source db is never copied into the output dataset
29. Record which sessions were excluded and the reason for each

### `D02` — Distil conversations into grounded facts with provenance

**Problem (verified):** The live ledger holds 449 records across 41 topics written by actors including agent, gateway, opencode-session-feed, researcher, fountain and writer. The store is thin for benchmarking and unevenly distributed across topics. Facts must be real, grounded and provenanced; fabricating facts to hit a count would poison every downstream metric.

**Done when:** The fact store grows substantially with every added fact grounded, provenanced and traceable, and the quality effect is measured.

**Roadmap:**

1. Define what qualifies as a grounded fact versus a note or an observation
2. Extract candidate facts from real conversation content only
3. Every extracted fact carries a source reference to its origin
4. Every extracted fact carries an actor
5. Every extracted fact carries recorded_time
6. Deduplicate against the existing 449 records before inserting
7. Detect contradictions with existing facts and flag rather than overwrite
8. Preserve superseded facts; never delete on correction
9. Use the real remember() path so the grounded firewall applies
10. Refuse to insert anything the firewall rejects
11. Target a documented corpus size rather than an arbitrary count
12. Avoid inflating the count with low-value or trivial facts
13. Add a relevance floor so trivial facts do not enter the store
14. Publish before and after topic distributions
15. Identify under-represented topics and fill them deliberately
16. Measure corpus growth rate honestly per run
17. Re-run the benchmark after growth to show the measured delta
18. Document what was extracted and what was excluded and why
19. Keep the whole extraction reproducible from the snapshot
20. Report the growth achieved per session with real numbers

### `D03` — Fact schema, typing and quality control

**Problem (verified):** 449 records across 41 topics with no documented schema. Nothing guarantees a record has a type, a valid interval or a usable topic, so corpus quality is entirely unenforced and defects only surface during benchmark runs.

**Done when:** A documented fact schema with validation enforced at write time, and every existing record conforming or explicitly quarantined.

**Roadmap:**

1. Define the canonical fact schema: id, content, topic, tags, actor, recorded_time, valid interval, provenance
2. Make required fields enforced at write time
3. Add a validator that rejects records missing required fields
4. Define a topic taxonomy with a controlled vocabulary
5. Map the existing 41 topics onto the taxonomy
6. Define tag conventions and normalise existing tags
7. Add a fact type field: assertion, preference, procedure or observation
8. Classify existing records by type
9. Add a confidence field distinct from the trust score
10. Validate valid intervals on every write
11. Reject records with impossible or inverted intervals
12. Add a content length policy
13. Reject near-empty facts that carry no information
14. Add a uniqueness policy for exact duplicate content
15. Make the validator report rather than silently repairing
16. Run the validator over all 449 existing records
17. Report exactly how many existing records fail and why
18. Fix or explicitly quarantine every failing record
19. Make schema version explicit on every record
20. Add a migration path for future schema changes
21. Add a schema version check at read time
22. Document the schema in the engine README
23. Enforce the schema in the 1500-fact benchmark corpus builder
24. Add tests for every validation rule
25. Make the validator available as a CLI subcommand

### `D04` — Temporal corpus for bi-temporal evaluation

**Problem (verified):** temporal.db has 752 events and 376 versions but the main ledger has no recorded-time axis. There is no dataset exercising corrections, retractions and late-learned facts, so bi-temporal retrieval cannot be measured at all despite being the headline differentiator.

**Done when:** A temporal corpus with known corrections and retractions exists, and every bi-temporal query has a verified expected answer per slice.

**Roadmap:**

1. Author facts each carrying a known valid interval
2. Author facts deliberately learned late, where known time lags valid time
3. Author a correction chain: original, corrected, then corrected again
4. Author at least 50 facts that are retracted
5. Author at least 50 facts that are superseded
6. Author facts that were true and later became false
7. Author facts learned out of chronological order
8. Author facts with identical content at different times
9. Record ground-truth valid intervals for every fact
10. Record ground-truth known intervals for every fact
11. Write the four-slice expected answer for every fact
12. Include boundary cases exactly at interval start and end
13. Include a case where valid_then differs from known_then
14. Verify every expected answer by hand on a sampled subset
15. Publish the temporal corpus separately from the flat corpus
16. Measure bi-temporal accuracy per slice and publish each
17. Report accuracy specifically where slices disagree with each other
18. Add a regression test per temporal construction
19. Document the construction procedure so it is reproducible
20. Make the temporal corpus a required benchmark dependency

### `D05` — Adversarial and trap corpus construction

**Problem (verified):** Three adversarial queries cannot distinguish correct abstention from retrieval failure. The suite cannot detect a system that confidently answers a question with nothing behind it, which is the most damaging real-world failure mode for a memory system.

**Done when:** At least 100 adversarial queries with a scoring model separating correct abstention from failure, and a system that passes.

**Roadmap:**

1. Author unanswerable queries where no supporting fact exists
2. Author queries for superseded facts asking for the old value as current
3. Author queries whose answer exists only in the simulated partition
4. Author queries carrying a false presupposition
5. Author genuinely ambiguous queries that need clarification
6. Author near-miss pairs differing in exactly one token
7. Author questions naming a plausible but wrong entity
8. Author questions requiring external knowledge not in the store
9. Author temporal traps using before and after a correction
10. Define the expected correct behaviour for every trap category
11. Implement the scoring model separating abstention from failure
12. Score a wrong confident answer worse than an honest abstention
13. Publish per-category accuracy rather than one aggregate
14. Publish abstention rate and false-abstention rate separately
15. Review the adversarial set for accidental answerability
16. Have a second reviewer independently check the expected answers
17. Document every trap and the failure mode it targets
18. Make the adversarial set part of the full corpus
19. Run and publish the adversarial results
20. Add an adversarial regression gate to CI

### `D06` — Corpus versioning, diffing and lineage

**Problem (verified):** No corpus version appears in the results, so published numbers cannot be tied to the data that produced them and a silent corpus change invalidates every prior comparison without warning.

**Done when:** Every corpus is versioned, every result records its corpus version, and corpus diffs are published alongside results.

**Roadmap:**

1. Assign a semantic version to every corpus
2. Record the corpus version in every benchmark result
3. Add a manifest with per-fact checksums
4. Add a corpus diff tool showing added, removed and modified facts
5. Refuse to compare results across incompatible corpus versions
6. Add a corpus changelog recording every change
7. Tag corpus releases in version control
8. Add lineage from corpus to result to published number
9. Document the corpus versioning policy
10. Make corpus changes a reviewed operation, never automatic
11. Verify the diff tool detects a single-fact modification
12. Publish the diff whenever a corpus version advances
13. Add a CI check refusing to publish results whose corpus version is unstated
14. Verify the diff tool detects a single-fact content change
15. Verify the diff tool detects a removed fact
16. Verify the diff tool detects a changed fact label or tag
17. Record the corpus version inside the corpus file itself, not only alongside
18. Fail a benchmark run whose manifest checksum does not match the corpus
19. Keep a machine-readable corpus registry listing every version
20. Never overwrite an existing corpus version in place

### `D07` — Corpus quality assurance and human validation

**Problem (verified):** The 14-fact corpus has no documented validation. A single wrong gold answer makes every downstream metric meaningless, and the entire positioning rests on winning on trust rather than a fast, unfalsifiable claim.

**Done when:** Every gold answer is verified, with documented human review of a statistically meaningful sample and recorded agreement.

**Roadmap:**

1. Review every gold answer in the 1500-fact corpus
2. Have a second reviewer independently verify a random sample
3. Measure and publish inter-reviewer agreement
4. Fix or remove every disputed gold answer
5. Verify distractor facts are genuinely not answers to any query
6. Verify near-miss facts differ in exactly the intended way
7. Check queries do not share wording with their own answers
8. Check no query contains its answer verbatim, making it trivial
9. Check temporal gold answers respect their interval boundaries
10. Check adversarial gold answers are genuinely unanswerable
11. Document the review process and the sample size used
12. Publish review outcomes including every disagreement
13. Store review results alongside the corpus
14. Make re-review possible whenever the corpus changes
15. Add a corpus lint command running all automated checks
16. Fail publication when lint finds a blocking issue
17. Record the reviewer identity or role for each review batch
18. Report the final verified-facts count honestly
19. Check temporal gold answers respect the half-open interval convention at the exact boundary
20. Check no adversarial query is accidentally answerable via the simulated partition
21. Verify distractors are topically adjacent so they genuinely test discrimination
22. Record the verified/unverified count per fact in the corpus manifest
23. Fail the lint when any gold answer lacks a reviewer record
24. Sample 10% of the corpus for full second review and publish that result
25. Re-run lint automatically whenever a corpus version advances

## Domain F. Index & Storage

### `F01` — Atomic index rebuild and crash safety

**Problem (verified):** A rebuild interrupted mid-write could corrupt the vector or BM25 index, and there is no evidence of atomic swap or crash recovery. Losing the index means losing retrieval until a full re-embed, which on this network-restricted box can hang indefinitely.

**Done when:** Index rebuild is atomic and interruption-safe, verified by fault injection.

**Roadmap:**

1. Implement temp-file-plus-rename for every index write
2. Verify an interrupted rebuild leaves the old index intact
3. Add fault injection tests interrupting a rebuild at each stage
4. Add index checksum verification at load time
5. Refuse to load any checksum-mismatched index
6. Add a rebuild command with progress reporting
7. Make rebuild resumable after an interruption
8. Measure rebuild time at 1500 facts
9. Verify rebuild preserves provenance and recorded times
10. Add a test proving rebuild equals incremental writes in result
11. Back up indexes before every rebuild
12. Document the rebuild procedure and its recovery steps
13. Ensure a failed rebuild never leaves a partially written index
14. Report rebuild time as a benchmark metric
15. Verify a rebuild interrupted mid-write leaves the previous index fully usable
16. Add fault injection tests at each stage of the rebuild
17. Verify index checksum is validated at load and a mismatch is refused
18. Verify rebuild preserves provenance, recorded time and intervals exactly
19. Measure rebuild time at 1500 facts and publish it
20. Verify rebuild is atomic on the vector index specifically

### `F02` — Storage growth, compaction and the deep-entries store

**Problem (verified):** entries/ holds 104 markdown files totalling 21.6 MB, backups/ holds 45 files around 45 MB, and the memory graph is 3.19 MB. Growth is unmanaged and the deep-entries store has no documented lifecycle, so it will grow without bound.

**Done when:** Storage growth is measured, compaction is safe, and the deep-entries lifecycle is documented.

**Roadmap:**

1. Measure current storage by category across every store
2. Set an explicit growth budget per store
3. Define a backup retention policy
4. Implement backup rotation with safe pruning
5. Never delete the only remaining copy of a record
6. Define the deep-entries lifecycle: create, keep, archive, delete
7. Verify deep entries stay retrievable before any pruning
8. Implement safe compaction that preserves retrieval
9. Measure the compaction impact on retrieval quality
10. Report storage growth over time as a trend
11. Alert on unexpected growth beyond the budget
12. Document the storage architecture and each store's purpose
13. Verify compaction is reversible where possible
14. Measure current storage by category before changing any retention
15. Define retention per store: ledger, indexes, graph, deep entries, backups
16. Measure the retrieval quality impact of compaction and publish it
17. Verify compaction is reversible or clearly documented as irreversible
18. Publish storage growth as a trend over time
19. Ensure backup rotation never removes the last good copy
20. Publish per-store storage so growth is attributable

### `F03` — Index/ledger consistency enforcement

**Problem (verified):** Measured drift is real: ledger 449 against vector_meta 448 and bm25_corpus 448. Records are being written without a guaranteed index update, so the index silently lags truth and search returns incomplete results.

**Done when:** Writes update every index atomically and any drift is detected and repaired automatically.

**Roadmap:**

1. Make every write path update all indexes
2. Add a write-time consistency assertion
3. Add an automatic reconciliation on startup
4. Add a background reconciler for continuous correction
5. Alert when drift persists beyond a threshold
6. Measure reconciliation time at 1500 facts
7. Add a test proving no write path can skip an index
8. Verify reconciliation preserves ordering
9. Document the consistency model precisely
10. Report drift as a first-class health metric
11. Measure how the current 449/448/448 mismatch arose and document the cause
12. Verify the repaired state returns all 449 records to every index
13. Measure and publish the cause of the current 449/448/448 index mismatch
14. Add a test proving no write path can skip an index update
15. Verify reconciliation preserves ordering and recorded time
16. Document the consistency model and what is guaranteed
17. Verify reconciliation cannot lose a record
18. Verify reconciliation is safe to run concurrently with reads
19. Verify drift detection runs before any benchmark publishes numbers
20. Publish the drift count as a standing trust metric

## Domain G. API, MCP & Interfaces

### `G01` — Repair and complete the MCP tool surface

**Problem (verified):** mem20_memory_index_health raises AttributeError because memory.py has no index_health attribute. A published tool that raises is worse than a missing one because callers trust it and silently mis-handle the failure.

**Done when:** Every advertised MCP tool runs successfully, proven by a test that invokes all of them.

**Roadmap:**

1. Fix mem20_memory_index_health to call a real function
2. Audit every advertised MCP tool by actually invoking it
3. List every tool that errors and fix each one
4. Add a test invoking every advertised tool
5. Make tool errors explicit and typed rather than raw exceptions
6. Document each tool's guarantees honestly
7. Ensure no read-path tool mutates the store
8. Add a tool-contract version identifier
9. Publish the audited tool list with pass and fail status
10. Report any tool that cannot be fixed rather than hiding it
11. Verify the memory tools all report consistent counts
12. Audit every advertised memory and cognition tool by invoking it live
13. Fix every tool that raises, starting with index_health
14. Ensure read-path tools never mutate the store
15. Add a test invoking every advertised tool end to end
16. Ensure a raising tool reports an error rather than silently passing
17. Audit every cognition and imagination tool, not only memory tools
18. Ensure a broken tool is reported rather than silently omitted
19. Add a coverage test so new tools are audited automatically
20. Document which tools are safe for read-only callers

### `G02` — Stable public API with trust metadata in every result

**Problem (verified):** The differentiator is trust, but results carry only content and score with no provenance, no confidence and no index-health state, so consumers cannot act on the system's actual advantage.

**Done when:** Every result carries provenance, confidence, index-health state and a retrieval-mode label, pinned by contract tests.

**Roadmap:**

1. Define the result envelope including every trust field
2. Include provenance on every result from every mode
3. Include a confidence score distinct from the similarity score
4. Include an index-health snapshot with each response
5. Include the retrieval mode that produced each result
6. Include temporal slices when a temporal query was used
7. Include an abstention flag with a reason code when empty
8. Version the API and publish the contract
9. Write contract tests pinning the envelope shape
10. Keep mem20api as the stable surface and mem20 as the engine
11. Document what is guaranteed versus what may change
12. Add an API changelog recording every contract change
13. Include the index generation so callers can detect a stale read
14. Include an abstention reason code when a query returns nothing
15. Include both temporal slices when a temporal query was used
16. Write contract tests pinning the envelope shape and types
17. Ensure the envelope serialises cleanly to JSON
18. Document backward-incompatible changes and their migration
19. Verify the envelope is stable across the four retrieval modes
20. Ensure trust metadata is present even for graph-sourced results

## Domain H. Documentation Systemwide

### `E01` — Restore the 12 missing or empty READMEs

**Problem (verified):** 12 organs are effectively undocumented. Worse, the mem20temporaldatabasefabricz README asserts the recall_at bi-temporal bug is fixed and locked down by tests, while 11 of those 14 tests currently fail on the remember() epistemic_status contract break. A README claiming test-backed correctness while its own suite is red is the exact failure mode this project exists to prevent.

**Done when:** Every organ has a substantive README whose claims are verified against actual code.

**Roadmap:**

1. Write mem20agentz README covering the agent platform and its CLI
2. Write mem20agentz_sdk README covering the OpenAI-style SDK absorption
3. Write mem20kimiz README covering parallel subagent fan-out and rate limits
4. Write mem20langz README covering stateful graph execution and checkpointing
5. Write mem20messenger README covering accounts, WebSocket proxy and the bot fleet
6. Write mem20officez README covering the 3D workspace and agent fleet
7. Write mem20orcaz README covering the deterministic workflow orchestrator
8. Write mem20oreo README covering the visual, NL-first programming language
9. Write mem20secretz README covering the floating-credential sweep
10. Write mem20unikitz README covering behaviour trees, GOAP and utility AI
11. Replace the zero-byte mem20factoryz README with real verified content
12. Replace the zero-byte mem20rpgz README with real verified content
13. Write memory_engine README covering the core engine and its members
14. Verify every factual claim in each README against the code
15. Include a verified quick start in each README
16. Document the entry point and CLI surface for each organ
17. Include a usage example that actually runs
18. State what each organ does not do, not only what it does
19. Add a test asserting every organ has a non-empty README
20. Surface the check in the sitemap so gaps are visible systemwide
21. Record the claim-verification date in each README
22. Never claim a feature that a code search does not confirm

### `E02` — Wire READMEs into packaging metadata (111 unwired)

**Problem (verified):** Of 158 packaged organs only 47 declare readme = README.md in pyproject. 111 READMEs sit on disk but never ship in package metadata, so for roughly 70% of packaged organs the README is decorative for anyone installing the package. This is the highest-leverage documentation defect actually measured.

**Done when:** Every packaged organ references its README, the content is verified, and the build includes it.

**Roadmap:**

1. Add readme = README.md to all 158 packaged organs' pyproject
2. Verify the built distribution actually includes the README
3. Verify the content renders in the package metadata view
4. Check each README's first line becomes the package description
5. Add a test asserting every packaged organ wires its README
6. Surface the wiring check in the sitemap report
7. Confirm every pyproject readme path resolves; a wrong path breaks the build
8. Add a build smoke test per organ for at least the top 40
9. Fix the 4 organs missing a console script: kimiz, langz, messenger, oreo
10. Verify each console script actually runs after install
11. Add a test asserting every declared console script resolves
12. Document the packaging conventions in the root README
13. Add a CI check failing when an organ ships without a README
14. Measure how many organs remain unwired after the change
15. Publish before and after wiring counts
16. Never auto-generate placeholder text; every README must be verified
17. Verify the sdist and wheel both contain the README after wiring
18. Confirm PyPI-style metadata renders the README first paragraph as the description
19. Publish the count of organs still unwired after the change, honestly
20. Add a CI check that fails when a packaged organ lacks readme wiring
21. Verify no pyproject readme path points at a missing file
22. Record the wiring change in each organ's changelog

### `E03` — Make documentation claims verifiable and test-backed

**Problem (verified):** 241 of 300 organs ship a README with zero test files. Documentation asserting untested behaviour is exactly the untrustworthy pattern that erodes confidence, and it covers roughly 80% of the estate.

**Done when:** Every factual README claim is either test-backed or explicitly marked as untested.

**Roadmap:**

1. Inventory factual claims across all READMEs
2. Classify each claim as verified, test-backed or unverified
3. Add tests backing claims in the highest-claim organs first
4. Mark untested claims explicitly rather than implying verification
5. Add a doc-claims manifest per organ
6. Add a CI check invalidating doc claims when code changes
7. Add a link checker across all READMEs
8. Add a command-example checker that actually executes every example
9. Fix every broken link and every failing example
10. Publish the count of verified versus unverified claims
11. Prioritise organs whose READMEs make the boldest claims
12. Cover mem20benchmarkz, mem20api and mem20temporaldatabasefabricz first
13. Add a freshness marker showing when claims were last verified
14. Never present an unverified claim as verified
15. Publish verification status in the sitemap
16. Add an explicit unverified-claims section to each key README
17. Prioritise verifying claims in organs whose READMEs state guarantees, not just features
18. Mark every unverified claim in place rather than removing it silently
19. Add a CI check that fails when code changes without a doc-claim update
20. Report the count of claims verified versus still unverified
21. Add a freshness marker showing when each claim was last verified
22. Never upgrade an unverified claim to verified without executing it

### `E04` — Root README accuracy and the generated SITEMAP appendix

**Problem (verified):** The root README claims 327 subsystems, 301 organs and 8,969 files. The live sitemap reports 329 subsystems, 302 organs and 9,181 files. The numbers drift because they are hand-maintained, which is precisely the pattern that makes documentation untrustworthy.

**Done when:** Root README numbers are generated from the live index, never hand-typed, and SITEMAP.md stays generated.

**Roadmap:**

1. Replace hand-typed counts with generated values
2. Add a build step injecting live counts into the root README
3. Verify the claim about 28 live systemd units against reality
4. Verify the version badge matches the pyproject version
5. Confirm the grounded-versus-simulated claim matches enforced code
6. Confirm the benchmark claim matches what the suite actually does
7. Regenerate SITEMAP.md via the sitemap build
8. Never hand-edit the generated SITEMAP.md
9. Add a CI check that root README counts match the live index
10. Document the README build process
11. Keep the honesty disclaimers about competitor comparability
12. Add a dated verification note to the root README
13. Verify the quick start commands in the root README still run
14. Link the benchmark report directly from the root README
15. Verify every quick start command in the root README still exits zero
16. Regenerate the organ, file and line counts from the live sitemap
17. Add a CI check failing when root README counts drift from the index
18. Keep the honest non-comparability disclaimer intact in the root README
19. Add a dated verification note recording when counts were last regenerated
20. Verify the version badge against the actual package version

### `E05` — Quickstart and architecture documentation that matches reality

**Problem (verified):** There is no single trustworthy onboarding path. A new user or agent must infer the architecture from roughly 300 directories and a generated sitemap, and the honest quickstart does not exist.

**Done when:** A verified quickstart takes a new user to a working retrieval call, and architecture docs match the code.

**Roadmap:**

1. Write a quickstart verified end to end by execution
2. Document install steps that are tested in CI
3. Document the first remember and recall call
4. Write an architecture overview of the core memory engine
5. Document the index architecture: vector, BM25, graph and temporal
6. Document the grounded-versus-simulated model precisely
7. Document the trust model and its exact guarantees
8. Document the retrieval fusion and reranking pipeline
9. Document the extension model for adding a new organ
10. Keep architecture docs adjacent to the organs they describe
11. Mark clearly which documents are generated and which are hand-written
12. Add a documentation review checklist covering accuracy and honesty
13. Verify every command in the quickstart exits zero
14. Link the quickstart from the root README
15. Verify every documented example actually runs in CI
16. Document how to read the benchmark report without over-reading it
17. Verify the quickstart reaches a working retrieval call
18. Ensure every documented command is covered by CI
19. Document the index architecture diagram accurately
20. Document the trust model in the quickstart path

## Domain I. Packaging & Distribution

### `E06` — Packaging consistency across 300 organs

**Problem (verified):** 142 of 300 organs have no pyproject.toml at all while 158 do, and all 158 declare versions. The estate is split between packaged and unpackaged with no stated policy, and 4 packaged organs lack console scripts entirely.

**Done when:** Every organ is either properly packaged or explicitly marked internal with a stated reason.

**Roadmap:**

1. Decide and document the packaging policy for the estate
2. Package the organs that genuinely should be packages
3. Mark the remainder internal with a documented reason
4. Ensure no declared console script is broken
5. Verify every entry point resolves after installation
6. Add a CI check that packaged organs import cleanly
7. Verify the 158 version strings follow one convention
8. Add accurate and minimal dependency declarations
9. Add a dependency audit across the estate
10. Document the organ naming convention and its documented exceptions
11. Verify the mem20*z convention is applied where intended
12. Keep the documented naming exceptions as deliberate exceptions
13. Report the packaged versus internal split honestly
14. Verify no organ is packaged with a broken manifest
15. Verify every organ is either packaged or explicitly marked internal with a reason
16. Verify no organ is packaged with a broken or missing manifest
17. Add a CI check that every declared entry point resolves after install
18. Document the organ naming convention and its deliberate exceptions
19. Report the packaged versus internal split honestly, including failures
20. Verify the packaged-versus-internal split is reviewed each release

### `E07` — Install, import and CI smoke tests estate-wide

**Problem (verified):** No reported evidence that organs install and import correctly at scale. A package that does not import stays invisible until someone depends on it in production.

**Done when:** CI verifies every packaged organ installs and imports cleanly, with failures reported honestly.

**Roadmap:**

1. Add a CI job that builds every packaged organ
2. Add a CI job installing every packaged organ into a clean venv
3. Add a CI job importing every organ and running its entry-point help
4. Add a smoke test for the mem20api public surface
5. Add a smoke test for the mem20benchmarkz CLI
6. Add a smoke test for the sitemap CLI
7. Record exactly which organs currently fail these checks
8. Fix failures or mark the affected organ internal
9. Report the pass rate honestly including every failure
10. Use nightly rather than per-commit runs if the suite proves slow
11. Ensure CI never publishes an unverified package
12. Publish the smoke-test result in the quality gate
13. Add an install smoke test per packaged organ covering import and entry point
14. Verify the install matrix runs on a clean virtualenv, not the live one
15. Record which organs fail and why, never suppressing the failure
16. Publish the pass rate honestly including every failure
17. Add an entry-point invocation check per packaged organ
18. Fail the CI job on any organ that fails to import
19. Record failures per organ so they are individually actionable
20. Ensure the smoke suite is hermetic and needs no network

## Domain J. Operations, Ecosystem & Product

### `H01` — Systemd, health and operational readiness

**Problem (verified):** The root README claims 28 live systemd units with no verification. Health is a checklist rather than an operational signal, so operators cannot tell whether the system is degraded.

**Done when:** Every service is a verified systemd unit with health checks, and health is a live signal rather than a static list.

**Roadmap:**

1. Verify every claimed systemd unit exists and is enabled
2. Verify MainPID has PPID=1 for every long-lived server
3. Confirm there are no floating background processes
4. Verify every restart policy is correct
5. Add health checks to every unit
6. Add a single consolidated health dashboard
7. Alert on index drift, health failure and latency regression
8. Document every service: unit, purpose, exec, env, port, health, restart
9. Verify every service survives a restart
10. Never take a port without checking every unit's ExecStart first
11. Report honestly anything that is not a unit
12. Verify the claimed unit count against reality and correct the README
13. Verify the claimed systemd unit count against reality and correct the README if wrong
14. Verify each long-lived server has MainPID with PPID=1
15. Confirm no floating background processes exist outside units
16. Document every service: unit, purpose, exec, env, port, health, restart policy
17. Verify no service holds a port claimed by another unit
18. Check every ExecStart before touching any port
19. Alert on any unit that fails to reach active state
20. Document restart policy for each unit explicitly

### `H02` — Sales and information websites

**Problem (verified):** No site deployment is verified in this pass. Public claims about mem20 need to match measured reality, especially the honest non-comparability of competitor figures, or the site becomes a liability.

**Done when:** Information and sales sites are live, and every technical claim traces to a reproducible measurement.

**Roadmap:**

1. Inventory existing sites and their real deployment state
2. Decide which sites are live and which remain drafts
3. Build an information site presenting architecture and honest capabilities
4. Build a sales site focused on the trust differentiator
5. Ensure every benchmark number on a site is reproducible
6. Keep the competitor non-comparability disclaimer on every benchmark page
7. Never state or imply parity with a competitor figure without a like-for-like run
8. Add a documentation site tied to the verified organ READMEs
9. Ensure all documentation is verified accurate before publishing
10. Add analytics only with consent and a published privacy statement
11. Deploy with TLS and a documented process
12. Verify every published URL actually resolves
13. Publish the benchmark report at a stable URL linked from the site
14. Keep the non-comparability disclaimer on every benchmark page
15. Ensure every technical claim on a site traces to a reproducible measurement
16. Verify every published URL resolves before announcing
17. Add a privacy statement before any analytics is enabled
18. Ensure every claim links to the reproducible benchmark run
19. Document the deployment process so it can be repeated
20. Verify no competitor figure appears without its disclaimer

### `H03` — Documentation and roadmap deduplication

**Problem (verified):** 2.0_roadmap contains step_08 through step_20 twice, once at the top level and once under human_package/steps, and all 13 pairs are md5-identical. Duplication guarantees drift and wastes review effort.

**Done when:** No duplicated documents remain and drift cannot recur.

**Roadmap:**

1. Verify the 13 duplicate pairs are still byte-identical
2. Choose one canonical location per duplicated document
3. Remove duplicates or replace them with links
4. Add a CI check detecting duplicate content
5. Document the roadmap directory convention
6. Check for duplication elsewhere across the estate
7. Report every duplicate found and its resolution
8. Ensure the canonical copy is the one referenced elsewhere
9. Verify no link breaks after removing duplicates
10. Verify the 13 duplicate step files are still md5-identical before removing
11. Replace duplicates with links to the single canonical copy
12. Add a CI check detecting byte-identical documents in the estate
13. Check for duplication beyond 2.0_roadmap across the whole estate
14. Verify no link breaks after the duplicates are removed
15. Report every duplicate found across the whole estate
16. Document the single-source convention for roadmaps
17. Confirm the consolidation preserves every roadmap's content
18. Verify no roadmap content is lost during consolidation
19. Publish the duplicate count before and after
20. Ensure the canonical roadmap location is documented

### `H04` — Toolchest registration and discoverability for the whole estate

**Problem (verified):** 300 organs exist and discoverability depends on the registry being current. An unregistered capability is invisible to every future session, which is the exact failure the registry exists to prevent.

**Done when:** Every installable organ is registered and discoverable in toolchest.

**Roadmap:**

1. Refresh the toolchest registry from current state
2. List registered organs against on-disk organs
3. Register every missing organ
4. Verify each registration actually runs
5. Add a CI check for registry drift
6. Document how to register a new organ
7. Report registration coverage honestly
8. Verify no registered entry points to a missing package
9. Refresh the registry from current on-disk state before comparing
10. Register every installable organ missing from the registry
11. Verify each registration actually runs when invoked
12. Add a CI check failing on registry drift
13. Report registration coverage honestly including any failures
14. Verify no registry entry points at a missing package
15. Document how an agent discovers a newly registered tool
16. Ensure registry refresh is cheap enough to run routinely
17. Report any organ that cannot be registered and why
18. Ensure registration covers every installable organ
19. Verify the registry is refreshed in routine operation
20. Document the registration requirement for new organs

### `H05` — Cross-subsystem quality gate and honest reporting

**Problem (verified):** No single gate covers the estate, and several claims across READMEs are unverified. The honest gap report is exactly the thing most likely to be quietly omitted.

**Done when:** One gate covers packaging, tests, docs and benchmarks, and every gap is reported rather than smoothed over.

**Roadmap:**

1. Define a single estate-wide quality gate
2. Include packaging verification in the gate
3. Include the test suite result in the gate
4. Include README presence and wiring in the gate
5. Include the benchmark smoke suite in the gate
6. Include the drift check in the gate
7. Report every failure with the organ explicitly named
8. Never suppress a failure to make the gate green
9. Publish the gap report with exact counts
10. Keep a written known-gaps document current
11. Update known-gaps on every release
12. Review the gate output with a human
13. Include documentation coverage, not just test results, in the gate
14. Include the benchmark smoke suite so quality is gated too
15. Name the failing organ explicitly in every report line
16. Publish the gap report with exact measured counts
17. Publish when each gate failure was first seen
18. Ensure the gate cannot be bypassed by a partial run
19. Include a rollback path if the gate blocks a good change
20. Verify the gate runs without network access

## Domain K. Testing & Quality Culture

### `L01` — Network isolation and deterministic clocks in the test suite

**Problem (verified):** The proven hang is a network call with no timeout inside the test path; the suite has no network policy so any hidden dependency can hang CI indefinitely. Temporal tests also depend on the wall clock, so results can vary by time of day.

**Done when:** The test suite cannot reach the network, any attempt fails fast visibly, and all tests are byte-reproducible against an injected clock.

**Roadmap:**

1. Add a global network guard to the test session
2. Fail fast on any outbound socket attempt
3. Identify every hidden network dependency
4. Remove or stub each hidden dependency
5. Run the suite with the network namespace blocked
6. Verify all tests pass hermetically with no network
7. Measure suite runtime with and without network available
8. Ensure the guard cannot be accidentally disabled
9. Report any test that cannot run hermetically
10. Introduce an injectable clock abstraction
11. Replace direct time calls in the engine with the clock
12. Use a fixed clock in tests
13. Verify results are identical across runs
14. Verify results are identical on a different day
15. Test boundary behaviour precisely at interval edges
16. Ensure production still uses the real clock
17. Document the network and clock policies
18. Report any test that cannot be made hermetic rather than hiding it
19. Verify no test depends on wall-clock ordering
20. Ensure production still uses the real clock after injection
21. Document the network and clock policies for contributors

### `L02` — Property-based, mutation and contract testing

**Problem (verified):** Retrieval has strong invariants that example tests miss: determinism, no cross-namespace leakage, monotonic supersession, half-open intervals. A passing suite can still miss defects if assertions are weak, especially on trust-critical code. And mem20api has no contract tests, so a breaking change ships silently.

**Done when:** Core invariants are property-tested over generated inputs, mutation testing shows the suite detects injected defects, and every public function is contract-pinned.

**Roadmap:**

1. Use hypothesis for property-based testing
2. Property: identical queries return identical results
3. Property: a supersession never resurrects the old value
4. Property: half-open intervals never overlap
5. Property: no result crosses a namespace boundary
6. Property: deduplication never loses provenance
7. Property: an empty store returns empty for every query
8. Property: packing never drops the gold answer at any budget
9. Property: fusion is commutative across arm ordering
10. Record every property violation as a real bug
11. Enable mutation testing on the memory engine
12. Run mutation testing on the grounded firewall
13. Run mutation testing on temporal filtering and the contamination check
14. Add tests for every surviving mutant
15. Report the mutation score honestly
16. Enumerate the public API surface
17. Write a contract test per function
18. Pin return shapes, types and error behaviour
19. Fail CI on an unintended breaking change
20. Verify contracts cover the trust metadata fields

### `L03` — Test the 241 untested organs

**Problem (verified):** 241 of 300 organs have zero test files. The estate is 80% untested, so most documented behaviour is unverified, including the organs making the boldest claims. Documentation asserting untested behaviour is exactly the untrustworthy pattern that erodes confidence.

**Done when:** Every organ making behavioural claims has at least one test, prioritised by claim strength rather than alphabetically.

**Roadmap:**

1. Rank organs by boldness of README claims
2. Add a smoke test per organ covering import and entry point
3. Add behaviour tests for the highest-claim organs first
4. Add a CI check that an organ with claims has tests
5. Measure estate-wide test coverage
6. Publish coverage per organ
7. Report the coverage percentage honestly including shortfalls
8. Never write tests that assert nothing
9. Verify new tests actually fail when the behaviour breaks
10. Update the published coverage figure after each addition
11. Publish coverage per organ so shortfalls are visible
12. Verify each new test actually fails when the behaviour breaks
13. Report the coverage percentage honestly including what remains untested
14. Never write a test that asserts nothing
15. Prioritise by claim strength, not alphabetically
16. Verify added tests fail when behaviour regresses
17. Track which organs remain untested and publish that list
18. Ensure each new test names the organ it covers
19. Verify coverage counts are measured, not estimated
20. Report the exact untested-organ list in the gap document

## Domain N. Scale & Performance

### `M01` — Retrieval performance and quality at 10k, 50k and 100k facts

**Problem (verified):** The corpus will grow well past 1500, and nothing is known about behaviour at scale because nothing has been measured above 14 facts in the benchmark. Stating a scaling limit without measuring it would be exactly the unverified claim this project exists to avoid.

**Done when:** Latency, memory, build time and quality are measured at 10k, 50k and 100k facts, and the scaling limits are documented honestly.

**Roadmap:**

1. Build corpora at 10k, 50k and 100k facts
2. Measure p50, p95 and p99 latency at each size
3. Measure memory footprint at each size
4. Measure index build and rebuild time at each size
5. Measure quality degradation at each size
6. Identify the size at which quality degrades materially
7. Identify the size at which latency becomes unacceptable
8. Document the scaling limits honestly
9. Report the recommended maximum corpus size
10. Publish the scaling curve as a headline figure
11. Verify the measurement harness handles each corpus size
12. Ensure synthetic corpora do not distort quality conclusions
13. Ensure synthetic corpora do not distort the quality conclusion
14. Verify the harness completes at each corpus size within a bounded time
15. Publish the recommended maximum corpus size with its measured basis
16. Document the scaling limits honestly including where quality breaks
17. Verify the harness terminates at the largest corpus size
18. Record the corpus size at which each metric becomes unreliable
19. Verify quality measurement is valid at each corpus size
20. Ensure scaling results are reproducible from a documented command

### `M02` — Concurrency safety, background index maintenance and write latency

**Problem (verified):** Multiple agents share one store with no evidence that concurrent access is safe, and the opencode.db shows 24 distinct working directories implying heavy multi-agent use. Index updates also appear to happen inline, so either writes block or the index lags and drift appears.

**Done when:** Concurrent access is verified safe with measured throughput, and index maintenance is inline or background based on measurement.

**Roadmap:**

1. Test concurrent reads for consistency
2. Test read-during-write consistency
3. Test concurrent writes for lost updates
4. Measure throughput under 32 concurrent clients
5. Verify no index corruption under load
6. Verify every index stays consistent under load
7. Test lock contention behaviour
8. Document the concurrency model precisely
9. Report any race condition found honestly
10. Measure write latency with inline indexing
11. Measure write latency with deferred indexing
12. Measure index lag under deferred indexing
13. Choose the approach based on measurement not preference
14. Bound the index lag explicitly
15. Alert when lag exceeds the bound
16. Verify crash recovery under the chosen approach
17. Verify crash recovery preserves consistency under the chosen indexing model
18. Publish the measured index lag if deferred indexing is chosen
19. Report any race condition found honestly rather than fixing silently
20. Verify no index corruption appears under sustained load

### `M03` — Memory footprint and cold-start optimisation

**Problem (verified):** The graph is 3.19 MB for only 38 entities and 70 edges, which extrapolates poorly to 1500 facts. Startup also loads the vector index, BM25 index and graph, and cold-start time is unmeasured despite affecting every agent session.

**Done when:** Per-fact memory cost is measured and reduced where wasteful, and cold start is measured and improved.

**Roadmap:**

1. Measure bytes per fact across all stores
2. Identify the largest memory contributors
3. Compress or deduplicate graph structures
4. Reduce redundant index metadata
5. Measure the reduction achieved
6. Verify retrieval quality is unchanged after reduction
7. Verify the reduction does not break retrieval
8. Measure cold-start time
9. Measure warm-start time
10. Measure per-index load cost
11. Make index loading lazy where safe
12. Verify lazy loading causes no first-query latency spike
13. Ensure lazy loading never returns partial results
14. Publish per-fact memory cost and startup numbers
15. Publish per-fact memory cost at each corpus size
16. Verify lazy loading never returns partial results to a caller
17. Ensure the reduction does not break provenance retention
18. Document the memory model and startup characteristics
19. Verify memory reduction does not regress latency
20. Verify lazy loading does not reorder results

## Domain O. Agent Ecosystem & Integration

### `N01` — Agent-platform retrieval integration and tool surface

**Problem (verified):** mem20agentz, crewz, langz, kimiz, orcaz and googlez all exist but retrieval integration depth across them is unknown. Trust tools are also not uniformly exposed, so an agent cannot check whether an answer is trustworthy at the point of use.

**Done when:** Every agent platform retrieves through the same stable API, and a composable retrieve-then-verify tool surface exists.

**Roadmap:**

1. Audit retrieval integration per agent platform
2. Record which platforms use mem20api
3. Route every platform through the stable API
4. Add a common result envelope across platforms
5. Add integration tests per platform
6. Verify each platform's integration actually works
7. Define the retrieval tool set
8. Define the trust tool set including health and provenance
9. Make tools composable: retrieve then verify
10. Add a verify-result tool
11. Add tool descriptions stating guarantees honestly
12. Ensure tool errors are actionable rather than raw exceptions
13. Test every tool
14. Document the tool contract
15. Publish the integration matrix
16. Publish the integration matrix showing which platform uses which surface
17. Verify each platform's integration test actually exercises retrieval
18. Add a verify-result tool so agents can check trust at point of use
19. Ensure trust tools are uniformly exposed across platforms
20. Document which surface each platform is expected to use

### `N02` — Usage guidance, namespace-per-agent isolation and decision durability

**Problem (verified):** An agent choosing hybrid gets a 10x latency penalty for a multi-hop quality loss, because nothing tells it which mode to pick. The fleetwide roadmap calls for isolated namespaces per bot but all 17 existing namespaces are test fixtures. And nothing measures whether a crashed agent's decisions survive.

**Done when:** Correct mode selection is guidance an agent can load, each agent gets a verified isolated namespace, and decisions survive a crash.

**Roadmap:**

1. Write a mode-selection guide from measured results
2. Include measured latency and quality per mode
3. Include the rerank decision guidance
4. Include the abstention contract
5. Include the trust metadata available per result
6. Make it a skill so agents load it automatically
7. Verify the guidance against the latest benchmark run
8. Document how to re-verify the guidance
9. Provision a namespace per agent on registration
10. Set an explicit ACL per namespace
11. Verify isolation between provisioned namespaces
12. Add cross-namespace leakage tests
13. Report fleet isolation coverage honestly
14. Ensure decisions are durable at write time
15. Implement crash recovery replay
16. Test recovery after a simulated crash mid-run
17. Verify no decision is lost and none duplicated
18. Measure and document recovery time
19. Measure and publish recovery time after a simulated crash
20. Verify crash recovery never duplicates decisions
21. Report fleet isolation coverage honestly including gaps
22. Document how to re-verify the usage guidance after a benchmark run

## Domain P. Governance, Process & Growth

### `O01` — Single source of truth and regression discipline

**Problem (verified):** Claims live in the root README, organ READMEs, benchmark reports, the sitemap and websites, and they drift as the root README's organ and file counts already demonstrate. Changes have also been made without recorded baselines, making regressions undetectable.

**Done when:** Every verified claim has one authoritative source and every change records a baseline before and after.

**Roadmap:**

1. Define the authoritative source for each class of claim
2. Make organ counts, file counts and LOC generated rather than typed
3. Make benchmark figures generated from results
4. Make every other document reference rather than restate
5. Add a CI check for restated numbers
6. Verify no document restates a generated figure
7. Document the claim hierarchy
8. Record the current benchmark as the formal baseline
9. Require a baseline measurement before a retrieval change
10. Require re-measurement after the change
11. Compare and publish the delta
12. Fail the gate on regression
13. Ensure baselines remain reproducible
14. Document the regression discipline
15. Verify no document anywhere restates a generated figure
16. Make the baseline reproducible so any later run can be compared
17. Fail the gate on regression rather than silently rebaselining
18. Document the claim hierarchy and the authoritative source per class
19. Verify the baseline itself is reproducible from a clean checkout
20. Ensure a claim change triggers re-verification, not just a doc edit

### `O02` — Honest gap reporting, release engineering and contribution model

**Problem (verified):** Several gaps are known and unwritten: 241 untested organs, 142 unpackaged, the broken health tool, the false-green MEMORY.md status. Unwritten gaps are invisible gaps. Versions exist but there is no release process, and 300 organs have no stated contribution conventions.

**Done when:** A maintained known-gaps document lists every gap with counts, a defined release process runs the gate, and contribution rules are enforced automatically.

**Roadmap:**

1. Create the known-gaps document
2. List every measured gap with exact counts
3. Include the untested-organ count
4. Include the unpackaged-organ count
5. Include the broken health tool
6. Include the absent MEMORY.md and USER.md
7. Never delete a gap without fixing it
8. Update known-gaps on every release
9. Define the release process
10. Automate the version bump
11. Run the full gate before any release
12. Generate and publish release notes
13. Verify installability of a release
14. Document organ creation conventions
15. Require a README for every new organ
16. Require a test for every new organ
17. Require toolchest registration for every new organ
18. Require packaging or an explicit internal marker
19. Add a CI check for each contribution requirement
20. Update the known-gaps document on every release, never only at creation
21. Verify installability of every release before it is tagged
22. Require the full quality gate to pass before any release
23. Publish release notes generated from the actual commit range

### `O03` — Roadmap execution and roadmap deduplication

**Problem (verified):** 52 roadmap files exist plus 45 in 2.0_roadmap with 13 confirmed md5-identical duplicate step files, and mem20 holds structured roadmaps separately. Multiple sources will diverge, and nothing tracks whether phases complete or stall.

**Done when:** One authoritative roadmap source exists with everything else referencing it, and every phase has a verifiable completion criterion.

**Roadmap:**

1. Verify the 13 duplicate pairs are still byte-identical
2. Choose one canonical location per duplicated document
3. Remove duplicates or replace them with links
4. Add a duplicate-content CI check
5. Verify no link breaks after removing duplicates
6. Inventory all roadmap sources across the estate
7. Select the authoritative representation
8. Generate or link the non-authoritative copies
9. Document the roadmap architecture
10. Give every phase a verifiable completion criterion
11. Prefer a command that exits zero over a subjective judgement
12. Mark phases completed only when the criterion passes
13. Report stalled phases
14. Report phases blocked on another phase
15. Publish completion status honestly
16. Publish phase completion status honestly, including stalled phases
17. Verify no phase is marked complete without its criterion passing
18. Report phases blocked on another phase explicitly
19. Verify no link breaks after roadmap consolidation
20. Ensure every phase criterion is machine-checkable

## Domain Q. Advanced Retrieval Research

### `P01` — Adaptive routing, graph structure and attribution-weighted fusion

**Problem (verified):** Mode selection is manual, so an agent eats whatever quality or latency it picks. The graph is built but underused as a ranking signal. And fusion treats all arms equally regardless of source reliability, so a well-provenanced fact ranks equally with an unprovenanced one.

**Done when:** A router beats any fixed mode, graph structure measurably improves ranking, and provenance quality influences fusion.

**Roadmap:**

1. Train a router on the labelled 300+ query set
2. Router features: query length, entity count, temporal cues, question type
3. Measure router accuracy at picking the best mode
4. Measure the quality gain over the best fixed mode
5. Measure the latency cost of routing
6. Verify the router never picks a disabled mode
7. Add centrality as a ranking signal
8. Add community detection and use community coherence as a signal
9. Measure the structural gain on multi-hop queries
10. Measure the structural gain on direct queries
11. Test whether structure helps or merely reflects co-occurrence
12. Measure the cost of computing the structural signals
13. Derive a provenance quality score
14. Weight fusion by provenance quality
15. Measure the trust-weighted accuracy gain
16. Measure the raw accuracy cost of weighting
17. Test that an unprovenanced fact can be demoted
18. Publish both raw and trust-weighted numbers
19. Make the router optional and always overridable by the caller
20. Publish both raw and trust-weighted fusion numbers
21. Measure the router's own latency cost separately from retrieval
22. Verify structure-based signals help rather than merely reflect co-occurrence

### `P02` — Diverse ensembles, answer faithfulness and perturbation robustness

**Problem (verified):** A hybrid of three similar arms is weaker than a genuinely diverse ensemble. Retrieval hit rate measures whether the right fact was found but not whether an answer composed from it is supported by it. And exact benchmark queries say little about behaviour on the paraphrases and typos real agents produce.

**Done when:** A diverse ensemble beats the current hybrid on held-out data, answer support is measured separately from hit rate, and robustness to perturbation is quantified.

**Roadmap:**

1. Add a genuinely different retriever such as a graph-native or exact-lexical arm
2. Train a combiner on the labelled set
3. Evaluate strictly on held-out queries
4. Compare against the current RRF hybrid
5. Report the gain with a confidence interval
6. Report honestly if diversity did not help
7. Define answer support precisely
8. Implement a support checker against retrieved evidence
9. Build a labelled support dataset
10. Measure support rate per mode
11. Compare support rate against hit rate to expose the gap
12. Add an unsupported-answer detector
13. Generate paraphrases of every benchmark query
14. Generate typos at realistic rates
15. Generate reordered phrasings
16. Measure hit rate under each perturbation
17. Identify which modes are most robust
18. Add robustness to the CI gate
19. Publish the gap between retrieval success and answer faithfulness
20. Add an unsupported-answer detector to the API surface
21. Verify the ensemble never trains on the held-out split
22. Report honestly if the diverse ensemble did not beat the current hybrid

### `P03` — Index format evolution, multilingual and code corpora, and dense subjects

**Problem (verified):** Index formats have no version or migration story, so any format change risks silent breakage across a store that has existed for months. The embedding model is English-only while BM25 has no multilingual tokenisation, and agent knowledge bases are full of code identifiers that tokenise badly.

**Done when:** Index formats are versioned with tested migrations, multilingual and code-heavy corpora are measured, and dense-subject limits are documented.

**Roadmap:**

1. Add a format version to every index
2. Write a migration for each format change
3. Test migration from the current format
4. Refuse to load an index from a future unknown version
5. Add a migration dry-run mode
6. Author a multilingual corpus slice in at least 5 languages
7. Measure vector retrieval per language to expose the English bias
8. Measure BM25 and hybrid retrieval per language
9. Measure cross-lingual retrieval: query in one language, fact in another
10. Add script-aware tokenisation and language detection
11. Evaluate a multilingual embedding model against the current one
12. Measure the quality and latency cost of the multilingual upgrade
13. Author a corpus slice of code identifiers and file paths
14. Measure retrieval on identifiers, file paths and version strings
15. Improve tokenisation for code and measure the improvement
16. Build a corpus with 500 facts on one subject
17. Identify the subject density at which quality breaks
18. Document all measured limits honestly
19. Add a migration dry-run so format changes can be rehearsed safely
20. Refuse to load an index written by a future unknown format version
21. Publish per-language results even where they are poor
22. Document the measured subject-density limit honestly

## Domain R. Communication & Enablement

### `Q01` — Honest positioning, reproducible demo and troubleshooting documentation

**Problem (verified):** The system correctly refuses to compare its numbers to Mem0 or Zep, but that leaves a vacuum a competitor will fill with an unfair comparison. A demo that cannot be reproduced is worse than no demo. And the proven network hang would cost any user hours with no troubleshooting documentation.

**Done when:** Positioning is honest and grounded in measurements, the demo runs from a clean checkout in CI, and every observed failure mode has a documented fix.

**Roadmap:**

1. State what mem20 does that others do not, measured
2. State honestly where mem20 is behind
3. Never claim parity or superiority on an uncompared metric
4. Lead with the trust differentiator that is actually implemented
5. Lead with grounded-versus-simulated separation enforced in code
6. Have the positioning reviewed for overclaiming
7. Build a demo that runs from a clean checkout
8. Verify every published command executes
9. Add a CI job running the demo
10. Keep the demo under five minutes end to end
11. Ensure the demo needs no network
12. Document the network-hang failure mode and its fix
13. Document the false-green MEMORY.md status
14. Document how to diagnose index drift
15. Document how to run the benchmark offline
16. Document how to read the benchmark report honestly
17. Verify every troubleshooting step
18. Verify every troubleshooting step by actually running it
19. Keep the demo under five minutes end to end and measure it
20. Ensure the demo needs no network so it runs hermetically
21. Link troubleshooting from the root README so it is findable

### `Q02` — Benchmark report as the primary artifact and lessons made queryable

**Problem (verified):** The benchmark report is the most credible artifact mem20 has and it is buried. Meanwhile lessons learned, such as the network-hang and false-green-status findings, are lost unless written to memory, so the next session re-learns them.

**Done when:** The benchmark report is the landing artifact with every claim tracing to it, and every non-obvious defect is stored as evidenced memory.

**Roadmap:**

1. Make the report the first thing linked from the root README
2. Show trust metrics before quality metrics
3. Show sample sizes and confidence intervals on every figure
4. Show what is not compared and why
5. Show known gaps inside the report itself
6. Keep the report generated, never hand-edited
7. Publish the report at a stable URL
8. Store every non-obvious defect as a memory with evidence
9. Store the verification method, not just the finding
10. Make memories searchable by symptom
11. Pin the lessons that would otherwise be re-learned
12. Review the pinned blocks periodically
13. Ensure the memory store is used for lessons, not just data
14. Keep the benchmark report generated, never hand-edited
15. Store the verification method alongside each remembered lesson
16. Make lessons searchable by symptom so the next session finds them
17. Review and prune pinned lessons periodically
18. Ensure pinned lessons are revisited when related work resumes
19. Ensure lessons are written before the session ends
20. Ensure pinned lessons load at session start
21. Verify a lesson is removed once it no longer applies

## Domain S. Multi-Agent & Fleet

### `R01-2` — Fleet load testing and shared-versus-isolated store strategy

**Problem (verified):** The opencode.db shows 24 distinct working directories and heavy multi-agent use, but no load test exists at fleet scale. Some knowledge must be shared across agents and some must be isolated, and that strategy is currently undefined.

**Done when:** Retrieval is verified stable at realistic fleet concurrency and a documented strategy governs what is shared versus isolated.

**Roadmap:**

1. Model realistic fleet concurrency from observed usage
2. Run a sustained load test
3. Measure latency under sustained load
4. Measure error rate under load
5. Verify no corruption under sustained load
6. Measure recovery after a burst
7. Document the tested limits honestly
8. Classify knowledge as shared or isolated
9. Implement cross-namespace read where sharing is intended
10. Guarantee isolation where isolation is intended
11. Test both directions explicitly
12. Document the classification
13. Model concurrency from observed usage rather than an invented number
14. Verify no corruption appears under sustained load
15. Document the tested limits including where the system degraded
16. Classify knowledge as shared or isolated and test both directions
17. Verify shared reads cannot mutate another namespace's facts
18. Document which knowledge classes are shared by default
19. Verify isolation holds under concurrent multi-agent load
20. Publish the load-test limits alongside the benchmark numbers
21. Verify shared facts cannot be mutated by a non-owner namespace
22. Measure isolation overhead under concurrent load
23. Document what happens when a shared fact is superseded
24. Ensure load-test corpora contain no real secrets

### `R02-2` — Agent knowledge transfer, write conflict resolution and per-agent policy

**Problem (verified):** The MALIC roadmap describes agent collisions producing transferable lessons, but nothing supports knowledge transfer beyond same-namespace reads. Two agents correcting the same fact concurrently can produce an inconsistent state with no defined resolution. And all agents share one retrieval configuration despite different needs.

**Done when:** Agents can transfer knowledge with the source recorded, concurrent conflicting writes resolve deterministically, and policy is tunable per agent.

**Roadmap:**

1. Support publishing a fact to a shared namespace
2. Support citing the source agent
3. Measure whether transferred knowledge helps the receiving agent
4. Track knowledge transfer success
5. Document the transfer model
6. Detect concurrent conflicting writes
7. Define a deterministic resolution policy
8. Test two agents correcting the same fact
9. Verify no write is silently lost
10. Document the resolution policy
11. Allow per-namespace retrieval configuration
12. Verify one agent's policy does not affect another
13. Provide sensible defaults per agent type
14. Document the configuration surface
15. Verify no concurrent write is silently lost
16. Verify one agent's retrieval policy cannot affect another's
17. Measure whether transferred knowledge measurably helps the receiving agent
18. Document the conflict-resolution and transfer models
19. Verify conflict resolution never silently loses provenance
20. Document the default policy for per-agent retrieval settings
21. Verify conflict resolution is deterministic across replays
22. Document how transferred facts are marked as second-hand

## Domain T. Data Governance

### `S01` — MEMORY.md and USER.md, and the false-green detection pattern

**Problem (verified):** memory_status reports MEMORY.md 0/2200 chars OK and USER.md 0/1375 chars OK, but neither file exists on disk. A status reporting OK for an absent file is a false green hiding a real gap, and this is a class of defect rather than a one-off.

**Done when:** Both files exist with real content, and every status surface in the estate distinguishes healthy, degraded and broken honestly.

**Roadmap:**

1. Fix status to report absent files as absent, never OK
2. Add a test that absent is distinguished from empty
3. Author real MEMORY.md content
4. Author real USER.md content
5. Verify reported character counts match the actual files
6. Ensure status cannot report OK for a missing file again
7. Document what belongs in each file
8. Inventory every status and health surface estate-wide
9. Identify every false-green pattern
10. Fix each one to report honestly
11. Add a test that a broken condition never reports OK
12. Add a test that a raising health function never reports healthy
13. Document the distinction between healthy, degraded and broken
14. Fix every status and health surface found to report falsely green
15. Add a test that a missing file never reports OK
16. Verify reported character counts match the actual files on disk
17. Add a regression test for the false-green status class
18. Publish the before and after status strings for comparison
19. Verify the fix covers every status surface, not just memory_status
20. Ensure the absent-versus-empty distinction is testable in CI

### `S02` — Ledger separation audit, retention, export and schema migration

**Problem (verified):** simulated_ledger.jsonl holds 85 records and the contamination rate is 0.0 on a clean store, so the separation that is the core claim needs a standing audit. There is also no retention policy across 449 records, 45 backups and 21.6 MB of deep entries, no documented export format, and no schema migration path for the recorded_time backfill.

**Done when:** Separation is audited standing, retention is implemented, the store round-trips losslessly, and schema migrations preserve provenance.

**Roadmap:**

1. Audit the grounded-versus-simulated separation weekly
2. Verify simulated records never appear in default retrieval
3. Verify simulated records appear only when explicitly requested
4. Verify promotion requires real evidence
5. Test the promotion gate against every bypass route
6. Alert immediately on any leak
7. Classify records by retention class
8. Implement archival for aged records
9. Implement a deletion path with an audit trail
10. Verify retrieval still works for archived records
11. Measure storage after retention is applied
12. Define a complete export format
13. Export ledger, indexes, graph, temporal and pins
14. Reimport into a clean store and verify intervals and provenance survive
15. Test round-trip losslessness
16. Version the record schema explicitly
17. Backfill recorded_time where derivable
18. Mark backfilled values as inferred, never as observed
19. Test every migration on a copy and verify counts
20. Test the promotion gate against every bypass route including the API
21. Verify round-trip export and reimport is lossless
22. Verify backfilled values are marked inferred and never presented as observed
23. Test every schema migration on a copy and verify counts before and after
24. Measure and publish the storage effect of retention

## Domain U. Quality Gates & Verification

### `T01-2` — One verification command and the definition of done

**Problem (verified):** Verification is scattered across many commands with no single honest answer to whether mem20 is working. Work has also been reported done without the sanity sweep being executed, which is precisely the rule violation the standing rules exist to prevent.

**Done when:** One command reports the whole system state honestly and exits non-zero when broken, and done is defined as a command that exits zero.

**Roadmap:**

1. Aggregate every health check into one command
2. Report healthy, degraded and broken distinctly
3. Exit non-zero on any broken component
4. Include the benchmark smoke result
5. Include the drift check
6. Include the test suite result
7. Include documentation coverage
8. Publish the output as the canonical system status
9. Define done as a command that exits zero
10. Require evidence of execution for every done claim
11. Prohibit reporting a partial pass as clean
12. Require reproduction before a fix is claimed
13. Require the full suite after every change
14. Enforce the definition of done in review
15. Include documentation coverage in the single verification command
16. Exit non-zero on any broken component, never zero with warnings
17. Require evidence of execution for every done claim in review
18. Verify the single command fails when any component is broken
19. Document the exit codes of the verification command
20. Ensure the command runs in CI on every change
21. Verify the command detects a broken component rather than passing
22. Ensure the command is safe to run against the live system
23. Document how to interpret each status in the output

### `T02-2` — Continuous verification, adversarial review and honest self-audit

**Problem (verified):** Published numbers drift from reality as the code changes and nobody notices until someone re-runs. Claims are written by the same system that produced the code, so blind spots persist. And nothing detects when a stated claim stops being true.

**Done when:** Every published figure is re-verified on a schedule, claims are adversarially reviewed by a second party, and stale figures are withdrawn.

**Roadmap:**

1. Re-run the benchmark on a schedule
2. Compare results against published figures
3. Mark figures stale when the code changes underneath them
4. Alert on divergence
5. Publish a verification timestamp per figure
6. Withdraw figures that cannot be reproduced
7. Have a second reviewer verify the boldest claims
8. Verify the bi-temporal claim against the actual code
9. Verify the grounded-firewall claim against real enforcement
10. Verify the benchmark comparability claim against the report
11. Verify the root README counts against the live index
12. Publish verification outcomes including every failure
13. Review the gate output with a human
14. Withdraw published figures that cannot be reproduced
15. Alert whenever a published figure diverges from a re-run
16. Publish verification outcomes including every failure found
17. Verify the bi-temporal and grounded-firewall claims against real enforcement
18. Schedule re-verification so drift is caught without manual action
19. Verify withdrawal actually removes the stale figure
20. Record who verified each claim and when
21. Publish which figures are currently stale
22. Ensure a withdrawn figure is visibly marked in the report
23. Verify re-verification compares against the same corpus version

### `T03` — Estate-wide quality gate and honest reporting

**Problem (verified):** No single gate covers the estate, and several claims across READMEs are unverified. The honest gap report is exactly the thing most likely to be quietly omitted when a gate looks nearly green.

**Done when:** One gate covers packaging, tests, docs and benchmarks, and every gap is reported rather than smoothed over.

**Roadmap:**

1. Define a single estate-wide quality gate
2. Include packaging verification
3. Include the test suite result
4. Include README presence and packaging wiring
5. Include the benchmark smoke suite
6. Include the drift check
7. Report every failure with the organ explicitly named
8. Never suppress a failure to make the gate green
9. Publish the gap report with exact counts
10. Keep a written known-gaps document current
11. Include README presence and packaging wiring in the gate
12. Include the benchmark smoke suite so quality regressions are caught
13. Publish the gap report with exact measured counts
14. Never suppress a failure to make the gate look green
15. Ensure gate failures name the organ and the failing check
16. Publish gate history so regressions are traceable
17. Ensure the gate names the failing check, not only the organ
18. Publish the gate result as part of the canonical status
19. Ensure gate output is machine-readable
20. Verify the gate exits non-zero on failure

## Domain V. Long-Term Architecture

### `U01` — Consolidate duplicate temporal implementations and the orphaned entries mirror

**Problem (verified):** remember() now requires epistemic_status and breaks every caller that omits it: 11 of 14 bi-temporal tests fail on memory.py:541 with zero occurrences of the field in the test file. This is the same class of drift as two competing temporal implementations, and it is the one that is actively red right now.

**Done when:** The remember()/epistemic_status contract break is repaired with all 14 bi-temporal tests green, one authoritative temporal implementation serves every path, and the orphaned mirror is reconciled or removed with the decision documented.

**Roadmap:**

1. Decide which temporal implementation is authoritative
2. Wire it into every retrieval path
3. Remove the duplicate implementation
4. Verify no regression in temporal correctness
5. Verify all 14 bi-temporal tests still pass
6. Verify the organ's 54 tests still pass
7. Document the consolidation
8. Determine what the orphaned mirror is and who created it
9. Reconcile the 16 overlapping records
10. Archive or remove the 563 non-overlapping files
11. Verify nothing unique is lost before removing
12. Document the decision
13. Verify nothing unique is lost before removing any orphaned file
14. Reconcile the 16 overlapping records against the live store
15. Verify both temporal test suites pass after consolidation
16. Document the consolidation decision and its rationale
17. Verify consolidation does not change temporal query results
18. Verify the orphaned mirror decision is reversible
19. Verify both temporal suites remain green after consolidation
20. Ensure no duplicate temporal code remains

### `U02` — Single retrieval engine, registry accuracy and dependency hygiene

**Problem (verified):** Several subsystems likely carry their own retrieval, and duplicated retrieval implementations drift into separate quality problems. The sitemap reports 329 subsystems while 300 organs exist on disk with 2 entries resolving to nothing, so the index is not fully accurate. And 300 organs have no dependency audit.

**Done when:** Retrieval implementations are inventoried and consolidated, the sitemap is accurate against disk, and dependencies are audited and pinned.

**Roadmap:**

1. Inventory retrieval implementations across the estate
2. Decide which are authoritative
3. Consolidate or clearly scope each
4. Verify quality is consistent across subsystems
5. Reconcile sitemap entries against disk
6. Fix the 2 entries that resolve to nothing
7. Handle case-variant naming correctly
8. Verify sitemap test-file counts against disk
9. Add a CI check for index drift
10. Inventory dependencies across all organs
11. Detect version conflicts
12. Pin versions where reproducibility matters
13. Detect abandoned dependencies
14. Add a dependency audit to CI
15. Document the architecture and the index scope
16. Add a CI check for sitemap index drift against disk
17. Add a dependency audit to CI and pin versions where reproducibility matters
18. Document the index scope and which roots are included
19. Verify quality is consistent across subsystems after consolidation
20. Verify every registry entry resolves to real on-disk code

### `U03` — Interface stability and the roadmap to 10,000 facts

**Problem (verified):** Public surfaces change without notice so consumers cannot rely on anything. And growth from 449 to 1500 to 10000 facts must be sustained, but no plan covers the intermediate stages or the operational reality of running them.

**Done when:** Stability tiers are defined and enforced, and each growth milestone has a quality bar, latency bar and a gate that must pass to advance.

**Roadmap:**

1. Define stability tiers for public surfaces
2. Mark each surface with its tier
3. Require deprecation notices before changes
4. Add contract tests per tier
5. Document the interface stability policy
6. Define growth milestones: 1500, 5000, 10000 and 50000 facts
7. Define the quality bar at each milestone
8. Define the latency bar at each milestone
9. Define the storage budget at each milestone
10. Define the operational requirements at each milestone
11. Define the gate that must pass to advance
12. Measure at each milestone and publish the results
13. Document the plan honestly including its risks
14. Publish measured results at each growth milestone as they are reached
15. Document the roadmap honestly including known risks
16. Require the gate to pass before advancing to the next milestone
17. Verify every public surface carries a stability tier
18. Verify each milestone gate is machine-checkable
19. Publish progress against each milestone target
20. Ensure each milestone has a named owner and gate

## Domain W. Advanced Retrieval Quality

### `X01` — Query-level cache warming and index warm-start on cold boot

**Problem (verified):** Startup loads the FAISS vector index (685 KB), the BM25 index (217 KB) and a 3.19 MB graph, and the embedding model may need a cold HF cache resolve that blocks. Nothing measures warm versus cold behaviour, so first-query latency is unpredictable and can include a hang.

**Done when:** Cold and warm start are measured separately and first-query latency is bounded and predictable.

**Roadmap:**

1. Measure cold-start time with an empty model cache
2. Measure warm-start time with a populated model cache
3. Measure per-index load cost for vector, BM25 and graph
4. Pre-resolve the embedding model path at install time
5. Warm the index in the background rather than blocking startup
6. Measure first-query latency separately from steady state
7. Bound the first-query latency so it cannot hang
8. Fail fast with a typed error rather than hanging when offline
9. Verify warm-start never returns partial results
10. Publish cold versus warm start numbers honestly
11. Document the startup contract for operators
12. Add a warm-start regression test
13. Measure whether pre-resolving the model path actually removes the hang
14. Verify a warm index never serves results from a superseded generation
15. Test warm-start behaviour with no network and no model cache
16. Ensure warm-start never masks a genuine index inconsistency
17. Verify a cold start with no network fails fast, never hangs
18. Document the operator-visible difference between cold and warm
19. Publish warm-start as a measured benchmark figure
20. Ensure startup cannot block on an unbounded network call

### `X02` — Negative-result analysis: why queries return nothing

**Problem (verified):** Nothing distinguishes a query that found nothing because the fact is absent from one that found nothing because of an indexing failure. For a trust-first system, a silent empty result is indistinguishable from data loss, and both look identical to a caller.

**Done when:** Every empty result carries a reason code distinguishing absent from unindexed from filtered from abstained.

**Roadmap:**

1. Define empty-result reason codes
2. Distinguish genuinely absent from present-but-unindexed
3. Distinguish filtered by namespace or ACL from genuinely absent
4. Distinguish abstained by confidence threshold from no candidate
5. Distinguish superseded from never existed
6. Return the reason code in every empty result envelope
7. Measure how often each reason occurs in practice
8. Fix any case where an unindexed fact reads as absent
9. Alert when the unindexed case occurs unexpectedly often
10. Document the empty-result contract in the API README
11. Test every reason code is reachable and correctly produced
12. Publish the reason-code distribution in the trust report
13. Distinguish an empty namespace from an empty corpus
14. Distinguish a filtered-by-trust-threshold empty from a genuinely empty one
15. Report how often unindexed-present facts are found and repaired
16. Make the reason code machine-readable in the JSON envelope
17. Add a dashboard panel showing empty-result reason distribution
18. Verify reason codes never leak internal state to callers
19. Verify reason codes survive JSON serialisation
20. Document every empty-result reason in the API reference
21. Verify the reason code is stable across versions

### `X03` — Ranking stability: reproducible results under equivalent queries

**Problem (verified):** Total, deterministic ordering is claimed by the temporal organ, but no test proves that semantically equivalent queries return byte-identical result order. Silent tie-breaking differences make benchmark numbers irreproducible and trust claims unverifiable.

**Done when:** Equivalent queries provably return byte-identical ordered results, verified by property test.

**Roadmap:**

1. Define total ordering semantics for ties
2. Make tie-breaking explicit and documented
3. Test identical queries return identical ordering
4. Test reordered-equivalent queries return identical ordering
5. Test paraphrased queries return a stable top set
6. Test case-folding does not change ordering unexpectedly
7. Remove any dependence on dict or set iteration order
8. Remove any dependence on wall-clock time in ranking
9. Remove any dependence on random seeds not explicitly pinned
10. Verify determinism survives an index rebuild
11. Verify determinism survives a process restart
12. Publish the determinism guarantee precisely
13. Verify determinism across a fresh process, not just within one
14. Pin any implicit ordering dependency found in the codebase
15. Verify determinism holds on a different machine or CPU
16. Report the determinism guarantee in the API docs
17. Publish the determinism test as part of the benchmark suite
18. Verify determinism is unaffected by index growth
19. Ensure ties are broken by a documented total order
20. Verify ordering is stable across repeated benchmark runs

### `X04` — Retrieval budget enforcement: bounded work per query

**Problem (verified):** Graph traversal and multi-hop decomposition can in principle expand without bound. There is no enforced budget, so a pathological query could consume unbounded time or memory, which on a shared box means one agent degrades every other agent.

**Done when:** Every query has a hard, tested budget for hops, edges examined, sub-queries and wall time.

**Roadmap:**

1. Define a per-query budget for hops
2. Define a budget for edges examined during traversal
3. Define a budget for decomposition sub-queries
4. Define a wall-clock budget per query
5. Enforce budgets in code, not only through configuration
6. Return partial results when a budget is exhausted, with a flag
7. Never silently truncate without signalling it
8. Test budget enforcement on a dense synthetic graph
9. Test budget enforcement on a cyclic graph
10. Measure how often budgets are hit in practice
11. Alert when budgets are hit unusually often
12. Make budgets configurable per agent
13. Measure budget-exhaustion frequency per query kind
14. Ensure budget exhaustion is reported, never silent
15. Verify partial results still carry full provenance
16. Document recommended budget defaults per agent type
17. Verify budgets hold for adversarial queries too
18. Verify budget exhaustion returns partial results, never an error
19. Ensure budgets cannot be disabled silently by an agent
20. Ensure budgets are enforced rather than merely configured

### `X05` — Schema and field weighting: topic, tags, content and actor

**Problem (verified):** Fields are treated as flat concatenated text for BM25 and a single blob for embedding, so a topic match scores the same as a content match. Structured fields carry different reliability and nothing exploits that.

**Done when:** Field-weighted retrieval is implemented and measured against flat concatenation on the labelled set.

**Roadmap:**

1. Define field weights for topic, tags, content and actor
2. Measure a topic match against an equivalent content match
3. Implement field-weighted BM25 scoring
4. Implement field-aware embedding or a field-priority fallback
5. Tune weights on a labelled probe set
6. Verify tag-exact matches outrank incidental token matches
7. Measure the effect on multi-hop and direct queries
8. Verify quality does not regress on any query kind
9. Make field weights configurable
10. Publish the measured field-weight effects
11. Document the field semantics in the API README
12. Add a regression test pinning field-weight ordering
13. Verify actor matches never outrank content matches improperly
14. Measure field-weight sensitivity on the labelled set
15. Document which fields are authoritative when they conflict
16. Verify field weighting never demotes a correct answer
17. Ensure field weights are published in the benchmark output
18. Verify field weighting holds under multi-hop queries
19. Verify field weighting is applied in every retrieval mode
20. Ensure field weights are versioned with the schema

### `X06` — Bench harness honesty: no metric that cannot detect a real failure

**Problem (verified):** A benchmark that cannot distinguish a correct abstention from a retrieval failure is worse than no benchmark, because it reports failure where the system is correct and success where it is not. The current adversarial hit_rate 0.000 cannot tell which happened.

**Done when:** Every published metric provably detects an induced failure before it is trusted as a gate.

**Roadmap:**

1. For each metric, induce the failure it claims to detect
2. Confirm the metric actually moves when the failure is induced
3. Confirm the metric returns to baseline when the failure is removed
4. Discontinue any metric that cannot detect its own target failure
5. Add a meta-test asserting each metric is failure-sensitive
6. Document which failure each metric is validated against
7. Publish the induced-failure results alongside normal results
8. Report metrics that could not be validated rather than hiding them
9. Review every published number for this failure mode
10. Require new metrics to pass validation before use as a gate
11. Keep the validation procedure documented and reproducible
12. Re-validate every metric after a corpus change
13. Re-validate every metric after the corpus grows to 1500
14. Publish which metrics are gate-worthy versus informational
15. Remove any metric that failed validation from the gate
16. Keep induced-failure validation as a required CI step
17. Publish a re-validation date for every metric
18. Ensure an unvalidated metric can never gate a release
19. Document the induced-failure proof for the headline metrics
20. Ensure validation covers the abstention metric specifically

### `X07` — Honest 0-to-1 roadmap: measurable retrieval improvement targets

**Problem (verified):** The project claims to win on retrieval quality and trust, but no target exists, so improvement cannot be demonstrated and regression cannot be defined. Published numbers on a 13-query corpus cannot anchor any goal.

**Done when:** Every retrieval and trust goal has a numeric target, a reproducible measurement command, and a published current value beside it.

**Roadmap:**

1. Set a numeric target for direct-query MRR on the 1500-fact corpus
2. Set a numeric target for multi-hop MRR above the current 0.640
3. Set a numeric target for adversarial correct-abstention rate
4. Set a numeric target for latency at the 1500-fact corpus
5. Set a numeric target for contamination rate remaining at exactly 0.0
6. Set a numeric target for provenance coverage
7. Set a numeric target for cross-namespace leakage remaining at 0
8. Define how each target will be measured reproducibly
9. Publish current measured values beside every target
10. Review progress against targets at each release
11. Report honestly when a target is missed rather than lowering it silently
12. Never state a target as achieved without the measured evidence
13. Publish the gap between current value and every target
14. Make target tracking a release checklist item
15. Verify each target has a reproducible measurement command
16. Report missed targets honestly at each review
17. Review targets with a human before each release
18. Ensure every target maps to exactly one measured metric
19. Publish target achievement only with its evidence attached
20. Ensure each target has a named reproducible command
