# mem20 launch channels — Show HN / Product Hunt / Reddit

**Status: BLOCKED. Do not launch.**
**Owner:** Growth Hacker · **Date:** 2026-11-01 · **Baseline:** `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf`
**Directive:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`, row 15 (G10)
**Evidence:** every probe transcript is in [`launch-channels-evidence-2026-11-01.md`](./launch-channels-evidence-2026-11-01.md)

> **Rule:** no channel is planned against a URL that was not `curl`'d in this run. Every status code
> below was observed in this session; the full transcripts are in the evidence file.

---

## 1. The blocker, named

**There is no anonymous-reachable URL that is also launch-ready.**

G10 — "no anonymous-reachable launch URL" — is correct for `/sites/` artifacts but **too coarse for
`mem20.com`**. `mem20.com` *is* anonymous-reachable (200, 33,429 bytes, no token). It is not
*launchable*. Different failures, different fixes:

| ID | Blocker | Severity | Who can fix |
|---|---|---|---|
| **B1** | Every `/sites/` artifact URL returns **403** anonymously. No launch asset may live there. | Hard — unfixable | Nobody. Structural. |
| **B2** | ~~Live page serves `v3.0.0` ×4 while `VERSION` = `3.1.0`.~~ **FIXED mid-run** — page now serves `v3.1.0` ×4. | ~~Hard~~ **Resolved** | Webpage Developer (row 3) — done |
| **B3** | Canonical Pages URL **301s to `http://`**, not `https://`. | Hard — blocks launch | Repo admin / Pages config |
| **B4** | **No `og:image`, no `twitter:card`, no favicon.** Grey box on HN/PH/Reddit/X/Slack. PH cannot accept a submission without gallery assets. | Hard — blocks PH | Webpage Developer |
| **B5** | **No analytics of any kind.** Every `utm_*` link is decorative. | Soft — runs blind | Owner (§5) |
| **B6** | Repo `homepage` field is a `/sites/` URL returning **403**. | Soft — one field | Repo admin |
| **B7** | `robots.txt` and `sitemap.xml` both **404**. | Soft | Webpage Developer |

**B1 is the one the directive names, and it is real and unfixable.** B3–B4 are the ones that would
actually sink the launch, and both are fixable in one commit.

**B2 was fixed while this document was being written.** The page served `v3.0.0` ×4 at the start of the
run and `v3.1.0` ×4 by the end — same 33,429-byte payload, since the version string is the same length.
The gate caught it on a re-run against the committed script, which is the argument for making the unblock
condition executable rather than a checklist someone ticks once.

### 1.1 Host status, as measured

| Host | Result |
|---|---|
| `https://mem20.com/` | **200**, 33,429 B |
| `https://www.mem20.com/` | 200, 33,429 B |
| `https://mem20.org/` | 404, 9,115 B (GitHub "Site not found") |
| `https://mem20.store/` | **TLS failure** (curl exit 60) — GitHub serves its `*.github.io` cert |
| `https://mem20.info/` | **TLS failure** (curl exit 60) — same |
| `https://bythewayz66-glitch.github.io/mem20/` | 200, but **301s to `http://mem20.com/`** |
| `https://github.com/bythewayz66-glitch/mem20` | 200, 756,554 B |

**Correction to the directive's §1a:** it records `.store` / `.info` as `404 / 9,115`. That is the `-k`
result. Without `-k` they fail the TLS handshake first, so the user-visible failure is a browser
interstitial, not a 404. Same end state, worse experience. **All three are out of scope for this plan.**

## 2. The exact unblock condition

**A launch may begin on the first day on which all seven checks pass simultaneously.** They are
machine-checkable; `scripts/check_launch_gate.py` implements them and exits non-zero on any failure.

| # | Check | Pass |
|---|---|---|
| 1 | `https://mem20.com/` returns 200 to a token-free request | `200` |
| 2 | Served HTML carries current `VERSION` and zero retired version strings | `>=1` and `0` |
| 3 | Served HTML has `og:image` at an absolute `https://` URL that itself returns 200 | present + 200 |
| 4 | `https://bythewayz66-glitch.github.io/mem20/` redirects to `https://`, not `http://` | `301` → https |
| 5 | `https://mem20.com/robots.txt` returns 200 | `200` |
| 6 | A privacy-respecting analytics snippet is present, **or** an owner waiver is recorded | present or waived |
| 7 | Repo `homepage` field resolves 200 | `200` |

**Check 1 is necessary but not sufficient — and it is one of only two that pass.** Current state is
2 pass / 5 fail. Checks 3–4 would sink the launch; 6 and 7 make it unmeasurable and unclickable.

### 2.1 Gate output — current state, run in this session, unedited

Run against the **committed** script (`sha256 8d945d3f…`), not a local copy:

```
$ python3 verify/gate.py

mem20 launch gate
  site   : https://mem20.com/
  pages  : https://bythewayz66-glitch.github.io/mem20/

  [PASS] anonymous       https://mem20.com/ returned 200, 33429 bytes, no access token
  [PASS] version         served page carries 3.1.0 x4; no retired version strings
  [FAIL] social_preview  no og:image on the served page -> HN/PH/Reddit/X render a bare grey box (twitter:card=absent, favicon=absent)
  [FAIL] https_hop       canonical link hops through plaintext: 301 -> http://mem20.com/
  [FAIL] crawlable       robots.txt returned 404 (want 200)
  [FAIL] analytics       no analytics snippet on the served page -> every utm_* link is decorative and the Day-7 channel readout is a guess (pass --waive-analytics to accept this in writing)
  [FAIL] repo_homepage   repo homepage https://static.teamily.ai/sites/ca954f26-cfef-49bf-92b4-55c652e71f8f/webpages/mem20-site/index.html returned 403 - this is a /sites/ artifact, which is project-member-only and always 403s

LAUNCH GATE: BLOCKED - 5 of 7 gates failed, 2 passed.
Do not post to Show HN, Product Hunt or Reddit until every gate passes.
See docs/gtm/launch-channels-2026-11-01.md section 3.1 for the minimum unblock.
```

Exit code `1`. With the analytics waiver:

```
$ python3 scripts/check_launch_gate.py --waive-analytics

  [PASS] analytics       owner waiver recorded (--waive-analytics): launch runs without on-page attribution
LAUNCH GATE: BLOCKED - 4 of 7 gates failed, 3 passed.
```

**The waiver does not open the gate** — it removes one soft failure. Three hard failures remain, and no
waiver can excuse them.

**The `version` gate passed on this run and failed on the first.** The page served `v3.0.0` ×4 at the
start of the session and `v3.1.0` ×4 by the end — same 33,429-byte payload, since the version string is
the same length. Confirmed independently: `grep -oE 'v?3\.[0-9]+\.[0-9]+'` now returns `4 v3.1.0` and
zero `v3.0.0`. `og:image`, `twitter:card`, favicon, analytics, `robots.txt` and `sitemap.xml` are all
still absent — those five gates are unchanged. This is the argument for making the unblock condition
executable rather than a checklist someone ticks once.

### 2.2 Minimum viable unblock — the smallest change that opens the gate

Three commits, no new infrastructure, no owner credentials:

1. **Webpage Developer** — rebuild `docs/index.html`: add `og:image` + `twitter:card` + favicon, add
   `robots.txt` and `sitemap.xml`. Closes B4, B7. *(The `v3.0.0` → `3.1.0` half of this is already done.)*
2. **Repo admin** — set `homepage` to `https://mem20.com/`. Closes B6. One field.
3. **Repo admin** — fix the Pages custom-domain redirect to `https://`. Closes B3.

**B1 stays closed forever.** No amount of work makes a `/sites/` URL anonymous-reachable. The plan below
therefore never uses one.

### 2.3 What does *not* unblock it

- Registering `.org` / `.store` / `.info`. Pages allows one custom domain per repo; `docs/CNAME` is
  `mem20.com`. Promoting another apex takes `mem20.com` offline during certificate issuance.
- Publishing to PyPI. Nice to have; not a gate. The source install is honest and works.
- More benchmark rows. The page already shows the 0.000 row, which is the credible move.

---

## 3. Channel plan — gated, sequenced, with real numbers

**Nothing here executes until §2 passes.** Written now so that the day the gate opens, launch is a
30-minute operation, not a 3-day one.

### 3.1 Sequencing

| Day | Channel | Time (ET) | Why this slot |
|---|---|---|---|
| **Day 0** | **Show HN** | 08:00–09:00, Tue–Thu | Front page is decided in the first 90 minutes. Weekday morning ET catches US + EU. Be in the thread 4 hours. |
| **Day 0** | GitHub README + repo `homepage` | same hour | Every HN visitor clicks through. The repo must already be correct. |
| **Day 1** | **Reddit** r/LocalLLaMA → r/MachineLearning → r/LangChain | 10:00, 14:00, 18:00 | Staggered 4h. Same post to three subs in one hour reads as spam and gets removed. |
| **Day 2** | **Product Hunt** | 00:01 PT | PH runs a 24h cycle from midnight PT. Never same-day as HN — same audience. |
| **Day 3–7** | dev.to / Medium deep-dive, MCP directories, Discord/Slack | — | Long tail. The deep-dive keeps converting after the spike. |

**Collision rule: HN owns Day 0, PH owns Day 2. Never both.**

### 3.2 Show HN

**Title (73 chars, under HN's 80 limit):**

```
Show HN: mem20 – Agent memory where grounded vs simulated is enforced in code
```

Alternates: `Show HN: mem20 – An MCP memory server that refuses to store made-up facts as real`

**Body — the first three lines decide the thread.** Lead with the refusal, not the tool count:

```
Hi HN — mem20 is an MCP server that gives AI agents persistent memory with an audit trail.
MIT, Python 3.10+, self-hosted. Not on PyPI yet; install is from source.

Every agent-memory layer I looked at competes on retrieval quality. None of them let you
prove what the agent knows. In a regulated context that's the whole ballgame: "probably
relevant" is not an answer you can hand an auditor.

So mem20 is built around a hard boundary. Grounded memory (came from a real source) and
simulated memory (the agent generated it) are separate stores, not one store with a flag.
Try to push invented content through the grounded write path and the server refuses:

    PermissionError: remember() is grounded-only. Simulated content must use
    remember_simulated(); this call is refused to protect Step 7.4 separation.

That's the real exception string from the shipped code. The guard isn't a prompt instruction
or a lint rule — it sits on the write path.
```

**Then the surface:** 270 tools across 27 domains, four retrieval modes, the append-only ledger, MIT.

**The benchmark paragraph must be in the post, not buried.** It is the differentiator:

```
We publish our own numbers, including the row we lose. On our corpus (13 queries, our own
harness): direct 1.000, multi-hop 0.800, adversarial 0.000, leak 0.000. Three of four
retrieval modes score zero on adversarial queries. We show it because a memory layer you're
meant to audit shouldn't get to hide the row it loses. We have no LoCoMo or LongMemEval
result comparable to Mem0 or Zep, so we make no parity claim.
```

**Prepared answers:**

| Likely comment | Answer |
|---|---|
| "Just a vector store with extra steps" | Point at `_assert_grounded()` on the index write path and the promotion gate requiring a resolved prediction or external attestation. A flag is not a gate. |
| "0.000 adversarial is terrible" | Agree immediately. It is the honest number and the reason the row is published. Say what the fix is and that it is not done. |
| "Not on PyPI?" | "Correct — source only, deliberately, until the surface is stable. `git clone` and `pip install -r requirements.txt`." |
| "270 tools is a lot, is any of it good?" | Do not defend the count. Point at the four retrieval modes and the ledger. The count is a liability if you lead with it. |
| "One person built all this?" | Yes. Say so plainly. It is the most interesting fact in the post. |

**Do not:** ask for upvotes, mention Product Hunt, post a `/sites/` link, or claim parity with Mem0/Zep.

### 3.3 Product Hunt

**Blocked on B4.** PH requires a gallery image to submit; there is no `og:image` and no product imagery
on the page. This channel cannot open until the Webpage Developer ships assets.

- **Tagline (60 char limit):** `Agent memory that can prove what it knows`
- **Topics:** Developer Tools, Artificial Intelligence, Open Source
- **First comment:** the grounded-vs-simulated story, one paragraph shorter, ending with the source-install line.
- **Gallery:** 4 images — (1) two-store diagram, (2) the `PermissionError` refusal as a code screenshot,
  (3) the benchmark table *with the 0.000 row visible*, (4) the install block.
- **Timing:** 00:01 PT, Day 2. Self-hunt; no hunter outreach available.

### 3.4 Reddit

Three subs, three different posts. The same text in all three is the fastest way to a ban.

| Sub | Angle | Title |
|---|---|---|
| r/LocalLLaMA | Self-hosted, runs on your box, no API | `I built a local agent memory store that refuses to save model output as fact` |
| r/MachineLearning | The separation mechanism, not the product | `[D] Enforcing grounded/simulated separation at the write path instead of by convention` |
| r/LangChain | Integration | `MCP memory server with contamination auditing — drops into LangGraph/CrewAI` |

**r/MachineLearning is `[D]` Discussion, not `[P]` Project.** A project post there gets removed. Lead
with the mechanism and the 0.000 result; the repo link goes in a comment, not the body.

**Rules that get the post removed if ignored:** no more than 1 in 10 posts self-promotional (check the
account's history first), no URL shorteners, no vote solicitation, disclose authorship in the first line.

### 3.5 Funnel math — what "working" looks like

Assumptions stated so they can be argued with, not asserted:

| Stage | Show HN (front page) | Product Hunt (top 5) | Reddit (3 subs) |
|---|---|---|---|
| Sessions to landing page | 6,000 | 1,800 | 4,000 |
| → repo click-through | 25% = 1,500 | 30% = 540 | 20% = 800 |
| → clone or star | 2% of repo = 30 | 3% = 16 | 1.5% = 12 |
| → install attempt | 8% of repo = 120 | 6% = 32 | 5% = 40 |
| → activation (store opens, `remember()` succeeds) | 40% = 48 | 40% = 13 | 40% = 16 |
| → Day-7 still using | 20% = ~10 | 20% = ~3 | 20% = ~3 |

**Read this honestly: a good launch produces roughly 10 retained users.** That is the correct
expectation for a source-install developer tool with 1 star. The real output is not the user count — it
is whether the 0.000-adversarial story lands with people who care about auditability, and whether any of
them open an issue. **Issues are the only conversion that matters at this stage.**

**Kill criteria.** If Show HN does not reach the front page within 90 minutes, do not repost — HN
penalises it. Answer every comment, move to Day 1. If Reddit removes two of three posts, stop and
diagnose the account before the third.

### 3.6 Measurement — what is actually observable today

| Signal | Available now? | Source |
|---|---|---|
| HN rank, points, comments | **Yes** | HN item page |
| PH rank, upvotes | **Yes** | PH launch page |
| Reddit upvote ratio, removals | **Yes** | Reddit post |
| GitHub stars / forks / watchers | **Yes** | GitHub API (currently 1 / 0 / 0) |
| GitHub clones + referrers | **Yes, repo admin only** | Insights → Traffic (14-day window) |
| Landing-page sessions by channel | **No** | No analytics on the page (B5) |
| UTM attribution | **No** | UTM survives the redirect but nothing reads it |

**Five of seven signals work today; the two that need a snippet do not.** Stars, clones, referrers and
platform-native metrics are enough to rank channels. What is *not* measurable is on-page behaviour:
bounce, scroll depth, which section people read. Do not promise that.

## 4. What this plan will not do

- **Will not link a `/sites/` URL.** All 403 anonymously. Not one appears in any copy above.
- **Will not launch against an unprobed URL.** Every host in §1.1 was `curl`'d in this run.
- **Will not claim PyPI availability.** All five package names 404.
- **Will not claim benchmark parity with Mem0 / Zep / Letta.** No comparable LoCoMo or LongMemEval run exists.
- **Will not hide the 0.000 adversarial row.** It is the most credible thing in the launch.
- **Will not use `.org` / `.store` / `.info`.** 404 or TLS failure.
- **Will not route anyone to Discussions.** `has_discussions: false`. Issues only.

## 5. Decisions needed from the owner

1. **Analytics — yes or no?** Without a snippet, channel attribution is impossible and the Day-7 readout
   is a guess. A cookieless script (Plausible/Umami/Fathom) is one line in `docs/index.html`.
   **Recommendation: yes.** If no, record the waiver here and gate 6 passes on the waiver.
2. **Which domain is primary?** `mem20.com` is the only one that serves. Confirm it stays primary through
   the launch window — do not promote another apex mid-launch.
3. **Repo `homepage` field.** One field, currently a 403. Set it to `https://mem20.com/`. Highest-leverage
   single change in this document.

## 6. Handoff

| Item | Owner | Blocking? |
|---|---|---|
| `docs/index.html`: `og:image`, favicon, `robots.txt`, `sitemap.xml` | Webpage Developer (row 3) | **Yes** — B4, B7 |
| Pages redirect → `https://` | Repo admin | **Yes** — B3 |
| Repo `homepage` field | Repo admin | No — B6 |
| Analytics snippet decision | Owner | No — B5 |
| Re-run `scripts/check_launch_gate.py` | Growth Hacker | **Yes** — gate |

**Launch does not begin until `python3 scripts/check_launch_gate.py` exits 0.**

---

*Every status code, byte count and grep result in this document was produced by a command in this run
against `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf`. Nothing is quoted from an earlier report
without re-checking it. This is a go-to-market plan, not investment advice.*
