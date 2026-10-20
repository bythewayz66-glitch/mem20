# mem20 Launch — Campaign Plan & Tracking Scheme (v2)

**Owner:** mem20 GTM Team Lead · **Seat:** Head of Marketing & Demand Generation / Data & Revenue Analytics Lead
**Supersedes:** Campaign Plan v1 (`documents/mem20-campaign/mem20-campaign-plan.md`)
**Campaign code:** `mem20_launch_2026q4`
**Updated:** 2026-10-14 — repo pointer, launch-page URL, benchmark claims and event taxonomy all corrected
**Status:** Ready for launch execution

---

## 0. Scope & Binding Inputs

| Input | Reference |
|---|---|
| Launch page (v2, LIVE) | https://static.teamily.ai/sites/66161135-9dd3-4110-9d76-87b9e526a037/webpages/mem20-launch/index.html |
| Launch copy pack (v2) | https://static.teamily.ai/sites/66161135-9dd3-4110-9d76-87b9e526a037/documents/mem20-gtm-v2/mem20-launch-copy-v2.md |
| **Claim ledger (v2)** | https://static.teamily.ai/sites/66161135-9dd3-4110-9d76-87b9e526a037/documents/mem20-gtm-v2/claim-ledger.md |
| **Canonical repo** | **github.com/bythewayz66-glitch/mem20** (public, `main`, v2.1.0rc2, MIT, HEAD `c274404`) |
| Binding rules | Copy pack v2 **Section 6 (claim ledger)** and **Section 7 (guardrails)** — every number published must trace to the ledger; every guardrail applies to campaign copy too. |

**Positioning wedge (do not dilute):** *"Auditable agent memory — the memory layer you can prove."*
The category answer is **"they optimize retrieval; nobody leads with auditability."** Never a retrieval-quality race.

### ⚠️ Three corrections from v1 that change campaign copy

1. **Repo pointer.** v1 pointed at `JaysonAIOnline/mem20`, which **404s**. Every campaign asset, tracked link and bio must use **`bythewayz66-glitch/mem20`**.
2. **The benchmark table is gone.** v1's guardrail said "adversarial 0.000 must stay disclosed." There is **no benchmark result of any kind** in the canonical repo — no `benchmarks/` directory, no published LoCoMo/LongMemEval/DMR run. The disclosure is now a stronger, simpler one: *"no published retrieval benchmark; we don't claim parity with anyone."*
3. **Launch page URL moved.** The v1 page is superseded by the v2 page above. All 12 tracked links re-point.

---

## 1. Campaign Definition

**Objective.** Drive qualified developer and regulated-industry traffic to the launch page and the canonical GitHub repo, converting to stars / clones / self-host installs, and generating enterprise inbound — with every placement attributable.

**Primary KPIs (the only ones that count):**
- GitHub **stars delta** and **unique cloners** during the launch window
- **Referral sessions** to the launch page, split by channel
- **HN front-page rank + comment quality**; **Product Hunt rank/upvotes**
- **Qualified inbound** (regulated-industry / platform-infra conversations started)

**Explicitly NOT success metrics:** raw impressions, follower counts, "reach."

**Target segments:**
1. **PRIMARY** — AI platform/infra engineers building production agents (LangGraph, CrewAI, Pydantic AI) who need memory that is trustworthy **and** self-hostable.
2. **SECONDARY** — regulated-industry AI teams (fintech, healthcare, legal, gov) where provenance/audit is a hard requirement.
3. **TERTIARY** — OSS / self-host-first teams and MCP-ecosystem builders.

---

## 2. Channel Strategy (Tiered)

| Tier | Channels | Timing | Role |
|---|---|---|---|
| **Tier 1 — Day 0** | Hacker News (Show HN), GitHub / OSS community, MCP ecosystem directories | Launch day | Primary spike; the audience that cares about the wedge |
| **Tier 2 — Day 1–3** | Product Hunt, Reddit (r/LocalLLaMA, r/MachineLearning, r/LangChain), dev.to / Medium technical deep-dive, LangChain & MCP Discord/Slack | Days 1–3 | Sustain + broaden; technical credibility |
| **Tier 3 — Day 3–10** | LinkedIn (regulated/enterprise angle), X/Twitter amplification, targeted outbound | Days 3–10 | Enterprise pipeline + long tail |

---

## 3. UTM / Tracking Scheme

**Convention:** `utm_source` (platform) · `utm_medium` (channel type) · `utm_campaign` (constant) · `utm_content` (placement/variant)

- `utm_campaign` = **`mem20_launch_2026q4`** (constant across every link)
- **Base page URL (v2):** `https://static.teamily.ai/sites/66161135-9dd3-4110-9d76-87b9e526a037/webpages/mem20-launch/index.html`
- **Outbound repo link (every channel):** `https://github.com/bythewayz66-glitch/mem20`

### Per-channel link table (copy-paste ready)

| # | Channel | Placement | `utm_content` |
|---|---|---|---|
| 1 | Hacker News | Show HN post | `?utm_source=hn&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=show_hn` |
| 2 | GitHub | README / repo link | `?utm_source=github&utm_medium=oss&utm_campaign=mem20_launch_2026q4&utm_content=readme` |
| 3 | MCP directories | Listing | `?utm_source=mcp_directory&utm_medium=directory&utm_campaign=mem20_launch_2026q4&utm_content=listing` |
| 4 | Product Hunt | Launch post | `?utm_source=producthunt&utm_medium=launch_platform&utm_campaign=mem20_launch_2026q4&utm_content=ph_launch` |
| 5 | Reddit | r/LocalLLaMA | `?utm_source=reddit&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=localllama` |
| 6 | Reddit | r/MachineLearning | `?utm_source=reddit&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=machinelearning` |
| 7 | Reddit | r/LangChain | `?utm_source=reddit&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=langchain` |
| 8 | dev.to | Technical deep-dive | `?utm_source=devto&utm_medium=blog&utm_campaign=mem20_launch_2026q4&utm_content=deep_dive` |
| 9 | Medium | Technical deep-dive | `?utm_source=medium&utm_medium=blog&utm_campaign=mem20_launch_2026q4&utm_content=deep_dive` |
| 10 | Discord/Slack | LangChain & MCP communities | `?utm_source=discord&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=langchain_mcp` |
| 11 | LinkedIn | Enterprise / regulated angle | `?utm_source=linkedin&utm_medium=social&utm_campaign=mem20_launch_2026q4&utm_content=enterprise_angle` |
| 12 | X / Twitter | Launch thread | `?utm_source=x&utm_medium=social&utm_campaign=mem20_launch_2026q4&utm_content=thread` |

> Replace the leading `?` with the full base page URL above, then append the query string. Every placement uses its own `utm_content` so a single channel's variants stay separable.

### Event taxonomy (spec for when the page's analytics snippet is wired)

| Event | Fires on | Why it matters |
|---|---|---|
| `page_view` | Page load | Top of funnel, by channel |
| `cta_click_github` | Any GitHub CTA click | Primary conversion intent |
| `install_copy` | Install-command copy | Self-host intent (the wedge audience) |
| `partition_demo_view` | Partition code capture in viewport | Proof-seeking behaviour — **replaces v1's `benchmark_table_view`** |
| `promotion_gate_view` | The four-path promotion table in viewport | Trust signal: did they read the open path? |
| `limits_view` | "What we do not claim" in viewport | Trust signal — did they read the caveats? |

> **Note:** the launch page is static with no analytics snippet. UTM attribution works today via the referrer/query string; the taxonomy above is the spec for a follow-up page version if event-level tracking is wanted. v1's `comparison_view` event is **dropped** — the v2 page replaces the competitor comparison table with the four-path promotion table, which is verifiable from the repo and doesn't rest on third-party self-reported figures.

---

## 4. Measurement Plan

**Per-channel success definition (not vanity):**

| Channel | Primary signal | Secondary signal | Threshold to call it "working" |
|---|---|---|---|
| Hacker News | Front-page rank + referral sessions | Comment quality / substantive questions | Front page ≥ 2h; ≥ 500 referral sessions |
| GitHub / OSS | Stars delta | Unique cloners | ≥ 100 stars in 72h |
| MCP directories | Listing → page sessions | Repo clicks | ≥ 50 sessions |
| Product Hunt | Rank + upvotes | Page sessions | Top-5 of the day |
| Reddit | Upvote ratio + comment depth | Page sessions | ≥ 50 upvotes, no removal |
| dev.to / Medium | Read-through + repo clicks | Page sessions | ≥ 1k reads |
| LinkedIn | Qualified inbound | Page sessions | ≥ 3 enterprise conversations |
| X | Reposts + repo clicks | Page sessions | ≥ 20 reposts |

**Reporting cadence:**
- **Launch day:** hourly snapshot (rank, sessions, stars) — 08:00–20:00 ET
- **Days 1–7:** daily roll-up (per-channel sessions, stars/clones delta, inbound)
- **Days 8–30:** weekly roll-up + a post-launch readout with channel ROI ranking

**Attribution rule:** every reported number must be traceable to a `utm_content` value or a platform-native metric (HN rank, PH rank, GitHub stars). No blended "traffic went up" claims.

**Baseline correction:** the repo is **public with 0 stars and 0 forks** as of 2026-10-14 (GitHub API). v1's §0 input row and the launch-day dashboard both reported "repo not resolvable (404)". That is resolved — the repo now resolves, so the dashboard will read real numbers on launch day. Any dashboard panel still showing 404 is stale.

---

## 5. Launch-Day Sequencing (collision avoidance)

| When | Action | Notes |
|---|---|---|
| **T-1 day** | Prep: repo README corrected to the canonical clone URL, MCP directory listings submitted, tracked links staged, v2 page QA'd | No public posts. **See the blocker in §8 — the repo README still prints the dead clone URL.** |
| **Day 0, 08:00–09:00 ET (Tue–Thu)** | **Show HN** post goes live | HN rewards early-morning ET weekday posts; be present in comments for 4h |
| **Day 0, +2h** | **X thread** amplification | Drives secondary traffic into the HN spike |
| **Day 0, +6h** | **GitHub README** link + MCP directory listings live | Captures the OSS long tail |
| **Day 1** | **Reddit** (r/LocalLLaMA first, then r/MachineLearning, r/LangChain) | Stagger 4h apart; each with its own `utm_content` |
| **Day 2, 00:01 PT** | **Product Hunt** launch | Deliberately NOT on Day 0 — avoids colliding with HN and lets PH run its own 24h cycle |
| **Day 3** | **dev.to / Medium** deep-dive + Discord/Slack shares | Technical credibility layer |
| **Day 3–10** | **LinkedIn** enterprise angle + targeted outbound | Regulated-industry pipeline |

**Collision rule:** HN and Product Hunt never launch the same day. HN owns Day 0; PH owns Day 2.

---

## 6. Guardrails Compliance Checklist (binding on ALL campaign copy)

- [ ] **No LoCoMo / LongMemEval / DMR claim, and no retrieval benchmark of any kind** — the repo ships none at this commit.
- [ ] **No "0.0 leak rate" or "1.000/0.800/0.000 hit rate" figure** — v1's numbers had no source and are withdrawn. The only survivable version is the captured `contamination_rate 0.0 / CLEAN` audit output.
- [ ] **Promotion gate described with its residual free-text path** — never "tamper-proof", "unfakeable" or "airtight".
- [ ] **Banned phrasings absent:** "provably secure", "tamper-proof memory", "matches Mem0", "beats Zep", "industry-leading retrieval", "65 distinct implementations", any unqualified superlative.
- [ ] **No competitor disparagement** — the line is "they optimize retrieval; nobody leads with auditability."
- [ ] **No `pip install mem20`** — the package is not on PyPI; install is from source.
- [ ] Every published number traces to the copy pack v2 **claim ledger**.

---

## 7. Ownership & Handoff

| Step | Owner | Status |
|---|---|---|
| 1. Market research | Market Research | ✅ Done |
| 2. Launch copy | Slides Assistant | ✅ Done (superseded by v2) |
| 3. Launch page | Webpage Developer | ✅ Live (superseded by v2) |
| 4. Campaign + tracking | Analytics Reporter | ✅ Done (superseded by v2) |
| 5. **GTM/positioning/launch correction** | **mem20 GTM Team Lead** | ✅ **This document** |
| 6. **Sidney/gabe publish** | **Server Builder** | ⏭️ **Next — see §8** |

**Finish condition:** the corrected GTM asset set reaches the Sidney server over ssh/sftp/rsync routed through gabe, and the mem20 repo README is corrected to the canonical clone URL. Until both are true, a launch reader who runs the first command on the landing page reaches a repo whose own README tells them to clone a 404.

---

## 8. Blocker for the publish leg

**Two things must ship together, or the launch is incoherent:**

1. **The corrected asset set** — this plan, the copy pack v2, the claim ledger, and the v2 launch page. Manifest and exact commands: `documents/mem20-sidney-publish-packet.md`.
2. **A repo README fix owned by the repo owner.** `README.md` line 186 still instructs `git clone https://github.com/JaysonAIOnline/mem20.git`, and its badges (lines 9–10) point at the same dead org — **6 references in `README.md`, 17 across the shipped top-level docs**, plus `docs/01-architecture.md` and `docs/02-tools-reference.md` still advertising "111 tools / 15 domains" against the README's own 257 / 26. GTM cannot fix this; it is a one-commit change for whoever holds the push.

**The Sidney leg is not runnable from this sandbox** — no SSH keys or config exist under `~/.ssh`, and `sidney` / `gabe` do not resolve via DNS. That leg is relayed to **Server Builder**, the infra owner in this group.
