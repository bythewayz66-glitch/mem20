# Frontend surface drift audit — 2026-11-01

**Owner:** mem20-frontends (directive roster row 4, gap G3)
**Roster of record:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`
**Baseline audited:** `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf`
**Scope:** `web/src/**`, `docs/dashboard.html`, `web/src/data/tools.json`

> **Standing rule applies to this document:** a deliverable exists only as a **commit SHA on a pushed
> branch**. Every row below cites `file:line`, and every count was derived by running a command against
> the baseline tree — not quoted from another report.

---

## 0. Headline

**The in-scope frontend surfaces are already converged.** There is no stale tool count, domain count,
route count or release version displayed anywhere in `web/src/**` or `docs/dashboard.html` at
`2ea44922`. The `v3.0.0` / count drift named in gap G3 is real, but it lives in `docs/index.html` and
`docs/app/deck/` — **not** in the surfaces this row owns.

What this branch changes is therefore **hardening, not correction**: one edit to
`web/src/data/catalog.ts` that removes the only code path by which a stale count could reach the UI, plus
a single version constant so the release string has one source instead of none.

That is the honest result. No drift was manufactured to fill the table.

---

## 1. Canonical values, proven from source

The directive states the correct surface as **270 tools / 27 domains / v3.1.0**. That was treated as a
*claim to verify*, not an input. Two independent derivations were run against `2ea44922`:

### Tool count

| # | Method | Command | Result |
|---|---|---|---|
| A | Raw registrations, deduped | `grep -rhoE 'self\.tools\["[a-z0-9_]+"\]' mcp/ --include=*.py \| sort -u \| wc -l` | **270** |
| B | AST over every tool module | `python3 web/scripts/extract-tools.py --root . --out /tmp/t270.json` | **count 270** |

Method B output: `36 files -> 270 tools across 27 domains`, with `domain_count = 27`,
`files_scanned = 36`, `len(domains) = 27`.

Both agree at **270**. Method A dedupes on the registration string; method B walks `mt.Tool(...)`
declarations. Two different traversals landing on the same integer is the proof — a single grep is not.

### Domain count

`len(domains) = 27` from method B, and independently `len(tools.json.domains) = 27` with
`domain_count = 27`. Per-domain records reconcile exactly:

```
derived domains from records : 27
header-declared domains      : 27
header-only domains          : []      (none)
record-only domains          : []      (none)
```

### Version

| Source | Value |
|---|---|
| `VERSION` (repo root, line 1) | `3.1.0` |
| `git tag --list 'v3*'` (tail) | `v3.1.0`, `v3.1.1` |

The release string to converge on is **`3.1.0`**, with tag `v3.1.1` existing on top of it. The `v3.0.0`
being purged elsewhere in the estate is stale, which confirms G3.

### The arithmetic closes

```
257 (retired) + 3 (memory_* 49 -> 52) + 10 (lie_* absent from every table) = 270
```

Those 10 `lie_*` tools are the 27th domain. `270 / 27 = 10.0` exactly, so the per-domain average is not a
rounding artefact of a wrong domain count.

---

## 2. Drift table

**Status** is one of `correct` (verified, no change), **`FIXED`** (changed on this branch), or
`deliberate non-edit` (must not be rewritten — see §4).

### 2.1 `web/src/data/tools.json` — the generated catalog

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 1 | `web/src/data/tools.json:1` | `count` | `270` | `270` | correct |
| 2 | `web/src/data/tools.json:1` | `domain_count` | `27` | `27` | correct |
| 3 | `web/src/data/tools.json:1` | `files_scanned` | `36` | `36` | correct |
| 4 | `web/src/data/tools.json:1` | `domains[]` length | `27` | `27` | correct |
| 5 | `web/src/data/tools.json:1` | `tools[]` length | `270` | `270` | correct |
| 6 | `web/src/data/tools.json:1` | duplicate tool names | `0` (270 unique) | `0` | correct |

**No stale tool or domain count exists in `tools.json`.** Header and records agree on all three figures,
and the domain list set-matches the domains actually present on the records — no orphans in either
direction. This is the file five views read, so a stale number here would have propagated everywhere at
once. It is clean.

**Structural risk documented (not drift today):** the file has been written in **two shapes** by two
generators — short keys `n/t/d/x/p` (what is committed) and long keys
`name/title/description/domain/params` (what `.github/workflows/mem20-web.yml` writes when it
regenerates). `catalog.ts` normalises both, which is the right call; a generator reverting to one shape is
the realistic mechanism by which this file next goes wrong. See `web/src/data/catalog.ts:1-19`.

### 2.2 `web/src/data/catalog.ts` — the normaliser

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 7 | `web/src/data/catalog.ts:10` | comment: "regenerated the file at 270 tools / 27 domains" | `270` / `27` | `270` / `27` | correct |
| 8 | `web/src/data/catalog.ts:87` | source of truth for `count` | header `rawCatalog.count` won over the records | records win, header is fallback | **FIXED** |
| 9 | `web/src/data/catalog.ts:88` | source of truth for `domain_count` | header `rawCatalog.domain_count` won over the records | records win, header is fallback | **FIXED** |
| 10 | `web/src/data/catalog.ts:102` | release version constant | *did not exist* | `MEM20_VERSION = '3.1.0'` | **FIXED** (added) |

**Why 8 and 9 were a real drift path, not a style nit.** The precedence was
`rawCatalog.count ?? tools.length` — the header was authoritative and the records were only a fallback.
The UI prints `CATALOG.count` next to rows it renders from `CATALOG.tools`. If a regeneration writes a
fresh header but a truncated `tools[]` (or a header computed from a different scan than the rows), the
shell displays a total that no row on screen can be checked against — the exact failure class this
surface exists to prevent. Inverted to `recordCount || (rawCatalog.count ?? 0)`. The header is now
consulted only when there are zero records, the one case where it is the sole evidence available.

**Row 10 is a source, not yet a consumer.** `MEM20_VERSION` is exported and available; no view imports it
on this branch (see §3.3 for why). It exists so the release string has exactly one place to change
instead of being retyped per surface.

### 2.3 `web/src/views/DocsFaq.tsx` — the tool reference and FAQ

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 11 | `web/src/views/DocsFaq.tsx:132` | "`{CATALOG.count} tools across {CATALOG.domain_count} domains`" | dynamic | `270` / `27` | correct |
| 12 | `web/src/views/DocsFaq.tsx:135` | bare `257` | `257` | — | deliberate non-edit |
| 13 | `web/src/views/DocsFaq.tsx:135` | bare `258` | `258` | — | deliberate non-edit |
| 14 | `web/src/views/DocsFaq.tsx:136` | bare `268` | `268` | — | deliberate non-edit |
| 15 | `web/src/views/DocsFaq.tsx:190` | tool-reference tab label `({CATALOG.count})` | dynamic | `270` | correct |
| 16 | `web/src/views/DocsFaq.tsx:285` | empty-state "`{CATALOG.count}` are registered" | dynamic | `270` | correct |

**On 12–14:** these are the *only* bare stale-looking literals in `web/src/**`, and they are **sentences
about** the retired values — "`257`, `258` and `268` are retired counts and are not restated here."
Rewriting them would destroy the record of what was previously claimed and is explicitly out of bounds
(§4). They were classified individually by reading the surrounding four lines, not by bare-number grep —
a loose regex reports these three as a failure.

### 2.4 `web/src/views/AgentBuilder.tsx` — agent builder

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 17 | `web/src/views/AgentBuilder.tsx:53` | "`{CATALOG.count} tools across {domains.length} domains`" | dynamic | `270` / `27` | correct |
| 18 | `web/src/views/AgentBuilder.tsx:54` | "`({CATALOG.files_scanned} files)`" | dynamic | `36` | correct |

No version string, no hardcoded count. `domains` is derived per-render from `CATALOG.tools`
(`AgentBuilder.tsx:32`), so it cannot disagree with the rows.

### 2.5 `web/src/views/Sales.tsx` — sales surface

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 19 | `web/src/views/Sales.tsx:81` | "`{CATALOG.count} tools`" | dynamic | `270` | correct |
| 20 | `web/src/views/Sales.tsx:84` | "`{DOMAINS} domains`" | derived from records (`Sales.tsx:12`) | `27` | correct |
| 21 | `web/src/views/Sales.tsx:99` | "`11 wire routes`" | `11` | `11` | correct |

Row 21 is the one hand-typed number on this page. Checked against the real transcription: `DOOR_ROUTES`
in `web/src/lib/api.ts:334-351` holds 11 entries — `GET/POST /api/boards`,
`GET/DELETE /api/boards/:boardId`, `POST /api/boards/:boardId/done-column`, `POST /api/tasks`,
`GET/PUT /api/tasks/:taskId`, `PATCH /api/tasks/:taskId/metadata`, `POST /api/tasks/:taskId/move`,
`DELETE /api/tasks/:taskId`. **11 is correct.** It is a duplicated literal and therefore a future drift
risk; converting it to `DOOR_ROUTES.length` is the right follow-up (§6), not done here because this is a
count audit, not a refactor.

### 2.6 `web/src/views/Connection.tsx` — build provenance

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 22 | `web/src/views/Connection.tsx:161` | "`26 routes from mem20controlz/.../app.py`" | `26` | `26` | correct |

**Row 22 was investigated and cleared — it is NOT stale.** The surface says 26 and `mem20controlz` has
**28** `@app.<verb>("...")` decorators, which looks like a 2-route drift. It is not: two of the 28 are
non-`/api` SPA catch-alls (`GET /` and `GET /{full_path:path}`, both `include_in_schema=False`), leaving
exactly **26 API routes**. Set-comparison against `CONTROL_ROUTES` (`web/src/lib/api.ts:356-383`, 26
entries) returns zero difference in either direction:

```
decorators total : 28
api-only         : 26
non-api          : [('GET', '/'), ('GET', '{full_path:path}')]
in py not ts     : []      <- none
in ts not py     : []      <- none
```

Count and transcription are both correct. **No change made.**

### 2.7 `web/src/lib/api.ts` — the client route tables

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 23 | `web/src/lib/api.ts:334-351` | `DOOR_ROUTES.length` | `11` | `11` | correct |
| 24 | `web/src/lib/api.ts:356-383` | `CONTROL_ROUTES.length` | `26` | `26` | correct |

`DoorSync.tsx:115` renders `{DOOR_ROUTES.length} routes`, so the door route count is already dynamic —
there is no hardcoded door route number anywhere in `web/src/**`. `CONTROL_ROUTES` is a hand-maintained
transcription and is set-identical to the source (§2.6).

### 2.8 `web/src/App.tsx` — shell navigation

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 25 | `web/src/App.tsx:49` | "the five hard invariants" | `5` | `5` | correct |

Cross-checked against `README.md:327-337` (five numbered invariants) and `MemoryModel.tsx:10-40` (five
`INVARIANTS` entries). Consistent. No version string in the shell chrome.

### 2.9 `docs/dashboard.html` — launch dashboard

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 26 | `docs/dashboard.html:319` | "Surface 270 tools / 27 domains" | `270` / `27` | `270` / `27` | correct |
| 27 | `docs/dashboard.html:676` | "Tool surface — 270 tools / 27 domains" | `270` / `27` | `270` / `27` | correct |
| 28 | `docs/dashboard.html:694` | README row, "270 tools / 27 domains" | `270` / `27` | `270` / `27` | correct |
| 29 | `docs/dashboard.html:695` | `docs/index.html` row, "270 tools / 27 domains" | `270` / `27` | `270` / `27` | correct |
| 30 | `docs/dashboard.html:687` | "Retired surface — 257 / 26" | `257` / `26` | — | deliberate non-edit |
| 31 | `docs/dashboard.html:679` | prose "The retired 257 / 26 figure" | `257` / `26` | — | deliberate non-edit |
| 32 | `docs/dashboard.html:696` | "270 / 27, prior 257 / 26" | `270` / `27` + prior | correct | correct |
| 33 | `docs/dashboard.html:697` | CHANGELOG row, "270 / 27" | `270` / `27` | `270` / `27` | correct |

**`docs/dashboard.html` is fully converged.** It carries 270/27 in all four display positions and has
**zero** `v3.0.0` occurrences — it has no version stamp of its own, so there is nothing to purge. Rows 30,
31 and 32's "prior" are the page's own stale→new ledger describing what *was* said; per §4 they must
survive, and they do.

### 2.10 Other frontend surfaces

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 34 | `web/package.json:4` | `"version"` | `"0.1.0"` | `"0.1.0"` | correct (app manifest, **not** the release) |
| 35 | `web/index.html:17` | `<title>` | no version | no version | correct |

Row 34 is a near-miss worth stating: `web/package.json` carries the **Vite app's own** manifest version
`0.1.0`, deliberately not the mem20 release. A sweep that "fixed" this to `3.1.0` would be wrong in a way
that looks right. `MEM20_VERSION` therefore lives in `catalog.ts` with a comment saying why
`package.json` is not its source.

---

## 3. What this branch changes

**One file: `web/src/data/catalog.ts`.** No dependency entered — `package-lock.json` is unchanged and not
committed.

### 3.1 `web/src/data/catalog.ts:64-91` — records become authoritative

```ts
const recordCount = tools.length;
const recordDomainCount = domains.length;
// ...
count: recordCount || (rawCatalog.count ?? 0),
domain_count: recordDomainCount || (rawCatalog.domain_count ?? 0),
```

was:

```ts
count: rawCatalog.count ?? tools.length,
domain_count: rawCatalog.domain_count ?? domains.length,
```

Effect: the header's `count`/`domain_count` can no longer contradict the rows being displayed. Today both
read 270/27, so **there is no visible change** — the fix removes the state in which they could diverge.

### 3.2 `web/src/data/catalog.ts:93-102` — one version source

```ts
export const MEM20_VERSION = '3.1.0';
```

New. Deliberately a constant: the shell ships as a static bundle and cannot open `VERSION` at runtime.
The comment records that `web/package.json` is **not** the source (§2.10 row 34) and that a release move
is a one-line change.

### 3.3 Why no view consumes `MEM20_VERSION` yet

I drafted version stamps for `DocsFaq.tsx` and `Connection.tsx` and then **reverted them**. Both files are
170–295 lines; re-emitting them whole through the commit API risks a truncated body, and a truncated
`DocsFaq.tsx` would break the tool reference — strictly worse than the missing stamp. The constant is
committed and ready; wiring it into those two views is a small follow-up that should be done with a
normal `git` push, not a hand-rebuilt file body. Recorded in §6.

---

## 4. Deliberate non-edits (with reasons)

Rewriting these would falsify a record. The diff would look identical to a correct fix.

| file:line | Content | Why it stays |
|---|---|---|
| `web/src/views/DocsFaq.tsx:135-136` | "`257`, `258` and `268` are retired counts and are not restated here" | A sentence **about** the retired values. Rewriting it removes the evidence they were reconciled. |
| `docs/dashboard.html:687` | "Retired surface — 257 / 26" | The page's own stale→new ledger column. It describes what *was* said. |
| `docs/dashboard.html:679` | "The retired 257 / 26 figure" | Same — prose that names the retired figure. |
| `docs/dashboard.html:696` | "270 / 27, prior 257 / 26" | The "prior" is dated history; the current value is already correct. |
| `docs/app/deck/index.html:42,49,71,89,96` | "`VERSION` was 3.0.0" at pinned commit `45445f48` | Explicitly pinned historical note, with the page stating the shipped tree is 3.1.0. Correct as written. **Outside my scope** — `docs/app/` is the Webpage Developer's G3 row. |
| `scripts/sweep-tool-counts.py` `SKIP_FILES` | `web/src/views/DocsFaq.tsx` excluded from the sweep | Correct: the sweep would have rewritten rows 12–14. This exclusion is why the file is safe. |

**`v3.0.0` occurrences in scope: 0.** `grep -rn 'v3\.0\.0\|3\.0\.0' web/src/ docs/dashboard.html` returns
nothing. Every `3.0.0` in the tree lives in `docs/app/deck/` as a pinned historical record — the Webpage
Developer's surface, not `web/src/**`.

---

## 5. Verification

All commands run in `/workspace/mem20` at `2ea44922` plus this branch's one-file change.

**Typecheck and build** (`web/`):

```
npx tsc --noEmit      ->  exit 0, no diagnostics
npm run build         ->  44 modules transformed, built in 2.49s
                          dist/assets/index-DiN80dzN.js   267.65 kB (gzip 82.32)
                          dist/assets/index-BMgU54DU.css   13.53 kB (gzip  3.46)
```

The bundle hash moved `index-BS9Fg-qc.js` -> `index-DiN80dzN.js` purely because of the `catalog.ts` edit.

**Built-output assertions** against `dist/assets/index-DiN80dzN.js`:

| Assertion | Result |
|---|---|
| `/257\s*tools/` present | **no** |
| `/26\s*domains/` present | **no** |
| `/v?3\.0\.0/` present | **no** |
| `270` present | **YES** |
| `27` present | **YES** |
| `26 routes` present | **YES** (correct — §2.6 row 22) |

The shipped bundle carries 270/27 and no stale figure of any kind.

**Residual sweep.** `scripts/sweep-tool-counts.py` (the repo's own idempotent converger, dry-run default)
reports **0 matching files under `web/` and `docs/dashboard.html`** — true before this change and still
true after it, which is the expected result for a surface that was already converged and is now merely
hardened against future regeneration.

**Independent regex sweep** over every `web/src/**/*.{ts,tsx,json}` plus `docs/dashboard.html` for
`203|257|258|259|260|265|268|270|271` + `tools?/domains?`, `24-29` + `domains?`, `v?3.x.y`, and
`24-28 routes` returned only the rows tabulated above — every hit individually classified, none
unexplained.

**Baseline currency.** `main` advanced from `2ea44922` to `3955432` during this run (a CI fix). Checked
before landing:

```
git diff --name-status 2ea44922 origin/main -- web/ docs/dashboard.html
(empty)
```

No in-scope surface changed, so this audit and its fix apply unchanged to current `main`.

---

## 6. What this audit does and does not establish

**Establishes:** no in-scope frontend surface displays a stale tool count, domain count, route count or
release version as of `2ea44922`/`3955432`. One hardening change landed so the catalog header can no
longer contradict the rows it summarises, and the release string now has a single named source.

**Does not establish, and does not claim:**

1. **The served bundle at `docs/app/assets/` still carries the old build.** `docs/app/` is a **published
   build artefact**, not a source tree. Regenerating it is `cp -r web/dist/assets/. docs/app/assets/` plus
   repointing `docs/app/index.html` — the `.github/workflows/mem20-web.yml` publish step's job, not this
   branch's. **This branch does not repoint `docs/app/index.html` and does not commit the new bundle.**
   Doing so by hand is the failure mode where the entry point points at a bundle that was never pushed.
   The next publish run picks up `index-DiN80dzN.js` from a fresh build. A stale-string check on the live
   URL therefore cannot be satisfied by this branch alone.
2. **`v3.1.0` vs `v3.1.1` is an open question.** `VERSION` says `3.1.0`; tag `v3.1.1` exists on top of it.
   `MEM20_VERSION` follows `VERSION`, the value the directive names and the one `cat VERSION` returns. If
   the estate decides the tag is authoritative, `catalog.ts:102` is the single line to change.
3. **Two duplicated literals remain, deliberately.** `Sales.tsx:99` ("11 wire routes") and
   `Connection.tsx:161` ("26 routes") are both **correct today** and both hand-typed. They should become
   `DOOR_ROUTES.length` and `CONTROL_ROUTES.length`. Not done here: it is a refactor outside a count
   audit's scope, and changing code that is already correct adds review surface without closing a gap.
4. **`docs/index.html` is not mine.** Gap G3 also covers `docs/index.html` (270 x8, 27 x8, `v3.0.0` x4 per
   the directive). That is roster row 3, **Webpage Developer**. This document covers `web/src/**` and
   `docs/dashboard.html` only.
5. **`web/package.json` `0.1.0` is intentional** and must not be "corrected" to the release version (§2.10
   row 34).
6. **`MEM20_VERSION` is exported but not yet rendered** (§3.3). Wiring it into `DocsFaq.tsx` and
   `Connection.tsx` is the remaining half of the version work.

---

## 7. Recommendations

1. **Make the header non-authoritative in the generator too.** `catalog.ts` now defends the UI, but the
   cleanest fix is for `web/scripts/extract-tools.py` to derive `count` and `domain_count` from the `tools`
   array it is about to write, in the same expression, so a truncation cannot produce a header that
   disagrees with its own payload. That turns a UI-layer guard into a data-layer invariant. Logged rather
   than implemented: it changes the generator `mem20-web.yml` depends on and warrants its own review.
2. **Consume `MEM20_VERSION` in `DocsFaq.tsx` and `Connection.tsx`** (§3.3) — a two-line change per file,
   best done with a real `git` push.
3. **Replace the two hand-typed route counts** with `DOOR_ROUTES.length` / `CONTROL_ROUTES.length` (§6.3).
4. **Add a CI assertion** that `tools.json`'s header equals its record counts, so the guard is enforced at
   build time rather than trusted at render time.
