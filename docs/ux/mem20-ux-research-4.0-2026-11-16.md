# mem20 4.0.0 — Live Surface UX Research

**Written:** 2026-11-16 · **Release under research:** `VERSION` = 4.0.0 · **Owner:** UX research
**Surface researched:** the public web surface at `https://mem20.com/` plus the shipped
`docs/app/` shell bundle, as deployed on 2026-11-16.
**Method:** instrumented inspection of the live deployment (HTTP probes, headless Chromium
139.0.7258.5, DOM/a11y/perf evaluation, WCAG 2.1 contrast computation).
**Evidence tier:** **T1 — directly observed.** Every number in this document was measured
against the live deployment on the capture date and is reproducible with the script in
[Appendix A](#appendix-a--reproduction). Nothing here is an estimate, a survey result, or a
carried-over figure from an earlier document.

---

## 0. Read this first — what this study is, and what it is not

This is a **heuristic and technical audit of a live surface**, graded against the product's own
stated thesis. It is *not* moderated usability testing with human participants: no participants
were recruited, no think-aloud sessions were run, and no task-completion rates were observed.
Where a finding depends on how a real person behaves, the finding says so and carries a lower
confidence grade. Where a finding is a fact about the deployment (a 404, a 0-pixel-wide nav, a
version string), the finding is stated as fact because it was measured as fact.

That distinction matters more than usual here. mem20's entire proposition is that a claim
should be separable from a guess, and that the line between them should survive the trip to a
reader. A UX research document that mixes observed facts with plausible-sounding guesses and
presents them at one confidence level is the exact failure the product exists to prevent. So
every finding below carries:

| Field | Meaning |
|---|---|
| **Severity** | S1 critical → S4 low. Impact on the user's ability to complete a real task. |
| **Confidence** | **Observed** (measured fact) · **Derived** (follows mechanically from an observed fact) · **Inferred** (my judgement about human behaviour; needs validation) |
| **Evidence** | The exact observation, with the number and how it was taken. |

Two further limits, stated up front rather than buried:

- **No analytics exist to consult.** The shared tracker at `docs/series/analytics.js` ships with
  `endpoint: ''` (its own comment: *"empty = local only"*). It is loaded on all four marketing
  pages and collects into a browser-side queue that is never transmitted. So this study cannot
  report traffic, funnels, or drop-off, and neither can anyone else on the team. See
  [F-10](#f-10--the-instrumentation-ships-but-transmits-nothing-s2).
- **The authenticated shell was not exercised.** `docs/app/` requests its backend at a hardcoded
  `http://127.0.0.1:8221`, which is unreachable from the public internet
  ([F-02](#f-02--the-public-shell-requests-a-loopback-address-s1)). Everything reported about the
  shell is therefore about its **static chrome, routing and failure state** — not about its
  populated views.

---

## 1. Executive summary

Six findings carry the release. They are ranked by severity, and the first three share one
root cause: **the surface a visitor lands on does not know which release it is.**

1. **The product contradicts itself about its own version.** The landing page advertises
   **v4.0.0**; the shell one click away renders **`mem20 v3.1.2`** in its persistent sidebar. Both
   are live, on the same domain, on the same day. For any other product this is a cosmetic bug.
   For a product whose thesis is *"a memory that can prove what it knows,"* it is a
   self-refuting claim in the first screenful. → [F-01](#f-01--three-different-version-identities-on-one-domain-s1)
2. **The public shell cannot reach its own backend.** The shipped bundle hardcodes
   `http://127.0.0.1:8221`. A visitor's browser dutifully calls their own machine and gets
   `ERR_CONNECTION_REFUSED`. The product's most capable surface is, for every person who is not
   the author sitting at that machine, permanently in its error state. → [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1)
3. **On a phone, the shell has no navigation at all.** At a 390 px viewport the shell's `<nav>`
   measures **0 px** wide and exactly **two** controls remain visible on the page. Nine
   destinations become unreachable. → [F-03](#f-03--the-shell-has-zero-width-navigation-on-mobile-s2)
4. **The surface tells the truth beautifully in exactly one place — the place everybody sees
   first.** The Kanban door-down message is the best copy on the property (*"The shell will not
   draw an empty board for a door it cannot reach. An empty board would read as 'no work', which
   is a different fact from 'no answer.'"*). It is also the default state for every visitor. The
   writing standard already exists in the product; it is simply confined to a failure path.
   → [F-04](#f-04--the-best-honesty-on-the-property-is-the-default-state-s2)
5. **487 tools across 129 domains is not a surface, it is a haystack.** The median domain
   contains **2** tools; **91 of 129 domains** hold two or fewer. One view (Agent Builder) renders
   **48,726 characters** of undifferentiated text. Discoverability, not capability, is the
   binding constraint on adoption. → [F-06](#f-06--the-tool-surface-has-collapsed-into-a-flat-haystack-s2)
6. **The two creative properties promise cadence they are not keeping, in the same words they
   use to promise honesty.** Chronicles declares *"New entries daily"* and *"Publishing daily"*;
   its newest installment is dated **2026-11-10**, six days before capture. The Comicbook Artist
   shows three issues, **zero pages**, all marked *in production*. → [F-07](#f-07--cadence-claims-are-not-met-and-the-gap-is-user-visible-s2)

The rest of the document turns these into eight recommendations with acceptance criteria
([§6](#6-recommendations)), each sized and instrumented so a reviewer can confirm or refute it
without re-reading this study.

### The one-sentence version

> The engineering surface is far ahead of the interface surface: 487 working tools sit behind a
> site that misstates its version, cannot reach its own API, and disappears on a phone — so the
> highest-leverage UX work for 4.0.0 is not new capability but **making the claim and the
> artefact agree.**

---

## 2. Scope, surface inventory, and what was measured

### 2.1 The live surface as it actually resolves

Every route below was requested directly. Status codes and byte counts are as returned.

| Route | Status | Bytes | What it actually is |
|---|---:|---:|---|
| `/` | 200 | 10,998 | Landing page. Static HTML. Advertises **v4.0.0**. |
| `/series/` | 200 | 6,802 | Series hub. Contains a self-reported "What is live right now" table. |
| `/series/comic/` | 200 | 8,216 | *The Comicbook Artist* — series bible + issue index. |
| `/series/chronicles/` | 200 | 6,862 | *Mem20-naration's Chronicles* — daily index. |
| `/series/chronicles/feed.xml` | 200 | 1,073 | RSS. Valid, 1 item. |
| `/series/data/comic-issues.json` | 200 | 1,398 | Machine-readable comic index. 3 issues. |
| `/series/data/chronicles.json` | 200 | 830 | Machine-readable chronicle index. 1 entry. |
| `/series/series.css` | 200 | 10,582 | Shared design system for all four marketing pages. |
| `/app/` | 200 | 957 | Vite SPA shell. 957 bytes of HTML; everything else is JS. |
| `/app/assets/index-B4bqkMyH.js` | 200 | 323,518 | The shell bundle. |
| `/app/assets/index-BMgU54DU.css` | 200 | 13,530 | The shell stylesheet. |
| `/README.md` | 200 | 3,584 | **Raw markdown served as the site's README.** |
| `/TOOL-DOMAINS.md` | 200 | 16,409 | **Raw markdown.** Domain list. |
| `/02-tools-reference.md` | 200 | 45,181 | **Raw markdown.** Tools reference. |
| `/05-complete-tools-reference.md` | 200 | 101,546 | **Raw markdown.** "Complete" tools reference — 101 KB. |
| `/ux/README.md` | 200 | 13,320 | **Raw markdown.** The prior UX acceptance specs, publicly served. |
| `/pricing/` | **404** | 9,379 | GitHub Pages default 404. |
| `/docs/` | **404** | 9,379 | GitHub Pages default 404. |
| `/dashboard/` | **404** | 9,379 | GitHub Pages default 404. |
| `/use-cases/` | **404** | 9,379 | GitHub Pages default 404. |
| `/market/` | **404** | 9,379 | GitHub Pages default 404. |
| `/sitemap.xml` | **404** | 9,379 | No sitemap. |
| `/robots.txt` | **404** | 9,379 | No robots file. |
| `/favicon.ico` | **404** | 9,379 | No favicon at the conventional path. |
| `/api/health` | **404** | 9,379 | No API on the web origin. |

Two structural facts follow immediately, and both are load-bearing for the rest of this study:

**The site is GitHub Pages.** Every response carries `server: GitHub.com` and a Fastly cache
header; `docs/CNAME` contains `mem20.com`. That explains the 404 behaviour: there is no
server-side rewrite, so any path without a matching file falls through to GitHub's own
"Page not found" page. That page is **not branded** — its title is
`Page not found &middot; GitHub Pages`, it uses GitHub's light-grey palette, and it contains no
mem20 navigation. A visitor who mistypes, or who follows a link into one of the five 404-ing
sections above, lands on a page belonging to a different company.

**The five 404-ing routes are the ones a buyer would try.** `pricing`, `docs`, `use-cases`,
`dashboard`, `market`. These are exactly the directories that exist in the repository as
source (`docs/pricing/`, `docs/use-cases/`, `docs/market/`, `docs/dashboard.html`) but are
served from a path that GitHub Pages does not map to a route. The work exists; the address does
not. See [F-05](#f-05--the-five-sections-a-buyer-would-try-are-all-404-s2).

### 2.2 The shell's real information architecture

`/app/` is a single-page app with **hash routing**. Nine destinations were confirmed by pressing
each control and reading the resulting `h1` and `location.hash`:

| Label in nav | Hash route | `h1` after activation | Text rendered | Deep-linkable |
|---|---|---|---:|---|
| Kanban | `#kanban` | Kanban | 869 chars | yes |
| Dreams | `#dreams` | Dreams | 1,457 | yes |
| Agent Builder | `#agents` | Agent Builder | **48,726** | yes |
| Teamily | `#teamily` | Teamily | 839 | yes |
| Docs / FAQ | `#docs` | Docs / FAQ | 1,464 | yes |
| Sales | `#sales` | Sales | 3,255 | yes |
| Memory model | `#memory` | Memory model | 2,910 | yes |
| Door Sync | `#door` | Door Sync | 3,215 | yes |
| Connection | `#connection` | Connection | 1,418 | yes |

Deep links were verified independently in **fresh browser contexts** (direct load of
`/app/#dreams`, `#memory`, `#docs`, `#agents`, `#sales`): each resolved to the correct view with
the correct `h1` and no redirect through the default view. **This is a genuinely good pattern and
is called out in [§5](#5-what-not-to-redesign) as a thing to keep.**

The nav is grouped by intent, not by module name:

```
OPERATE   Kanban · Dreams · Agent Builder · Teamily
UNDERSTAND  Docs / FAQ
SELL      Sales
TRUST     Memory model · Door Sync · Connection
```

That grouping is a coherent, defensible IA — it maps to what a visitor wants to do rather than
to how the codebase is organised. It is undermined, not by its structure, but by the fact that
on a phone it is zero pixels wide, and that every view it leads to is blocked by an unreachable
backend.

### 2.3 The tool surface

Read from the live pin in `docs/surface.json`, which is generated from the server's JSON-RPC
`tools/list` and cross-checked against an AST catalog (`only_ast` and `only_live` both empty —
the two counts agree exactly).

| Metric | Value |
|---|---:|
| MCP tools | **487** |
| Domains | **129** |
| Median tools per domain | **2** |
| Domains with exactly 1 tool | **15** |
| Domains with ≤ 2 tools | **91** (71% of all domains) |
| Largest domain (`memory`) | **55** |
| Unwired tools | **19** |

Largest domains, for orientation:

| Domain | Tools | | Domain | Tools |
|---|---:|---|---|---:|
| `memory` | 55 | | `braid` | 9 |
| `cognitive` | 19 | | `communication` | 9 |
| `world` | 14 | | `dev` | 9 |
| `versioncontrol` | 11 | | `marketing` | 9 |
| `cloudservice` | 10 | | `thought_process` | 9 |
| `database` | 10 | | `cloudstorage` | 8 |
| `filesystem` | 10 | | `design` | 8 |
| `lie` | 10 | | `edgefleet` | 8 |
| `productivity` | 10 | | `finance` | 8 |
| | | | `webscraping` | 8 |

---

## 3. Who this surface is for

Personas here are **derived from the copy the surface actually addresses**, not invented to
populate a slide. Each one names the route that speaks to them and the exact phrase that
identifies them as the addressee. A persona that no page addresses is listed in
[§3.6](#36-personas-deliberately-rejected) as rejected, because a persona the product does not
speak to cannot be used to justify a design decision.

### 3.1 P1 — Dana, the evaluating engineer

**Identified by:** the landing page's primary CTA pair — *"Read the source"* and *"Install from
PyPI"* — and the `Run it` section's literal clone-and-install shell block.
**Context:** has been handed mem20 as a candidate memory layer. Has 15 minutes and a working
terminal. Will not read a benchmark table, but will run `git clone` if the block looks honest.
**What she needs from the surface:** a version she can trust, an install path that works on the
first try, and a way to see the tools without reading 101 KB of markdown.
**What the surface gives her:** a version badge that contradicts the shell one click away
([F-01](#f-01--three-different-version-identities-on-one-domain-s1)); a working install block
(**positively verified** — the commands are real and the venv path is correct); and
`05-complete-tools-reference.md`, a 101 KB raw markdown file that is served but **not linked from
anywhere on the site** ([F-11](#f-11--101-kb-of-reference-material-is-orphaned-s3)).
**Her most likely exit:** hits `/docs/`, gets GitHub's 404, concludes the project is
half-finished.

### 3.2 P2 — Sam, the memory-integrity reviewer

**Identified by:** the landing page's *"The one rule"* section, which splits the entire product
into `grounded` and `simulated` panels — and by the shell's `Memory model` view, whose copy is
*"the five hard invariants, enforced at the store layer."*
**Context:** this is the person the product is *for*. Sam's job is to answer "can I trust what
this thing tells my agent?" and he came to the surface specifically to check that the
grounded/simulated partition is enforced rather than promised.
**What he needs:** the invariants, each tied to the code that enforces it, and evidence the
partition survives retrieval.
**What the surface gives him:** the strongest content on the entire property. The `Memory model`
view lists five invariants and names the actual functions (`_assert_grounded()` in
`_add_to_vector_index()` and `_add_to_bm25_index()`; `_allow_simulated=False` by default; an
append-only ledger with validated tags). The origin-tagging discipline is real in the data layer
too — `chronicles.json` carries an `origin_legend` and the RSS items carry
`<category>grounded</category>`.
**What undermines it:** he reaches this view through a shell that says `v3.1.2` and that is
permanently showing a red *"door down"* state. A reviewer whose entire job is verifying claims
reads those two signals before he reads the invariants, and they tell him the surface is not
under control. This is the highest-cost instance of [F-01](#f-01--three-different-version-identities-on-one-domain-s1)
and [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1).

### 3.3 P3 — Ada, the reader

**Identified by:** the landing page's *"Two series, one thesis"* section: *"A memory product is
hard to feel from a feature list. So mem20 also publishes two creative properties that carry the
same idea to people who will never read a benchmark table."*
**Context:** arrived from the comic or the chronicle, not from a search for memory middleware.
She is on a phone. She has no intention of installing anything.
**What she needs:** the page to be readable on her phone, and the next installment to exist.
**What the surface gives her:** at 390 px, `/series/` is **182 px wider than her viewport**;
`/series/comic/` overruns by **106 px** and `/series/chronicles/` by **96 px**. Content is
clipped and the page scrolls sideways ([F-04](#f-04--the-best-honesty-on-the-property-is-the-default-state-s2)
companion, [F-08](#f-08--the-series-pages-break-horizontally-on-a-phone-s2)). Chronicles promises
*"New entries daily"* and has not published since 2026-11-10
([F-07](#f-07--cadence-claims-are-not-met-and-the-gap-is-user-visible-s2)). The comic offers three
titles and zero pages.
**Why she matters commercially:** she is the entire justification for the series existing. If she
bounces, the two creative properties are cost without return — a conclusion the team should reach
from evidence rather than from attrition.

### 3.4 P4 — Ray, the operator

**Identified by:** the shell's `Kanban`, `Door Sync` and `Connection` views, and the door-down
copy written specifically for him.
**Context:** runs mem20 locally, door on `:8221`, wants to see boards and dreams.
**What he needs:** a shell that tells him the difference between "down" and "empty", and a
connection screen that lets him point the shell at the right host.
**What the surface gives him:** the best state design in the product — and the single most
important constraint for [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1)'s fix,
because the shell **already has** a `Connection` view (1,418 chars, hash `#connection`) and a
visible `config` control. The mechanism to retarget the API exists. What does not exist is a way
to reach it on mobile, or a default that is anything other than loopback.

### 3.5 P5 — Priya, the integrator

**Identified by:** `docs/surface.json`, the two machine-readable series feeds, and the RSS.
**Context:** writes against APIs. Wants the tool list as data, not prose.
**What she needs:** a stable, generated, machine-readable description of the surface, and feeds
that actually update.
**What the surface gives her:** this is the property's quiet strength. `surface.json` is
genuinely generated and self-cross-checked; the two JSON feeds exist and are valid; the RSS is
well-formed with a proper `<atom:link rel="self">`. All of it works. None of it is linked from
the site ([F-11](#f-11--101-kb-of-reference-material-is-orphaned-s3), [F-12](#f-12--the-machine-readable-surface-is-unlisted-s3)).

### 3.6 Personas deliberately rejected

| Rejected persona | Why |
|---|---|
| **The enterprise buyer** | No page addresses procurement, SSO, or seat models, and `/pricing/` returns 404. Designing for a persona with no route is designing for a screen that does not exist. |
| **The mobile-first consumer** | Would flatter the mobile findings, but the shell is a local operator tool by construction (`127.0.0.1`). Reserved until [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1) is resolved and the shell has a real hosted backend. |
| **The AI agent as user** | Tempting given the product category, but no agent-facing entry point is documented on the web surface (the MCP transport is stdio, not HTTP). Out of scope for interface research; belongs to a protocol study. |
| **The contributor** | `CONTRIBUTING.md` exists and the toolchain is real, but no web route addresses contribution. Covered by repo docs, not by this surface. |

---

## 4. Findings

Severity: **S1** critical · **S2** high · **S3** medium · **S4** low.
Confidence: **Observed** · **Derived** · **Inferred**.

---

### F-01 — Three different version identities on one domain (S1)

**Confidence:** Observed.

| Where | What it says | Source of that string |
|---|---|---|
| Repository `VERSION` | `4.0.0` | the file |
| Landing page fact tile (`/`) | `v4.0.0` | hardcoded badge in `docs/index.html` |
| Shell persistent sidebar (`/app/`) | **`mem20 v3.1.2`** | hardcoded in `docs/app/assets/index-B4bqkMyH.js` |

The shell's string is not a stale file — it is baked into the shipped bundle and renders on every
view, directly beneath the door-status pill, in the sidebar a visitor cannot dismiss.

**Why this is S1 and not a cosmetic nit.** Three audiences read this string and all three are
harmed by it:

- **P1 (evaluating engineer)** now has to decide which of two live version numbers to believe
  before he has installed anything. His cheapest resolution is *"this project does not track its
  own releases"* and his cheapest action is to close the tab.
- **P2 (memory-integrity reviewer)** is evaluating a product that claims to never mix a verified
  fact with an unverified one. The first version number he sees is unverified against the second.
- **P4 (operator)** cannot tell whether the shell he is running matches the engine he installed.
  That is an operational question with a wrong-answer cost.

**Derived consequence:** every future bug report against the shell is ambiguous. "The shell says
v3.1.2" is now a true statement about a 4.0.0 deployment, so the version field has stopped being
usable as a support triage signal. The cost compounds silently from here.

---

### F-02 — The public shell requests a loopback address (S1)

**Confidence:** Observed (network trace), Derived (consequence).

Loading `https://mem20.com/app/` in a clean browser context produced exactly one API request:

```
GET http://127.0.0.1:8221/api/boards   →  net::ERR_CONNECTION_REFUSED
```

Two browser console errors, both from that request. The base URL is **hardcoded into the
bundle** — no environment substitution, no runtime config lookup, and no host derived from
`location`. The sidebar renders it literally as part of the door-status UI:

```
door down
config
http://127.0.0.1:8221
```

**Interpretation.** `127.0.0.1` inside a browser means *the machine the browser is running on*.
For the author developing locally with the door up on `:8221`, this works. For **every other
person on earth**, the shell is in its permanent failure state. The published URL of the shell is
therefore a demo of an error message.

**This is not a broken deploy — it is a correctly deployed local developer tool.** The bundle is
self-consistent; it simply assumes a topology (`shell and door on the same host`) that the URL it
is published at contradicts.

**What makes this the highest-value fix in the release:** the shell already treats this state as
a first-class condition rather than a blank screen (see [F-04](#f-04--the-best-honesty-on-the-property-is-the-default-state-s2)),
and it already ships a `Connection` view with a `config` control intended to retarget the
host. The affordance for recovery exists. It is (a) unreachable on mobile
([F-03](#f-03--the-shell-has-zero-width-navigation-on-mobile-s2)) and (b) not offered as the
primary action from the error state. A visitor in the error state sees `retry door` — which will
retry the same unreachable loopback — but the *useful* recovery is the `config` control
immediately above it.

---

### F-03 — The shell has zero-width navigation on mobile (S2)

**Confidence:** Observed.

At a 390 × 844 viewport with `is_mobile=True`, the shell's `<nav>` element measures
**`width: 0px`**. Enumerating every interactive element with a non-zero bounding box returned
exactly **two**:

```
BUTTON "retry door"      width 308
BUTTON "open Door Sync"  width 308
```

All nine navigation controls (`Kanban`, `Dreams`, `Agent Builder`, `Teamily`, `Docs / FAQ`,
`Sales`, `Memory model`, `Door Sync`, `Connection`) measure **`width: 0`** and are not
rendered. No hamburger, no drawer, no `<select>`, no `aria-label`-bearing menu toggle was present
in the accessibility tree at that viewport. The page does not overflow horizontally
(390 / 390), so this is not a clipping artefact — the navigation is genuinely absent.

**Consequence (Derived).** A phone visitor to `/app/` can reach exactly two things, and both of
them are recovery actions for a backend that is unreachable
([F-02](#f-02--the-public-shell-requests-a-loopback-address-s1)). The shell's worst-case state is
the *only* state a mobile visitor can reach.

**Confidence note.** Whether a real mobile user would want this shell at all is **Inferred** and
unvalidated — the shell is a local operator tool. That is precisely why the finding matters: if
the shell is not meant for phones, 0 px navigation is the wrong way to say so. Absence reads as
breakage, not as intent. See [R-05](#r-05--decide-and-declare-the-shells-mobile-posture).

---

### F-04 — The best honesty on the property is the default state (S2)

**Confidence:** Observed (copy), Inferred (behavioural impact — this is the most important thing
to validate with participants).

The Kanban view's door-down copy, verbatim from the live bundle:

> **Kanban door is unreachable — http://127.0.0.1:8221**
> The shell will not draw an empty board for a door it cannot reach. An empty board would read as
> "no work", which is a different fact from "no answer". Start the door …

This is the strongest interface writing in the entire estate, and it is worth spending a sentence
on why, because it should become the template:

- It distinguishes **absence from emptiness** — "no answer" ≠ "no work" — which is the exact
  distinction most operations tools collapse.
- It names the **specific** endpoint, not "the service".
- It states a **design decision and its reason** ("will not draw an empty board") rather than
  apologising.
- It offers a **next action**, not a shrug.

**The problem is placement, not quality.** This paragraph is what a first-time visitor sees,
because [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1) guarantees the door is
down for everyone. The product's clearest, most principled writing is spent explaining a
topology the visitor did not choose.

**Inferred risk (needs validation).** A visitor whose first impression of a *trust* product is
"unreachable — here is why that is honest" learns two things: the product cares about honesty
(good) and the product is currently down (bad). Which of those dominates is an empirical
question. My judgement is that the second dominates for P1 and P3, and the first for P2 — but
that is a hypothesis for [§7](#7-measurement-plan), not a finding.

---

### F-05 — The five sections a buyer would try are all 404 (S2)

**Confidence:** Observed.

`/pricing/`, `/docs/`, `/dashboard/`, `/use-cases/`, `/market/` all return **404**. All five exist
as source in the repository. The 404 body is GitHub's default page — `Page not found &middot;
GitHub Pages`, GitHub's light palette, GitHub's CSS, zero mem20 branding, zero mem20 navigation.
A visitor who follows a link into `/pricing/` from anywhere has left the product and has no route
back except the browser's Back button.

Worse: the 404 page is the **highest-traffic page that does not exist**, and it is unbranded. It
also means there is no `/sitemap.xml` (404) and no `/robots.txt` (404), so search engines have no
machine-readable map of a surface that already fails to describe itself in prose.

**Derived.** Every one of these five is a dead end reached by *intent*. This is the single
cheapest S2 to fix: a branded `docs/404.html` plus a routing note. GitHub Pages serves
`404.html` automatically if it exists at the site root.

---

### F-06 — The tool surface has collapsed into a flat haystack (S2)

**Confidence:** Observed (distribution), Inferred (discoverability cost).

The tool surface is **487 tools across 129 domains**, with a **median of 2 tools per domain** and
**91 of 129 domains (71%) holding two or fewer**. Fifteen domains hold exactly one tool each, and
their names are generated compounds that no one would search for:

```
mem20asynccollaborationcapsulesz      mem20milestoneriskpredictorz
mem20autonomoustrafficcontrollerz     mem20prioritycollisionresolverz
mem20batteryawareagentschedulerz      mem20zerodowntimemigrationbrainz
mem20crdtcollaborationenginez         rm052 · rm239
mem20dynamicphasereplannerz
```

Meanwhile one domain (`memory`) holds **55 tools — 11% of the entire surface in a single
namespace**, which is the namespace whose internal distinctions (grounded vs simulated, remember
vs remember_simulated, store vs simulate_store) carry the product's core claim.

**The interface consequence is measured, not assumed.** The shell's `Agent Builder` view renders
**48,726 characters** of text — more than the landing page, the series hub, the comic page and the
chronicles page *combined* (10,998 + 6,802 + 8,216 + 6,862 = 32,878). That is a question of
where a person who is looking for one of 487 tools begins.

**The measured distribution says the answer is "nowhere":**

| Band | Domains | Share |
|---|---:|---:|
| 1 tool | 15 | 11.6% |
| ≤ 2 tools | 91 | 70.5% |
| ≤ 3 tools | 94 | 72.9% |
| ≥ 20 tools | 1 | 0.8% |

A flat list of 129 domains is not a navigable IA when 71% of the entries are singletons. The
surface needs **task-shaped grouping above the domain layer**, not a longer list. See
[R-06](#r-06--give-487-tools-a-task-first-entry-point).

**Honest counterweight:** 487 tools is a genuine achievement and the `docs/surface.json`
machinery that publishes it (generated from live `tools/list`, cross-checked against the AST
catalog with `only_ast`/`only_live` both empty) is better instrumented than most commercial
surfaces. The problem is purely one of presentation.

---

### F-07 — Cadence claims are not met, and the gap is user-visible (S2)

**Confidence:** Observed.

Both creative properties state a cadence and neither is meeting it, on a page whose own
governing principle is that a surface must not overstate its progress.

**Chronicles** — declares *"Publishing daily"*, *"New entries daily"*, and
`"cadence": "daily"` in its own JSON feed.

| Field | Value |
|---|---|
| Entries published | **1** |
| Newest installment date | **2026-11-10** |
| Capture date | **2026-11-16** |
| Days since last installment | **6** |
| RSS `<lastBuildDate>` | Tue, 10 Nov 2026 |

**The Comicbook Artist** — declares *"In production"* and a three-issue index.

| Issue | Title | State | Pages |
|---|---|---|---:|
| 1 | The Sketch That Was Never Inked | `in_production` | **0** |
| 2 | Two Versions of Page Nine | `planned` | **0** |
| 3 | The Studio That Forgot Its Own Hand | `planned` | **0** |

Zero pages have shipped. The series hub's badges say *"in production"* and *"New entries daily"*
for both, and its own `state_legend` defines `planned` as *"canon exists, art not started."*

**Why this is a UX finding and not an editorial one.** The same page carries this sentence:

> *"Stated plainly, because a series home that overstates its own progress is the exact failure
> mode mem20 exists to prevent."*

The page names its own failure mode and then commits it one section above. A surface cannot
credibly lecture on overstatement while showing a "daily" badge over a six-day-old entry — and
P3, the reader this material was built for, is precisely the reader least likely to care about
the excuse and most likely to simply notice.

**Note on the reporting standard this study follows:** the honest framing is available and was
almost used. The hub already says *"each index below marks exactly which entries are published
and which are still in production."* That mechanism works — the `state` field is accurate. The
defect is confined to the **static badges** ("New entries daily", "Publishing daily",
"In production") which do not read from the state field. Fix the badges, keep the data.

---

### F-08 — The series pages break horizontally on a phone (S2)

**Confidence:** Observed.

Measured `scrollWidth` vs `clientWidth` across three viewports. Overflow means the page is wider
than the screen, so content is clipped and the page scrolls sideways.

| Page | 1440 px | 390 px | 320 px |
|---|---|---|---|
| `/` | no overflow | **no overflow** | **no overflow** |
| `/series/` | no overflow | **overflow +182 px** | **overflow +252 px** |
| `/series/comic/` | no overflow | **overflow +106 px** | **overflow +176 px** |
| `/series/chronicles/` | no overflow | **overflow +96 px** | **overflow +166 px** |

The landing page **does not overflow at any width** — its own media queries
(`@media(max-width:900px)`) collapse `.facts`, `.split` and `.series-strip` correctly. So the
root cause is a fix that was applied on the landing page and not carried into the shared
`series.css` used by the three series pages. This is a one-file fix, not a redesign.

Screenshots at 390 px confirm the clipping visually: the series hub's two-up property cards and
the chronicles body run past the right edge.

---

### F-09 — Keyboard focus is effectively invisible (S3)

**Confidence:** Observed.

The shared stylesheet (`series.css`, 10,582 bytes, used by all four marketing pages) contains
**zero** occurrences of `outline`, `:focus`, or `:focus-visible`. No focus style is authored
anywhere on the marketing surface.

Tab-order was walked on the live landing page for ten stops. Every stop reported the browser's
default ring:

```
outline-style: auto · outline-width: 1px · outline-color: rgb(16, 16, 16)
```

`rgb(16,16,16)` against the page background `#070A0F` is a contrast ratio of **1.04:1**. WCAG
2.2 SC 2.4.11 (*Focus Appearance*) requires **3:1** for a focus indicator against the adjacent
colour. Against the card surface `#101724` it is **1.06:1**. In practice the focus ring is
present in the DOM and invisible to a sighted keyboard user on every one of the four marketing
pages.

For contrast, the *text* palette on this surface is excellent and needs no work:

| Token | Ratio on `#070A0F` | AA (4.5) |
|---|---:|---|
| `--text` `#E8EFF7` | 17.11 | pass |
| `--text-2` `#B8C6D6` | 11.41 | pass |
| `--muted` `#8296AC` | 6.52 | pass |
| `--accent` `#2FD4C4` | 10.70 | pass |
| `--amber` `#F5B841` | 11.15 | pass |
| `--chron` `#46B8F5` | 8.91 | pass |

Only two tokens fail, and both are **non-text** (border colours `--line` `#1E2A3C` at 1.37 and
`--line-2` `#293850` at 1.68), so they are not WCAG text failures. The entire colour contrast
work for this surface is done. Only the focus indicator is missing.

---

### F-10 — The instrumentation ships but transmits nothing (S2)

**Confidence:** Observed.

`docs/series/analytics.js` (5,629 bytes) is loaded on all four marketing pages — `/`,
`/series/`, `/series/comic/`, `/series/chronicles/`. Its own configuration block reads:

```js
var CFG = {
  endpoint: '',            // e.g. 'https://collector.example.com/e' — empty = local only
  site: 'mem20.com',
  respectDNT: true,
  trackOutbound: true,
  trackNav: true,
  trackSeries: true
};
```

`endpoint` is empty. The tracker queues events in the browser and never sends them.

**Why this is a finding and not a passing note.** Every UX document in this repository that came
before this one — including the four desktop acceptance specs indexed in
[`docs/ux/README.md`](./README.md) — ends with a section of the form "reviewers cannot verify
that a surface feels right, but they can verify counters," and names the counters each feature
must emit. That requirement is correct and nothing transmits. So the correct reading of the
current state is: **the team has specified instrumentation it cannot receive, and therefore has
no usage evidence for any interface decision it has made.** The tracker is also mis-scoped — it
covers the four marketing pages and not `/app/`, the surface where the interaction actually is.

The privacy posture is genuinely good and should be preserved on the way to fixing this
(cookie-free, DNT/GPC respected, no cross-site tracking, no personal data). Enabling delivery does
not require weakening it.

---

### F-11 — 101 KB of reference material is orphaned (S3)

**Confidence:** Observed.

These files are served publicly as **raw markdown**, returned with
`content-type: text/markdown` and rendered by the browser as plain text:

| Path | Bytes | What it is |
|---|---:|---|
| `/05-complete-tools-reference.md` | 101,546 | The complete tools reference |
| `/02-tools-reference.md` | 45,181 | Tools reference |
| `/TOOL-DOMAINS.md` | 16,409 | Domain listing |
| `/ux/README.md` | 13,320 | The prior UX acceptance specs |
| `/README.md` | 3,584 | The repository README |

None of the five is linked from the landing page. The landing page has **16 anchors total**, and
all of them point at `./`, `series/`, `series/comic/`, `series/chronicles/`, GitHub, or PyPI. A
visitor can therefore reach the README only by guessing the filename.

**This is the most consequential orphan for P1.** She was promised *"the repository publishes its
own measured figures … in `README.md`"* by a note on the landing page — which then does not link
to `README.md`. The sentence points at a document the reader cannot navigate to. For P5 the same
is true of `surface.json`, which is not reachable from the site at all
([F-12](#f-12--the-machine-readable-surface-is-unlisted-s3)).

---

### F-12 — The machine-readable surface is unlisted (S3)

**Confidence:** Observed.

| Artefact | Served | Linked from the site |
|---|---|---|
| `docs/surface.json` | yes (in repo) | **no** |
| `/series/data/comic-issues.json` | 200 | yes — from `/series/comic/` |
| `/series/data/chronicles.json` | 200 | yes — from `/series/chronicles/` |
| `/series/chronicles/feed.xml` | 200 | yes — RSS links present |

The two series feeds are correctly linked from their own pages — the series team got this right,
and it is the pattern to copy. `surface.json` is the outstanding case: the single most useful
artefact for P5, generated and self-cross-checked, with no route to it.

---

### F-13 — The shell has no unique title, description or canonical (S3)

**Confidence:** Observed.

`/app/` returns 957 bytes of HTML whose `<title>` is **`mem20 — auditable agent memory`** —
byte-identical to the landing page's title. It has no `<link rel="canonical">`, no
`og:*` tags, and no `<meta name="description">`. All four marketing pages have unique titles, a
canonical, and a full `og:` set; the shell has none of the three.

**Derived.** A shared URL to a shell view renders with the landing page's title and description,
so a link posted to a team channel is indistinguishable from a link to the homepage. Combined
with the fact that the shell's nine views are all reachable by hash, every shareable deep link
inherits the wrong identity.

---

## 5. What not to redesign

Recording this explicitly, because the strongest parts of this surface are the parts most likely
to be rewritten by someone fixing the findings above.

1. **The Kanban door-down copy.** Distinguishes absence from emptiness, names the endpoint, states
   the design decision and its reason, offers a next action. Make this the house style for every
   empty and error state ([F-04](#f-04--the-best-honesty-on-the-property-is-the-default-state-s2)).
2. **The nine-view nav grouping** (`OPERATE / UNDERSTAND / SELL / TRUST`). Organises by intent,
   not by module. Fix its mobile rendering; do not re-taxonomise it.
3. **Hash-routed deep links.** Verified working from fresh contexts: `/app/#dreams`,
   `#memory`, `#docs`, `#agents`, `#sales` all resolve correctly. Do not migrate to path routing
   without preserving these.
4. **The version rendering itself.** The shell *has* a version slot in the sidebar chrome, in the
   right place, in the right visual weight. It is populated with the wrong string. That is a
   one-line fix, not a component to be rebuilt.
5. **The text palette and type system.** Every text token passes AA, most by a wide margin. The
   `Space Grotesk` / `Inter` / `IBM Plex Mono` triad is doing real work: display, body and
   machine text are visually distinct without being loud.
6. **The origin-tagging discipline.** `grounded`/`simulated` is enforced in the data, the ledger,
   the JSON legend, and the RSS `<category>`. It is the product's thesis rendered as data. Nothing
   about the findings above should cause it to be relaxed.
7. **The privacy posture of the tracker.** Cookie-free, DNT-aware, no cross-site, no personal
   data. Turn on the endpoint; keep all of it.

---

## 6. Recommendations

Eight recommendations. Each carries an owner-shaped label, a size, acceptance criteria that a
reviewer can run, and the finding it closes. Nothing here requires a new backend contract: every
one is a change to a file that already exists.

---

### R-01 — Make the version identity single-sourced

**Closes:** [F-01](#f-01--three-different-version-identities-on-one-domain-s1) · **Size:** S ·
**Surface:** `docs/app/`, `docs/index.html`

Inject the version into the shell bundle at build time from the repository `VERSION` file
(or from the same generated artefact that populates the landing page badge) instead of a literal
string. The shell's sidebar already renders the slot.

**Acceptance criteria**

- **AC-1.1** `VERSION`, the landing badge, and the shell sidebar all report the same value. Verify:
  `cat VERSION`, read the `/` fact tile, read the `/app/` sidebar. Any three-way mismatch is a fail.
- **AC-1.2** A release that bumps `VERSION` changes all three with no other edit. Verify: bump
  `VERSION` on a branch, rebuild, confirm all three move.
- **AC-1.3** No version literal appears in `docs/app/assets/*.js`. Verify:
  `grep -c 'v3\.1\.2' docs/app/assets/*.js` returns `0`.
- **AC-1.4** *(negative test)* Set `VERSION` to a sentinel (`0.0.0-test`), build, confirm the
  sidebar shows `0.0.0-test` — proving it reads the file rather than a cache.

---

### R-02 — Make the API base configurable, and make the error state offer recovery

**Closes:** [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1) · **Size:** M ·
**Surface:** `docs/app/`

Two changes, in this order of importance.

1. **Resolve the base URL at runtime**, in precedence order: a value the user has saved in the
   existing `Connection` view → a build-time default → `http://127.0.0.1:8221` for a locally
   served shell only. A shell served from a public origin must never silently default to loopback.
2. **Promote `config` to the primary action of the error state.** Today the door-down panel offers
   `retry door` (which retries the same unreachable host) and the useful `config` control sits
   above it. Swap the emphasis: the primary action in the door-down state should be the one that
   can actually change the outcome.

**Acceptance criteria**

- **AC-2.1** Loading the shell from a public origin issues **no** request to `127.0.0.1`. Verify:
  load with a clean profile, capture all requests, assert none match `127.0.0.1` or `localhost`.
- **AC-2.2** Saving a host in `Connection` survives reload and is the host used for the next
  request. Verify: set host to a stub, reload, observe the request target.
- **AC-2.3** The door-down state's primary button is the one that leads to `Connection`. Verify:
  read the button order and the `href`/handler of the first button in the panel.
- **AC-2.4** *(negative test)* With no saved host and a public origin, the shell must not present
  a loopback URL as if it were the configured backend. Verify: the door-down copy must not read
  `http://127.0.0.1:8221` unless the user configured it.

---

### R-03 — Fix mobile rendering of the shell and the series pages

**Closes:** [F-03](#f-03--the-shell-has-zero-width-navigation-on-mobile-s2),
[F-08](#f-08--the-series-pages-break-horizontally-on-a-phone-s2) · **Size:** M ·
**Surface:** `docs/app/assets/index-*.css`, `docs/series/series.css`

Two independent fixes that share one acceptance harness.

- **Series pages:** port the landing page's working responsive rules into `series.css`. The
  landing page already collapses `.facts`, `.split` and `.series-strip` under 900 px and does not
  overflow at 320 px; the three series pages use the same class names and do not inherit the
  rules. This is a copy of an existing solution, not new design.
- **Shell:** give the nav a mobile presentation (drawer, bottom bar, or an explicit
  "not optimised for small screens" declaration — see [R-05](#r-05--decide-and-declare-the-shells-mobile-posture)).
  A 0 px nav is not a choice; it is an absence.

**Acceptance criteria**

- **AC-3.1** `scrollWidth == clientWidth` at 320, 390 and 768 px for `/`, `/series/`,
  `/series/comic/`, `/series/chronicles/`. Verify: the script in [Appendix A](#appendix-a--reproduction);
  any positive delta is a fail.
- **AC-3.2** On the shell at 390 px, all nine destinations are reachable by a visible control.
  Verify: enumerate interactive elements with non-zero bounding boxes; assert ≥ 9 distinct
  destination controls.
- **AC-3.3** No horizontally clipped text at 320 px. Verify: screenshot at 320 px; any text
  running past the right edge is a fail.
- **AC-3.4** *(negative test)* At 320 px the page must not require horizontal scrolling to read
  any paragraph. Verify: `document.documentElement.scrollWidth <= innerWidth + 1`.

---

### R-04 — Ship a branded 404 and a sitemap

**Closes:** [F-05](#f-05--the-five-sections-a-buyer-would-try-are-all-404-s2) · **Size:** S ·
**Surface:** `docs/404.html`, `docs/sitemap.xml`, `docs/robots.txt`

Add `docs/404.html` using the existing nav and footer from the landing page, with the honest copy
style of [F-04](#f-04--the-best-honesty-on-the-property-is-the-default-state-s2) and links to the
four live surfaces. Add `sitemap.xml` covering the real routes, and `robots.txt` pointing at it.

Separately, decide each of the five 404-ing sections: **route it, or stop advertising it.** A
`/pricing/` that 404s is worse than no pricing page, because it converts a visitor's intent into
a dead end at GitHub's branding.

**Acceptance criteria**

- **AC-4.1** `/does-not-exist-xyz` returns a page whose `<title>` contains `mem20` and whose body
  contains the site nav. Verify: fetch an invented path; assert the title and the presence of the
  four nav links. Today it returns `Page not found &middot; GitHub Pages`.
- **AC-4.2** `/sitemap.xml` returns 200 and lists every route that returns 200. Verify: parse the
  sitemap, fetch every URL in it, assert all 200.
- **AC-4.3** `/robots.txt` returns 200 and references the sitemap.
- **AC-4.4** *(negative test)* No route in `sitemap.xml` returns 404. A sitemap that advertises a
  dead route is a self-inflicted 404 farm.

---

### R-05 — Decide and declare the shell's mobile posture

**Closes:** [F-03](#f-03--the-shell-has-zero-width-navigation-on-mobile-s2),
[F-01](#f-01--three-different-version-identities-on-one-domain-s1) secondary ·
**Size:** S · **Surface:** `docs/app/`

The shell is, by construction, a local operator tool: it talks to a door on `127.0.0.1:8221`. It
is entirely defensible for it to be desktop-only. What is not defensible is *silently* being
desktop-only by measuring its nav at 0 px.

Pick one and make it explicit:

- **Option A — support it:** see [R-03](#r-03--fix-mobile-rendering-of-the-shell-and-the-series-pages).
- **Option B — declare it:** below 768 px, render a short, honest page in the product's own
  voice — *"this shell runs against a door on your own machine; it is a desktop tool"* — with a
  link back to the four public surfaces. This takes an afternoon and is strictly better than a
  page with two buttons that both fail.

**Acceptance criteria**

- **AC-5.1** At 390 px the shell either presents ≥ 9 reachable destinations (Option A) or presents
  an explicit declaration naming the constraint and linking to the public surface (Option B).
- **AC-5.2** *(negative test)* There is no viewport width at which the shell renders a nav of
  width 0 *and* no declaration. Verify: sweep 320–1024 px in 40 px steps; assert the invariant at
  each step.

---

### R-06 — Give 487 tools a task-first entry point

**Closes:** [F-06](#f-06--the-tool-surface-has-collapsed-into-a-flat-haystack-s2) ·
**Size:** L · **Surface:** `docs/app/` (Agent Builder), served `TOOL-DOMAINS.md`

The measured distribution — median 2 tools per domain, 71% of domains at ≤ 2 tools — means the
domain list cannot be the primary navigation. Above the domain layer, add **task-shaped entry
points**, each resolving to a filtered tool set:

| Entry point | Resolves to |
|---|---|
| "Remember something and be able to prove it later" | `memory` (55) — the grounded path |
| "Store a hypothesis without polluting what I know" | `memory` simulated path |
| "Search across everything I have stored" | `memory` retrieval + `braid` (9) |
| "Connect to a database / filesystem / cloud" | `database` (10), `filesystem` (10), `cloudservice` (10) |
| "Reason about what might be true" | `cognitive` (19), `world` (14), `thought_process` (9) |
| "Run a working session with an agent" | `communication` (9), `productivity` (10) |
| "Everything else" | the ≤ 2-tool tail, grouped alphabetically and collapsed by default |

Three rules for the view itself:

1. **Never render 48,726 characters as one page.** Paginate or filter; the current single-view
   dump is longer than the four marketing pages combined.
2. **Lead with the grounded/simulated distinction inside `memory`,** because that namespace holds
   11% of the surface and the whole claim.
3. **Render the 19 unwired tools as a separate, labelled section** rather than mixing them into
   the working set — the surface already knows they are unwired; the interface should say so.

**Acceptance criteria**

- **AC-6.1** A task-shaped entry point exists for each of the seven rows above, and each resolves
  to a non-empty tool set. Verify: activate each; assert a non-zero count and a stable filter.
- **AC-6.2** The Agent Builder view renders no more than ~2,000 characters before requiring a
  filter or pagination. Verify: `document.body.innerText.length` at first paint of `#agents`.
  Today: 48,726.
- **AC-6.3** Unwired tools are labelled in the UI with the same vocabulary as
  `docs/surface.json`. Verify: the 19 names appear under a distinct heading.
- **AC-6.4** *(negative test)* No tool is reachable **only** by scrolling. Verify: every one of
  the 487 names is reachable through a filter or a labelled section.

---

### R-07 — Make the cadence badges read from the data

**Closes:** [F-07](#f-07--cadence-claims-are-not-met-and-the-gap-is-user-visible-s2) ·
**Size:** S · **Surface:** `docs/series/`, `docs/series/data/*.json`

The data layer is already honest — `state: planned` and `state: in_production` are accurate, and
the `state_legend` defines them. The defect is that the static badges don't read it.

Replace the hardcoded claims with derived ones:

- Chronicles: instead of *"New entries daily"*, render *"Last installment 2026-11-10"* plus the
  count. If the cadence promise is worth keeping, keep it — but derive "daily" from `cadence` in
  `chronicles.json` and surface the delta when it is exceeded.
- Comic: instead of *"In production"* as a blanket badge, render the per-issue `state` from
  `comic-issues.json` — which already distinguishes `ready` / `in_production` / `planned`.

**Acceptance criteria**

- **AC-7.1** No date or state literal appears in the series HTML that is not also present in the
  corresponding JSON feed. Verify: diff the numbers/dates in the rendered page against the feed.
- **AC-7.2** When the newest chronicle entry is older than `cadence`, the page says so. Verify:
  compare `max(entries.date)` to the current date and assert a visible delta.
- **AC-7.3** The comic index reports `pages` per issue from the feed, including `0`. Verify:
  the three shipped issues render `0, 0, 0` pages today, matching the feed exactly.
- **AC-7.4** *(negative test)* A feed with zero entries must render "no installments yet", not an
  empty list and not a stale date.

---

### R-08 — Turn on the tracker, and make focus visible

**Closes:** [F-09](#f-09--keyboard-focus-is-effectively-invisible-s3),
[F-10](#f-10--the-instrumentation-ships-but-transmits-nothing-s2),
[F-11](#f-11--101-kb-of-reference-material-is-orphaned-s3),
[F-12](#f-12--the-machine-readable-surface-is-unlisted-s3),
[F-13](#f-13--the-shell-has-no-unique-title-description-or-canonical-s3) ·
**Size:** S · **Surface:** `docs/series/`, `docs/`, `docs/app/`

Five small, independent fixes bundled because each is a one-file change:

1. **Focus indicator.** Add one rule to `series.css`:
   `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }`. The accent is
   10.70:1 against the background — comfortably above the 3:1 requirement.
2. **Tracker endpoint.** Set `CFG.endpoint` to a real collector, keeping every privacy property
   in the file as it stands. Add the tracker to `/app/`.
3. **Link the orphaned docs.** Add a `Docs` group to the landing-page footer linking `README.md`,
   `TOOL-DOMAINS.md`, `02-tools-reference.md` and `05-complete-tools-reference.md` — or, better,
   render them as HTML instead of serving raw markdown.
4. **Link `surface.json`.** Add it to the footer next to the other machine-readable artefacts,
   following the pattern the series pages already use for their JSON feeds.
5. **Shell metadata.** Give `/app/` its own `<title>`, `<meta name="description">` and
   `<link rel="canonical">`.

**Acceptance criteria**

- **AC-8.1** Tab through `/` — every focused element has a visible indicator with ≥ 3:1 contrast
  against its adjacent colour. Verify: the tab-walk in [Appendix A](#appendix-a--reproduction);
  assert `outlineColor` resolves to a token, not `rgb(16,16,16)`.
- **AC-8.2** `analytics.js` on a public page issues at least one network request to `endpoint`.
  Verify: capture requests on `/`; assert a request to the configured collector.
- **AC-8.3** `DNT: 1` still suppresses that request. Verify: send the header; assert **no**
  collector request. The privacy guarantee must survive the fix.
- **AC-8.4** `/app/` has a `<title>` distinct from `/`, plus a description and a canonical. Verify:
  compare the two titles; assert inequality.
- **AC-8.5** *(negative test)* No documentation page is reachable only by guessing its filename.
  Verify: crawl from `/` and assert every served `*.md` and `surface.json` is reached within two
  hops.

---

### 6.1 Sequencing

| Wave | Recommendations | Rationale |
|---|---|---|
| **1 — stop the self-contradiction** | R-01, R-04, R-08 | Smallest possible change that removes the three credibility defects a first-time visitor meets. R-01 is a build-time injection; R-04 is one file plus a decision; R-08 is five one-liners. |
| **2 — make the shell reachable** | R-02, R-05 | R-02 decides whether the published shell can work for anyone but its author. R-05 forces the mobile question to be answered rather than absorbed. |
| **3 — fix the reading experience** | R-03, R-07 | Visual and editorial integrity once the identity and access questions are settled. |
| **4 — make the surface navigable** | R-06 | The largest piece, and the only one that needs design exploration rather than a fix. Do it last so it is built on a surface that is already honest. |

---

## 7. Measurement plan

Because [F-10](#f-10--the-instrumentation-ships-but-transmits-nothing-s2) is true, the honest
first step of any measurement plan here is **turning on collection**. The table below is written
so that each metric is collectable by the existing tracker once `CFG.endpoint` is set — no new
instrumentation is invented.

| Metric | Definition | Questions it answers | Recommendation |
|---|---|---|---|
| `version_consistency` | 1 when `VERSION` == badge == shell, else 0 | Does the surface agree with itself? | R-01 |
| `page_view{route}` | Per-route view count | Which of the four surfaces is actually visited? | R-04, R-08 |
| `404_hit{path}` | Requests landing on the branded 404 | Which dead routes do people actually hit? | R-04 |
| `shell_api_fail{host}` | Failed `/api/*` requests by target host | Is anyone configuring a real backend? | R-02 |
| `connection_save{host_kind}` | Saves in the `Connection` view | Does the recovery path get used? | R-02 |
| `tools_filter_used{entry}` | Task-shaped entry points activated | Which groupings earn their place? | R-06 |
| `feed_staleness_days` | Days since newest chronicle entry | Is the cadence claim true? | R-07 |
| `keyboard_focus_visible` | 1 when a Tab stop has ≥ 3:1 indicator | Is focus usable? (spot-check, not continuous) | R-08 |

**Baseline is not available**, and that is the point: every number in this table starts at
"unmeasured". The first sprint after R-08 produces the baseline; everything before it should be
read as pre-evidence.

### 7.1 The study this document cannot replace

The findings above are technical and heuristic. They do not tell anyone how a real person reacts
to landing on a trust product that reports two versions of itself. That needs participants. The
minimum viable study, scoped to what is cheapest to run:

- **5 participants per persona**, P1 (evaluating engineer) and P2 (memory-integrity reviewer).
  Five is the point of diminishing returns for qualitative defect discovery at this stage; it is
  not a statistically powered sample and should not be reported as one.
- **Two task scenarios, unmoderated, screen-recorded:**
  1. *"You have 15 minutes. Decide whether mem20 4.0.0 is a memory layer you would put under a
     production agent, and show me what convinced you."* — measures whether the version
     contradiction is noticed and what it costs.
  2. *"Find the tool that lets you store something and later prove it was stored. Show me how you
     looked."* — measures whether 487 tools is navigable, and by what strategy
     ([F-06](#f-06--the-tool-surface-has-collapsed-into-a-flat-haystack-s2)).
- **Success criteria:** scenario 1 — participant states the correct version and names the
  grounded/simulated partition without prompting; scenario 2 — participant locates the correct
  tool in under 3 minutes without being told the domain name.
- **The one number to watch:** how many of five notice the version contradiction unaided. If it
  is 0/5 that is a real and useful result — it means the defect is an audit finding rather than a
  user-facing one, and R-01 drops from wave 1 to wave 3.

---

## 8. Open questions this study did not answer

Stated as questions, because each one is a decision the team owes an answer to and none of them
is answerable from the surface alone.

1. **Is `/app/` meant to be public?** Everything in [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1),
   [F-03](#f-03--the-shell-has-zero-width-navigation-on-mobile-s2) and
   [R-05](#r-05--decide-and-declare-the-shells-mobile-posture) follows from this one. A local
   operator tool published at a public URL is a category error, not a bug, and the fix differs
   entirely depending on the answer.
2. **Should the five 404-ing sections exist?** `pricing`, `docs`, `use-cases`, `dashboard`,
   `market` all have repo source. Routing them and not routing them are both defensible; leaving
   them as 404s is not.
3. **Is the Chronicles cadence a promise or an aspiration?** The data model supports either. The
   `.json` says `daily`; the calendar says otherwise. Only the team knows which is true.
4. **Was the comic ever intended to ship pages?** Three issues, three titles, zero pages. Either
   the art is coming or the index should say `planned` at the series level.
5. **Who owns the live surface?** `docs/series/data/*.json` names `site_owner: mem20-webdev` and
   `canon_owner` separately for each property. That split is good practice and this document was
   written to respect it — but the shell's ownership is not declared anywhere, and the version
   contradiction sits precisely in the gap between "the site" and "the shell".

---

## Appendix A — Reproduction

Every measurement in this document is reproducible. Requires `curl` and a Chromium-capable
Playwright install.

```bash
# 1. route inventory + status codes
for p in "" series/ series/comic/ series/chronicles/ app/ pricing/ docs/ \
         dashboard/ use-cases/ market/ sitemap.xml robots.txt favicon.ico api/health; do
  printf '%-24s -> ' "/$p"
  curl -sL -o /dev/null -w '%{http_code} %{size_download}\n' --max-time 20 "https://mem20.com/$p"
done

# 2. focus indicator (expect: rgb(16, 16, 16) — the failing value)
# 3. mobile overflow   (expect: series +182px, comic +106px, chronicles +96px at 390px)
# 4. shell request trace (expect: GET http://127.0.0.1:8221/api/boards, ERR_CONNECTION_REFUSED)
python3 - <<'PY'
from playwright.sync_api import sync_playwright

pages = {
    "root":   "https://mem20.com/",
    "series": "https://mem20.com/series/",
    "comic":  "https://mem20.com/series/comic/",
    "chron":  "https://mem20.com/series/chronicles/",
    "app":    "https://mem20.com/app/",
}

with sync_playwright() as p:
    b = p.chromium.launch()

    # 2. focus indicator
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page(); pg.goto(pages["root"], wait_until="networkidle")
    for i in range(10):
        pg.keyboard.press("Tab")
        print("focus", i + 1, pg.evaluate(
            "()=>{const c=getComputedStyle(document.activeElement);"
            "return c.outlineStyle+' '+c.outlineWidth+' '+c.outlineColor;}"))
    ctx.close()

    # 3. mobile overflow
    for name, url in pages.items():
        for w in (320, 390, 768):
            ctx = b.new_context(viewport={"width": w, "height": 844})
            pg = ctx.new_page(); pg.goto(url, wait_until="networkidle")
            m = pg.evaluate("()=>({s:document.documentElement.scrollWidth,"
                            "c:document.documentElement.clientWidth})")
            print(f"overflow {name}@{w}", m["s"] - m["c"], "px")
            ctx.close()

    # 4. shell request trace + text volume
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page(); reqs = []
    pg.on("requestfailed", lambda r: reqs.append(r.url))
    pg.goto(pages["app"], wait_until="load"); pg.wait_for_timeout(4000)
    print("failed requests:", reqs)
    for frag in ("#kanban", "#dreams", "#agents", "#memory"):
        pg.goto(pages["app"] + frag, wait_until="load"); pg.wait_for_timeout(1500)
        print(frag, "text length:", pg.evaluate("document.body.innerText.trim().length"))
    ctx.close()
    b.close()
PY
```

**Capture environment:** Chromium `139.0.7258.5` · capture date `2026-11-16` · all probes
anonymous (no auth), from a public network.

---

## Appendix B — Findings index

| ID | Finding | Severity | Confidence | Recommendation |
|---|---|---|---|---|
| [F-01](#f-01--three-different-version-identities-on-one-domain-s1) | Three version identities on one domain | **S1** | Observed | R-01 |
| [F-02](#f-02--the-public-shell-requests-a-loopback-address-s1) | Public shell requests loopback | **S1** | Observed | R-02, R-05 |
| [F-03](#f-03--the-shell-has-zero-width-navigation-on-mobile-s2) | Zero-width nav on mobile | S2 | Observed | R-03, R-05 |
| [F-04](#f-04--the-best-honesty-on-the-property-is-the-default-state-s2) | Best honesty is the default state | S2 | Observed / Inferred | R-02, §5 |
| [F-05](#f-05--the-five-sections-a-buyer-would-try-are-all-404-s2) | Five intent routes 404, unbranded | S2 | Observed | R-04 |
| [F-06](#f-06--the-tool-surface-has-collapsed-into-a-flat-haystack-s2) | 487 tools in a flat haystack | S2 | Observed / Inferred | R-06 |
| [F-07](#f-07--cadence-claims-are-not-met-and-the-gap-is-user-visible-s2) | Cadence claims unmet | S2 | Observed | R-07 |
| [F-08](#f-08--the-series-pages-break-horizontally-on-a-phone-s2) | Series pages break on mobile | S2 | Observed | R-03 |
| [F-09](#f-09--keyboard-focus-is-effectively-invisible-s3) | Focus ring invisible (1.04:1) | S3 | Observed | R-08 |
| [F-10](#f-10--the-instrumentation-ships-but-transmits-nothing-s2) | Tracker transmits nothing | S2 | Observed | R-08 |
| [F-11](#f-11--101-kb-of-reference-material-is-orphaned-s3) | 101 KB of docs orphaned | S3 | Observed | R-08 |
| [F-12](#f-12--the-machine-readable-surface-is-unlisted-s3) | `surface.json` unlisted | S3 | Observed | R-08 |
| [F-13](#f-13--the-shell-has-no-unique-title-description-or-canonical-s3) | Shell has no unique metadata | S3 | Observed | R-08 |

**Totals:** 13 findings — 2 critical, 6 high, 5 medium. 8 recommendations across 4 waves.

---

## Appendix C — Relationship to prior UX work

This document continues the research line indexed in [`docs/ux/README.md`](./README.md) and does
not supersede it.

| Prior work | Relationship |
|---|---|
| [`docs/ux/README.md`](./README.md) — UX acceptance specs #37–#40 | Covers the **desktop shell** (`mem20controlz/`). This document covers the **public web surface** (`mem20.com/` + `docs/app/`). Disjoint surfaces; shared house style (acceptance criteria runnable by a reviewer, negative tests, instrumented). |
| [`desktop-personas-2026-11-01.md`](./desktop-personas-2026-11-01.md) · [`desktop-task-flows-2026-11-01.md`](./desktop-task-flows-2026-11-01.md) | Five desktop personas and fifteen task flows. The personas here (P1–P5) are **web-surface** personas and do not reuse the desktop set, because the addressees differ: the desktop shell addresses an operator; the landing page addresses an evaluator. |
| [`surface-gap-register-2026-11-01.md`](./surface-gap-register-2026-11-01.md) | Six gaps in the desktop views. Its **G-06** notes a tool-count slice mismatch, latent because the desktop catalog (270 tools across 27 domains) sat below the 400-item slice. **That latency has since resolved into a live defect here:** the *web* surface now carries the full 487 tools across 129 domains ([F-06](#f-06--the-tool-surface-has-collapsed-into-a-flat-haystack-s2)). The register's own reasoning was correct; the surface moved out from under its premise. |
| [`docs/hygiene/doc-count-gate.md`](../hygiene/doc-count-gate.md) | The gate that fails CI on a stale tool/domain band in a live doc. This document uses only the live pin (**487 tools / 129 domains**) and passes the gate; it is also out of the gate's scope by filename date stamp, as intended for dated records. |

**Note for whoever maintains the gate's scope list:** `docs/ux/` is not currently in the gate's
in-scope prefixes, and it is also not in the excluded list. Dated filenames happen to exempt every
file currently in that directory, so the gate is neither enforcing nor deliberately exempting this
directory — it is exempting it by accident. Worth an explicit decision either way.

---

**Author:** UX Research · **Capture date:** 2026-11-16 · **Release:** 4.0.0
**Next action:** [R-01](#r-01--make-the-version-identity-single-sourced) and
[R-04](#r-04--ship-a-branded-404-and-a-sitemap) in wave 1; the study in
[§7.1](#71-the-study-this-document-cannot-replace) scheduled against the first build that
ships them.
