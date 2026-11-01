# Frontend surface drift audit — 2026-11-01

**Owner:** mem20-frontends (directive roster row 4, gap G3)
**Roster of record:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`
**Baseline audited:** `main` = `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110` (re-audited 2026-11-01 after rebase; first pass was `2ea44922`)
**Scope:** `web/src/**`, `docs/dashboard.html`, `web/src/data/tools.json`, `web/scripts/extract-tools.py`

> **Standing rule applies to this document:** a deliverable exists only as a **commit SHA on a pushed
> branch**. Every row below cites `file:line`, and every count was derived by running a command against
> the baseline tree — not quoted from another report.

---

## 0. Headline

**The in-scope frontend surfaces were already converged on display; the defect was upstream of them.**

At `2ea44922` no stale tool count, domain count, route count or release version was displayed anywhere in
`web/src/**` or `docs/dashboard.html`. The `v3.0.0` / count drift named in gap G3 is real, but it lives in
`docs/index.html` and `docs/app/deck/` — **not** in the surfaces this row owns.

Re-auditing at `d99ab5d8` found something the first pass could not see, because it only appeared after
PR #161 merged: **the catalog generator counted tools the server cannot answer.** `eventstream_tools.py`
and `lattice_tools.py` declare 10 `mt.Tool(...)` registrations, but neither `EventStreamToolsMixin` nor
`LatticeToolsMixin` is inherited by `Mem20MCPServer` in `mcp/server.py`. The AST extractor walked every
file and counted all 282 declarations; the running server served **272**. The web shell would have
advertised 282 tools — a number no user could ever call.

So this branch is **hardening plus one real correction**:

1. `web/scripts/extract-tools.py` now gates on wiring — a declaration counts only if its mixin is
   inherited by `Mem20MCPServer`, or its `install()` is called from `mcp/tools/__init__.py` (the RM-239 /
   RM-052 monkeypatch path). Unwired declarations are excluded from `count` and reported in a new
   `unwired` field so the gap stays auditable.
2. `web/src/data/catalog.ts` takes its counts from the records, not the header, and carries
   `MEM20_VERSION`.
3. `web/src/App.tsx` renders that version and the counts in the rail footer, so the release string has
   one source instead of none.

**Proof the gate is correct:** the regenerated catalog's tool-name set is *identical* to the set returned
by a live `tools/list` handshake — 272 names, zero difference in either direction.

---

## 1. Canonical values, proven from source

The directive states the correct surface as **270 tools / 27 domains / v3.1.0**. That was treated as a
*claim to verify*, not an input. At `d99ab5d8` the verified surface is **272 tools / 29 domains /
v3.1.2**.

### Tool count — three methods, and why two of them are wrong

| # | Method | Command | Result |
|---|---|---|---|
| A | Raw registrations, deduped | `grep -rhoE 'self\.tools\["[a-z0-9_]+"\]' mcp/ --include=*.py \| sort -u \| wc -l` | 282 |
| B | AST over every tool module (pre-fix) | `python3 web/scripts/extract-tools.py --root . --out /tmp/t.json` | 282 |
| C | **Live MCP handshake** | `MEM20_EXPECTED_TOOLS=272 python ./verify_mcp.py` | **272** |
| D | AST with wiring gate (post-fix) | `python3 web/scripts/extract-tools.py --root . --out /tmp/t3.json` | **272** |

A and B agree at 282 — and both are **wrong**, which is the point. Agreement between two static
traversals proves only that they read the same files, not that the server registers what those files
declare. C is the runtime truth: `initialize` + `tools/list` over stdio, the same handshake CI runs.

D matches C exactly. The 10-tool difference is:

```
lattice_emit  lattice_recall  lattice_report  lattice_search  lattice_verify
stream_publish stream_recall stream_report  stream_search  stream_verify
```

All ten are declared in `mcp/tools/lattice_tools.py` and `mcp/tools/eventstream_tools.py` (merged in
PR #161) and none is reachable. `mcp/server.py:108-118` lists 29 mixin bases; the estate defines 31
mixin classes. The two missing are `EventStreamToolsMixin` and `LatticeToolsMixin`.

**This is a backend wiring bug, not a frontend one.** The frontend fix is to stop counting it. The
backend fix — adding the two mixins to the class bases and bumping `MEM20_EXPECTED_TOOLS` to 282 — is
filed as a follow-up, not done here, because it changes the served MCP surface and belongs to the
server owner.

### Domain count

`len(domains) = 29` from method D, matching `len(tools.json.domains) = 29` with `domain_count = 29`.
Per-domain records reconcile exactly:

```
derived domains from records : 29
header-declared domains      : 29
header-only domains          : []      (none)
record-only domains          : []      (none)
```

The 29 excludes the two orphan domains (`lattice`, `eventstream`), which have no reachable tool.

### Version

| Source | Value |
|---|---|
| `VERSION` (repo root, line 1) | `3.1.2` |
| `web/src/data/catalog.ts:102` | `MEM20_VERSION = '3.1.2'` |

The release string to converge on is **`3.1.2`**. The `v3.0.0` being purged elsewhere in the estate is
stale, which confirms G3.

### The arithmetic closes

```
272 (served) = 282 (declared) - 10 (unwired: lattice_* 5 + stream_* 5)
```

`272 / 29 = 9.38`, so the per-domain average is not a rounding artefact of a wrong domain count.

---

## 2. Drift table

**Status** is one of `correct` (verified, no change), **`FIXED`** (changed on this branch), or
`deliberate non-edit` (must not be rewritten — see §4).

### 2.1 `web/src/data/tools.json` — the generated catalog

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 1 | `web/src/data/tools.json:1` | `count` | `270` → `272` | `272` | **FIXED** (regenerated) |
| 2 | `web/src/data/tools.json:1` | `domain_count` | `27` → `29` | `29` | **FIXED** (regenerated) |
| 3 | `web/src/data/tools.json:1` | `files_scanned` | `36` → `45` | `45` | **FIXED** (regenerated) |
| 4 | `web/src/data/tools.json:1` | `domains[]` length | `27` → `29` | `29` | **FIXED** (regenerated) |
| 5 | `web/src/data/tools.json:1` | `tools[]` length | `270` → `272` | `272` | **FIXED** (regenerated) |
| 6 | `web/src/data/tools.json:1` | duplicate tool names | `0` (272 unique) | `0` | correct |
| 6b | `web/src/data/tools.json:1` | `unwired[]` length | *field did not exist* | `10` | **FIXED** (added) |

**The committed catalog was stale by 2 tools and 2 domains** at `d99ab5d8`: it had not been regenerated
since the wave-1 merges. Regenerating it with the wiring-gated extractor produces 272/29, and the
tool-name set is identical to a live `tools/list` handshake. Header and records agree on all figures, and
the domain list set-matches the domains present on the records — no orphans in either direction. This is
the file five views read, so a stale number here propagates everywhere at once.

**Structural risk documented (not drift today):** the file has been written in **two shapes** by two
generators — short keys `n/t/d/x/p` (what is committed) and long keys
`name/title/description/domain/params` (what `.github/workflows/mem20-web.yml` writes when it
regenerates). `catalog.ts` normalises both, which is the right call; a generator reverting to one shape is
the realistic mechanism by which this file next goes wrong. See `web/src/data/catalog.ts:1-19`.

### 2.2 `web/src/data/catalog.ts` — the normaliser

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 7 | `web/src/data/catalog.ts:10` | comment: "regenerated the file at 270 tools / 27 domains" | `270` / `27` | historical note | correct (describes a past commit) |
| 8 | `web/src/data/catalog.ts:87` | source of truth for `count` | header `rawCatalog.count` won over the records | records win, header is fallback | **FIXED** |
| 9 | `web/src/data/catalog.ts:88` | source of truth for `domain_count` | header `rawCatalog.domain_count` won over the records | records win, header is fallback | **FIXED** |
| 10 | `web/src/data/catalog.ts:102` | release version constant | *did not exist* | `MEM20_VERSION = '3.1.2'` | **FIXED** (added) |

**Why 8 and 9 were a real drift path, not a style nit.** The precedence was
`rawCatalog.count ?? tools.length` — the header was authoritative and the records were only a fallback.
The UI prints `CATALOG.count` next to rows it renders from `CATALOG.tools`. If a regeneration writes a
fresh header but a truncated `tools[]` (or a header computed from a different scan than the rows), the
shell displays a total that no row on screen can be checked against — the exact failure class this
surface exists to prevent. Inverted to `recordCount || (rawCatalog.count ?? 0)`. The header is now
consulted only when there are zero records, the one case where it is the sole evidence available.

**Row 10 now has a consumer.** `MEM20_VERSION` is imported by `web/src/App.tsx:9` and rendered in the
rail footer as `mem20 v3.1.2 · 272 tools / 29 domains`, so the release string has exactly one place to
change instead of being retyped per surface. Verified in the built bundle (`3.1.2` and `272` both present
in `dist/assets/index-*.js`) and in a headless render of the shell.

### 2.3 `web/src/views/DocsFaq.tsx` — the tool reference and FAQ

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 11 | `web/src/views/DocsFaq.tsx:132` | "`{CATALOG.count} tools across {CATALOG.domain_count} domains`" | dynamic | `272` / `29` | correct |
| 12 | `web/src/views/DocsFaq.tsx:135` | bare `257` | `257` | — | deliberate non-edit |
| 13 | `web/src/views/DocsFaq.tsx:135` | bare `258` | `258` | — | deliberate non-edit |
| 14 | `web/src/views/DocsFaq.tsx:136` | bare `268` | `268` | — | deliberate non-edit |
| 15 | `web/src/views/DocsFaq.tsx:190` | tool-reference tab label `({CATALOG.count})` | dynamic | `272` | correct |
| 16 | `web/src/views/DocsFaq.tsx:285` | empty-state "`{CATALOG.count}` are registered" | dynamic | `272` | correct |
| 16b | `web/src/views/DocsFaq.tsx:133-141` | method sentence: "parsing every `mt.Tool(…)` in `mcp/tools/*.py`" | described the pre-fix method | describes the wiring gate | **FIXED** (copy) |

**On 12–14:** these are the *only* bare stale-looking literals in `web/src/**`, and they are **sentences
about** the retired values — "`257`, `258` and `268` are retired counts and are not restated here."
Rewriting them would destroy the record of what was previously claimed and is explicitly out of bounds
(§4). They were classified individually by reading the surrounding four lines, not by bare-number grep —
a loose regex reports these three as a failure.

### 2.4 `web/src/views/AgentBuilder.tsx` — agent builder

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 17 | `web/src/views/AgentBuilder.tsx:53` | "`{CATALOG.count} tools across {domains.length} domains`" | dynamic | `272` / `29` | correct |
| 18 | `web/src/views/AgentBuilder.tsx:54` | "`({CATALOG.files_scanned} files)`" | dynamic | `45` | correct |

No version string, no hardcoded count. `domains` is derived per-render from `CATALOG.tools`
(`AgentBuilder.tsx:32`), so it cannot disagree with the rows.

### 2.5 `web/src/views/Sales.tsx` — sales surface

| # | file:line | Value | Current | Correct | Status |
|---|---|---|---|---|---|
| 19 | `web/src/views/Sales.tsx:81` | "`{CATALOG.count} tools`" | dynamic | `272` | correct |
| 20 | `web/src/views/Sales.tsx:84` | "`{DOMAINS} domains`" | derived from records (`Sales.tsx:12`) | `29` | correct |
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

**Five files, no new dependency** — `package-lock.json` is unchanged and not committed.

| File | Change |
|---|---|
| `web/scripts/extract-tools.py` | wiring gate: count only tools whose mixin is inherited by `Mem20MCPServer` or whose `install()` runs from `mcp/tools/__init__.py`; emit `unwired[]` |
| `web/src/data/tools.json` | regenerated: 270/27 → **272/29**, plus `unwired[]` (10) |
| `web/src/data/catalog.ts` | records authoritative over header; `MEM20_VERSION = '3.1.2'` |
| `web/src/App.tsx` | rail footer renders `mem20 v3.1.2 · 272 tools / 29 domains` |
| `web/src/views/DocsFaq.tsx` | FAQ method sentence now describes the wiring gate |

### 3.1 `web/scripts/extract-tools.py` — the wiring gate

```python
wired = wired_mixins(root)          # base classes of Mem20MCPServer
installed = installer_modules(root) # modules whose install() runs from tools/__init__.py
declared = mixin_classes(tree)
is_wired = (not declared) or bool(declared & wired) or p.stem in installed
```

A `mt.Tool(...)` declaration is not a tool. It becomes one only when the mixin that declares it is
inherited by `Mem20MCPServer` — that inheritance is what runs `register_*_tools()` and populates
`self.tools`. The gate also honours the RM-239 / RM-052 monkeypatch path, where a module attaches its
tool by wrapping an existing mixin's `register_*_tools` from `mcp/tools/__init__.py`.

If `Mem20MCPServer` cannot be parsed the script **exits 2** rather than emitting an unchecked catalog —
a silent fallback to "count everything" is exactly the bug being fixed.

Unwired declarations are excluded from `count` and written to `unwired[]`, so the gap is auditable
instead of invisible.

### 3.2 `web/src/data/catalog.ts` — records authoritative, one version source

```ts
count: recordCount || (rawCatalog.count ?? 0),
domain_count: recordDomainCount || (rawCatalog.domain_count ?? 0),
// ...
export const MEM20_VERSION = '3.1.2';
```

was `rawCatalog.count ?? tools.length` — header authoritative, records a fallback. The UI prints
`CATALOG.count` next to rows rendered from `CATALOG.tools`; if a regeneration writes a fresh header but a
truncated `tools[]`, the shell shows a total no row can be checked against. Inverted.

`MEM20_VERSION` is a constant because the shell ships as a static bundle and cannot open `VERSION` at
runtime. `web/package.json` is deliberately **not** the source (it carries the app's own `0.1.0`).

### 3.3 `web/src/App.tsx` — the version now has a consumer

The rail footer renders:

```
mem20 v3.1.2 · 272 tools / 29 domains
```

This closes the "exported but never rendered" gap from the first pass. Verified in the built bundle and
in a headless render (§5).

---

## 4. Deliberate non-edits (with reasons)

Rewriting these would falsify a record. The diff would look identical to a correct fix.

| file:line | Content | Why it stays |
|---|---|---|
| `web/src/views/DocsFaq.tsx:139-141` | "`257`, `258`, `268` and `270` are retired counts and are not restated here" | A sentence **about** the retired values. Rewriting it removes the evidence they were reconciled. |
| `docs/dashboard.html:687` | "Retired surface — 257 / 26" | The page's own stale→new ledger column. It describes what *was* said. |
| `docs/dashboard.html:679` | "The retired 257 / 26 figure" | Same — prose that names the retired figure. |
| `docs/dashboard.html:696` | "270 / 27, prior 257 / 26" | The "prior" is dated history. |
| `docs/app/deck/index.html:42,49,71,89,96` | "`VERSION` was 3.0.0" at pinned commit `45445f48` | Explicitly pinned historical note. **Outside my scope** — `docs/app/` is the Webpage Developer's G3 row. |
| `scripts/sweep-tool-counts.py` `SKIP_FILES` | `web/src/views/DocsFaq.tsx` excluded from the sweep | Correct: the sweep would have rewritten the retired-count sentence. |

**`v3.0.0` occurrences in scope: 0.** `grep -rn 'v3\.0\.0\|3\.0\.0' web/src/ docs/dashboard.html` returns
nothing.

---

## 5. Verification

All commands run in `/workspace/mem20` at `d99ab5d8` plus this branch's changes.

**Runtime truth (the number everything else is checked against):**

```
MEM20_EXPECTED_TOOLS=272 python ./verify_mcp.py
  TOOL_COUNT: 272
  LIE_TOOLS: 10
  RESULT: PASS
```

**Catalog equals runtime, name for name:**

```
python3 web/scripts/extract-tools.py --root . --out /tmp/t3.json
  45 files -> 272 tools across 29 domains
  WARNING: 10 tool(s) declared but NOT wired into Mem20MCPServer (excluded from count)

catalog tool-name set == tools/list tool-name set  ->  True
only-in-catalog: []      only-in-runtime: []
```

**Typecheck and build** (`web/`):

```
npm run typecheck  ->  exit 0, no diagnostics
npm run build      ->  44 modules transformed, built in 1.81s
                       dist/assets/index-CQaAsJUi.js   269.07 kB (gzip 82.36)
                       dist/assets/index-BMgU54DU.css   13.53 kB (gzip  3.46)
```

**Built-output assertions** against `dist/assets/index-CQaAsJUi.js`:

| Assertion | Result |
|---|---|
| `272` present | **YES** |
| `282` present | **no** |
| `3.1.2` present | **YES** |
| `/v?3\.0\.0/` present | **no** |

**Headless render** (Chromium, 1440×900, `dist/` served over HTTP):

```
RAIL_FOOT: door down | config | http://127.0.0.1:8221 | mem20 v3.1.2 · 272 tools / 29 domains
HAS_272: True   HAS_282: False
page errors: none (only ERR_CONNECTION_REFUSED from the :8221 door probe, expected — loopback-only)
```

The shell renders, the footer carries the verified figures, and no stale count appears anywhere.

---

## 6. What this audit does and does not establish

**Establishes:** the web catalog now counts exactly what the MCP server serves — 272 tools / 29 domains,
proven by set-equality against a live `tools/list` handshake. The 10-tool gap between source declarations
and the served surface is documented and surfaced in `unwired[]` rather than silently counted.

**Does not establish, and does not claim:**

1. **The 10 unwired tools are a backend bug I did not fix.** `EventStreamToolsMixin` and
   `LatticeToolsMixin` are missing from `mcp/server.py:108-118`. Adding them would make 282 real and
   require bumping `MEM20_EXPECTED_TOOLS` in `.github/workflows/mcp-verify.yml:47`. That changes the
   served MCP surface and belongs to the server owner — filed as a follow-up, not done here.
2. **The served bundle at `docs/app/assets/` still carries the old build.** `docs/app/` is a published
   build artefact, not a source tree. `.github/workflows/mem20-web.yml` regenerates and republishes it on
   push to `main`/`mem20frontendz`. This branch does not hand-edit `docs/app/index.html` — doing so is the
   failure mode where the entry point points at a bundle that was never pushed.
3. **`docs/index.html` is not mine.** Gap G3 also covers it. That is roster row 3, **Webpage Developer**.
4. **`web/package.json` `0.1.0` is intentional** and must not be "corrected" to the release version.
5. **Two hand-typed route counts remain.** `Sales.tsx:99` ("11 wire routes") and `Connection.tsx:161`
   ("26 routes") are both correct today; they should become `DOOR_ROUTES.length` /
   `CONTROL_ROUTES.length`. Refactor, not a count fix.

---

## 7. Recommendations

1. **Wire the two orphan mixins** into `mcp/server.py` and bump `MEM20_EXPECTED_TOOLS` to 282 — or delete
   the two modules if they are not meant to ship. Either way the 10-tool gap should not persist.
2. **Add a CI assertion** that the catalog's tool-name set equals a live `tools/list` set, so the wiring
   gate is enforced at build time rather than trusted at render time.
3. **Replace the two hand-typed route counts** with `DOOR_ROUTES.length` / `CONTROL_ROUTES.length` (§6.5).
4. **Have the generator derive `count`/`domain_count` from the array it writes**, in the same expression,
   so a truncation cannot produce a header that disagrees with its own payload.

