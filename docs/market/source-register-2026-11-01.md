# Source register — competitive matrix refresh, 2026-11-01

Every figure in `competitive-matrix-2026-11-01.csv` and `.md` carries one or more of
the identifiers below. This file is the lookup table: an ID here is what "carries a
source" means in the acceptance criteria.

**Repo-of-record figures (R-prefixed)** are reproducible from the repository itself by
the stated command. **Market figures (S-prefixed)** are external and carry the page, the
date read, and the exact claim being used.

Read rule: a competitor figure is used *only* for the claim recorded against it. Where a
vendor publishes no price, the matrix says so (`quote-only`) rather than inventing a
"six figures" band — that was the main defect in v3 (see §4 of the report).

---

## R — Repository figures (reproducible from this repo)

| ID | Figure | Value | Reproduce with |
|---|---|---|---|
| R1 | Distinct MCP tools | **270** | `grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' \| sort -u \| wc -l` |
| R2 | `register_*_tools` groups | **28** | `grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py \| sort -u \| wc -l` |
| R3 | Domain count (27 = 28 − A2A) | **27** | taxonomy in `docs/TOOL-DOMAINS.md`; `28 − 1 = 27`, `265 + 5 = 270` |
| R4 | Version | **3.1.0** | `cat VERSION` |
| R5 | Runtime registry size | **270**, clean partition | `python3 scripts/surface_measure.py` (constructs `Mem20MCPServer`, reads `self.tools`) |
| R6 | TAM | **$1.28B** | `docs/finance/inputs.json` → `house_numbers.tam_usd = 1280000000` |
| R7 | SAM | **$282M** | `house_numbers.sam_usd = 282000000` |
| R8 | SOM (ARR) | **$1.68M** | `house_numbers.som_arr_usd = 1680000` |
| R9 | Blended ACV | **$14,000** | `house_numbers.blended_acv_usd = 14000` |
| R10 | Accounts to realise SOM | **120** | `house_numbers.som_accounts = 120`; `120 × $14,000 = $1,680,000` |
| R11 | SAM account floor | **20,142** | `docs/finance/README.md` §2.3; `$282M ÷ $14,000 = 20,142.86` |
| R12 | TAM account floor | **91,428** | `docs/finance/README.md` §2.3; `$1.28B ÷ $14,000 = 91,428.57` |
| R13 | SOM horizon | **3 years** (terminal rung) | `docs/finance/model_output.json` → `ramp` = 40 / 80 / 120 accounts, year-3 exit ARR $1,680,000 |
| R14 | SAM/TAM | **22.03%** | `$282M ÷ $1.28B = 22.0312%` |
| R15 | SOM/SAM | **0.596%** | `$1.68M ÷ $282M = 0.5957%` |
| R16 | SOM/TAM | **0.131%** | `$1.68M ÷ $1.28B = 0.1313%` |
| R17 | Broad category base (context only) | **$6.49B** | TBRC, "Agentic AI Orchestration and Memory Systems" (2025); auditable slice `$1.28B ÷ $6.49B = 19.72%` |
| R18 | `memory_audit_contamination` exists | live | R1 registry enumeration; returns a contamination rate |
| R19 | `memory_promote`, `memory_set_epistemic_status`, `memory_epistemic_veto`, `memory_list_simulated`, `memory_quarantine_simulated`, `memory_timeline`, `memory_decay`, `memory_contradict` exist | live | R1 registry enumeration |
| R20 | `a2a_*` tools | **5** | R5 per-group map: `a2a_list`, `a2a_call`, `a2a_discover`, `a2a_history`, `a2a_orchestrate` |

**Reproduction note for R5.** `scripts/surface_measure.py` must run from **outside** the repo root,
because `mcp/` is the server directory and putting the repo root on `sys.path[0]` shadows the
MCP SDK. Import the SDK first, then insert `mcp/` on `sys.path`.

---

## S — Market figures (external, with read date)

All S-entries were read **2026-11-01**. Prices are in the vendor's own unit and are
snapshots, not commitments — the category repriced materially inside the eight weeks
between the v3 matrix and this refresh (see the `MOVED` rows below).

| ID | Subject | Claim used | Source |
|---|---|---|---|
| S1 | Mem0 licence + tiers | Apache-2.0 core/SDKs; managed platform proprietary; tiers free / $19 / $249 / custom | developersdigest.tech "Best AI Agent Memory Providers in 2026" (updated 2026-10-18); membase.com agent-memory comparison |
| S2 | Mem0 pricing detail | Hobby $0 (10,000 add / 1,000 retrieval per month), Starter $19/mo, Pro $249/mo incl. graph memory, Enterprise custom | usagepricing.com/blueprint/mem0; membase.com |
| S3 | Mem0 pricing churn | $79 Growth tier launched 2026-05-11, discontinued 2026-07-20; Graph Memory toggled on/off Pro and Enterprise more than once | pricingsaas.com "Mem0 drops its $19 Starter and $249 Pro plans" (briefing dated 2026-10-27) |
| S4 | Mem0 auditability | memory event history explains why a fact was added, updated, deleted or retrieved; per-record, not a store-wide ledger | valkey.io "AI agent memory with Valkey and Mem0"; mem0.ai (SOC 2 Type 1, HIPAA, GDPR; "every read and write logged") |
| S5 | Zep tiers | Free 10,000 credits/mo; $125/mo Flex (50,000 credits); $375/mo Flex Plus (200,000 credits); Enterprise custom | developersdigest.tech/agent-memory/zep (as of 2026-10-18); resources.rework.com best-agent-memory-tools-2026 |
| S6 | Zep self-hosting withdrawn | Zep Community Edition no longer supported; Zep README states CE is unsupported; Graphiti (Apache-2.0) is the remaining self-host path | developersdigest.tech/agent-memory/zep; vectorize.io "Hindsight vs Zep"; caura.ai "6 Zep Alternatives" (CE deprecated Apr 2025) |
| S7 | Zep temporal model | bi-temporal knowledge graph; tracks fact validity windows, invalidates rather than deletes | vectorize.io "Hindsight vs Zep (Graphiti)" |
| S8 | Letta licence + tiers | Apache-2.0; Free (3 stateful agents), Pro $20/mo, API $20/mo + $0.10/active agent, Teams Pro $20/seat/mo, Enterprise custom | developersdigest.tech/agent-memory/letta (as of 2026-10-18); membase.com |
| S9 | Letta architecture shift | 2026: flagship moved to Letta Code; V1 API server retired to archive branch; MemFS git-backed memory filesystem | developersdigest.tech/agent-memory/letta; trustvector.guard0.ai/agents/memgpt |
| S10 | Letta self-host | full framework and server self-hostable, free apart from LLM costs | resources.rework.com best-agent-memory-tools-2026 |
| S11 | LangMem | MIT library for LangGraph agents; **no published standalone price found** — the $39/seat figure is LangSmith Plus, carried from v3 and **not re-verified** | docs.langchain.com memory + long-term memory docs (carried v3 figure, flagged `UNVERIFIED`) |
| S12 | Cognee licence + self-host | Apache-2.0; open-source engine free to self-host forever | cognee.ai/faq; developersdigest.tech/agent-memory/cognee |
| S13 | Cognee tiers | Free $0 (1M tokens, 1 workspace); Standard $1.00 per 1M tokens + $5/additional workspace; Enterprise BYOC quote | cognee.ai/faq; developersdigest.tech/agent-memory/cognee; hydradb.com cognee review |
| S14 | Cognee pricing move | Standard reduced from $2.50 to $1.00 per 1M tokens; confirmed in Cognee newsletter 2026-09-24; Cognee 1.0 shipped 2026-06-26 | theaiagentindex.com/agents/cognee |
| S15 | AWS AgentCore Memory rates | $1.00/GB ingested, $0.20/GB retrieved, $0.10/GB-month stored (short-term, as of 2026-10-06); long-term $0.75/1,000 records/mo (built-in), $0.25/1,000 (override), $0.50/1,000 retrievals | aws.amazon.com/bedrock/agentcore/pricing; devopsity.com AgentCore pricing 2026 |
| S16 | AWS memory repricing | short-term memory moved from $0.25/1,000 new events to consumption-based pricing on 2026-10-06 | aws.amazon.com/bedrock/agentcore/pricing; builder.aws.com AgentCore hidden costs |
| S17 | Vertex AI Agent Engine rates | sessions and Memory Bank $0.25 per 1,000 events; runtime $0.0864/vCPU-hr, memory $0.0090/GB-hr | cloudzero.com "Google Vertex AI Pricing 2026"; majormatters.co Vertex AI Agent Builder pricing (as of Sep 2026) |
| S18 | Vertex free tier | from Sep 2026, 50 vCPU-hrs, 100 GiB-hrs memory, 1 GiB-month storage free per account per month | jonjones.ai Vertex AI Agent Builder operator guide 2026 |
| S19 | Pinecone tiers | Starter $0 (2 GB storage, 2M write / 1M read units per month, us-east-1); Standard $50/mo minimum; Enterprise $500/mo | pecollective.com/tools/pinecone; layer3labs.io "Is Pinecone Free?" |
| S20 | Pinecone billing model | serverless, $0.33/GB storage + read/write units | spendark.com "Vector Database Pricing 2026" |
| S21 | Redis licensing | Redis 8 is **tri-licensed AGPLv3 / RSALv2 / SSPLv1**; AGPLv3 is OSI-approved. Redis 7.2 and earlier are BSD; 7.4–7.8 source-available only | acemq.com/guides/redis-licensing (checked 2026-10-26); developersdigest.tech/vector-databases/redis (quoting redis LICENSE) |
| S22 | Redis vector pricing | free 30 MB tier; Pro $200/mo minimum for production-grade vector workloads | resources.rework.com "Best Vector Databases in 2026" |
| S23 | Weaviate cloud tiers | Sandbox 14-day; Flex $45/mo min; Plus $280/mo annual; Premium custom (BYOC, HIPAA). The $25/mo Serverless tier was **retired Oct 2025** | ranksquire.com "Weaviate Cloud Pricing 2026" |
| S24 | Weaviate licence | BSD-3, self-hosted $0 licence, full feature set; identical codebase self-hosted or managed | ranksquire.com; tech-insider.org Pinecone vs Weaviate vs Qdrant 2026 |
| S25 | watsonx.governance tiers | free trial (Essentials, 200 resource units, 3 use cases); Essentials $0.60 per resource unit; Standard/Premium/on-prem **quote-only**; on-prem priced per VPC | aicompliancevendors.com/vendors/ibm-watsonx-governance (checked 2026-09-21); kosmoy.com IBM comparison |
| S26 | watsonx.governance frameworks + standing | EU AI Act, NIST AI RMF, ISO/IEC 42001 accelerators; Gartner Leader, first MQ for AI Governance Platforms, 2026-06-16 (13 vendors assessed) | kosmoy.com; aicompliancevendors.com |
| S27 | ServiceNow AI Control Tower scope | expanded at Knowledge 2026 to Discover / Observe / Govern / Secure / Measure across any AI system; 30 enterprise integrations; Google Cloud, AWS, Azure, SAP, Oracle, Workday | newsroom.servicenow.com press release, Knowledge 2026 |
| S28 | ServiceNow pricing | **no published price for AI Control Tower**; tier uplifts of 20–30% reported for Foundation/Advanced bundles. v3's "six figures" is therefore unverified | finance.yahoo.com ServiceNow AI Control Tower (2026); erp.today Knowledge 2026 |
| S29 | Lyzr OpenController capability | signed record generated by the control that allowed or refused each call; two-person rule on every promotion including admins; deployed inside the customer's cloud account | lyzr.ai/blog/best-tools-for-ai-compliance-and-audit-trails (2026) |
| S30 | Lyzr pricing | platform Free / $19 Starter / $99 Pro / $999 Organization; production runs $0.08 per agent run (cloud), $0.03 (VPC); OpenController itself quote-only | landbase.com "Lyzr Pricing in 2026"; reply.io Lyzr review 2026 |

---

## What is deliberately *not* sourced, and is marked as such

Two cells in v3 carried a figure with no published basis. This refresh does not replace
them with a different guess — it marks them:

| Row | v3 claim | Status now |
|---|---|---|
| ServiceNow AI Control Tower — entry | "six figures" | **No published price exists.** Recorded as `quote-only` and flagged `UNVERIFIED` in v3. |
| LangMem — top public price | "$39/seat" | That is LangSmith Plus, a different product. Recorded as carried-but-unverified (`S11`). |

Both are called out in the report's §4 so a reader is never handed an invented number.
