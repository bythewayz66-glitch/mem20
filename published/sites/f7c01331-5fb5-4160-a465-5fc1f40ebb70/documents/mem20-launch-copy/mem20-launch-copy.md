# mem20 — Launch Copy Pack (v1)

**Prepared by:** Slides Assistant (copywriting) · **Round 2 of 10**
**Source:** Market Research findings (completed) · **Product:** mem20 v2.1.0rc2 · `github.com/JaysonAIOnline/mem20`
**Audience:** AI platform/infra engineers; regulated-industry AI teams; OSS/self-host-first + MCP builders
**Wedge (holds across every asset):** *Auditable agent memory — the memory layer you can prove.*

---

## 0. How to use this pack

- Sections 1–4 are the core launch assets. Section 5 is channel-specific.
- Section 6 is the **claim ledger**: every number below is tied to its source. Do not add a number that is not in Section 6.
- Section 7 is the **guardrail list** — the three caveats that MUST be honored in every public asset.
- Copy is written to be pasted as-is. Bracketed `[ ]` items need a human decision before publish.

---

## 1. The one-liner (use everywhere)

> **mem20 is persistent memory for AI agents — with a hard partition between what an agent actually knows and what it made up.**

Short alt (nav bars, meta descriptions):
> Auditable agent memory. Grounded vs simulated, enforced — not hoped for.

---

## 2. Show HN post

**Title (76 chars)**

```
Show HN: mem20 – Auditable memory for AI agents (grounded vs simulated)
```

Alt titles:
```
Show HN: mem20 – Agent memory with contamination auditing and a provenance ledger
Show HN: mem20 – MIT agent-memory server that proves what it remembers
```

**Body**

```
Hi HN — I'm launching mem20, an MCP server that gives AI agents persistent
memory with an audit trail.

The problem I kept hitting: every memory layer competes on retrieval quality,
and none of them let you *prove* what the agent knows. In a regulated context
that's the whole ballgame — you don't need "probably relevant", you need
"here is where this came from and here is the evidence it was promoted."

What mem20 is:

- An MCP server (JSON-RPC 2.0 over stdio), Python, MIT licensed.
- ~258–260 tools across 26 domains.
- A HARD partition between grounded memory (came from a real source) and
  simulated memory (the agent generated it). These are not the same store
  with a flag — they are separate.
- Contamination auditing, so you can detect when simulated content has bled
  into grounded memory.
- Evidence-based promotion: content moves from simulated to grounded only
  with evidence attached, not by asserting it.
- An append-only, origin-tagged ledger — every entry says where it came from.

Published benchmarks (v2.1.0rc2, our own harness):
  hit rate  — 1.000 direct | 0.800 multi-hop | 0.000 adversarial
  leak rate — 0.000 on clean stores

I want to be straight about those numbers. The 0.000 adversarial hit rate is
a real weakness, not a marketing smudge: hard adversarial queries defeat the
retrieval path today, and it's on the roadmap. And we do not have a published
LoCoMo/LongMemEval comparable to Mem0 or Zep — so I'm not claiming one.

Why MIT and self-hosted matters here: if your memory layer is the thing you
must audit, you can't audit someone else's black box. Run it on your own
infrastructure, read the code, no lock-in.

Repo: https://github.com/JaysonAIOnline/mem20

Happy to answer anything — especially the adversarial hit rate and where the
promotion gate needs hardening. That's the stuff I'd ask about too.
```

*Note: keep the self-critical paragraph. This audience rewards it and it pre-empts the top comment.*

---

## 3. README / landing headline + subhead

**H1**

```
Auditable agent memory — the memory layer you can prove.
```

**Subhead**

```
mem20 is an MIT-licensed MCP server that gives AI agents persistent memory with
a hard partition between grounded and simulated content, contamination auditing,
evidence-based promotion, and an append-only, origin-tagged ledger. ~258 tools
across 26 domains. Self-hosted. Zero lock-in.
```

**Alt subhead (shorter, for hero sections with an image)**

```
Persistent memory for AI agents — with the audit trail that regulated teams need.
Grounded vs simulated, enforced in the architecture.
```

**Hero CTA microcopy**

```
Primary:   Get started on GitHub      → github.com/JaysonAIOnline/mem20
Secondary: Read the architecture docs → [docs link]
Tertiary:  pip install mem20          → [confirm PyPI availability before publish]
```

---

## 4. Value-prop bullets

**Short form (3 bullets — landing page, PH gallery)**

- **Prove it, don't just retrieve it.** A hard grounded/simulated partition plus an append-only origin-tagged ledger tells you where every memory came from.
- **Catch contamination before it ships.** Auditing detects simulated content bleeding into grounded memory — leak rate 0.000 on clean stores.
- **Own your memory layer.** MIT licensed, Python, self-hosted. No lock-in, no black box, no vendor holding your audit trail.

**Long form (6 bullets — README, deep-dive posts)**

1. **Hard grounded/simulated partition.** Not a boolean flag on one store — two distinct memory classes, so "the agent made this up" is structurally visible.
2. **Contamination auditing.** Detect when simulated content has entered grounded memory, before it becomes a decision.
3. **Evidence-based promotion.** Nothing graduates from simulated to grounded without evidence attached to the promotion.
4. **Append-only, origin-tagged ledger.** Every memory carries its source; history cannot be quietly rewritten.
5. **MCP-native and broad.** JSON-RPC 2.0 over stdio, ~258–260 tools across 26 domains — drops into LangGraph, CrewAI, Pydantic AI and the rest of the MCP ecosystem.
6. **MIT, self-hosted, Python.** Audit the code you depend on. Run it in your own VPC.

---

## 5. Channel-specific variants

### 5a. Hacker News
Use Section 2 as-is. Comment-strategy notes:
- Lead replies with the adversarial 0.000 weakness if it isn't already the top comment — owning it first is worth more than defending it.
- Be explicit that benchmarks are self-published on our harness, and that no LoCoMo/LongMemEval comparison exists yet.
- Point "why not Mem0/Zep?" questions at the *category* answer: they optimize retrieval; nobody leads with auditability. Do not disparage their numbers.

### 5b. Product Hunt

**Tagline (60 char)**

```
Auditable memory for AI agents — grounded vs simulated
```

**Description**

```
mem20 gives AI agents persistent memory you can actually prove. A hard partition
separates grounded memory from simulated content, contamination auditing catches
bleed between them, and an append-only origin-tagged ledger records where every
memory came from. MIT-licensed MCP server, Python, self-hosted — ~258 tools
across 26 domains. Built for teams who need "here's the evidence," not
"probably relevant."
```

**First comment (maker comment)**

```
Maker here. Every agent-memory tool on the market competes on retrieval quality.
We built mem20 around a different question: can you *prove* what your agent
knows? That's the grounded/simulated partition + the audit ledger. It's MIT and
self-hosted because you can't audit a black box. Honest caveat up front: our
adversarial hit rate is 0.000 today — that's a known weakness, and we'd rather
tell you than have you find it.
```

### 5c. LinkedIn (regulated-industry / enterprise angle)

```
Most agent-memory systems answer "what is relevant?"

Regulated AI teams have to answer a harder question: "what does this agent
actually know, and can you show me where it learned it?"

mem20 is persistent memory for AI agents built around that second question:

— A hard partition between grounded memory and simulated content
— Contamination auditing to catch simulated content leaking into grounded stores
— Evidence-based promotion — nothing becomes "known" without evidence
— An append-only, origin-tagged ledger for every memory
— MIT licensed, Python, self-hosted — no lock-in, no black box

~258 tools across 26 domains, delivered over MCP (JSON-RPC 2.0 over stdio).

It's not a retrieval-quality race. It's a trust and provenance race.

github.com/JaysonAIOnline/mem20

#AgenticAI #AIGovernance #MLOps #AIInfrastructure #Auditability
```

### 5d. X / Twitter

**Single post (269 chars)**

```
Most agent memory competes on retrieval quality.

mem20 competes on proof.

Hard grounded/simulated partition. Contamination auditing. Evidence-based
promotion. Append-only origin ledger.

MIT. Self-hosted. ~258 tools over MCP.
```

**Thread**

```
1/ Agent memory has a trust problem nobody's selling a fix for.

Every tool answers "what's relevant?" None answer "can you prove what this
agent knows?"

We built mem20 for the second question. 🧵

2/ The core idea: HARD partition between grounded memory (real source) and
simulated memory (agent-generated).

Not a flag on one store. Two classes. "The agent made this up" is structurally
visible instead of silently plausible.

3/ Around that: contamination auditing (catch simulated content bleeding into
grounded), evidence-based promotion (nothing graduates without evidence), and an
append-only origin-tagged ledger.

Every memory says where it came from. History can't be quietly rewritten.

4/ Why MIT + self-hosted: you can't audit a black box. If your memory layer is
the thing under audit, run it yourself. Python, MCP-native (JSON-RPC 2.0 over
stdio), ~258 tools across 26 domains.

5/ Straight talk: our adversarial hit rate is 0.000 today. That's a weakness, not
a footnote. We also don't have a published LoCoMo/LongMemEval comparable to
Mem0 or Zep — so we're not claiming one.

6/ The wedge is auditability, and it's genuinely unoccupied. If you're building
production agents in a regulated context and "probably relevant" isn't good
enough:

github.com/JaysonAIOnline/mem20
```

---

## 6. Claim ledger (every number, with source)

| Claim in copy | Number | Source |
|---|---|---|
| Tools / domains | ~258–260 tools, 26 domains | Market research (product spec, v2.1.0rc2) |
| Transport / license / language | JSON-RPC 2.0 over stdio · MIT · Python | Market research (product spec) |
| Hit rate | 1.000 direct · 0.800 multi-hop · 0.000 adversarial | Published benchmark, mem20 v2.1.0rc2 |
| Leak rate | 0.000 on clean stores | Published benchmark, mem20 v2.1.0rc2 |
| Mem0 pricing/status | Apache 2.0 · ~59.9k stars · $24M Series A · Free→$19→$79→$249 | Market research, verified Oct 2026 |
| Mem0 benchmark dispute | vendor 94.4 LongMemEval vs independent 49.0 (45-pt gap) | Market research, verified Oct 2026 |
| Zep/Graphiti | Flex $125/mo (50k credits) · Flex Plus $375/mo · vendor DMR 94.8% | Market research, verified Oct 2026 |
| Letta | Apache 2.0 · ~23.6k stars · $10M seed · Pro $20/mo · LoCoMo 74.0% | Market research, verified Oct 2026 |
| Market size | $6.49B (2025) → $9.0B (2026), CAGR ~38.7%, $33.5B by 2030 | The Business Research Company |
| Market size (alt) | $6.16B (2025) → $69.1B (2033), CAGR 35.3% | SkyQuest |
| Broader agents market | $7.6B (2025) → $10.9B (2026), CAGR 49.6%, $182.9B by 2033 | Grand View Research |
| Regional mix | NA ~39.6% revenue share; APAC fastest-growing | Market research, verified Oct 2026 |

**Rule for downstream assets:** if it isn't in this table, it doesn't go on the page.

---

## 7. Guardrails — do not overclaim (MANDATORY)

1. **No LoCoMo/LongMemEval claim.** mem20 has no published benchmark comparable to Mem0 or Zep. Never imply parity, never cite their numbers as ours.
2. **Adversarial hit rate 0.000 must be disclosed** in any asset that shows the benchmark table. Frame it as a known weakness with a roadmap — never omit it from the HN post or the maker comment.
3. **The promotion gate's self-attestation hole was flagged in a prior audit.** Do not describe promotion as tamper-proof or cryptographically enforced. The accurate claim is *evidence-based promotion with an append-only audit trail*. Use "auditable," not "unfakeable."

**Banned phrasings:** "provably secure", "tamper-proof memory", "matches Mem0", "beats Zep", "industry-leading retrieval", any unqualified superlative.

---

## 8. Handoff note for Webpage Developer

Page should be built around the wedge, not a feature grid:
- **Hero:** H1 + alt subhead from Section 3, secondary CTA to GitHub.
- **Section 2:** the 3 short value-prop bullets from Section 4.
- **Section 3:** "How the partition works" — grounded vs simulated, promotion, ledger (three-tier diagram).
- **Section 4:** benchmark table **with the adversarial 0.000 row visible** and the no-LoCoMo caveat directly under it.
- **Section 5:** comparison table (mem20 vs Mem0 vs Zep vs Letta) using Section 6 rows only.
- **Section 6:** install + GitHub CTA, MIT badge, self-host note.
- **Footer:** market context stats with attributions (BTRC / SkyQuest / Grand View).

Handoff after the page: Analytics Reporter sets up campaign + tracking.
