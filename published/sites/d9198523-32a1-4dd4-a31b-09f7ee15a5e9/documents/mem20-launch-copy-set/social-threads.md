# Social threads — publish-ready (v3 · canonical-repo-corrected)

**Channels:** X / Twitter, LinkedIn, Reddit · **Wedge:** *Auditable agent memory — the memory layer you can prove.*
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20

---

## X / Twitter

### Single post (263 chars)

```
Most agent memory competes on retrieval quality.

mem20 competes on proof.

Hard grounded/simulated partition. Contamination auditing. Evidence-based
promotion. Append-only origin ledger.

MIT. Self-hosted. 270 tools over MCP.
https://github.com/bythewayz66-glitch/mem20
```

### Thread (6 posts)

**1/**
```
Agent memory has a trust problem nobody's selling a fix for.

Every tool answers "what's relevant?" None answer "can you prove what this
agent knows?"

We built mem20 for the second question. 🧵
```

**2/**
```
The core idea: a HARD partition between grounded memory (real source) and
simulated memory (agent-generated).

Not a flag on one store. Two classes, enforced on write — the vector and BM25
indexes reject simulated records outright.

"The agent made this up" becomes structurally visible.
```

**3/**
```
Around that: contamination auditing (catch simulated content bleeding into
grounded), evidence-based promotion (nothing graduates without
prediction_error_evidence attached), and an append-only origin-tagged ledger.

Every memory carries its origin. History can't be quietly rewritten.
```

**4/**
```
Why MIT + self-hosted: you can't audit a black box. If your memory layer is the
thing under audit, run it yourself.

Python, MCP-native (JSON-RPC 2.0 over stdio), 270 tools across 27 domains.
Installs with a clone, a venv and requirements.txt.
```

**5/**
```
Straight talk: our adversarial hit rate is 0.000 today. Real weakness, not a
footnote. Benchmarks are self-reported on our harness and not independently
audited.

We also don't have a published LoCoMo/LongMemEval comparable to Mem0 or Zep —
so we're not claiming one. And promotion is evidence-based, not tamper-proof.
```

**6/**
```
The wedge is auditability, and it's genuinely unoccupied. If you're building
production agents in a regulated context and "probably relevant" isn't good
enough:

https://github.com/bythewayz66-glitch/mem20
```

---

## LinkedIn (regulated / enterprise angle)

```
Most agent-memory systems answer "what is relevant?"

Regulated AI teams have to answer a harder question: "what does this agent
actually know, and can you show me where it learned it?"

mem20 is persistent memory for AI agents built around that second question:

— A hard partition between grounded memory and simulated content, enforced at
  the storage layer rather than by convention
— Contamination auditing to catch simulated content leaking into grounded stores
— Evidence-based promotion — nothing becomes "known" without evidence attached
— An append-only, origin-tagged ledger for every memory
— MIT licensed, Python, self-hosted — no lock-in, no black box

270 tools across 27 domains, delivered over MCP (JSON-RPC 2.0 over stdio).

It's not a retrieval-quality race. It's a trust and provenance race.

To be precise about the claim: this is evidence-based promotion with an
append-only audit trail — not tamper-proof. The promotion gate's attestation is
self-reported today, and we say so.

github.com/bythewayz66-glitch/mem20

#AgenticAI #AIGovernance #MLOps #AIInfrastructure #Auditability
```

---

## Reddit variants

### r/LocalLLaMA (self-host angle)

**Title:** `mem20 – MIT, self-hosted agent memory with a grounded/simulated partition (auditable, no black box)`

**Body:**
```
I've been frustrated that most agent-memory tooling is a black box you can't
self-host end to end. mem20 is an MIT-licensed Python MCP server you run in your
own VPC: JSON-RPC 2.0 over stdio, 270 tools across 27 domains.

The interesting architectural bit is a HARD partition between grounded memory
(real source) and simulated memory (agent-generated) — two classes, not a flag.
The vector and BM25 indexes assert grounded-only on write, so simulated records
can't reach them; the ledger validates origin/store tags at the append path.

Honest limits: adversarial hit rate is 0.000 today (real weakness, on the
roadmap), the benchmarks are self-reported on our own harness rather than
independently audited, and there's no published LoCoMo/LongMemEval comparable to
Mem0/Zep, so I'm not claiming one. Promotion is evidence-based, not tamper-proof.

Install is from source right now (not on PyPI):

  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20 && python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py

Repo: https://github.com/bythewayz66-glitch/mem20
Happy to hear where this breaks — especially the promotion gate.
```

### r/MachineLearning (technical angle)

**Title:** `[P] mem20: an agent memory substrate with provenance as the primary invariant (MIT, MCP)`

**Body:**
```
Most memory systems for LLM agents optimise retrieval. mem20 inverts the design
goal: the primary invariant is provenance.

- Grounded and simulated memory are distinct classes, enforced at the write path
  (`_assert_grounded()` on both the vector and BM25 index writers).
- The ledger is append-only and origin/store tagged, validated by
  `_validate_partition_tags()` at the lowest append.
- Promotion between partitions requires `prediction_error_evidence` — a linked
  prior prediction resolved in the item's favour, or a registered external
  verifier.

Self-reported benchmarks on our own harness: hit rate 1.000 direct / 0.800
multi-hop / 0.000 adversarial; leak rate 0.000 on clean stores. The adversarial
0.000 is disclosed as a known limitation — hard adversarial queries defeat the
retrieval path today. These are not independently audited and there is no
reproduction script in the repo, so treat them as vendor-reported.

We have no LoCoMo/LongMemEval result comparable to Mem0 or Zep and don't claim
one. Would value critique on the promotion gate, which currently relies on
self-attestation rather than cryptographic enforcement.

Repo: https://github.com/bythewayz66-glitch/mem20
```

### r/LangChain (integration angle)

**Title:** `mem20 — MCP-native agent memory (270 tools, grounded/simulated partition)`

**Body:**
```
For anyone wiring memory into LangGraph / CrewAI / Pydantic AI: mem20 is an MCP
server (JSON-RPC 2.0 over stdio) that adds persistent memory with an audit trail
— a hard grounded/simulated partition, contamination auditing, evidence-based
promotion, and an append-only origin-tagged ledger. 270 tools across 27 domains,
MIT, Python.

Because it speaks MCP, it registers like any other stdio server:

  claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py

Install from source for now (not on PyPI yet):

  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20 && python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt

Repo: https://github.com/bythewayz66-glitch/mem20
```

---

## Guardrail check (all variants)

- [x] No LoCoMo/LongMemEval claim
- [x] Adversarial 0.000 disclosed wherever benchmarks appear
- [x] Benchmarks labelled self-reported / not independently audited
- [x] Promotion framed as evidence-based, not tamper-proof
- [x] No banned phrasings, no competitor disparagement
- [x] Canonical repo only; no bare registry install
