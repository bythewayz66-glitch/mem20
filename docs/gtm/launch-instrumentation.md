# Launch Instrumentation — what is measurable today, and what is not

**Status:** measurement plan, implementable with no third-party account.
**Companion files:** `docs/gtm/utm-registry.csv` (the 12 tracked links), `scripts/check_gtm_claims.py` (the claim gate).
**Baseline:** `main` at `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`.

This document exists to stop the campaign from reporting numbers it cannot source. It states
what the current stack can measure, what it cannot, and the one decision that changes the answer.

---

## 1. The honest starting position: there is no attribution today

The public page is static HTML with **no analytics snippet**. Measured on `main` at the baseline:

| Surface | Analytics loader present? | Evidence |
|---|---|---|
| `docs/index.html` (the live public page) | **No** | 0 matches for `gtag`, `analytics`, `plausible`, `umami`, `posthog`, `googletagmanager` |
| `docs/dashboard.html` | **No** | 6 matches, all prose/placeholder references to a future "site analytics key" — no loader, no endpoint |

Consequence: **a `utm_*` query string is currently recorded nowhere.** The links in
`utm-registry.csv` are correct and they survive the redirect chain (verified below), but until a
snippet exists they are inert. Sending traffic through them today produces no per-channel data.

This is the single most important sentence in this document: **the campaign is not instrumented,
and no amount of link hygiene changes that.**

---

## 2. Redirect topology — verified, and it does preserve the query string

Every tracked link is built on `https://bythewayz66-glitch.github.io/mem20/`. That host does not
serve the page directly; it redirects. Verified anonymously (no token) on 2026-11-01:

| Hop | Result |
|---|---|
| `https://bythewayz66-glitch.github.io/mem20/?utm_...` | **301** → `http://mem20.com/?utm_...` |
| `https://mem20.com/` | **200**, byte-identical to committed `docs/index.html` (md5 `fb8095ebda3f6355b3a4ed8bd28867b4`) |
| `https://mem20.org/` | **200**, a JS redirector that rebuilds the target as `https://mem20.com` + `location.pathname` + `location.search` + `location.hash` |

Two things worth recording because they were previously assumed rather than measured:

1. **The 301 preserves the full query string.** The `Location` header carries
   `utm_source`, `utm_medium`, `utm_campaign` and `utm_content` intact. All 12 links were followed
   end-to-end and all 12 returned **200** with `utm_content` still present in the final URL.
2. **The redirect is `https` → `http`.** The first hop downgrades the scheme. The query survives,
   but a browser that upgrades or a client that refuses the downgrade may not complete the hop.
   Worth fixing at the Pages level; it does not break attribution once a snippet exists.

`mem20.org` is **not** a 404 — it is a working redirector that preserves the query string. Any
earlier note calling it a dead end is wrong.

---

## 3. What CAN be measured today, with no third-party account

These are real, available, and require only repo admin access:

| Signal | Source | Available? | Notes |
|---|---|---|---|
| Repo page views (daily, unique) | GitHub traffic API `traffic/views` | **Yes** | 14-day rolling window only |
| Repo clones (daily, unique) | GitHub traffic API `traffic/clones` | **Yes** | 14-day rolling window only |
| Referring sites | GitHub traffic API `traffic/referrers` | **No — 404** | Endpoint returns `Not Found` for this repo |
| Popular paths | GitHub traffic API `traffic/paths` | **No — 404** | Endpoint returns `Not Found` for this repo |
| Stars / forks / watchers / open issues | Repo metadata | **Yes** | Point-in-time counters |
| HN rank, PH rank, Reddit vote ratio | Platform-native UI | **Yes** | Manual capture, no API key needed |

**The 404s matter.** `traffic/referrers` and `traffic/paths` are the two endpoints that would give
referral attribution without any snippet. Both are unavailable here, so **GitHub cannot substitute
for on-page analytics.** Do not plan around them.

### The noise floor, measured

From the 14-day window ending 2026-10-31:

| Metric | Total | Unique | Daily unique mean | Daily unique sd |
|---|---|---|---|---|
| Repo views | 20 | 8 | 0.71 | 0.83 |
| Repo clones | 13,021 | 901 | 106.29 | 86.63 |

Read this carefully before quoting any launch number:

- **Views are near zero** (8 unique viewers in 14 days). Any launch traffic is a step change from
  almost nothing, which is good for detection but means there is no baseline to compute a lift against.
- **Clones are not a human signal.** 901 unique cloners against 8 unique viewers is not plausible
  human behaviour; it is CI, mirrors and automation. **Do not report clone counts as interest.**
  If clones are used at all, they must be labelled as automation-contaminated.
- With a daily view sd of 0.83, a single day of 5 views is not evidence of anything. The campaign
  needs multi-day aggregation before any per-channel claim is defensible.

---

## 4. What CANNOT be measured today

Stated plainly so no one promises it:

- **Per-channel sessions.** Requires a snippet reading `utm_*`. Not present.
- **On-page events.** The event taxonomy in the campaign plan (`page_view`, `cta_click_github`,
  `install_copy`, `partition_demo_view`, `promotion_gate_view`, `benchmark_view`, `limits_view`)
  is a **specification for a future page version**, not something currently firing.
- **Activation.** See §5 — the current page has no activation step to observe.
- **Referral source.** `traffic/referrers` is 404.
- **Anything beyond 14 days.** GitHub traffic is a rolling window; history is not retained.

---

## 5. Funnel definition — static page vs gateway-required steps

The campaign plan's thresholds ("≥ 500 referral sessions", "≥ 100 stars in 72h") mix two different
kinds of step. They must be reported separately, because only one kind is observable today.

**Observable on static GitHub Pages / `mem20.com` (no server, no snippet):**

| Step | Observable today? | How |
|---|---|---|
| S1. Impression | No | Platform-native only (HN rank, PH rank) |
| S2. Click-through to page | **No** | Needs `utm_*` capture |
| S3. Repo visit | Partially | `traffic/views` — but not attributable to a channel |
| S4. Star / fork | **Yes** | Repo counters, delta over a window |
| S5. Clone | **Yes, but contaminated** | `traffic/clones` — automation-dominated (§3) |

**Gateway-required steps (need a server, an account, or a snippet):**

| Step | Observable today? | Why not |
|---|---|---|
| S6. Install completed | No | No telemetry; source install leaves no trace |
| S7. First successful MCP handshake | No | Local process, no reporting |
| S8. Activation (first useful memory op) | No | No event stream |
| S9. Retention (D7 / D30) | No | No user identity |

**Activation, defined so it can be built later:** a new user is *activated* when they complete a
source install, start the MCP server, and issue one successful tool call against a non-empty store.
That is the earliest point at which the product has done something for them. It is currently
**unobservable** — there is no event at that boundary. Until there is, activation rate cannot be
reported, and any activation figure in launch copy is unsourced.

**Practical consequence for launch reporting:** the only defensible per-channel claim available on
day one is *platform-native* (HN rank, PH rank, Reddit vote ratio) plus *repo-level* deltas
(stars, views) that are **not** attributable to a specific channel. Report it that way.

---

## 6. The one decision needed from the owner

Everything in §4 collapses to a single choice:

> **Add a privacy-respecting analytics script to `docs/index.html`, or accept that the launch has
> no attribution.**

| Option | What it buys | What it costs |
|---|---|---|
| **A. Add a snippet** (Plausible, Umami, or a self-hosted counter) | Per-channel sessions from `utm_*`; the event taxonomy in §4 becomes implementable; the campaign plan's thresholds become checkable | One script tag in `docs/index.html`; a privacy note on the page; a hosting decision for the collector |
| **B. Accept no attribution** | Zero work, zero third-party dependency | Every per-channel number in the campaign plan stays unverifiable; reporting is limited to platform-native rank and unattributed repo deltas |

**Recommendation: A.** The campaign plan already commits to per-channel thresholds and an
attribution rule ("every reported number must trace to a `utm_content` value or a platform-native
metric"). Option B makes that rule unsatisfiable for the primary metric. A self-hosted counter
avoids the third-party dependency if that is the objection.

This is an owner decision, not a GTM-runnable one: it changes the public page.

---

## 7. Known drift found while building this (not fixed here)

**The tool-surface number is inconsistent between CI and the claim ledger.**

| Source | Says | Location |
|---|---|---|
| CI pin | **272** | `.github/workflows/mcp-verify.yml:47` → `MEM20_EXPECTED_TOOLS: "272"` |
| Claim ledger V7 | **270**, and asserts CI pins 270 | `docs/gtm/claim-ledger.md:90` |

The ledger's V7 row states "CI `.github/workflows/mcp-verify.yml` pins `MEM20_EXPECTED_TOOLS: "270"`".
That is no longer true — the pin is 272. The ledger row is stale on its own evidence.

`python3 verify_mcp.py` could not be used to settle it in this environment (it exits with
`EOF from server`), so **272 is reported here as the CI pin, not as a verified handshake count.**
A raw `grep -rhoE 'self\.tools\[' mcp/ --include="*.py" | wc -l` returns 286 literal hits and 282
unique quoted names at this HEAD, which matches neither number — the counting method matters and
should be pinned down by whoever owns the surface claim.

**This file does not edit `claim-ledger.md`** — that file is owned by the GTM Team Lead
(`docs/ws1-gtm-claim-ledger-refresh`). The drift is recorded here so it is not lost.

---

## 8. The claim gate

`scripts/check_gtm_claims.py` is a deterministic, dependency-free check over `docs/gtm/*.md`.

```
python3 scripts/check_gtm_claims.py              # gate: this seat's files only
python3 scripts/check_gtm_claims.py --scope all  # audit: whole directory
python3 scripts/check_gtm_claims.py --strict     # fail on any violation, any owner
```

It flags four classes of statement:

1. **`RETIRED_TOOL_COUNT`** — 257 / 258 / 268 (or 26 domains) presented as the current surface.
2. **`SITES_URL`** — a `/sites/` or `/files/` artifact URL used as a destination. Those return 403
   to an anonymous visitor, so a launch link pointing at one is a dead end. URLs quoted *as
   evidence of the 403* are recorded separately and do not fail the run.
3. **`PYPI_INSTALL`** — a published-package install path. The packages are not on PyPI; install is
   source-only. A source install (`pip install -r requirements.txt`) is correct and does not fire.
4. **`UNLEDGERED_PERF_FIGURE`** — a rate or latency absent from `claim-ledger.md`.

**The expected surface is read from the CI pin, never hardcoded in the script** — a gate that pins
the number in a second place starts drifting the moment the first place moves, which is exactly the
failure in §7.

**Ownership decides the exit code.** Violations in files owned by another seat are printed as
attributed follow-ups and do not fail the run, so the gate can be adopted today rather than after
that debt clears.

**Known limitation, stated so it is not over-trusted:** the perf check is *value-presence*, not
*semantic*. It confirms a figure appears in the ledger; it cannot confirm the ledger attributes it
to the same arm. A concrete caveat found while building this: the ledger records one p50 latency
against `semantic` at n=250, while launch copy cites the same value against `hybrid` at n=13.
The gate passes that line because the value is present. **A human must still check that a figure is
attached to the right arm and sample size.**
