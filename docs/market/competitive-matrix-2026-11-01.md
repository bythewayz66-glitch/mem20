# Competitive matrix — refresh against the v3.1.0 surface

**Lane:** H16 — Market Research (positioning)
**Repo:** `github.com/bythewayz66-glitch/mem20`
**Baseline measured:** `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (`main`, 2026-11-01T06:20:25-07:00)
**Supersedes:** `published/sites/54ed398d-…/documents/mem20-market-research-v3/competitive-matrix.csv`
**Companion files:** `competitive-matrix-2026-11-01.csv`, `source-register-2026-11-01.md`

---

## 1. Verdict

The v3 matrix was not merely stale in its tool count. It was **stale in its prices** — and in
the direction that flatters nobody, because the whole category repriced inside the eight weeks
between the two revisions. Four competitor rows carry an entry price that is now wrong, one
licence label is wrong, and two prices were never published in the first place.

| Measure | v3 (2026-10-16) | Now (2026-11-01) | Status |
|---|---|---|---|
| mem20 surface | 257 tools / 26 domains *(retired)* | **270 tools / 27 domains** | refreshed (`R1`,`R2`,`R3`) |
| mem20 version | `v2.1-rc2` | **`v3.1.0`** | refreshed (`R4`) |
| Row pinned to | `8e2f803` | **`2ea44922`** | refreshed (§2) |
| Named players | 13 + reference | **13 + reference** | unchanged |
| Rows whose price moved | — | **7 of 13** | §5 |
| Cells with an invented/absent source | 2 | **0** (2 marked unverified) | §6 |
| TAM / SAM / SOM | $1.28B / $282M / $1.68M | **$1.28B / $282M / $1.68M** | held, sourced (`R6`–`R8`) |
| Blended ACV | $14,000 | **$14,000** | held (`R9`) |

**The house numbers did not move.** $1.28B / $282M / $1.68M is carried verbatim from
`docs/finance/inputs.json` on every run and this refresh did not re-derive it. What moved is
everything around it.

---

## 2. Method, and what "against the current surface" means here

Two independent measurements of the product surface, plus a dated re-read of every competitor
claim. Nothing in this file is quoted from the v3 report without being re-checked first.

### 2.1 The surface, measured from code — twice

**Static enumeration** (`R1`, `R2`):

```bash
grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' | sort -u | wc -l   # 270 distinct
grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py | sort -u | wc -l          # 28 groups
```

**Runtime instantiation** (`R5`) — construct the real server and read the registry that
`tools/list` actually serves:

```
RUNTIME_TOOLS 270
REGISTRAR_METHODS 28
SUM_OF_GROUPS 270 UNION 270
PARTITION_CLEAN True
```

Both methods agree exactly, and the 28 groups partition the 270 tools with **no overlap and
no remainder**. `scripts/surface_measure.py` must be run from outside the repo root, because `mcp/` is
the server directory and putting the repo root on `sys.path[0]` shadows the MCP SDK — the script
imports the SDK first, then inserts `mcp/` on `sys.path`.

### 2.2 Why 270 tools and 27 domains are both correct

They are not the same measurement, and a matrix that conflates them produces a table that does
not sum.

| Step | Value | Meaning |
|---|---:|---|
| `register_*_tools` groups | **28** | one per domain module, plus the A2A layer (`R2`) |
| − the A2A transport (`register_a2a_tools`, 5 tools) | −1 | `a2a_list`, `a2a_call`, `a2a_discover`, `a2a_history`, `a2a_orchestrate` (`R20`) |
| **= domains** | **27** | the product taxonomy (`R3`) |
| **= distinct tools** | **270** | 265 in the 27 domains + 5 A2A (`R1`) |

`28 − 1 = 27` and `265 + 5 = 270`. Both reconcile. The honest formulation, which this matrix
uses, is **"270 tools in 27 domain groups plus the A2A transport layer"** — with the table
summing to 265, not the retired 257.

**The v3 matrix published the retired 257 / 26 pair, and its per-domain table also summed to that retired 257.** That is
`docs/ops/surface-measurement-2026-10-31.md`'s finding reproduced here: the retired figure predates the
`lie_*` domain entirely (10 live tools, `mcp/tools/lie_tools.py`) and undercounts `memory_*`
at 49 against 52 actually registered. The retired 257/26 pair is therefore superseded by 270/27.

### 2.3 Per-group map at `2ea44922`

28 groups, 270 tools, clean partition. This is the surface the matrix's reference row describes.

| Group | Tools | Group | Tools | Group | Tools |
|---|---:|---|---:|---|---:|
| `memory` | 42 | `cloudservice` | 10 | `thought_process` | 9 |
| `cognitive` | 19 | `database` | 10 | `cloudstorage` | 8 |
| `world` | 14 | `filesystem` | 10 | `design` | 8 |
| `enhanced_memory` | 13 | `lie` | 10 | `finance` | 8 |
| `versioncontrol` | 11 | `productivity` | 10 | `webscraping` | 8 |
| `braid` | 9 | `communication` | 9 | `blender` | 7 |
| `dev` | 9 | `marketing` | 9 | `search` | 7 |
| `procedural` | 6 | `a2a` | 5 | `irc` | 5 |
| `unity` | 5 | `roadmap` | 4 | `integration` | 3 |
| `job` | 2 | | | | |
| | | | | **total** | **270** |

---

## 3. The refreshed matrix

13 named players plus mem20 as the reference row, scored on the four attributes that decide
the auditable slice: self-hostability, whether the store has a temporal model, whether grounded
and simulated content are separated, and whether provenance is a property of the memory store
or a feature bolted onto the orchestration layer.

`Price status` is the refresh finding: `MOVED` = was wrong in v3, `CORRECTED` = claim wrong,
`SHARPENED` = right but underspecified, `CONFIRMED` = re-verified unchanged, `UNVERIFIED` = no
published price exists.

### A · Developer memory APIs

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **Mem0** | Apache-2.0 core + proprietary cloud | yes (core) | Passive LLM fact extraction into a vector store; graph gated to upper tier | timestamps + per-record event history; no bi-temporal | no | no — event history is per-memory | $0 Hobby | MOVED |
| **Zep** / Graphiti | Graphiti Apache-2.0; hosted core closed | Graphiti only — CE **discontinued** | Bi-temporal knowledge graph; invalidate rather than delete | **strongest in category** | no | graph-level fact invalidation | $0 (10,000 credits/mo) | MOVED |
| **Letta** (MemGPT) | Apache-2.0 | yes (framework + server) | LLM edits its own memory via tool calls; MemFS git-backed | no | no | no | $0 Free (3 agents) | CORRECTED |
| **LangMem** | MIT | yes | Framework-bound memory for LangGraph agents | no | no | no | $0 (library) | UNVERIFIED |
| **Cognee** | Apache-2.0 + cloud | yes (engine free forever) | Knowledge graph + vector index over docs, code, conversations | Enterprise feature | Enterprise / manual primitives in OSS | no | $0 Free (1M tokens) | CONFIRMED |

### B · Hyperscaler embedded memory

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **AWS AgentCore Memory** | managed only | no | Platform-native short + long-term memory, consumption-priced | no | no | CloudWatch adjacent | $1.00/GB ingested | CONFIRMED |
| **Vertex AI Agent Engine** | managed only | no | Platform-native sessions + Memory Bank | no | no | Cloud Logging adjacent | $0.25/1,000 events | CONFIRMED |

### C · Infrastructure substrate

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **Pinecone** | proprietary, managed | no | Serverless managed vector database | no | no | no | $0 Starter (2 GB) | SHARPENED |
| **Redis** | **AGPLv3 / RSALv2 / SSPLv1** (Redis 8) | yes | Vector + session + operational state in one store | no | no | no | $0 (self-host) | SHARPENED |
| **Weaviate** | BSD-3 + cloud | yes | Open-source hybrid vector search (BM25F + vector) | no | no | no | $0 licence | SHARPENED |

### D · Governance-adjacent platforms — the real competitive set

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **IBM watsonx.governance** | commercial | no | Enterprise AI risk + audit trail to EU AI Act / NIST AI RMF / ISO 42001; Gartner MQ Leader (Jun 2026) | no | no | orchestration layer | free trial; $0.60/unit Essentials | CORRECTED |
| **ServiceNow AI Control Tower** | commercial | no | Discover/Observe/Govern/Secure/Measure across any AI system | no | no | workflow layer | quote-only | UNVERIFIED |
| **Lyzr OpenController** | commercial | no | Signed record from the control that allowed or refused each call | no | no | **yes, at orchestration layer (signed)** | platform Free tier | CORRECTED |

### Reference · mem20

| Player | Access | Self-host | Architecture bet | Temporal | Grounded/simulated | Provenance in store | Entry | Price status |
|---|---|---|---|---|---|---|---|---|
| **mem20** | MIT | yes (source) | Memory + cognition substrate over MCP JSON-RPC 2.0; **270 tools / 27 domains / v3.1.0** | append-only ledger + timeline + decay + contradiction detection | **enforced at the storage layer** | **yes — the store is the ledger** | $14,000 blended ACV | REFRESHED |

Every row's cells carry source IDs in `competitive-matrix-2026-11-01.csv`; the lookup table is
`source-register-2026-11-01.md`. No cell is unsourced.

---

## 4. What the refreshed reference row can now claim — and only because it is in the registry

The v3 reference row asserted four capabilities. At `2ea44922` three of them name a live tool,
which is the difference between a positioning claim and a checkable one (`R18`, `R19`):

| Claim | Backing tool at `2ea44922` | Checkable? |
|---|---|---|
| Enforces a grounded / simulated partition at the storage layer | `memory_set_epistemic_status`, `memory_epistemic_veto`, `memory_list_simulated`, `memory_quarantine_simulated` | yes — tools are in the registry |
| Evidence-based promotion with an audit trail | `memory_promote` | yes |
| Publishes a contamination rate | `memory_audit_contamination` | yes — returns `contamination_rate` |
| Temporal reasoning over the store | `memory_timeline`, `memory_decay`, `memory_contradict` | yes |

**One guardrail this refresh keeps.** Promotion is described as *"evidence-based promotion with
an append-only audit trail"* — never "tamper-proof", never "unfakeable". The promotion gate's
self-attestation hole stays disclosed, per the standing rule in
`published/content/mem20-long-form-v3/numbers-ledger.md` §5.

**And the column that decides the deal still holds.** Read the last two columns across groups
A, B and C: **not one** product separates grounded from simulated memory, and in group D
provenance lives at the orchestration layer, outside the memory store. That is a structural gap,
not a feature gap — it cannot be closed by adding logging to a system whose memory records were
never typed by epistemic status in the first place.

---

## 5. What moved since v3 — the actual finding of this refresh

The tool count was the assigned gap. The pricing drift is the finding. Seven of thirteen rows
changed, and four of those were simply wrong.

| Player | v3 said | Correct now | Source |
|---|---|---|---|
| **Mem0** | $0 → $249/mo | $0 Hobby → **$19 Starter** → $249 Pro → custom. Note the $79 Growth tier existed 2026-05-11 → 2026-07-20 only | `S2`,`S3` |
| **Zep** | $25/mo → $375/mo | **$0 (10,000 credits) → $125/mo Flex → $375/mo Flex Plus.** The $25/mo entry is gone | `S5` |
| **Letta** | $0 → $200/mo | $0 Free (3 agents) → **$20/mo Pro**, API $20/mo + $0.10/active agent, Teams Pro $20/seat | `S8` |
| **Cognee** | $0 → $1/M tokens | $0 Free (1M tokens) → **$1.00/1M tokens + $5/workspace**. Standard was cut from $2.50 to $1.00 on 2026-09-24 | `S13`,`S14` |
| **Redis** | "source-available" | **AGPLv3 / RSALv2 / SSPLv1** — Redis 8 added AGPLv3, an OSI-approved licence. "Source-available" was accurate for 2024, wrong now | `S21` |
| **Weaviate** | $0 → usage | $0 licence; **$45/mo Flex min**, $280/mo Plus, Premium custom. The $25/mo Serverless tier was **retired Oct 2025** | `S23` |
| **IBM watsonx.governance** | "six figures" | free trial; **$0.60 per resource unit** Essentials; Standard/Premium/on-prem quote-only. "Six figures" is not a published entry price | `S25` |

### Why this matters for positioning, not just accuracy

Three of these movements strengthen the mem20 argument rather than weaken it, and they do so
with the competitor's own numbers:

1. **Zep withdrew self-hosting and re-anchored at $125/mo.** The strongest temporal model in the
   category removed the option a regulated buyer needs most (`S6`,`S7`). mem20 is MIT and ships
   a whole self-hostable substrate where Zep now offers Graphiti only.
2. **The hyperscaler memory meter is a commodity.** AWS short-term ingestion moved to
   $1.00/GB ingested on 2026-10-06 (`S15`,`S16`); Vertex bills $0.25 per 1,000 sessions/memory
   events (`S17`). Neither store types epistemic status. The storage component is being priced
   like storage — which is exactly the layer where mem20 claims a different property.
3. **Governance platforms still do not reach the memory layer.** watsonx.governance is a
   Leader in the first Gartner MQ for AI Governance Platforms (`S26`) and Lyzr can produce a
   *signed* record of who was allowed to act (`S29`) — both at the orchestration layer. Neither
   records what the agent **knew** and why it was permitted to know it.

**The counter-argument, stated plainly.** Mem0 already advertises "every read and write
logged" with SOC 2 Type 1 / HIPAA / GDPR (`S4`), and Cognee sells provenance as an Enterprise
feature (`S13`). "Nobody else does audit" is no longer a defensible sentence. The defensible
sentence is narrower and survives the refresh: **nobody else makes the epistemic partition —
grounded vs simulated — a property of the stored record rather than a log written beside it.**
Any copy that overreaches past that will be checkable against a competitor's own homepage.

---

## 6. Market sizing — carried, not re-derived, and sourced

The assignment's constraint was to keep TAM $1.28B / SAM $282M / SOM $1.68M sourced. They are
carried verbatim from `docs/finance/inputs.json` (`house_numbers`), and the rule there is
binding: **TAM and SAM are CARRIED, never re-derived.** This refresh asserts them equal to the
house figure and does not re-open them.

| Layer | Figure | Source | Arithmetic cross-check |
|---|---|---|---|
| **TAM** | **$1.28B** | `docs/finance/inputs.json` → `tam_usd = 1280000000` (`R6`) | auditable slice of the $6.49B broad category (`R17`): `$1.28B ÷ $6.49B = 19.72%` |
| **SAM** | **$282M** | `sam_usd = 282000000` (`R7`) | 22.03% of TAM (`R14`) |
| **SOM (ARR)** | **$1.68M** | `som_arr_usd = 1680000` (`R8`) | 0.596% of SAM (`R15`), 0.131% of TAM (`R16`) |
| Blended ACV | $14,000 | `blended_acv_usd = 14000` (`R9`) | tier ladder 72/12/12/4 prices to $14,000 exactly |
| Accounts to realise SOM | 120 | `som_accounts = 120` (`R10`) | `120 × $14,000 = $1,680,000` — **exact** |

### 6.1 Three corrections to how v3 presented these

The figures are unchanged. Three things around them were wrong and are fixed here.

1. **Horizon.** v3 labelled SOM "12-month obtainable". The canonical model states SOM as the
   **terminal rung of a three-year ramp** — 40 / 80 / 120 accounts, year-3 exit ARR $1,680,000
   (`R13`). A figure reached at the end of year 3 is not a 12-month obtainable. This refresh
   uses **3-year obtainable**, matching the artefact that produces the number.
2. **SAM account count.** v3 built the SAM row on **20,100** accounts → $281.4M, a −$600,000
   gap against $282M, and then reported two different SAM/TAM ratios on one line. The correct
   floor is **20,142** (`R11`; `$282M ÷ $14,000 = 20,142.86`), which reproduces $282M to within
   $12,000 (0.004%). 20,100 is 25× the residual of the right count and does not reproduce it at all.
3. **Ratio provenance.** Ratios are computed off the **dollar figures**, not off account counts.
   `SAM ÷ TAM = $282M ÷ $1.28B = 22.03%`.

### 6.2 Residuals, disclosed rather than smoothed

| Layer | Floor accounts | Integer build | Residual |
|---|---:|---|---|
| TAM | 91,428 (`R12`) | $1,279,992,000 | −$8,000 (−0.0006%) |
| SAM | 20,142 (`R11`) | $281,988,000 | −$12,000 (−0.0043%) |
| SOM | 120 (`R10`) | $1,680,000 | **$0 (exact)** |

Total residual across the three rows is −$20,000. The house dollar figures are authoritative;
the account counts are derived and are never multiplied back into a "corrected" TAM or SAM.

**$1.28B is not the category.** The broad base is $6.49B (TBRC 2025), against Mordor $6.27B and
SkyQuest $6.16B for the same category (`R17`). The house TAM quotes the **slice**, at the top of
the published band. Any asset quoting $6.49B as mem20's TAM is out of family. Any diligence team
using Mordor's base and the same 19.72% share would shrink the TAM to about $1.24B — a
hypothetical that must stay attached to that conditional or it becomes a second TAM in circulation.

---

## 7. Defects found and deliberately not fixed

Recorded, not silently repaired. Each is either an owner decision or belongs to a surface this
lane does not own.

| # | Defect | Status |
|---|---|---|
| 1 | **Two cells have no published source.** ServiceNow AI Control Tower "six figures" and LangMem "$39/seat" (which is LangSmith Plus). | Marked `UNVERIFIED` in the matrix. Not replaced with a different guess. |
| 2 | **`lie_status` is registered twice** — `mcp/tools/lie_tools.py`, second assignment overwrites the first. 272 assignment sites vs 270 distinct keys. | Recorded. Removing a registration changes the exposed schema; that is a behaviour change and belongs with tests, not a docs refresh. |
| 3 | **`published/sites/54ed398d-…` still serves the v3 surface** (retired 257/26, pinned `8e2f803`). | Out of scope for this lane — see §8. |
| 4 | **`published/sites/…/mem20-market-research-v3/gabe-bundle/` retains a retired hostname in its path.** | Known: the `chore(infra)` purge deliberately excluded `published/sites/**`. Content is clean; the path is not. |

---

## 8. Scope limits

- **What this refresh is.** The matrix, the surface numbers it depends on, the pricing behind
  every row, and the market-sizing arithmetic — all re-verified at `2ea44922` and dated 2026-11-01.
- **What it is not.** It does not re-publish the `mem20-market-research-v3` webpage. That
  surface is owned by the Webpage Developer lane and its rebuild is a separate slice. This file
  is the corrected source-of-truth the rebuild should consume.
- **Competitor figures are snapshots, not commitments.** The category repriced materially inside
  eight weeks; treat any row older than a quarter as needing a re-read before it goes in
  customer-facing copy.
- **No competitor disparagement.** Competitor numbers are cited as their own claims, never
  repeated as mem20's. Where a competitor's number is disputed in its own sources, the matrix
  says "sources disagree" rather than picking the flattering one.

---

## 9. Reproducing every repo figure

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20 && git checkout 2ea4492209dfaae6afb22ca884132a0d1849bfcf

cat VERSION                                                                     # 3.1.0
grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' | sort -u | wc -l       # 270
grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py | sort -u | wc -l             # 28
grep -c '"tam_usd": 1280000000' docs/finance/inputs.json                         # 1
python3 -c "import json;h=json.load(open('docs/finance/inputs.json'))['house_numbers'];print(h['tam_usd'],h['sam_usd'],h['som_arr_usd'],h['blended_acv_usd'],h['som_accounts'])"

# runtime (from outside the repo root)
pip install 'mcp' 'mcp-types>=2.3.0' 'aiohttp'
cd /tmp && python3 /path/to/mem20/scripts/surface_measure.py   # RUNTIME_TOOLS 270 / PARTITION_CLEAN True
```

Market-claim consistency still passes at the standing figures:

```bash
python3 scripts/audit_market_claims.py .        # exit 0
```

---

**SOURCE:** every figure in this document carries an `R` or `S` identifier resolvable in
`source-register-2026-11-01.md`. Repository figures were re-measured in this run at
`2ea4492209dfaae6afb22ca884132a0d1849bfcf`; market figures were read 2026-11-01 and each carries
its page and read date. Nothing is quoted from the v3 report without re-checking it.

**DISCLAIMER:** As an AI Agent, I cannot provide legally protected, personalized investment
advice. This analysis is for informational purposes only and does not constitute investment
advice or recommendations. Consult a licensed financial advisor before making investment
decisions.
