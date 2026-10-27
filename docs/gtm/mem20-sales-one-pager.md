# mem20 — Sales One-Pager (v3)

**Seat:** VP of Sales · **Artifact:** one-pager + pilot-to-paid motion + capacity model
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **Public site:** https://bythewayz66-glitch.github.io/mem20/
**Version 3.0.0 · MIT · Python 3.10+ · 270 tools / 27 domains · JSON-RPC 2.0 over stdio**
**Updated:** 2026-10-26 · **Numbers:** house numbers per claim ledger v3 §4

---

## 1. The 30-second pitch

> Every agent-memory vendor sells you relevance. mem20 sells you **proof**.
>
> Grounded facts and simulated hypotheses live in **separate stores** — not one store with a flag. Try to write invented content through the grounded path and the server raises `PermissionError`. Every entry carries its origin and store in an append-only ledger, and `audit_contamination()` reports a contamination rate plus six violation classes for your store.
>
> Since 3.0 it also refuses an **unlabeled** write: every fact must declare how it was learned — observed, inferred, imagined, user_stated, hypothesis, agent_generated, unlabeled. A fact nobody can vouch for is not stored as a fact.
>
> MIT-licensed, Python, self-hosted, **270 tools across 27 domains**, over MCP. You can read the code that holds your audit trail, because you cannot audit a black box.

**The one line for the email subject:** `The memory layer you can prove — grounded vs simulated, enforced in code.`

---

## 2. Who this is for (and who it is not)

| Tier | Segment | Trigger | Where they live |
|---|---|---|---|
| **A** | **Regulated AI teams** — fintech, healthcare, legal, gov | A model risk / audit function asked "where did the agent learn this?" and the answer was "the vector store" | LinkedIn, industry conferences, direct outbound |
| **B** | **AI platform / infra engineers** building production agents | Their agent confabulated in staging and polluted the memory store | GitHub, HN, LangChain & MCP Discord, r/LocalLLaMA |
| **C** | **Self-host-first / OSS teams** and MCP-ecosystem builders | Cannot send memory to a vendor cloud | MCP directories, GitHub |

**Not a fit — say so early and save both sides the cycle:**
- Teams that only need retrieval relevance and have no audit obligation. Mem0 or a plain vector DB is cheaper.
- Teams that want a **managed SaaS with no operational surface**. mem20 is source-install, self-hosted; there is **no PyPI package and no hosted offering**. If they cannot run a Python service, the install is a blocker, not a feature.
- Teams needing a **published benchmark comparable to Mem0 or Zep**. We do not have one and will not claim one.

---

## 3. The three objections and the honest answers

| Objection | Answer |
|---|---|
| *"Where are your LoCoMo / LongMemEval numbers?"* | **We don't have them.** What ships is a 13-query internal corpus: direct 1.000, multi-hop 0.800, adversarial **0.000**, leak 0.000. The adversarial number is a real weakness and it is in the table, not buried. Any figure set against Mem0's 92.5 or Zep's 94.8% is a category error — different corpora, different metrics, vendor self-reported. **Lead with this; it is why they trust the rest.** |
| *"How do I install it? Pip?"* | **Source only.** `git clone` + `pip install -r requirements.txt`. There is **no PyPI package** under `mem20`, `mem20-ai` or `mem20oreo` — all 404, checked 2026-10-26. One caveat worth stating up front: the install pins `mcp>=2.1.1`; installing `mcp<2` produces a misleading "mcp package not installed" error. |
| *"Is the promotion gate airtight?"* | **No — narrowed, not closed.** Bare calls are refused and the prediction-error path demands structured evidence tied to a recorded prior prediction. A free-text `confirmation` argument still promotes. We publish the four-path test result rather than describing the gate as airtight. Say this before they find it. |

**Never say:** tamper-proof, unfakeable, provably secure, matches Mem0, beats Zep, industry-leading retrieval. One of those in a deal and the whole trust position collapses.

---

## 4. Commercial model

**House numbers — restated, not re-measured** (claim ledger §4):

| Metric | Value |
|---|---|
| TAM | **$1.28B** |
| SAM | **$282M** |
| SOM | **$1.68M** |
| Blended ACV | **$14,000** |

**Capacity arithmetic (estimate — derived, not measured):**

$$ \text{accounts to realise SOM} = \frac{1{,}680{,}000}{14{,}000} = 120 \text{ accounts} $$

At 120 accounts and a 4-quarter year, that is **30 net-new accounts per quarter** — roughly **2.3 per month**. For a $14K blended ACV with a self-serve, source-install entry, that is a land-and-expand shape, not an enterprise-field-sales shape. **Two enterprise AEs closing 1.5 accounts/month each covers the whole SOM**; the rest of the funnel is developer-led.

**Packaging (proposal — no price list exists in the repo; these are GTM proposals, label them as such):**

| Tier | Shape | Price (proposed) | What the buyer gets |
|---|---|---|---|
| **Free / OSS** | MIT, self-host, unlimited | $0 | Everything in the repo. This is the funnel, not a trial. |
| **Supported** | Annual support + version-locked build | **$14,000/yr** (the blended ACV anchor) | Response SLAs, upgrade guidance, install hardening review |
| **Compliance pack** | Supported + audit-evidence package | **proposed $28,000–$42,000/yr** | Written partition/audit evidence mapping for their model-risk file, plus a QBR cadence |
| **Platform** | Multi-team / multi-VPC deployment | **proposed $56,000+/yr** | Deployment review, custom violation-class coverage, named engineer |

> The Free tier is deliberately real, not crippled. For an auditable product, a crippled free tier is the fastest way to lose the developer who was going to champion it.

---

## 5. Pilot → paid motion (6 weeks)

| Week | Stage | Gate to advance | Owner |
|---|---|---|---|
| 0 | **Qualify** — audit obligation confirmed, a named model-risk/security stakeholder, Python service deployable | Stakeholder named + a written "we must be able to show provenance" statement | AE |
| 1 | **Install & partition demo** — they run it in their own VPC; we walk the `remember()` refusal and `audit_contamination()` on **their** store | `contamination_rate` reported on their data, not ours | AE + their engineer |
| 2–3 | **First grounded recall in their agent** — one real workflow, grounded writes only | Their agent answers one real question with an auditable origin pointer | Their engineer |
| 4 | **Adversarial / contamination test** — they deliberately try to pollute the store | They confirm the refusal path fires and the audit reports CLEAN | Their engineer |
| 5 | **Value review** — the audit-evidence question, answered from their store | Their stakeholder accepts the audit output as evidence | AE |
| 6 | **Close** — Supported or Compliance pack | Signed | AE |

**The technical win condition is not "it works."** It is: *their* store, *their* data, a contamination rate *they* produced, and an origin pointer *they* can hand an auditor. Anything less and this becomes another "nice retrieval layer" conversation that loses on price to a vector DB.

**Expansion triggers (hand to Customer Success):**
- A second team deploys from the same repo → multi-team Platform conversation
- Contamination audit flags a violation class they did not know existed → Compliance pack
- They hit a scale or latency wall on hybrid retrieval → deployment review, paid
- Reranking latency becomes a complaint (≈10x, 101ms vs 16ms p50) → tuning engagement, `MEM20_RERANK=0` first, then paid help

---

## 6. Competitive line (no disparagement, no borrowed numbers)

| Vendor | Their frame | Our line |
|---|---|---|
| Mem0 | extract-and-retrieve, retrieval quality | They answer *"what is relevant?"* We answer *"what does this agent actually know?"* Different question, different buyer. |
| Zep / Graphiti | temporal knowledge graph | Graph structure is not provenance. A graph edge does not tell an auditor where the fact came from. |
| Letta / MemGPT | stateful agent runtime | Runtime, not audit substrate. We are the memory layer, we drop into any MCP host. |
| LangMem | framework-native memory | Framework-coupled. Ours is MCP-native and runs under any host. |
| Plain vector DB | storage primitive | A vector store has no concept of grounded vs simulated at all. That is the entire gap. |

**Do not cite their benchmark figures as a baseline and do not dispute them.** They are vendor self-reported. The category claim is enough: *they optimize retrieval; nobody leads with auditability.*

---

## 7. What to send after the call

1. Repo: `https://github.com/bythewayz66-glitch/mem20`
2. Site: `https://bythewayz66-glitch.github.io/mem20/`
3. Install (paste verbatim, it is two lines and it is not pip-from-PyPI):
   ```
   git clone https://github.com/bythewayz66-glitch/mem20.git
   cd mem20 && pip install -r requirements.txt && python mcp/mcp_server.py
   ```
4. The partition refusal, quoted as the first code sample — it closes more deals than any diagram.

**Do not send a `/sites/` CDN link.** Every `/sites/` URL returns 403 to an anonymous reader. If an asset is only hosted there, it cannot be sent to a customer.

---

## 8. Hand-off

The next seat is **Head of Customer Success**, and the input they need is §5: the six-week pilot gates and the four expansion triggers. Their first job is the week-2 gate — *first grounded recall in the customer's own agent* — because that, not the signed contract, is where this product is won or lost.
