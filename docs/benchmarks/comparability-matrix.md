# Benchmark comparability matrix

**Status:** reference document. Replaces the prose caveat in `benchmarks/results/latest.md` with a sourced, per-figure verdict.
**Compiled:** 2026-10-27. **Baseline `main`:** `1264076698a00878acc3adacf7bf1d51eea315cc`.

---

## 1. What this document is for

`benchmarks/results/latest.md` carries this warning:

> **These numbers are not comparable to competitor benchmarks.** Mem0's LoCoMo (92.5) and LongMemEval (94.4) figures and Zep's DMR (94.8%) come from different corpora — two of the three are private or vendor-defined — and different metrics. Nothing here refutes or reproduces them. These results describe this corpus only.

A warning in prose is unfalsifiable and unhelpfully vague: a reader cannot tell *which* part of a comparison breaks, or how badly. This document resolves each competitor figure into four attributes — **corpus, metric, source, verdict** — and states the specific mismatch. Every number below was read from the page or paper cited next to it; nothing is reconstructed from memory, and no figure is quoted that a source did not print.

Three figures are in scope, plus the reproductions that make the picture legible.

---

## 2. There are three independent axes of non-comparability, not one

The existing caveat collapses everything into "different corpora and different metrics." In fact each comparison breaks on up to three separate axes, and any one of them alone is disqualifying:

| Axis | What it means | Why it alone is disqualifying |
|---|---|---|
| **A — Corpus** | Which questions were asked, over what history, at what scale. | A hit rate over 13 queries and one over 1,540 answer different questions. Corpus size and question mix set the difficulty ceiling. |
| **B — Metric stage** | *Which stage of the pipeline the number measures.* Retrieval hit, or end-to-end answer correctness? | mem20 reports **retrieval** results — did the expected evidence appear in the top-k, with no reader model and no judge. Mem0 and Zep report **end-to-end QA accuracy** — a model read the retrieved context, wrote an answer, and a second model graded it. These are different quantities and neither bounds the other. |
| **C — Harness** | Answer model, judge model, retrieval budget (top-k), dataset variant/cleaning, prompt. | The same system on the same corpus moves by tens of points across harnesses — demonstrated below. |

Axis B is the one the current prose omits entirely, and it is the most important of the three: mem20's table has no answer-accuracy column at all.

---

## 3. The matrix

| # | Figure | Claimed by | Corpus (Axis A) | Metric (Axis B) | Harness (Axis C) | Source | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **LoCoMo 92.5** | Mem0 | LoCoMo public 10-conversation release, **1,540** questions, 4 of 5 categories | End-to-end QA accuracy, LLM-judge | Mem0 managed platform, v3 pipeline; top-200 retrieval; GPT-5 answerer + GPT-5 judge | `mem0ai/memory-benchmarks` README (92.5% = 1425/1540); `mem0.ai/research` | **Not comparable** (A, B, C) |
| 2 | **LongMemEval 94.4** | Mem0 | LongMemEval `_S`, **500** questions, 6 types, cleaned file | End-to-end QA accuracy, LLM-judge | top-200 retrieval; GPT-5 answerer + GPT-5 judge (472/500) | `mem0ai/memory-benchmarks` README (94.4% = 472/500) | **Not comparable** (A, B, C) |
| 3 | **DMR 94.8%** | Zep | DMR = **500-conversation subset of Multi-Session Chat**, ~60 messages each | End-to-end QA accuracy, LLM-judge | Zep/Graphiti; top-10 retrieved nodes + edges; GPT-4-turbo | arXiv 2501.13956v1 (§4, §4.2) | **Not comparable** (A, B, C) |
| 4 | mem20 `hybrid` direct **1.000**, multi-hop **0.800**, adversarial **0.000**; leak **0.000** | mem20 | `mem20-agent-kb-v1`: **14** grounded facts, 3 simulated, **13** queries | **Retrieval only** — hit@5, MRR, leak rate. No reader, no judge | `hybrid` mode, `k=5`, MiniLM-L6-v2 384-dim, cross-encoder on | `benchmarks/results/latest.md`, `benchmarks/results/latest.json` | **Reference row** |

Verdicts above are all *against mem20's row*. The cross-vendor pairs among rows 1–3 are also non-comparable to each other, which §5 shows empirically.

---

## 4. Per-figure detail — what each source actually printed

### 4.1 Mem0 LoCoMo 92.5

Read from `github.com/mem0ai/memory-benchmarks`, section **Results → Mem0 Platform → LoCoMo**:

> | Metric | Top 200 | Top 50 |
> | **Overall** | **92.5%** (1425/1540) | **91.8%** (1414/1540) |

So 92.5 is an **exact fraction with a stated denominator**: 1,425 of 1,540. The retrieval budget is explicit (`--top-k N  Retrieved memories count (default: 200)`), and the scoring path is stated:

> Ingest → Search → Evaluate … **Evaluate**: An LLM generates an answer from retrieved memories, then a judge LLM scores correctness against ground truth.

That is Axis B: the score includes an answer model and a judge. mem20's table includes neither.

**The 1,540 is not the whole benchmark.** The public LoCoMo release at `github.com/snap-research/locomo` contains **1,986** QA pairs across ten conversations; counting categories in `data/locomo10.json` gives `1: 282, 2: 321, 3: 96, 4: 841, 5: 446`. The arithmetic reconciles exactly — **1,986 − 446 (category 5, the adversarial class) = 1,540**. Mem0's denominator is the public release minus the adversarial category.

> **This is the sharpest single fact in this document.** Mem0's 92.5 is computed with the adversarial class excluded. mem20 reports **0.000** on its adversarial class. Setting "92.5" against mem20's adversarial "0.000" compares a number that excludes the category to a number that *is* that category. Any asset that puts those two in one row is making a category error, not a comparison.
>
> The subtraction is arithmetic performed on two figures actually read (1,986 total, 446 in category 5, 1,540 claimed); it is labelled as such and is not an independent measurement.

Also note the internal spread. Mem0's **research paper** (arXiv 2504.19413) is reported — by two secondary trackers that reproduce its protocol, not by my reading of its own table — to show LoCoMo **66.9** with GPT-4o-mini as both answerer and judge. Same corpus, same vendor, **25.6 points apart** from 92.5, with the difference being harness only (Axis C). Flagged as second-hand because I read the 92.5/1,425-of-1,540 figure at first hand but not the 66.9. Either way the conclusion holds: no cross-vendor LoCoMo row can be read as a ranking.

### 4.2 Mem0 LongMemEval 94.4

Read from the same README, section **Results → Mem0 Platform → LongMemEval**:

> | Metric | Top 200 | Top 50 |
> | **Overall** | **94.4%** (472/500) | **94.8%** (474/500) |

Denominator 500, matching LongMemEval's 500 human-curated questions (`arxiv.org/abs/2410.10813`, five core abilities). The vendor's stated configuration is a cleaned dataset file at a top-200 budget with GPT-5 as both answerer and judge.

**Number collision worth flagging:** Mem0's LongMemEval figure at top-50 is also **94.8** — the same digits as Zep's DMR 94.8% in row 3, on a different corpus, a different metric denominator (474/500 vs. an accuracy on a 500-conversation MSC subset), and a different vendor. Any table that matches "94.8" to "94.8" is matching two unrelated quantities. This collision is a strong argument for never publishing bare benchmark numbers without their corpus and harness attached.

**Independent reproductions of the same benchmark name diverge sharply.** A third-party evaluation widely cited in 2026 puts Mem0 at **49.0** on LongMemEval (GPT-4o configuration) against the 94.4 self-reported — a 45.4-point spread under one benchmark name. I did not obtain that source's dataset variant, top-k or prompt, so its configuration is **unknown** to me and I record its verdict as **unknown**, not as a refutation:

| Row | Figure | Provenance | Verdict |
|---|---|---|---|
| 4.2a | Mem0 LongMemEval **49.0** | Third-party evaluation, GPT-4o; dataset variant and retrieval config **not stated in material I read** | **Unknown** — cannot be located on all three axes, so it neither confirms nor refutes 94.4 |

Recording *why* it is unknown is the point: an unlocated number is not evidence, in either direction.

### 4.3 Zep DMR 94.8%

Read from arXiv 2501.13956v1. The corpus definition is explicit:

> The first evaluation employs the Deep Memory Retrieval (DMR) task developed in [3], which uses a **500-conversation subset of the Multi-Session Chat dataset** introduced in "Beyond Goldfish Memory: Long-Term Open-Domain Conversation" [22].

The measurement method:

> We then evaluated Zep's performance by ingesting the conversations and using its search functions to **retrieve the top 10 most relevant nodes and edges**. **An LLM judge** compared the agent's responses to the provided golden answers. Zep achieved **94.8% accuracy with gpt-4-turbo** and 98.2% with gpt-4o-mini …

And Zep's own limitation statement, which is unusually candid and should be carried verbatim by anyone quoting the number:

> However, these results must be contextualized: **each conversation contains only 60 messages, easily fitting within current LLM context windows.**

That last sentence is decisive. On a 60-message conversation the *entire history* fits in the context window, so a full-context baseline — no memory system at all — scores **94.4% with gpt-4-turbo** and **98.0% with gpt-4o-mini** in the same table. Zep's 94.8 is +0.4 over simply pasting everything in. DMR therefore measures almost nothing about memory architecture at this scale, which is precisely why Zep's paper pivots to LongMemEval. A DMR number cannot be set against a system evaluated on 13 queries over a 14-fact store — and, more usefully, it cannot be set against *anything* modern.

### 4.4 Zep LongMemEval-S (context row)

Same paper, Table 2 — included because it shows Axis C in isolation:

| Memory | Model | Score | Avg context tokens |
|---|---|---:|---:|
| Full-context | gpt-4o-mini | 55.4% | 115k |
| Zep | gpt-4o-mini | 63.8% | 1.6k |
| Full-context | gpt-4o | 60.2% | 115k |
| Zep | gpt-4o | 71.2% | 1.6k |

Zep's LongMemEval-S result is 71.2% (gpt-4o) / 63.8% (gpt-4o-mini). Note that the paper's headline framing is a **relative improvement** ("15.2% accuracy improvement … 18.5% improvement"), not a flat accuracy — an easy thing to misquote. Mem0's 94.4 and Zep's 71.2 are on the same benchmark family, so this pair is the *least* mismatched in this document on Axis A, and still differs on Axis C (answer model, judge, top-k, dataset cleaning), which is exactly why the 23-point gap is not attributable to architecture alone.

### 4.5 Letta LoCoMo 74.0% (context row)

Read from `letta.com/blog/benchmarking-ai-agent-memory` (12 Aug 2025):

> This simple agent achieves **74.0%** on LoCoMo with GPT-4o mini and minimal prompt tuning, significantly above Mem0's reported **68.5%** score for their top-performing graph variant.

Published as a direct rebuttal, with a methodology dispute attached: Letta states it could not backfill LoCoMo into MemGPT/Letta without significant refactoring, and that Mem0 did not respond to requests for clarification. The harness here is also *agentic* (the agent chooses how many times to call `search_files`, under tool rules) rather than Mem0's fixed single-pass top-200. So this row differs on Axis C twice over: model choice **and** a fundamentally different retrieval protocol.

The dispute resolves, for present purposes, into a single usable conclusion: **LoCoMo has no adjudicated result.** Mem0's replication scored Zep at 58.44; Zep revised its own LoCoMo figure to 75.14 ± 0.17 over 10 runs (`getzep/zep-papers` issue #5). Every LoCoMo number in circulation is a party's number.

### 4.6 mem20 — the reference row, stated plainly

From `benchmarks/results/latest.md` and `latest.json`:

- **Corpus:** `mem20-agent-kb-v1` — 14 grounded facts, 3 simulated facts, 13 queries. Per-kind `n` is 2–5.
- **Metric:** retrieval only. Per `mem20benchmarkz/mem20benchmarkz/bench.py`: `hit@k` is "fraction of answerable queries whose top-k results contain the expected evidence"; `mrr` is mean reciprocal rank; `leak@k` is "for adversarial queries, the fraction that returned any grounded support at all." Default `k=5`.
- **Measured:** `hybrid` direct 1.000 / multi-hop 0.800 / adversarial 0.000; leak rate 0.000; `semantic` and `keyword` comparable; `graph` on `n=2`.

Three consequences that follow directly:

1. **No answer model, no judge.** mem20's numbers stop at retrieval. Mem0's and Zep's start at retrieval and add two models. Even with a shared corpus these would not be the same quantity.
2. **13 queries.** At `n=5` a hit rate of 1.000 is five queries, not a confidence interval. The corpus is a CI regression gate by design, and the file says so.
3. **adversarial 0.000 is a real weakness on a 3-query slice.** It stays visible. This document exists to make it impossible to launder that row by pairing it with a competitor number computed *without* an adversarial class.

---

## 5. Correcting the existing warning

The prose caveat makes a specific factual claim: *"two of the three are private or vendor-defined."* On the evidence read for this document, that needs tightening:

| Corpus | Public? | What is actually vendor-defined |
|---|---|---|
| LoCoMo | **Public** — `snap-research/locomo`, 10-conversation release, CC BY-NC 4.0 per the paper | The harness: which of 5 categories, top-k, answer model, judge, prompt |
| LongMemEval | **Public** — arXiv 2410.10813, 500 questions | The harness: cleaned-vs-original file, top-200, GPT-5 answerer + judge |
| DMR | **Public-derived** — a 500-conversation subset of Multi-Session Chat | The **task definition and harness** — DMR was defined by the MemGPT team and re-run by Zep with its own top-10/LLM-judge setup |

I found **no private corpus** in any source I read. The accurate statement is stronger and more defensible:

> **All three corpora are public. What is vendor-defined in every case is the harness — the retrieval budget, the answer model, the judge model, and the dataset variant — and in one case (DMR) the task definition itself.** The corpora are not the barrier to comparison; the unstandardised harness is.

This matters practically: "we can't compare because the corpus is private" invites the reply "then run it on the public corpus." "We can't compare because there is no standardised harness, and the same vendor moves 25+ points across its own harnesses" is not answerable that way, and §4.1 and §4.4 both support it with figures.

---

## 6. What a reader may and may not conclude

**May conclude:**

- mem20 publishes retrieval hit-rate, MRR and leak rate on a 13-query internal corpus; it publishes no answer-accuracy figure.
- Mem0's LoCoMo 92.5 and LongMemEval 94.4 are end-to-end QA accuracies on public corpora, self-reported, under a stated vendor harness.
- Zep's DMR 94.8% is an end-to-end QA accuracy on 60-message MSC conversations, where a no-memory full-context baseline scored 94.4%.
- The published LoCoMo and LongMemEval figures across vendors span tens of points under differing harnesses, including within a single vendor.
- **Nothing in mem20's results refutes or reproduces any competitor figure, and no competitor figure refutes or reproduces mem20's.**

**May not conclude:**

- That mem20 is better or worse than Mem0, Zep or Letta on any benchmark. No shared corpus, no shared metric, no shared harness.
- That any competitor number in this document is wrong. Several are self-reported and two are actively disputed, but "disputed" is not "refuted" — the 49.0 row is recorded as *unknown* for exactly this reason.
- That a DMR comparison says anything about memory architecture at 60 messages.
- That mem20's adversarial 0.000 can be set beside a figure whose denominator excludes the adversarial class.

**Citation rule for any downstream asset:** every competitor number must travel with its corpus, its metric stage and its source. A bare "92.5" or "94.8" is not a citable fact — §4.2 shows the same digits meaning two unrelated things.

---

## 7. Method and sources

**Method.** Three disputed figures were traced to the page or paper that prints them. Corpus and metric attributes were taken from the source text, not inferred, except where explicitly labelled as arithmetic (§4.1 denominator reconciliation) or as a count performed on the public dataset file (§4.1 category tally). Where a source did not state a configuration attribute, the row's verdict is `unknown` rather than filled in by assumption.

**Sources read for this document:**

1. `github.com/mem0ai/memory-benchmarks` — README, Results §Mem0 Platform (LoCoMo, LongMemEval, BEAM tables), How It Works, Configuration.
2. `mem0.ai/research` — LoCoMo category scores, 1,540-question composition, token cost.
3. `arxiv.org/html/2501.13956v1` — *Zep: A Temporal Knowledge Graph Architecture for Agent Memory*: Abstract; §4 DMR corpus definition; §4.2 DMR results and limitation; §4.3.2 LongMemEval-S Table 2 and Table 3.
4. `letta.com/blog/benchmarking-ai-agent-memory` (12 Aug 2025) — Letta Filesystem 74.0% on LoCoMo; methodology dispute statement.
5. `github.com/snap-research/locomo` — release notes: ten conversations; 50-conversation initial release; subset rationale.
6. `arxiv.org/abs/2410.10813` — *LongMemEval*: 500 questions, five core abilities.
7. `github.com/getzep/zep-papers` issue #5 — Zep's revised LoCoMo 75.14 ± 0.17; 58.44 replication figure.
8. Repository files: `benchmarks/results/latest.md`, `benchmarks/results/latest.json`, `mem20benchmarkz/mem20benchmarkz/bench.py` (metric definitions, `k` default), `docs/benchmarks/README.md` §6.
9. `data/locomo10.json` from the public LoCoMo repository — conversation count and per-category QA tally.

**Not verified here:** the 49.0 LongMemEval reproduction's configuration (recorded as `unknown`); Mem0's own paper table (the 66.9 figure in §4.1 is second-hand, flagged inline); Zep's current research page (reports higher figures under conditions not covered by the arXiv paper read); any competitor's trustworthiness or contamination metric — **no competitor in this document publishes one**, which is the whole reason mem20's trust block has no column to sit in.

**Evidence standard for this file:** a figure is attributed first-hand only if the page or paper printing it was read during compilation. Everything else is labelled second-hand or `unknown` in place, and no figure was inferred to fill a gap in a row.
