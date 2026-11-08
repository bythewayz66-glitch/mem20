## 5. Long-form article (~1,500 words)

# Your agent's memory has no provenance. That's the bug.

Every team building an agent eventually hits the same wall, and it is never the wall they planned for. The plan is retrieval: embed the corpus, tune the index, measure recall, ship. Then the agent runs for three weeks and someone asks it a question about a customer, and it answers confidently, and the answer is wrong, and nobody can tell you where the wrong part came from.

That is not a retrieval failure. Retrieval worked. It found something relevant. The failure is that the system had no way to distinguish a fact it was told from a fact it invented, and no record of which was which.

### Retrieval quality is the wrong axis

The agent-memory market has converged on a single competitive axis: how good is your recall. Benchmarks measure hit rate on direct questions, multi-hop questions, adversarial questions. Vendors publish the flattering rows. It is a reasonable axis — if your problem is "the agent can't find the right document," better retrieval is the fix.

But most production failures are not "couldn't find it." They are "found it, plus something it made up, and presented both with identical confidence." A memory layer that stores an invented fact next to a real one, in the same table, with the same schema, has destroyed the only information that mattered: whether the fact was ever true.

You cannot recover that downstream. You can add a confidence score, but a confidence score is a model's opinion about its own output, which is exactly the thing you were trying to audit. You can add a prompt instruction — "never state anything you didn't retrieve" — and you have added a suggestion, not a constraint. Prompts are advisory. Storage is not.

### What a hard boundary looks like

mem20 is an MCP server that gives agents persistent memory. Its central design decision is that grounded memory and simulated memory are not a flag on a row. They are separate stores with separate write paths.

Grounded memory is content that came from a real source. Simulated memory is content the agent generated. When code tries to push invented content through the grounded write path, the server raises:

```
PermissionError: remember() is grounded-only. Simulated content must use
remember_simulated(); this call is refused to protect Step 7.4 separation.
```

That is the shipped exception string, not an illustration of one. The guard sits on the write path, which means it holds regardless of what any prompt says, what any model decides, or what any tool-calling chain does. It is the difference between a policy and a mechanism.

The second half of the boundary is labelling. Every write must declare how the content was learned: `observed`, `inferred`, `imagined`, `user_stated`, `hypothesis`, `agent_generated`, or `unlabeled`. An unlabeled write is refused. This closes the obvious loophole — a system that separates grounded from simulated is only as good as its ability to tell which is which, and the honest answer is that only the writer knows. So the writer has to say.

Promotion from simulated to grounded is not a flag flip. It goes through a gate that wants evidence: a recorded prior prediction that resolved in the agent's favour, or a registered external verifier. An agent cannot promote its own guess to a fact by asserting it more confidently.

### The audit is the product

Once provenance is structural, you can audit it. mem20 reports a `contamination_rate` for a store and lists the specific entries that violated the partition, across six violation classes. A clean store reports `0.0` and `CLEAN`.

On the shipped benchmark corpus — 700 grounded facts, 1,300 simulated facts, 250 queries — the measured trust properties are:

- `contamination_rate`: **0.0**
- ledger records: **700**
- degraded queries: **0** of 250
- graph entities: **654**, edges: **3,601**

These are not retrieval scores. They are properties of the store, and they are reproducible: clone the repo, run the audit, get the same numbers. That reproducibility is the actual deliverable. A vendor telling you their memory is trustworthy is marketing. A vendor shipping the audit you can run yourself is evidence.

### Now the part that doesn't flatter us

Here is the full retrieval benchmark, every row, six modes, six query classes, n in parentheses:

| mode | direct | multi-hop | adversarial | adv-hard | contradiction | unanswerable |
|---|---|---|---|---|---|---|
| `bm25` | **1.000** (60) | **0.800** (30) | **0.767** (60) | **0.025** (40) | **0.050** (40) | **0.000** (20) |
| `vector` | **0.900** (60) | **1.000** (30) | **0.667** (60) | **0.750** (40) | **1.000** (40) | **0.000** (20) |
| `hybrid` | **1.000** (60) | **0.533** (30) | **0.167** (60) | **0.050** (40) | **1.000** (40) | **0.000** (20) |
| `hybrid-rerank-off` | **1.000** (60) | **1.000** (30) | **0.650** (60) | **0.625** (40) | **1.000** (40) | **0.000** (20) |
| `keyword` | **1.000** (60) | **0.467** (30) | **0.167** (60) | **0.025** (40) | **0.125** (40) | **0.000** (20) |
| `graph` | — | **0.033** (30) | — | — | — | — |

Three things to take from it.

**Direct recall is solved and therefore uninteresting.** Three modes hit 1.000. If your problem is "find the fact I stored," any of them works.

**Multi-hop is the real weakness, and it is mode-dependent.** Graph retrieval scores 0.033 — it is nearly useless on this corpus. Vector and hybrid-rerank-off score 1.000. Hybrid with reranking on scores 0.533, which is worse than either of its components, a result worth its own investigation. Anyone who tells you their memory layer is uniformly strong on multi-hop is either not measuring it or not publishing it.

**Abstention fails completely.** Unanswerable questions score **0.000 in every single mode**, n=20. Not one mode, not one weak configuration — all six. A memory system that cannot say "I don't know" is a confabulation engine with a database attached. Ours is not there yet, and the honest framing is that provenance enforcement and abstention are different problems: we solved the first and have not solved the second.

We publish this because a benchmark you only show when it flatters you is not a benchmark. It is a brochure.

### What this is for, and what it isn't

mem20 is for teams building agents where being wrong is expensive and being unable to explain why is worse: regulated industries, internal knowledge systems, anything with an auditor on the other end. The value is that when the agent says something, you can trace it to a store, an origin, and a ledger entry — and when it invents something, the invention is quarantined where you can see it.

It is not the strongest retrieval system available, and the table above is why we can say that without hedging. If your only requirement is recall on a clean corpus, a well-tuned vector index will serve you and cost you less.

### Getting started

Source install only — there is no PyPI package:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
python mcp/mcp_server.py
```

311 tools across 39 domains. MIT. Python 3.10+. JSON-RPC 2.0 over stdio. Self-hosted.

Repo: https://github.com/bythewayz66-glitch/mem20
Site: https://mem20.com/

---

## 6. README / install block

```markdown
## Install

mem20 is installed from source. There is no PyPI package — `mem20`, `mem20-ai`
and `mem20oreo` all return 404 on pypi.org, so any `pip install` of the project
name will fail.

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
python mcp/mcp_server.py
```

Requires Python 3.10+. `requirements.txt` pins the full runtime set, including
`aiohttp` and `mcp-types`, which the server imports at module scope — a clean
install of the manifest is sufficient to boot.

Verify the surface after install:

```bash
python verify_mcp.py     # expects TOOL_COUNT: 311, RESULT: PASS
```

## What it is

An MCP memory server with a hard, storage-level partition between grounded
memory (came from a real source) and simulated memory (the agent generated it).
The grounded write path raises `PermissionError` on invented content. Every write
declares its origin and lands in an append-only ledger.

311 tools across 39 domains · MIT · JSON-RPC 2.0 over stdio.

## Benchmark

Full results in `benchmarks/results/latest.json` (250 queries, 700 grounded /
1,300 simulated facts). Direct recall reaches 1.000 on three of six modes;
multi-hop ranges from 0.033 to 1.000; unanswerable questions score 0.000 in every
mode. We publish the whole table, including the failures.
```

---
