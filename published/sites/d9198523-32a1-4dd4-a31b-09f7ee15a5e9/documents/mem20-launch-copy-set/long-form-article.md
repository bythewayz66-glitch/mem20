# Agent Memory Has a Trust Problem. mem20 Is Built Around the Other Question.

*Long-form deep-dive — for dev.to / Medium / technical blog. ~1,450 words.*
*Repo: https://github.com/bythewayz66-glitch/mem20*

---

Every agent-memory system on the market is answering the same question: **"what is relevant?"**

Vector search, graph traversal, temporal decay, hybrid retrieval — the entire category competes on how well it can pull the *right* context back at the *right* moment. Mem0 optimises extraction and retrieval. Zep builds a temporal knowledge graph. Letta makes the runtime stateful. It is a real race, and retrieval quality is genuinely getting better.

But there is a second question almost nobody is selling an answer to:

**"Can you prove what this agent actually knows?"**

If you are building agents for a regulated context — fintech, healthcare, legal, government — that second question is the whole ballgame. "Probably relevant" is not an answer you can put in an audit file. You need to be able to say: *here is the memory, here is where it came from, and here is the evidence that it was allowed in.*

That is the gap mem20 is built around.

## The failure mode that motivated it

Picture a production agent six months into its life. It has a memory store with a few thousand entries. Most came from real sources — user messages, retrieved documents, tool outputs. Some the agent generated itself: a summary, an inference, a "hypothesis" it wrote down while reasoning.

Now a compliance officer asks: *which of these are facts, and which are the agent's own inventions?*

With a conventional memory layer, the honest answer is "we don't know." Simulated and grounded content share one store, distinguished at best by a boolean flag. And flags get set wrong. Content bleeds. A summary of a summary becomes a "fact." The store slowly contaminates itself, and nobody notices until a decision built on an invented memory goes wrong.

This is not hypothetical — it is the structural weakness of every "extract and retrieve" memory design. The store has no opinion about the difference between what happened and what was imagined.

## What mem20 does differently

mem20 is an MCP server that gives AI agents persistent memory with an audit trail. It is MIT licensed, written in Python, and speaks JSON-RPC 2.0 over stdio, so it registers with any MCP host — Claude Code, Cursor, or your own client — like any other server.

The design decision that matters is that provenance is not a feature bolted onto a retrieval system. It is the invariant the storage layer enforces. Concretely, in the code:

**1. A hard partition, enforced on write.**
Grounded memory (real observations, user statements, events) and simulated memory (hypotheticals, counterfactuals, model output) are separate classes. `remember()` is grounded-only by default. Simulated content goes through its own path. Crucially, `_add_to_vector_index()` and `_add_to_bm25_index()` both call `_assert_grounded()`, so a simulated record reaching either index **raises immediately**. This is not a flag you can forget to check; it is an assertion in the write path.

**2. An append-only ledger with validated tags.**
Every ledger entry carries `origin` (`user`, `tool`, `simulated`) and `store` (`memory`, `imaginated`). `_validate_partition_tags()` rejects mismatches at the lowest append path, so a mislabelled entry cannot enter the log in the first place. The log is appended, never rewritten in place.

**3. Evidence-based promotion.**
`promote_simulated_to_grounded()` accepts a simulated record only when it carries `prediction_error_evidence` — either a linked prior prediction that resolved in the item's favour, or an attestation from a registered external verifier. Nothing graduates because someone asserted it should.

**4. Contamination auditing.**
`memory_audit_contamination()` inspects both the grounded store and the BM25 corpus for simulated records and returns `contamination_rate`, `violations`, and `violations_simulated_in_bm25_corpus`. A clean system reports rate `0.0`. This is a check you can run as a gate, not a dashboard you hope stays green.

**5. A prediction ledger that closes the loop.**
`world_model_record_prediction` and `world_model_resolve_prediction` couple a forecast to its observed outcome. That is what makes "evidence" a measurable thing rather than a vibe: the promotion gate can point at a prediction that was made and then resolved.

Around the memory core sits the rest of the surface — cognitive operations (reasoning, planning, reflection), a procedural skill library, a roadmap registry, an agent self-model, and the operational tool domains (filesystem, databases, cloud control planes, version control, messaging, scraping). That is where the **270 tools across 27 domains** figure comes from: it is the live count of registered tools on the server (268 domain tools plus 2 infrastructure tools), not a marketing round-up.

## The numbers — including the ones that aren't good

On our own harness, the self-reported benchmarks are:

| Metric | Result |
|---|---|
| Hit rate — direct | **1.000** |
| Hit rate — multi-hop | **0.800** |
| Hit rate — adversarial | **0.000** |
| Leak rate (clean stores) | **0.000** |

Three things to say about that table, in order of importance.

First, the 0.000 adversarial hit rate is not a typo and it is not a marketing smudge. **It is a real weakness.** Hard adversarial queries defeat the retrieval path today, and closing that is on the roadmap. If you are evaluating mem20 for a hostile-input environment, that number is the first thing you should ask about.

Second, these figures are **self-reported on our own internal harness**. They are not independently audited, and there is no reproduction script for them in the repository. Treat them the way you should treat any vendor benchmark — ours included. The leak rate of 0.000 is the one number with a mechanism behind it you can verify yourself: run `memory_audit_contamination()` on a fresh store and read `contamination_rate`.

Third, we do **not** have a published LoCoMo/LongMemEval result comparable to Mem0's or Zep's. So we do not claim one. Any agent-memory vendor quoting a benchmark number is quoting *their* harness.

## The honest caveat on promotion

The promotion gate — the mechanism that decides whether simulated content becomes grounded — was flagged in an internal audit for a self-attestation hole. In plain terms: the evidence requirement is only as strong as the attestation behind it, and that attestation is currently self-reported rather than cryptographically enforced.

So the accurate claim is **"evidence-based promotion with an append-only audit trail,"** not "tamper-proof" and not "unfakeable." If you need a cryptographic guarantee today, mem20 is not that yet, and we would rather say so than have you discover it in production.

This is also the most interesting open problem in the project. A provenance system that can be lied to by its own caller is better than one with no provenance at all — but it is not finished. The obvious directions are signed attestations from verifiers with keys you control, and a promotion path where the evidence object itself is hash-committed into the ledger entry. Neither is shipped.

## What the monorepo actually is

One thing worth being clear about, because it affects how you evaluate this: `mem20` is a monorepo. Alongside the memory and cognition core it carries roughly 293 `mem20*z` subsystem packages, plus engines for 3D, game tooling, model serving and operations. The memory substrate is the part with the architectural argument above. The rest is breadth, and it is uneven: the repo's own sitemap records 632 of 875 registered capabilities reporting `ok`, 142 `unpackaged`, and 101 `degraded`. If you are adopting mem20 for the auditability wedge, evaluate the memory core; treat the subsystems as a menu, not a promise.

## Why auditability is the right wedge

Look at the competitive landscape and the pattern is obvious: Mem0, Zep, Letta, Supermemory, Cognee, and the infrastructure players all compete on **retrieval quality**. It is a legitimately contested axis, and the incumbents are strong at it.

Nobody leads with **auditability**. It is an unoccupied position, and it is unoccupied for a reason that makes it defensible: auditability is not a feature you add later — it is an architectural commitment you make at the memory-model level. You have to decide *before* you write the store that grounded and simulated are different classes, that promotion needs evidence, and that the ledger is append-only. Retrofitting provenance onto a single unified store is not a sprint.

That is the bet: as agentic systems move into regulated industries, "what can you prove?" becomes a procurement question. mem20 is positioned to answer it.

## Install it

mem20 is not yet published to PyPI, so install from source today:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py
```

That is the plain path. If you want it always-on, there is a systemd installer:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git /opt/mem20
sudo /opt/mem20/install.sh --user $USER --dir /opt/mem20
curl http://localhost:8080/health
```

You will need an API key for an OpenAI-compatible chat-completions endpoint (the default base URL is NVIDIA's `integrate.api.nvidia.com/v1`) if you want the cognitive tools — the memory core runs without one.

One gotcha worth naming, because it costs an afternoon if you hit it blind: the repo's `mcp/` directory is a **script** directory with no `__init__.py`, on purpose. Importing it as `mcp.*` would shadow the upstream `mcp` SDK. That is why the server does `from server import main`, and why the installed `mem20-mcp` console script goes through `launcher.py` instead of a plain module path.

## What we're asking

If you build agents for a regulated context — or you have ever been asked "how do you know that's true?" about something your agent said — try it and tell us where the promotion gate hurts.

The adversarial hit rate is 0.000. The promotion gate self-attests. Both are on the board, disclosed, and open for critique. The wedge is auditability, and the whole point of an auditable memory layer is that we should be held to it too.

**Repo:** https://github.com/bythewayz66-glitch/mem20

---

*This article's references and install block were re-pointed to the canonical repository during the mem20 repo migration. See `mem20-reference-audit.csv` and the publish report for the full stale→new ledger and the verified evidence for each claim.*
