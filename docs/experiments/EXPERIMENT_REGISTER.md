# mem20 4.0 — Experiment Register

**Release:** mem20 `4.0.0` · **Branch:** `main` · **Baseline:** `0224a64946a2c00313a9872515893157adcbc47e`
**Generated:** 2026-11-16T13:01:39Z · **Owner of this register:** Experiment Tracker
**Machine-readable twin:** [`register.json`](./register.json) — same ids, same metrics, built to be diffed.

> **Sourcing rule.** Every baseline below is read from a committed artifact or produced by a
> command this register names. No figure is hand-typed, estimated, or carried over from a chat
> message. Regenerate with `python3 docs/experiments/build_register.py`; check it with
> `python3 docs/experiments/verify_register.py`.

## Headline

| | Count |
|---|---:|
| Open hypotheses | **10** |
| Accepted | 0 |
| Rejected | 0 |
| Distinct owners | 6 |
| Hypotheses with no owner | **1** |

Every hypothesis is **open**. None has been accepted or rejected, because none has a
completed measurement against its target yet. A register that showed decisions here would be
claiming results that do not exist.

## Register

| ID | Hypothesis | Owner | Metric | Baseline | Target | Status |
|---|---|---|---|---:|---:|---|
| `H-4.0-01` | Criterion-6 wiring is the binding constraint on 4.0 conformance | Server Builder | subsystems passing criterion 6 (cross_ok) | 1 | 67 | **open** |
| `H-4.0-02` | Cross-encoder reranking is a net loss on multi-hop retrieval | AI Engineer | multi_hop hit rate, hybrid vs hybrid-rerank-off | 0.5333 | 1.0 | **open** |
| `H-4.0-03` | Graph traversal is not competitive on the scale corpus | Mem20 Benchmark Dataset Builder | graph multi_hop hit rate | 0.0333 | 0.8 | **open** |
| `H-4.0-04` | Bi-temporal recall_at is the largest unmeasured trust claim | AI Engineer | recall_at scored rows in the benchmark of record | 0 | 1 | **open** |
| `H-4.0-05` | main is release-clean enough to tag v4.0.0 | GitHub Repo Assistant | red check runs on main HEAD | 3 | 0 | **open** |
| `H-4.0-06` | Two subsystems are below the 6/7 floor and block the wave-2 exit | UNASSIGNED | lowest conformance score among discovered subsystems | 5 | 6 | **open** |
| `H-4.0-07` | Every discovered subsystem has a named owner | Mem20-admin | discovered subsystems with no owner row | 4 | 0 | **open** |
| `H-4.0-08` | The published tool surface matches the registered surface | Server Builder | unwired tools in the published surface | 19 | 0 | **open** |
| `H-4.0-09` | Keyless LLM coverage is sufficient for the 4.0 default path | AI Engineer | verified keyless chat providers | 3 | 5 | **open** |
| `H-4.0-10` | The conformance gate's discovery set is stable | Mem20-admin | subsystems discovered by the gate | 67 | 211 | **open** |

## Detail

### `H-4.0-01` — Criterion-6 wiring is the binding constraint on 4.0 conformance

**Hypothesis.** If a subsystem imports and uses >=5 other mem20 modules, it reaches 7/7 on the renovation gate; the program's conformance ceiling is therefore set by criterion 6, not by missing domain logic.

**Owner.** Server Builder — wave-1 owner of mcp / mem20_mcp / gateway (RENOVATION_PLAN.md §4)

**Subsystems.** `mcp`, `mem20_mcp`, `gateway`, `mem20meshz`

| Metric field | Value |
|---|---|
| Name | subsystems passing criterion 6 (cross_ok) |
| Baseline | **1** |
| Denominator | 67 |
| Target | 67 |
| Unit | subsystems |
| Source | `scripts/renovation/conformance.py --all` |

**Evidence.**
- criterion 6 passes on 1/67 subsystems
- 66/67 subsystems fail exactly this criterion and nothing else
- docs/renovation/4.0/RENOVATION_PLAN.md §2.1 records 7/211 at the 2026-11-01 baseline

**Decision rule.** Accept when cross_ok >= 90% of discovered subsystems; reject if the rate is unchanged after wave-1 lands.

**Next action.** Land the wave-1 exit gate (mcp, memory_engine, toolchest, gateway, mem20corez at 7/7) and re-run the gate.

### `H-4.0-02` — Cross-encoder reranking is a net loss on multi-hop retrieval

**Hypothesis.** Disabling the cross-encoder (hybrid-rerank-off) raises multi_hop hit rate and cuts p50 latency versus the default hybrid path, so reranking should not be on by default.

**Owner.** AI Engineer — owner of memory_engine and mem20agentz (RENOVATION_PLAN.md §4)

**Subsystems.** `memory_engine`, `mem20agentz`

| Metric field | Value |
|---|---|
| Name | multi_hop hit rate, hybrid vs hybrid-rerank-off |
| Baseline | **0.5333** |
| Comparator | 1.0 |
| Baseline p50 | 1797.13 ms |
| Comparator p50 | 27.3 ms |
| Target | 1.0 |
| Unit | hit rate |
| Source | `benchmarks/results/latest.json recall.<mode>.multi_hop.hit_rate + latency_ms.<mode>.p50` |

**Evidence.**
- hybrid multi_hop = 0.5333 at p50 1797.13 ms
- hybrid-rerank-off multi_hop = 1.0 at p50 27.3 ms
- vector multi_hop = 1.0 at p50 204.94 ms

**Decision rule.** Accept if rerank-off holds multi_hop >= 0.95 and p50 <= 100 ms across a second corpus; reject on any direct-kind regression.

**Next action.** Re-run the 7-mode benchmark on a second corpus before flipping the default; one corpus is not enough to change a shipped default.

### `H-4.0-03` — Graph traversal is not competitive on the scale corpus

**Hypothesis.** Graph traversal underperforms every text mode on multi_hop because the corpus has no entity-anchored multi-hop probes; the 1.000 figure in the README comes from a 13-query corpus.

**Owner.** Mem20 Benchmark Dataset Builder — owner of mem20benchmarkz (RENOVATION_PLAN.md §4)

**Subsystems.** `mem20benchmarkz`

| Metric field | Value |
|---|---|
| Name | graph multi_hop hit rate |
| Baseline | **0.0333** |
| Target | 0.8 |
| Unit | hit rate |
| Source | `benchmarks/results/latest.json recall.graph.multi_hop.hit_rate` |

**Evidence.**
- graph multi_hop = 0.0333 on n=30 probes
- vector multi_hop = 1.0 on the same corpus
- docs/benchmarks/experiment-registry.md §1 records the 13-query vs 250-query discrepancy

**Decision rule.** Accept the corpus-gap explanation if entity-anchored probes lift graph above 0.80; otherwise treat graph as a regression.

**Next action.** Add entity-anchored multi-hop probes to the corpus generator, then re-score graph.

### `H-4.0-04` — Bi-temporal recall_at is the largest unmeasured trust claim

**Hypothesis.** recall_at is unit-tested but never benchmark-scored, so the bi-temporal correctness that the trustworthiness claim rests on has no measured row.

**Owner.** AI Engineer — owner of memory_engine, where recall_at is implemented

**Subsystems.** `memory_engine`

| Metric field | Value |
|---|---|
| Name | recall_at scored rows in the benchmark of record |
| Baseline | **0** |
| Target | 1 |
| Unit | scored modes |
| Source | `benchmarks/results/latest.json mode_surface` |

**Evidence.**
- docs/benchmarks/experiments.json modes[id=recall_at].scored = false
- blocker: corpus carries no as-of anchor, so there is no gold record
- tests/test_recall_at_bitemporal.py exists but is not a benchmark

**Decision rule.** Accept when recall_at has a scored row with n>0 and a committed artifact; a scored flag without a measurement is a false promotion.

**Next action.** Add an as-of query kind to the corpus generator and a _run_mode branch in bench.py.

### `H-4.0-05` — main is release-clean enough to tag v4.0.0

**Hypothesis.** VERSION on main reads 4.0.0 but no v4.0.0 tag exists and three check runs are red, so the release is not taggable until those checks are green.

**Owner.** GitHub Repo Assistant — owner of CI/check-run state and tag hygiene in the roster

**Subsystems.** `mcp`, `mem20api`

| Metric field | Value |
|---|---|
| Name | red check runs on main HEAD |
| Baseline | **3** |
| Target | 0 |
| Unit | check runs |
| Source | `GitHub check-runs API for the main HEAD SHA` |

**Evidence.**
- VERSION = 4.0.0 on main
- no v4.0.0 tag exists; latest semver tag is v3.1.2
- red: MCP handshake (shallow clone), Tests, artifact evidence

**Decision rule.** Accept when all check runs on main HEAD are green and a v4.0.0 tag points at that SHA.

**Next action.** Fix the three red checks, then tag v4.0.0 at the green SHA.

### `H-4.0-06` — Two subsystems are below the 6/7 floor and block the wave-2 exit

**Hypothesis.** mem20portalz and mem20webgpuz sit at 5/7, below every other discovered subsystem, and must reach 6/7 before wave 2 can be declared complete.

**Owner.** UNASSIGNED — neither subsystem appears in subsystem-assignments.csv — needs an owner decision

**Subsystems.** `mem20portalz`, `mem20webgpuz`

| Metric field | Value |
|---|---|
| Name | lowest conformance score among discovered subsystems |
| Baseline | **5** |
| Target | 6 |
| Unit | criteria passed of 7 |
| Source | `scripts/renovation/conformance.py --all` |

**Evidence.**
- mem20portalz = 5/7, failing tests, cross_ok
- mem20webgpuz = 5/7, failing domain_logic, cross_ok
- neither has a row in docs/renovation/4.0/subsystem-assignments.csv

**Decision rule.** Accept when no discovered subsystem scores below 6/7.

**Next action.** Assign an owner in subsystem-assignments.csv, then close the failing criteria.

### `H-4.0-07` — Every discovered subsystem has a named owner

**Hypothesis.** The gate discovers subsystems that the owner map does not cover, so the renovation plan's claim that all subsystems are assigned is false at this commit.

**Owner.** Mem20-admin — author of RENOVATION_PLAN.md and the assignment CSV

**Subsystems.** `mem20api`, `mem20portalz`, `mem20webgpuz`, `teamz`

| Metric field | Value |
|---|---|
| Name | discovered subsystems with no owner row |
| Baseline | **4** |
| Target | 0 |
| Unit | subsystems |
| Source | `conformance gate vs subsystem-assignments.csv` |

**Evidence.**
- gate discovered 67 subsystems; CSV has 175 rows
- unassigned: mem20api, mem20portalz, mem20webgpuz, teamz

**Decision rule.** Accept when every subsystem the gate discovers has an owner and branch in the CSV.

**Next action.** Add the missing rows to subsystem-assignments.csv with owner, wave and branch.

### `H-4.0-08` — The published tool surface matches the registered surface

**Hypothesis.** docs/surface.json is the published contract; if the number of registered tools drifts from it, clients bind to a surface the server does not serve.

**Owner.** Server Builder — owner of mcp and the tool surface

**Subsystems.** `mcp`, `mem20_mcp`

| Metric field | Value |
|---|---|
| Name | unwired tools in the published surface |
| Baseline | **19** |
| Target | 0 |
| Unit | tools |
| Source | `docs/surface.json unwired_tools` |

**Evidence.**
- surface.json declares 487 tools across 129 domains
- 19 tools are declared but unwired
- cross_check: {"ast_domains": 129, "ast_tools": 487, "only_ast": [], "only_live": []}

**Decision rule.** Accept when unwired_tools is empty and the AST/live cross-check agrees.

**Next action.** Wire or remove the unwired tools, then regenerate surface.json.

### `H-4.0-09` — Keyless LLM coverage is sufficient for the 4.0 default path

**Hypothesis.** Three verified keyless chat providers plus local vision/embed/TTS/ASR are enough to run the default path without an API key; the remaining gap is model size, not provider count.

**Owner.** AI Engineer — owner of mem20agentz / mem20dreamz / mem20kilnz keyless rewire

**Subsystems.** `mem20agentz`, `mem20dreamz`, `mem20kilnz`

| Metric field | Value |
|---|---|
| Name | verified keyless chat providers |
| Baseline | **3** |
| Target | 5 |
| Unit | providers |
| Source | `TODO.md 2026-11-11 keyless LLM rewire` |

**Evidence.**
- TODO.md: only 3 chat entries verified (pollinations, ollama-qwen, ollama-gemma)
- TODO.md: mem20kilnz live engine verification blocked — engine source dir missing
- TODO.md: mem20dreamz idle loop saturates the box (4x180s concurrent calls)

**Decision rule.** Accept at 3 if the default path never needs a key; reject if any shipped route still requires one.

**Next action.** Decide whether 3 providers is the 4.0 bar; if yes, close the TODO with that rationale.

### `H-4.0-10` — The conformance gate's discovery set is stable

**Hypothesis.** The gate discovers 67 subsystems at this commit while the 2026-11-01 plan recorded 211, so either discovery changed or the plan's baseline is stale; conformance rates are not comparable until this is resolved.

**Owner.** Mem20-admin — author of the renovation plan and the gate

| Metric field | Value |
|---|---|
| Name | subsystems discovered by the gate |
| Baseline | **67** |
| Comparator | 211 |
| Target | 211 |
| Unit | subsystems |
| Source | `conformance gate vs RENOVATION_PLAN.md §2` |

**Evidence.**
- gate discovered 67 subsystems at this commit
- RENOVATION_PLAN.md §2 records 211 at d99ab5d8 (2026-11-01)
- issue #182 already tracks a stale conformance table

**Decision rule.** Accept the 67 figure once the discovery rule is documented; until then report both numbers and do not compare rates across them.

**Next action.** Document the discovery rule in the gate and regenerate the plan's baseline table.

## Measured context

### Conformance gate

`scripts/renovation/conformance.py --all` discovered **67** subsystems at this commit.

| Score | Subsystems |
|---|---:|
| 5/7 | 2 |
| 6/7 | 64 |
| 7/7 | 1 |

| # | Criterion | Passing | Rate |
|---|---|---:|---:|
| 1 | Domain logic present | 66 / 67 | 98.5% |
| 2 | No stubs | 67 / 67 | 100.0% |
| 3 | Tests present | 66 / 67 | 98.5% |
| 4 | CLI surface | 67 / 67 | 100.0% |
| 5 | Registered with MCP/gateway | 67 / 67 | 100.0% |
| 6 | README with runnable example | 67 / 67 | 100.0% |
| 7 | >=5 other mem20 modules imported and used | 1 / 67 | 1.5% |

### Retrieval benchmark of record

| Mode | multi_hop hit rate | p50 ms |
|---|---:|---:|
| `bm25` | 0.8 | 102.2 |
| `vector` | 1.0 | 204.94 |
| `hybrid` | 0.5333 | 1797.13 |
| `hybrid-rerank-off` | 1.0 | 27.3 |
| `graph` | 0.0333 | 208.4 |
| `keyword` | 0.4667 | 1692.2 |
| `constant` | 0.0 | 0.0 |

### Published surface

- `docs/surface.json`: **487 tools across 129 domains**, 19 unwired.

## What this register does not claim

- It does not claim any hypothesis is validated. All ten are open.
- It does not re-measure retrieval. Those numbers are read from `benchmarks/results/latest.json`.
- It does not reconcile the 67-vs-211 subsystem count; `H-4.0-10` exists because that gap is unresolved.
- It does not assign owners to unowned subsystems; `H-4.0-06` and `H-4.0-07` record the gap instead.

---
**Experiment Tracker** · 2026-11-16T13:01:39Z · statistical confidence: not applicable — this is a register of open hypotheses, not a measurement.
