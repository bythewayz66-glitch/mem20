# Competitive and market analysis — the agent-memory category against the 487-tool / 129-domain surface

**Lane:** H16 — Market Research (competitive intelligence + market sizing)
**Repo:** `github.com/bythewayz66-glitch/mem20`
**Baseline measured:** `0224a64946a2c00313a9872515893157adcbc47e` (`main`, 2026-11-16T06:55:07Z)
**Version on main:** `4.0.0`
**Supersedes:** `competitive-matrix-2026-11-01.md` (pinned `2ea44922`, 270 tools / 27 domains / v3.1.0)
**Companion files:** `competitive-matrix-2026-11-16.csv`, `source-register-2026-11-16.md`

---

## 1. Verdict

The surface nearly doubled in fifteen days and the category's price anchor disappeared in six.
Both facts change the argument, and only one of them is good news.

| Measure | 2026-11-01 (`2ea44922`) | 2026-11-16 (`0224a64`) | Change |
|---|---:|---:|---|
| MCP tools | 270 | **487** | **+217 (+80.4%)** |
| Domains | 27 | **129** | **+102 (+377.8%)** |
| Tools per domain | 10.0 | **3.78** | **−62.2%** |
| Unwired (declared, not registered) | 0 | **19** | new |
| Version | 3.1.0 | **4.0.0** | major |
| Tracked files | 8,536 | **11,439** | +2,903 |
| TAM / SAM / SOM | $1.28B / $282M / $1.68M | **$1.28B / $282M / $1.68M** | held, carried |
| Blended ACV | $14,000 | **$14,000** | held |

**Three findings, in order of how much they should change what we say.**

1. **The surface grew by breadth, not by depth.** 89 of the 129 domains are `mem20*z`-family
   modules holding 168 tools (34.5%); 91 domains hold two tools or fewer and together account for
   167 tools (34.3%). The core memory stack — `memory`, `cognitive`, `world`, `procedural`,
   `thought_process`, `lie`, `braid`, `versioncontrol` — is **133 tools, 27.3% of the surface**.
   "487 tools" is true and it is a *breadth* claim. It is not a claim that the memory layer got
   3.6× deeper, and any asset that implies so is contradicted by this table.

2. **The 19 unwired tools are the differentiator's own tools.** `gateway_admission`,
   `gateway_provenance`, `gateway_translate`, `lattice_emit/recall/report/search/verify`,
   `memory_engine_guard/health/namespace/recall/subsystem/veto`, and
   `stream_publish/recall/report/search/verify` are declared in source but registered by no
   inherited mixin, so they are absent from `tools/list`. The provenance and gateway surface —
   the thing this product sells — is the part that is not on the wire. That is a shipping gap,
   not a positioning gap, and it is the single highest-value item in this document.

3. **Mem0 removed its published price on 2026-11-02.** The four-tier ladder (Hobby $0 /
   Starter $19 / Pro $249 / Enterprise) was replaced by **Free + Custom (quote-only)**. The
   category's most-cited self-serve anchor is now dark. This cuts both ways: it removes the
   "$19 and you're done" objection, and it removes the number our own price-positioning work
   was benchmarked against. §5 works through what survives.

**What did not change, and should not be re-litigated.** TAM $1.28B / SAM $282M / SOM $1.68M
and blended ACV $14,000 are carried verbatim from `docs/finance/inputs.json` on every run. This
document asserts them equal to the house figure and does not re-derive them. §6 triangulates
them against three independent analyst bases without moving them.

---

## 2. Method — what "against the live surface" means here

### 2.1 The surface, measured three ways

`docs/surface.json` is generated, not hand-written. Its `cross_check` block is the acceptance
gate, and at `0224a64` it reads:

```json
{"ast_domains": 129, "ast_tools": 487, "only_ast": [], "only_live": []}
```

Both symmetric differences are empty, which is the only condition under which the generator
writes the file. Three independent counts agree:

| Measurement | Value | Command |
|---|---:|---|
| Live `tools/list` (wire surface) | **487** | `python3 scripts/surface_manifest.py --check` |
| AST catalog, wired | **487** | `mt.Tool(...)` declarations in inherited modules |
| AST declarations, unwired | **19** | declared, registered by no mixin |
| Domains | **129** | distinct owning modules after documented folds |
| Names only in `tools/list` | **0** | must be 0 |
| Names only in AST catalog | **0** | must be 0 |

Source-level counts on the same tree, for a reader who wants to see the raw material:

```bash
grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' | sort -u | wc -l   # 494
grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py | sort -u | wc -l         # 128
ls mcp/tools/*_tools.py | wc -l                                              # 153
```

**494 assignment sites vs 487 distinct keys is not a contradiction** — it is the known
double-registration class recorded in the 2026-11-01 matrix (§7, defect 2: `lie_status`
registered twice). Seven assignment sites overwrite an existing key. The wire surface is 487
because the registry is a dict; the source has 494 writes. Both numbers are correct and they
measure different things. Do not quote 494 as a tool count.

### 2.2 Why 129 domains and 487 tools are both correct

The 2026-11-01 document had to explain `28 − 1 = 27` and `265 + 5 = 270`. That arithmetic is
retired. At `0224a64` the domain count is a **module count**, not a registrar count:

| Step | Value | Meaning |
|---|---:|---|
| `register_*_tools` functions in `mcp/server.py` | 128 | one per inherited mixin |
| distinct owning modules after documented folds | **129** | the product taxonomy |
| distinct tools on the wire | **487** | what a client receives |

128 registrars producing 129 domains is possible because one registrar covers two modules
(`memory` folds `mcp/memory_tools.py` and `mcp/tools/enhanced_memory_tools.py`). The
authoritative mapping is `docs/TOOL-DOMAINS.md`, which is generated by
`scripts/surface_manifest.py` and must not be hand-edited.

**The honest formulation, which this document uses throughout:** *"487 tools across 129
domains, of which 133 tools in 8 domains are the memory-and-cognition stack and 19 declared
tools are not yet wired."* Not "487 memory tools."

### 2.3 What this document re-measured vs. carried

| Class | Treatment |
|---|---|
| Surface counts, domain distribution, unwired list | **Re-measured** at `0224a64` in this run |
| Benchmark rows | **Read** from `benchmarks/results/latest.json` at `0224a64`; not re-run |
| House numbers (TAM/SAM/SOM/ACV) | **Carried** from `docs/finance/inputs.json`; not re-derived |
| Competitor prices and licences | **Re-read** 2026-11-16; every row carries an `S` id |
| Analyst market bases | **Re-read** 2026-11-16; used for triangulation only |

---

## 3. Surface anatomy — the finding the tool count hides

A single number cannot describe a 129-domain surface. This section is the part a diligence
reader will actually use, because it is the part that says where the product is deep and where
it is wide.

### 3.1 Concentration

| Slice | Domains | Tools | Share of 487 |
|---|---:|---:|---:|
| Top 10 domains | 10 | 158 | **32.4%** |
| Top 20 domains | 20 | 241 | **49.5%** |
| Top 30 domains | 30 | 291 | **59.8%** |
| Domains with ≥10 tools | 9 | 149 | 30.6% |
| Domains with 5–9 tools | 18 | 116 | 23.8% |
| Domains with 3–4 tools | 11 | 38 | 7.8% |
| Domains with exactly 2 tools | 76 | 152 | 31.2% |
| Domains with exactly 1 tool | 15 | 15 | 3.1% |

**91 of 129 domains (70.5%) hold two tools or fewer and together hold 167 tools (34.3%).**
That is the shape of an absorption program, not the shape of a product that grew organically
one capability at a time. It is not a defect — breadth is a real moat against a buyer who wants
one server instead of nine — but it is a *different* moat from depth, and the two must not be
sold with the same sentence.

### 3.2 The two populations

| Population | Domains | Tools | Tools/domain |
|---|---:|---:|---:|
| `mem20*z`-family modules | **89** | **168** | 1.89 |
| Everything else | **40** | **319** | **7.98** |

The 40 non-family domains average 7.98 tools each. The 89 family domains average 1.89. The
family is where the long tail lives; the non-family set is where the product is actually built
out. A buyer evaluating "is this a serious memory substrate" is evaluating the 40, and the 40
are strong. A buyer evaluating "does this cover my whole agent estate" is evaluating the 89,
and the 89 are thin per module.

### 3.3 The memory-and-cognition stack

| Domain | Tools | What it is |
|---|---:|---|
| `memory` | **55** | store, recall (semantic/hybrid/graph), timeline, decay, contradict, promote, epistemic status, quarantine, contamination audit, namespaces, PII scan, ingest (pdf/code/image/audio) |
| `cognitive` | 19 | `cog_*`, `corrigibility_*`, `imagination_*`, `theory_*` |
| `world` | 14 | `affective_*`, `world_*` |
| `versioncontrol` | 11 | `vcs_*` |
| `lie` | 10 | `lie_*` — the deception/consistency surface |
| `thought_process` | 9 | `beam_*`, `tot_*`, `react_*`, `reflexion`, `least_*` |
| `braid` | 9 | Rust-backed execution braid |
| `procedural` | 6 | `procedural_*` |
| **Total** | **133** | **27.3% of the surface** |

`memory` alone is 55 tools and 11.3% of the entire surface — larger than the next three domains
combined. That is the depth claim, and it is defensible.

### 3.4 The epistemic-partition tools, named

The differentiator is not a slogan; it is eight tool names. At `0224a64``these are registered
and on the wire:

```
memory_set_epistemic_status   memory_epistemic_veto      memory_list_simulated
memory_quarantine_simulated   memory_promote             memory_audit_contamination
memory_self_audit             memory_simulate_store
```

Plus the temporal set: `memory_timeline`, `memory_decay`, `memory_contradict`.

**And the ones that are not on the wire:** `gateway_provenance`, `memory_engine_veto`,
`memory_engine_guard`, `lattice_verify`, `stream_verify`. The store-level partition ships. The
*gateway-level* provenance enforcement — the layer that would let a buyer say "no agent may
read a simulated record without an explicit veto check" — is declared and unwired. §8 treats
this as the top risk.

### 3.5 Benchmark position, stated before anyone asks

From `benchmarks/results/latest.json` at `0224a64` — corpus `mem20-scale-corpus-v2`, 700
grounded / 1,300 simulated / 250 queries, 7 scored modes:

| Mode | Query class | n | Hit rate | MRR | Leak |
|---|---|---:|---:|---:|---:|
| `bm25` | adversarial_hard | 40 | **0.025** | 0.006 | 0.000 |
| `keyword` | adversarial_hard | 40 | **0.025** | 0.006 | 0.000 |
| `hybrid` | adversarial_hard | 40 | 0.050 | 0.050 | 0.000 |
| `graph` | multi_hop | 30 | **0.033** | 0.033 | 0.000 |
| `vector` | adversarial_hard | 40 | **0.750** | 0.583 | 0.000 |
| `hybrid-rerank-off` | adversarial_hard | 40 | 0.625 | 0.515 | 0.000 |
| all modes | unanswerable | 20 | 0.000 | 0.000 | 0.000 |

Trust block: `contamination_rate 0.0`, `contamination_violations 0`, `stale_pointer_rate 0.0`,
`indexed_entries 1400`, `graph_entities 654`, `graph_edges 3601`, `ledger_records 700`.

**This bounds the whole document.** mem20 sells auditable separation, not retrieval leadership.
Sparse retrieval collapses on hard adversarial queries (0.025); dense retrieval is materially
better on the same class (0.750). The split *is* the finding — do not average the modes into one
"adversarial score." Graph traversal at 0.033 on multi-hop is the weakest multi-hop mode and it
is measured; do not present graph traversal as a strength. Unanswerable 0.000 is correct
abstention, not a defect, and it does not cancel a weak hit rate.

---

## 4. The refreshed competitive matrix

13 named players plus mem20 as the reference row, scored on the four attributes that decide the
auditable slice: self-hostability, whether the store has a temporal model, whether grounded and
simulated content are separated, and whether provenance is a property of the memory store or a
feature bolted onto the orchestration layer.

`Price status`: `MOVED` = was wrong in the prior revision · `CORRECTED` = claim wrong ·
`SHARPENED` = right but underspecified · `CONFIRMED` = re-verified unchanged ·
`UNVERIFIED` = no published price exists.

### A · Developer memory APIs

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **Mem0** | Apache-2.0 core + proprietary cloud | yes (core) | Passive LLM fact extraction into vector store; graph gated to top tier | timestamps + per-record event history; no bi-temporal | no | no — event history is per-memory | **$0 Free → Custom (quote-only)** | **MOVED** |
| **Zep** / Graphiti | Graphiti Apache-2.0; hosted core closed | Graphiti only — CE **discontinued** | Bi-temporal knowledge graph; invalidate rather than delete | **strongest in category** | no | graph-level fact invalidation | $0 (10,000 credits/mo) → $125/mo Flex | CONFIRMED |
| **Letta** (MemGPT) | Apache-2.0 | yes (framework + server) | LLM edits its own memory via tool calls; MemFS git-backed | no | no | no | $0 Free (3 agents) → $20/mo Pro | CONFIRMED |
| **LangMem** | MIT | yes | Framework-bound memory for LangGraph agents | no | no | no | $0 (library) | UNVERIFIED |
| **Cognee** | Apache-2.0 + cloud | yes (engine free forever) | Knowledge graph + vector index over docs, code, conversations | Enterprise feature | Enterprise / manual primitives in OSS | no | $0 Free (1M tokens) → $1.00/1M tokens | CONFIRMED |
| **Supermemory** | proprietary + OSS core | partial | Credit-metered personalization + institutional memory | no | no | Enterprise only | $0 + $5 credits/mo | NEW |

### B · Hyperscaler embedded memory

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **AWS AgentCore Memory** | managed only | no | Platform-native short + long-term memory, consumption-priced | no | no | CloudWatch adjacent | $1.00/GB ingested | CONFIRMED |
| **Vertex AI Agent Engine** | managed only | no | Platform-native sessions + Memory Bank | no | no | Cloud Logging adjacent | $0.25/1,000 events | CONFIRMED |

### C · Infrastructure substrate

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **Pinecone** | proprietary, managed | no | Serverless managed vector database | no | no | no | $0 Starter (2 GB) → $50/mo min | CONFIRMED |
| **Redis** | **AGPLv3 / RSALv2 / SSPLv1** (Redis 8) | yes | Vector + session + operational state in one store | no | no | no | $0 (self-host) | CONFIRMED |
| **Weaviate** | BSD-3 + cloud | yes | Open-source hybrid vector search (BM25F + vector) | no | no | no | $0 licence → $45/mo Flex min | CONFIRMED |

### D · Governance-adjacent platforms — the real competitive set

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **IBM watsonx.governance** | commercial | no | Enterprise AI risk + audit trail to EU AI Act / NIST AI RMF / ISO 42001; Gartner MQ Leader (Jun 2026) | no | no | orchestration layer | free trial; $0.60/resource unit Essentials | CONFIRMED |
| **ServiceNow AI Control Tower** | commercial | no | Discover/Observe/Govern/Secure/Measure across any AI system | no | no | workflow layer | quote-only | UNVERIFIED |
| **Lyzr OpenController** | commercial | **yes — customer's own cloud account** | Signed record from the control that allowed or refused each call; per-call authorization, budgets, quarantine | no | no | **yes, at orchestration layer (signed)** | platform Free tier; OpenController quote-only | SHARPENED |
| **Sentra** | commercial | yes (VPC / air-gapped) | Governed organization memory: permission-aware context, named approver, record of what is true now | partial ("what is true now") | no | **yes, at the memory layer** | quote-only | NEW |

### Reference · mem20

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **mem20** | MIT | yes (source) | Memory + cognition substrate over MCP JSON-RPC 2.0; **487 tools / 129 domains / v4.0.0**; 133-tool memory stack | append-only ledger + timeline + decay + contradiction detection | **enforced at the storage layer** | **yes — the store is the ledger** | $14,000 blended ACV | REFRESHED |

Every row's cells carry source IDs in `competitive-matrix-2026-11-16.csv`; the lookup table is
`source-register-2026-11-16.md`. No cell is unsourced.

### 4.1 The column that decides the deal

Read the `Grounded/simulated` column across groups A, B and C: **not one** product separates
grounded from simulated memory. In group D, provenance lives at the orchestration layer
(watsonx, ServiceNow, Lyzr) — outside the memory store.

**One row now breaks that cleanly, and it must be disclosed.** Sentra describes itself as
"governed organization memory" with "a record of what is true now," permission-aware context and
a named approver, deployable air-gapped. That is a memory-layer provenance claim, not an
orchestration-layer one. It does not claim an epistemic partition — "what is true now" is a
currency claim, not a grounded/simulated typing — so the narrow differentiator survives. But
"nobody else puts provenance in the memory store" is no longer a sentence that survives contact
with a competitor's homepage. The defensible sentence is narrower:

> **Nobody else makes the epistemic partition — grounded vs simulated — a property of the
> stored record rather than a log written beside it.**

That sentence is checkable against every row above and it is the only one this document
authorises.

---

## 5. What moved since 2026-11-01 — and what it costs us

### 5.1 Mem0 removed its published price

| Date | Plans |
|---|---|
| through 2026-10-26 | Hobby $0 · Starter $19/mo · Pro $249/mo · Enterprise custom |
| **from 2026-11-02** | **Free · Custom (quote-only)** |

Free now gives 10,000 adds / 1,000 retrievals for 30 days with Mem0 paying model calls, then
50,000 adds / 10,000 retrievals monthly with your own LLM key, plus usage-based billing under a
cap you set. Graph memory, user profiles, SSO, audit logs, SLA and on-prem moved into Custom.

**Why this matters more than a price change.** The 2026-11-01 matrix used Mem0's $19 → $249
ladder as the category's self-serve anchor and argued mem20's $14,000 ACV against a buyer who
could "start at $19." That comparison is now unavailable: the buyer's alternative is a quote.
Two consequences, one good and one bad:

- **Good.** The "$19 and you're done" objection is gone. A quote-only competitor cannot be used
  to anchor a price down, and the buyer must now compare *scope*, where 487 tools and a
  self-hostable MIT substrate are legible.
- **Bad.** Our own price-positioning work loses its reference point. `docs/pricing/` derives the
  tier ladder against a competitive band that included $19/$249. That band is now
  Free/quote-only, and the derivation should be re-read before it is quoted again. This document
  does not re-derive it — that is a pricing-lane decision — but it flags the dependency.

**Also note the churn rate.** Mem0 has changed its published pricing at least four times in
2026 (Growth tier launched 2026-05-11 and killed 2026-07-20; Graph Memory toggled on/off Pro;
Starter/Pro removed 2026-11-02). Any competitor price older than a quarter is a liability.

### 5.2 Everything else held

Zep $125/mo Flex, Letta $20/mo Pro, Cognee $1.00/1M tokens, AWS $1.00/GB ingested, Vertex
$0.25/1,000 events, Pinecone $50/mo min, Weaviate $45/mo Flex min, watsonx $0.60/resource unit
— all re-verified unchanged. The category repriced hard in October and then went quiet in
November. That quiet is the window.

### 5.3 Two rows are new and one is sharpened

| Row | Change | Why it is in the matrix |
|---|---|---|
| **Supermemory** | NEW | Credit-metered, $5/mo included credits; appears in every 2026 comparison shortlist. Omitting it would make the matrix look curated. |
| **Sentra** | NEW | The first memory-layer provenance claim from a governance vendor. Breaks the clean "group D is orchestration-only" story — disclosed in §4.1. |
| **Lyzr OpenController** | SHARPENED | Now confirmed self-hostable **inside the customer's own cloud account**, with per-call authorization, budgets and quarantine. Previously recorded as orchestration-layer only. |

---

## 6. Market sizing — carried, triangulated, not re-derived

The house figures are carried verbatim from `docs/finance/inputs.json` (`house_numbers`). The
rule there is binding: **TAM and SAM are CARRIED, never re-derived.** This document asserts them
equal to the house figure and does not re-open them.

| Layer | Figure | Source | Arithmetic cross-check |
|---|---|---|---|
| **TAM** | **$1.28B** | `house_numbers.tam_usd = 1280000000` | auditable slice of the $6.49B broad category: `$1.28B ÷ $6.49B = 19.72%` |
| **SAM** | **$282M** | `house_numbers.sam_usd = 282000000` | 22.03% of TAM |
| **SOM (ARR)** | **$1.68M** | `house_numbers.som_arr_usd = 1680000` | 0.596% of SAM, 0.131% of TAM |
| Blended ACV | $14,000 | `house_numbers.blended_acv_usd = 14000` | tier ladder 72/12/12/4 prices to $14,000 exactly |
| Accounts to realise SOM | 120 | `house_numbers.som_accounts = 120` | `120 × $14,000 = $1,680,000` — **exact** |

### 6.1 Triangulation against three independent analyst bases

The house TAM is a *slice*, and the slice is only meaningful if the base is stable. Three
independent 2026 bases for the same category:

| Source | 2025 base | Terminal | CAGR | Implied 2026 |
|---|---:|---|---:|---:|
| **Mordor Intelligence** | $6.27B | $28.45B (2030) | 35.32% | ~$8.48B |
| **SkyQuest** | $6.16B | $69.13B (2033) | 35.3% | ~$8.33B |
| **TBRC** | — | $37.11B (2030) | 40.2% | — |
| **House base used** | **$6.49B** | — | — | — |

The three bases agree on 2025 to within 5.4% ($6.16B–$6.49B) and on growth to within 5 points of
CAGR (35.3%–40.2%). **The house base of $6.49B sits at the top of the published band** — that is
a disclosed choice, not an error, and it is the reason the TAM is $1.28B rather than ~$1.22B.

**The conditional that must stay attached.** A diligence team using Mordor's $6.27B base and the
same 19.72% share would compute a TAM of about **$1.24B**. That is a hypothetical under a
different base, not a second house figure. Any asset that excerpts it without the conditional
publishes a competing TAM. Keep the conditional.

### 6.2 What the growth rate implies for the SOM

At 35.3% CAGR the category roughly doubles every 2.3 years. The SOM is the terminal rung of a
**three-year ramp** — 40 / 80 / 120 accounts, year-3 exit ARR $1,680,000 — not a 12-month
obtainable. A figure reached at the end of year 3 is not a 12-month number, and the two live
marketing surfaces that still say "12-month" contradict the model that produces the figure.
This document uses **3-year obtainable** throughout.

**Sanity check on the SOM against the growth rate.** $1.68M against a $282M SAM is 0.596%. If
the SAM grows at 35.3% for three years it reaches ~$700M, so the year-3 SOM is ~0.24% of the
year-3 SAM. That is a *conservative* share for a 120-account book, which is the right direction
for a plan that has to be believed. It also means the SOM is not the constraint — distribution
is.

### 6.3 Residuals, disclosed rather than smoothed

| Layer | Floor accounts | Integer build | Residual |
|---|---:|---|---|
| TAM | 91,428 | $1,279,992,000 | −$8,000 (−0.0006%) |
| SAM | 20,142 | $281,988,000 | −$12,000 (−0.0043%) |
| SOM | 120 | $1,680,000 | **$0 (exact)** |

Total residual −$20,000. The house dollar figures are authoritative; the account counts are
derived and are never multiplied back into a "corrected" TAM or SAM.

---

## 7. Demand drivers — the regulatory clock is the real tailwind

Market size says the category is growing. It does not say anyone is *forced* to buy. Two things
are forcing them.

### 7.1 EU AI Act — Article 12 is a memory requirement

| Milestone | Date | Status |
|---|---|---|
| Prohibitions + AI literacy | 2025-02-02 | in force |
| **Transparency duties** | **2026-08-02** | **in force** |
| Code of Practice on Transparency of AI-Generated Content | 2026-06-10 | published; ~190 signatories by end-July 2026 |
| Detection interoperability solution required | 2027-02-02 | upcoming |
| **Annex III high-risk rules** | **2027-12-02** | upcoming |

**Article 12 requires automatic event logging with traceability to source data for high-risk
systems. Article 13 requires transparency sufficient for a deployer to interpret outputs.**

Read that as a product requirement and it is not a logging requirement — it is a *provenance*
requirement. "Traceability to source data" is exactly the grounded/simulated distinction: a
record must be able to say not only where it came from but whether it was observed or
generated. A log written beside an untyped store cannot answer that, because the store never
recorded the type.

**The timing is the argument.** Transparency duties are live now; Annex III high-risk lands
2027-12-02. A buyer who needs an auditable memory layer in December 2027 has to start
accumulating the record well before then — an audit trail cannot be reconstructed for activity
nobody recorded. That gives a ~12-month buying window starting now, which is the single most
useful fact in this document for a sales conversation.

### 7.2 MCP — the distribution channel is now standard

| Fact | Value |
|---|---|
| Monthly SDK downloads | 97M |
| Public MCP servers | 9,400+ |
| Fortune 500 with active AI agents in production | 80% |
| Fortune 500 with MCP server implementations | **28%** |
| Native support | Anthropic, OpenAI, Google DeepMind, Microsoft |
| Governance | donated to Linux Foundation Agentic AI Foundation, Dec 2025 |
| Gartner: enterprise apps with task-specific agents by end-2026 | 40% |
| Gartner: API gateway vendors with MCP features | 75% |

**The gap that matters.** MCP is protocol-neutral about what a server exposes. Most servers
expose raw data, not governed context. The protocol enables quality; it does not enforce it.
That is precisely the gap a 487-tool governed memory server occupies — and it is also the reason
"487 tools" is a *distribution* asset: a buyer already running MCP clients can adopt without a
new integration.

**The counter-reading, stated plainly.** 28% MCP adoption among the Fortune 500 means 72% have
not adopted it. A 487-tool MCP server is a bet that the 28% grows. If MCP stalls, the surface
advantage is worth much less than the memory-layer advantage. The memory-layer argument does not
depend on MCP; the distribution argument does.

---

## 8. Where mem20 can and cannot win

### 8.1 The ICP, stated as a filter

A buyer qualifies if **all four** hold:

1. **Regulated or audited** — financial services, healthcare, government, insurance. Article 12
   applies or a regulator asks "what did the agent know."
2. **Self-hosting is mandatory** — data cannot leave the estate. This eliminates AWS AgentCore,
   Vertex, Pinecone, ServiceNow and watsonx on deployment grounds alone.
3. **Agents already in production** — not a pilot. Memory governance is a production problem.
4. **Multiple agent frameworks** — the buyer will not standardise on LangGraph or Letta, so a
   framework-bound memory (LangMem, Letta) is disqualified.

That filter is narrow and it is the point. It excludes the entire hyperscaler group and the
entire substrate group, and it leaves mem20 competing against Zep-without-CE, Cognee Enterprise,
Lyzr OpenController and Sentra.

### 8.2 Where the product wins

| Win | Why it holds | Evidence |
|---|---|---|
| **Epistemic partition in the store** | No competitor types records as grounded vs simulated at write time | §4.1; 8 named tools |
| **Self-hostable + MIT** | Zep withdrew CE; hyperscalers are managed-only; Lyzr/Sentra are commercial | §4 |
| **Published contamination rate** | `memory_audit_contamination` returns a number; nobody else publishes one | `trust.contamination_rate 0.0` |
| **Breadth in one server** | 487 tools / 129 domains vs a competitor's single-purpose API | §3 |
| **MCP-native** | Adoptable by any MCP client without a new integration | §7.2 |

### 8.3 Where the product loses, and must not pretend otherwise

| Loss | Why | What to say instead |
|---|---|---|
| **Retrieval quality** | Sparse 0.025, graph 0.033 on hard classes | "We publish every row. We sell provable separation, not the best retrieval score." |
| **Temporal model** | Zep/Graphiti's bi-temporal graph is stronger | "Zep models time better. Zep also withdrew self-hosting." |
| **Ecosystem and community** | Mem0 ~48K stars, 21 framework integrations; mem20 is not on PyPI | Do not compete on stars. Compete on auditability. |
| **19 unwired tools** | The gateway/lattice/stream provenance layer is not on the wire | Disclose it. It is a roadmap item, not a claim. |
| **Long-tail thinness** | 89 family domains at 1.89 tools each | Sell the 40 non-family domains; do not sell "129 domains" as 129 capabilities. |

### 8.4 The one thing that would change the verdict

If a hyperscaler ships epistemic typing in a managed memory store — a `grounded`/`simulated`
flag on the record with a query-time filter — the differentiator collapses to a self-hosting
argument. Nothing in the 2026-11-16 evidence suggests that is imminent: AWS and Vertex both
price memory as storage and neither types records. But it is the watch item, and it should be
re-checked quarterly alongside the price re-read.

---

## 9. Pricing implications

The blended ACV of $14,000 is carried and not re-derived here. Three observations that bear on
it, offered as inputs to the pricing lane rather than as a new derivation:

1. **The self-serve anchor is gone.** With Mem0 at Free/quote-only, the buyer's comparison set is
   Zep $125/mo, Letta $20/mo, Cognee $1.00/1M tokens — all *infrastructure* prices, none of them
   a governance price. $14,000 sits in a different budget line (compliance, not tooling), which
   is defensible but must be argued explicitly rather than by comparison.
2. **The governance comparables are quote-only.** watsonx Standard/Premium, ServiceNow AI
   Control Tower, Lyzr OpenController and Sentra all publish no price. A $14,000 blended ACV is
   therefore *below* the visible floor of the governance set and *above* the ceiling of the
   memory-API set. That is a coherent position and it is the one to hold.
3. **The tier ladder's competitive band needs a re-read.** `docs/pricing/` derives 72/12/12/4
   against a band that included Mem0's $19/$249. That band no longer exists. The derivation is
   not wrong, but its inputs are stale, and quoting it without that caveat is a defect.

---

## 10. Defects found and deliberately not fixed

Recorded, not silently repaired. Each is either an owner decision or belongs to a surface this
lane does not own.

| # | Defect | Status |
|---|---|---|
| 1 | **19 declared tools are unwired** — `gateway_*` (3), `lattice_*` (5), `memory_engine_*` (6), `stream_*` (5). The provenance/gateway layer is absent from `tools/list`. | Recorded. Wiring changes the exposed schema and needs tests; belongs with the owning subsystem, not a docs refresh. **Highest-value item in this document.** |
| 2 | **494 assignment sites vs 487 distinct keys.** Seven writes overwrite an existing key (`lie_status` is the known case). | Recorded. Removing a registration is a behaviour change. |
| 3 | **Two cells have no published source** — ServiceNow AI Control Tower entry, LangMem top price. | Marked `UNVERIFIED`. Not replaced with a different guess. |
| 4 | **`docs/pricing/` competitive band is stale** — derived against Mem0's retired $19/$249 ladder. | Flagged in §9. Pricing-lane decision. |
| 5 | **Two live marketing surfaces still say "12-month obtainable"** for a 3-year SOM. | Out of scope for this lane; the model says 3-year. |
| 6 | **`published/sites/54ed398d-…` still serves the v3 surface** (retired 257/26). | Out of scope; owned by the Webpage Developer lane. |

---

## 11. Reproducing every repo figure

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20 && git checkout 0224a64946a2c00313a9872515893157adcbc47e

cat VERSION                                                                    # 4.0.0
python3 -c "import json;d=json.load(open('docs/surface.json'));print(d['cross_check'])"
# {'ast_domains': 129, 'ast_tools': 487, 'only_ast': [], 'only_live': []}

python3 -c "import json;d=json.load(open('docs/surface.json'));print(len(d['domain_counts']),sum(d['domain_counts'].values()),len(d['unwired_tools']))"
# 129 487 19

grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' | sort -u | wc -l      # 494
grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py | sort -u | wc -l            # 128
ls mcp/tools/*_tools.py | wc -l                                                 # 153

python3 scripts/surface_manifest.py --check                                     # exit 0 = no drift

python3 -c "import json;h=json.load(open('docs/finance/inputs.json'))['house_numbers'];print(h['tam_usd'],h['sam_usd'],h['som_arr_usd'],h['blended_acv_usd'],h['som_accounts'])"
# 1280000000 282000000 1680000 14000 120

python3 -c "import json;d=json.load(open('benchmarks/results/latest.json'));print(d['corpus'],d['facts'],d['simulated'],d['queries']);print(d['trust']['contamination_rate'])"
# mem20-scale-corpus-v2 700 1300 250 / 0.0
```

Market-claim consistency still passes at the standing figures:

```bash
python3 scripts/audit_market_claims.py .        # exit 0
```

---

## 12. Scope limits

- **What this is.** A competitive and market analysis of the agent-memory category, measured
  against the surface at `0224a64`, with every competitor price re-read on 2026-11-16.
- **What it is not.** It does not re-publish any webpage, does not re-derive TAM/SAM/SOM/ACV,
  and does not wire the 19 unwired tools. Those are separate lanes.
- **Competitor figures are snapshots, not commitments.** Mem0 changed its published pricing four
  times in 2026. Treat any row older than a quarter as needing a re-read before it goes in
  customer-facing copy.
- **No competitor disparagement.** Competitor numbers are cited as their own claims, never
  repeated as mem20's. Where a competitor's number is disputed in its own sources, the matrix
  says "sources disagree" rather than picking the flattering one.
- **The benchmark bounds every retrieval claim in this document.** §3.5 is not optional context.

---

**SOURCE:** every figure carries an `R` or `S` identifier resolvable in
`source-register-2026-11-16.md`. Repository figures were re-measured in this run at
`0224a64946a2c00313a9872515893157adcbc47e`; market figures were read 2026-11-16 and each carries
its page and read date. Nothing is quoted from the 2026-11-01 matrix without being re-checked.

**DISCLAIMER:** As an AI Agent, I cannot provide legally protected, personalized investment
advice. This analysis is for informational purposes only and does not constitute investment
advice or recommendations. Consult a licensed financial advisor before making investment
decisions.
