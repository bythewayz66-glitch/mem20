# mem20 Launch — Campaign Plan & Tracking Scheme (v3)

**Owner:** mem20 GTM Team Lead · **Seat:** Head of Marketing & Demand Generation / Data & Revenue Analytics Lead
**Supersedes:** Campaign Plan v2 (`published/sites/66161135-…/documents/mem20-gtm-v2/mem20-campaign-plan-v2.md`, 2026-10-14)
**Campaign code:** `mem20_launch_2026q4`
**Updated:** 2026-10-26 — base URL repointed off the 403 CDN, tool surface to 270/27, install line to source-only, benchmark section reinstated under its own caveat
**Status:** Ready for execution — one owner action outstanding (§8)

---

## 0. Scope & Binding Inputs

| Input | Reference |
|---|---|
| **Public base URL (the only one)** | **https://bythewayz66-glitch.github.io/mem20/** — HTTP 200, byte-identical to `docs/index.html` at HEAD `7c0b3e8` |
| Launch copy pack (v3) | `docs/gtm/mem20-launch-copy.md` (this directory) |
| **Claim ledger (v3)** | `docs/gtm/claim-ledger.md` (this directory) |
| Sales one-pager (v3) | `docs/gtm/mem20-sales-one-pager.md` (this directory) |
| Canonical repo | **github.com/bythewayz66-glitch/mem20** — public, `main`, MIT, HEAD `7c0b3e8` at capture (**v3.0.0 at that HEAD; the shipped tree is v3.1.0 at `27c1e5fb`**) |
| Install path | `git clone https://github.com/bythewayz66-glitch/mem20.git` → `pip install -r requirements.txt` — **no PyPI package exists** |
| Binding rules | Copy pack v3 §6 (claim ledger index) and §7 (guardrails) |

**Positioning wedge (do not dilute):** *"Auditable agent memory — the memory layer you can prove."*
The category answer is **"they optimize retrieval; nobody leads with auditability."** Never a retrieval-quality race.

### Three corrections from v2 that change every tracked link

1. **The base URL was wrong in a way that broke the campaign.** v2's base page was a `static.teamily.ai/sites/…` URL. Every `/sites/` path returns **403 to an anonymous request** — re-verified today on v2's own launch page and on the orchestrator status page. A campaign pointed at a 403 logs zero referral sessions and reads as a dead product. **Base URL is now the GitHub Pages site.** No `/sites/` URL appears anywhere in this plan.
2. **The tool surface is 270 / 27, not 268 / 26.** The live handshake returns 270 and 27 mixins register. Every asset, directory listing and ad line changes.
3. **The benchmark table is back — restricted.** v2 said the repo shipped no benchmark. At this HEAD `benchmarks/results/latest.md` ships on `main`. It may be cited **only** with its own "not comparable to competitor benchmarks" warning and with the adversarial 0.000 row visible.

---

## 1. Campaign Definition

**Objective.** Drive qualified developer and regulated-industry traffic to the public site and the canonical GitHub repo; convert to stars / clones / self-host installs; generate enterprise inbound — with every placement attributable.

**Primary KPIs (the only ones that count):**
- GitHub **stars delta** and **unique cloners** during the launch window
- **Referral sessions** to the Pages site, split by channel
- **HN front-page rank + comment quality**; **Product Hunt rank/upvotes**
- **Qualified inbound** (regulated-industry / platform-infra conversations started)

**Explicitly NOT success metrics:** raw impressions, follower counts, "reach."

**Target segments:**
1. **PRIMARY** — AI platform/infra engineers building production agents (LangGraph, CrewAI, Pydantic AI) who need memory that is trustworthy **and** self-hostable.
2. **SECONDARY** — regulated-industry AI teams (fintech, healthcare, legal, gov) where provenance/audit is a hard requirement.
3. **TERTIARY** — OSS / self-host-first teams and MCP-ecosystem builders.

**Baseline (measured 2026-10-26, GitHub API):** `stargazers_count = 1`, `forks_count = 0`, `open_issues = 9`, `watchers = 1`. Any dashboard panel predating this that shows "repo not resolvable / 404" is stale — the repo resolves.

---

## 2. Channel Strategy (Tiered)

| Tier | Channels | Timing | Role |
|---|---|---|---|
| **Tier 1 — Day 0** | Hacker News (Show HN), GitHub / OSS community, MCP ecosystem directories | Launch day | Primary spike; the audience that cares about the wedge |
| **Tier 2 — Day 1–3** | Product Hunt, Reddit (r/LocalLLaMA, r/MachineLearning, r/LangChain), dev.to / Medium technical deep-dive, LangChain & MCP Discord/Slack | Days 1–3 | Sustain + broaden; technical credibility |
| **Tier 3 — Day 3–10** | LinkedIn (regulated/enterprise angle), X/Twitter amplification, targeted outbound | Days 3–10 | Enterprise pipeline + long tail |

**Channel note — Issues, not Discussions.** The repo has `has_issues=true` and `has_discussions=false`. "Open an issue" is a **valid** routing instruction; a Discussions board is **not** — do not route anyone there. Open-ended community goes to Discord / Reddit / dev.to.

---

## 3. UTM / Tracking Scheme

**Convention:** `utm_source` (platform) · `utm_medium` (channel type) · `utm_campaign` (constant) · `utm_content` (placement/variant)

- `utm_campaign` = **`mem20_launch_2026q4`** (constant across every link)
- **Base page URL:** `https://bythewayz66-glitch.github.io/mem20/`
- **Outbound repo link (every channel):** `https://github.com/bythewayz66-glitch/mem20`

### Per-channel link table (copy-paste ready)

| # | Channel | Placement | Full tracked URL |
|---|---|---|---|
| 1 | Hacker News | Show HN post | `https://bythewayz66-glitch.github.io/mem20/?utm_source=hn&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=show_hn` |
| 2 | GitHub | Repo homepage / README | `https://bythewayz66-glitch.github.io/mem20/?utm_source=github&utm_medium=oss&utm_campaign=mem20_launch_2026q4&utm_content=readme` |
| 3 | MCP directories | Listing | `https://bythewayz66-glitch.github.io/mem20/?utm_source=mcp_directory&utm_medium=directory&utm_campaign=mem20_launch_2026q4&utm_content=listing` |
| 4 | Product Hunt | Launch post | `https://bythewayz66-glitch.github.io/mem20/?utm_source=producthunt&utm_medium=launch_platform&utm_campaign=mem20_launch_2026q4&utm_content=ph_launch` |
| 5 | Reddit | r/LocalLLaMA | `https://bythewayz66-glitch.github.io/mem20/?utm_source=reddit&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=localllama` |
| 6 | Reddit | r/MachineLearning | `https://bythewayz66-glitch.github.io/mem20/?utm_source=reddit&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=machinelearning` |
| 7 | Reddit | r/LangChain | `https://bythewayz66-glitch.github.io/mem20/?utm_source=reddit&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=langchain` |
| 8 | dev.to | Technical deep-dive | `https://bythewayz66-glitch.github.io/mem20/?utm_source=devto&utm_medium=blog&utm_campaign=mem20_launch_2026q4&utm_content=deep_dive` |
| 9 | Medium | Technical deep-dive | `https://bythewayz66-glitch.github.io/mem20/?utm_source=medium&utm_medium=blog&utm_campaign=mem20_launch_2026q4&utm_content=deep_dive` |
| 10 | Discord/Slack | LangChain & MCP communities | `https://bythewayz66-glitch.github.io/mem20/?utm_source=discord&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=langchain_mcp` |
| 11 | LinkedIn | Enterprise / regulated angle | `https://bythewayz66-glitch.github.io/mem20/?utm_source=linkedin&utm_medium=social&utm_campaign=mem20_launch_2026q4&utm_content=enterprise_angle` |
| 12 | X / Twitter | Launch thread | `https://bythewayz66-glitch.github.io/mem20/?utm_source=x&utm_medium=social&utm_campaign=mem20_launch_2026q4&utm_content=thread` |

### Analytics constraint — read this before promising event data

The Pages site is **static HTML with no analytics snippet**, and GitHub Pages gives no server-side request logs. So:

- **What is measurable today:** `utm_*` query strings (once a snippet exists), GitHub-native counters (`stars`, `forks`, `watchers`, `open_issues`, traffic/clone data for repo admins), and platform-native metrics (HN rank, PH rank, Reddit vote ratio).
- **What is NOT measurable today:** on-page events. v2's event taxonomy (`cta_click_github`, `install_copy`, `partition_demo_view`, `promotion_gate_view`, `limits_view`) is retained below as the **spec for the next page version**, not as something currently firing.
- **Do not report a metric you cannot source.** No blended "traffic went up" claims.

### Event taxonomy (spec for when a snippet is added)

| Event | Fires on | Why it matters |
|---|---|---|
| `page_view` | Page load | Top of funnel, by channel |
| `cta_click_github` | Any GitHub CTA click | Primary conversion intent |
| `install_copy` | Install-command copy | Self-host intent (the wedge audience) |
| `partition_demo_view` | Partition code capture in viewport | Proof-seeking behaviour |
| `promotion_gate_view` | The promotion-path table in viewport | Trust signal: did they read the open path? |
| `benchmark_view` | Benchmark table in viewport | Trust signal — **reinstate only with the caveat block adjacent** |
| `limits_view` | "What we do not claim" in viewport | Trust signal — did they read the caveats? |

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
- **Days 8–30:** weekly roll-up + post-launch readout with channel ROI ranking

**Attribution rule:** every reported number must trace to a `utm_content` value or a platform-native metric. No blended claims.

---

## 5. Launch-Day Sequencing (collision avoidance)

| When | Action | Notes |
|---|---|---|
| **T-1 day** | Prep: repo `homepage` field repointed off the 403 `/sites/` URL (§8), MCP directory listings submitted, tracked links staged, Pages site QA'd on mobile | No public posts |
| **Day 0, 08:00–09:00 ET (Tue–Thu)** | **Show HN** post goes live | HN rewards early-morning ET weekday posts; be present in comments for 4h |
| **Day 0, +2h** | **X thread** amplification | Drives secondary traffic into the HN spike |
| **Day 0, +6h** | **GitHub homepage/README** link + MCP directory listings live | Captures the OSS long tail |
| **Day 1** | **Reddit** (r/LocalLLaMA first, then r/MachineLearning, r/LangChain) | Stagger 4h apart; each with its own `utm_content` |
| **Day 2, 00:01 PT** | **Product Hunt** launch | Deliberately NOT on Day 0 — avoids colliding with HN and lets PH run its own 24h cycle |
| **Day 3** | **dev.to / Medium** deep-dive + Discord/Slack shares | Technical credibility layer |
| **Day 3–10** | **LinkedIn** enterprise angle + targeted outbound | Regulated-industry pipeline |

**Collision rule:** HN and Product Hunt never launch the same day. HN owns Day 0; PH owns Day 2.

---

## 6. Guardrails Compliance Checklist (binding on ALL campaign copy)

- [ ] **Tool surface is 270 tools / 27 domains.** No 257, 258 or 268 anywhere.
- [ ] **No PyPI implication** — no `pip install mem20`, no PyPI badge, no "coming soon". Install is `git clone` + `pip install -r requirements.txt`.
- [ ] **No `/sites/` URL in any tracked link, ad, post, bio or listing.** Base URL is `https://bythewayz66-glitch.github.io/mem20/`.
- [ ] **Benchmark numbers carry the "not comparable to competitor benchmarks" warning** and keep the adversarial 0.000 row visible.
- [ ] **No cross-vendor comparison** — never set mem20 numbers against Mem0 LoCoMo 92.5 / LongMemEval 94.4 or Zep DMR 94.8% (vendor self-reported, different corpora).
- [ ] **Promotion gate described with its residual free-text path** — never "tamper-proof", "unfakeable" or "airtight".
- [ ] **House numbers labelled as house numbers** — $1.28B TAM / $282M SAM / $1.68M SOM / $14,000 blended ACV are restated, not re-measured.
- [ ] **Banned phrasings absent:** "provably secure", "tamper-proof memory", "matches Mem0", "beats Zep", "industry-leading retrieval", "0.0 leak rate" (as a benchmark), "65 distinct implementations", any unqualified superlative.
- [ ] **No competitor disparagement** — the line is "they optimize retrieval; nobody leads with auditability."
- [ ] Every published number traces to claim ledger v3.

---

## 7. Ownership & Handoff

| Step | Owner | Status |
|---|---|---|
| 1. Market research | Market Research | ✅ Done |
| 2. Launch copy | Slides Assistant | ✅ Done (v1 → v2) |
| 3. Launch page | Webpage Developer | ✅ Done — Pages site live |
| 4. Campaign + tracking | Analytics Reporter | ✅ v2 → ✅ **v3 (this document)** |
| 5. GTM/positioning/launch correction | mem20 GTM Team Lead | ✅ **This document + copy pack v3 + claim ledger v3 + one-pager v3** |
| 6. Funnel instrumentation on the Pages surface | **Data & Revenue Analytics Lead** | ⏭️ **Next** — see §8 |

**Finish condition:** every tracked link resolves to a 200 for an anonymous visitor, the Pages surface carries a working analytics snippet or a documented decision not to, and the repo `homepage` field no longer points at a 403. Until the third is true, the most-clicked link on the repo is a dead end.

---

## 8. Outstanding owner actions (not GTM-runnable)

1. **Repo `homepage` field is a 403.** GitHub API returns `homepage: "https://static.teamily.ai/sites/ca954f26-…/webpages/mem20-site/index.html"` — an anonymous request to it returns **403**. One-field fix: point it at `https://bythewayz66-glitch.github.io/mem20/?utm_source=github&utm_medium=oss&utm_campaign=mem20_launch_2026q4&utm_content=readme`. Whoever holds repo admin does this; it is the highest-leverage single change in this plan.
2. **`docs/CNAME` — RESOLVED 2026-10-31.** It names `mem20.com`, which resolves and returns 200. The old legacy-zone hostname is retired and must not be cited; the CNAME branch (creating a DNS record for it) is obsolete.
3. ~~**`docs/index.html` still says 268 / 26 domains.**~~ **Closed.** Re-measured at `27c1e5fb`: **0** occurrences of `268`, **10** of `270`. Campaign copy and the public page now agree.
4. **One in-tree doc still disagrees with the live surface:** `docs/02-tools-reference.md` says 268/26. `toolchest/inventory.json` was regenerated 2026-10-29 and now reports `counts.mcp: 0`, so it no longer contradicts the surface — it simply no longer counts it. Same P1 owner, same retirement.
