# #38 — Command palette (Cmd-K) across panels, CLI audit and dream lineages

| | |
|---|---|
| **Issue** | [#38](https://github.com/bythewayz66-glitch/mem20/issues/38) — `enhancement`, `severity:medium` |
| **Surface** | `mem20controlz/mem20controlz/web/src/` (React UI) |
| **Source clause** | `docs/audit/mem20controlz-desktop-overhaul-plan.md` **C6** |
| **Depends on** | `status.js` vocabulary (`README.md` §1); the existing `NAV`, registry and dreams endpoints |
| **Blocked by** | Nothing — "no backend change required beyond what already exists" (issue text). Every AC below is client-side. |

## 1. What "done" means

From anywhere in the console, one keystroke opens a search field. Typing filters
across **every navigable surface and every legal action**, ranked predictably.
Selecting an entry either navigates or executes — and for anything that costs
money, writes to disk, or changes fleet state, "executes" means **opens the
existing confirmation affordance, never fires blind**.

The registry is the interesting case: it grows with the estate (100+ subsystems is
the stated demo scale), so the palette must stay correct as panels appear and
disappear without anyone editing palette code.

## 2. The surface inventory the palette must cover

This is the real, current inventory — the palette is only complete if all of it
is reachable. Source of truth in parentheses; adding a tab later must not require
touching the palette (§4 AC-38-06).

**Top-level tabs (5)** — `NAV` in `App.jsx`:
`overview` · `subsystems` · `cli` (CLI coverage) · `websites` · `dreams`

**Sub-views (9)** — `SUBTABS` in `tabs/Websites.jsx` and `tabs/Dreams.jsx`:
`websites/sites` · `websites/dns` · `websites/health` · `websites/logs` ·
`websites/pages` · `dreams/review` · `dreams/new` · `dreams/runs` · `dreams/hollow`

**Registry panels (dynamic, 100+)** — `/api/registry` `panels[]`; each needs an
entry, searchable by `name`, `id`, `binary`, `description`.

**Dream lineages (dynamic)** — `/api/dreams` list; each opens
`Dreams → Review → DreamDetailView`.

**Actions (5)** — the set that is safe to express as one-shot commands:

| Action | Effect | Guard required |
|---|---|---|
| Refresh registry | re-poll `/api/registry` | none |
| Run CLI audit | `GET /api/cli/coverage` (spawns `--help` per CLI; TTL 600 s) | explicit, shows pending |
| Start a dream run | `POST /api/dreams/runs` | **confirmation** — runs cost money |
| Promote a dream | `POST /api/dreams/{id}/promote` | **confirmation** — writes to disk |
| Sign out | `POST /api/auth/logout` | confirmation |

## 3. Trigger and keyboard contract

- **AC-38-01.** `⌘K` on macOS and `Ctrl+K` on Windows/Linux opens the palette from
  any tab, any sub-view, whether or not focus is in a text field. Pressing the
  same combo again closes it (toggle, not stack).
  *Verify:* open from the DNS form with the name field focused — palette opens
  once and the field keeps its value on close.

- **AC-38-02.** Bare letters are **never** global shortcuts. No printable
  keystroke outside the palette may navigate or execute; only modified combos
  (⌘/Ctrl+K) are bound.
  *Verify:* press `d`, `s`, `r` on the Overview with no input focused → nothing
  happens.

- **AC-38-03.** Full keyboard operation inside the palette: `↑`/`↓` move the
  highlight, `Enter` activates, `Tab` cycles the scope chips, `Esc` closes, and
  `⌘/Ctrl+Enter` activates the highlighted entry in a "background" sense where
  applicable (see AC-38-13). The active option is exposed via
  `aria-activedescendant` so a screen reader announces it.
  *Verify:* complete every AC below using the keyboard only, never the mouse.

- **AC-38-04.** Focus is trapped in the palette while open, `role="dialog"` +
  `aria-modal="true"` + a labelled search input, and focus **returns to the
  previously focused element** on close. `Esc` with an open confirmation dialog
  closes the confirmation first, then the palette — not both at once.
  *Verify:* open from a DNS field, `Esc` twice; focus lands back in the DNS field.

- **AC-38-05.** The palette never runs an action on close, on `Esc`, on unmount,
  or on a keystroke that merely highlights. Execution requires an explicit
  `Enter`/click on an entry.

## 4. Entry construction — one source of truth

- **AC-38-06.** Entries are **derived at runtime** from `NAV`, each module's
  `SUBTABS`, `registry.panels` and the dreams list. A newly added tab, sub-view or
  registry panel appears in the palette with no palette-source edit.
  *Verify:* add a dummy entry to `NAV.items` and rebuild — it is searchable
  immediately. A reviewer may instead assert the derivation directly (single
  `buildPaletteEntries({nav, subtabs, panels, dreams})` used by one call site).

- **AC-38-07.** Each entry carries a **kind** — `tab | view | subsystem | dream |
  action` — rendered as a distinct affordance, so a user knows before pressing
  `Enter` whether the entry moves them or does something. The kind is also what
  `palette_select{kind}` is dimensioned by (`README.md` §3).
  *Verify:* an action entry is visually and semantically distinguishable from a
  navigation entry without reading the label.

- **AC-38-08.** Every entry's *destination* is asserted navigable before it is
  shown. No entry may exist for a surface that cannot be reached — a result that
  does nothing on `Enter` is a bug, not a gap.
  *Verify:* programmatically activate **every** entry produced by an empty query
  against a live backend; zero entries leave the UI on the same screen except
  actions, which must produce a visible effect.

- **AC-38-09.** Subsystem entries carry their live status pill
  (`StatusPill` + `toneForStatus`), so the palette doubles as a status browser —
  this is the primary defence against §1.1 AC-V1 being violated in a new surface.
  A panel with `status` absent or unrecognised renders `unknown`, never `ok`.
  *Verify:* a `no-health` panel shows the `no-health` tone in the palette, not a
  green dot.

## 5. Matching and ranking — specified, not left to taste

Fuzzy matching is where palettes quietly become unreliable, so the rule is stated
so two implementers produce the same order.

- **AC-38-10.** A candidate matches when the query is a **case-insensitive
  subsequence** of any of: label, id, binary, description/hint, or alias. Ranking
  is tiered, and the tiers are ordered:
  1. exact label match
  2. label **prefix** match
  3. match starting at a **word boundary** (`dns` matches `Websites · DNS`)
  4. contiguous substring anywhere
  5. scattered subsequence
  Ties break by shorter label, then alphabetically by label, then by kind order
  (`action < tab < view < subsystem < dream` — actions are what power users come
  for).
  *Verify:* with the query `dns`, `websites/dns` and `DnsView` outrank any
  subsystem whose description merely contains `d`,`n`,`s` scattered. With `ov`,
  `Overview` is first.

- **AC-38-11.** Results are capped at **50** rendered rows, with an explicit
  "showing 50 of N — refine your query" line when capped. Scrolling never loads
  more silently.
  *Verify:* query `e` against 100+ panels → exactly 50 rows plus the count line.

- **AC-38-12.** A scope prefix switches the search domain and is discoverable from
  the UI (a hint line, or chips via `Tab`): `>` for actions only, `@` for
  subsystems only, `#` for dreams only, `/` for views only. Scopes compose with
  free text (`@mcp`, `#hollow`).
  *Verify:* `>` lists only actions; `@` lists only registry panels.

- **AC-38-13.** Status filtering is available as a token, because "jump me to what
  is broken" is the highest-value query in an ops console: `status:unreachable`
  (and the other four statuses) filters subsystem entries by their live status.
  *Verify:* `status:unreachable` returns exactly the panels whose `status` is
  `unreachable`, and nothing else.

## 6. Execution semantics

- **AC-38-14.** Navigation entries perform a **single state transition** to the
  target and close the palette. A view entry lands on the correct tab *and*
  sub-tab (e.g. `websites/logs` activates the Websites tab with `logs` selected),
  matching what a mouse click on that tab does — no divergent code path.
  *Verify:* compare state after palette-navigating to `websites/logs` vs clicking
  Logs; identical, including the tab bar's `aria-selected`.

- **AC-38-15.** Dream entries open the specific lineage: `Dreams → Review →
  DreamDetailView(<id>)`. The palette must not fetch the artifact inline — the
  dream list deliberately never carries artifacts (hundreds of KB per lineage;
  see `dreams.py` module docstring); the detail view fetches exactly one.
  *Verify:* network log shows a single `/api/dreams/{id}` on open, and no artifact
  payload on the palette's own requests.

- **AC-38-16.** Costly or destructive actions require confirmation **before** the
  request is sent: a dream run (spends money), a promote (writes a pack to disk),
  sign-out. The confirmation states what will happen and, for a run, that it
  costs money. Cancelling sends no request at all.
  *Verify:* activate "Start a dream run", cancel → zero `POST /api/dreams/runs`
  in the network log. Confirm → exactly one.

- **AC-38-17.** The CLI audit action is explicit about being slow and is never
  auto-fired: it navigates to CLI coverage and issues the audit request, showing a
  pending state, and it must not re-fire on a warm cache (TTL 600 s) in a way that
  claims a fresh audit. If the response is `cached: true`, the UI says so and
  shows `age_s`.
  *Verify:* trigger twice inside the TTL → the second is served cached
  (`cached: true`) and the UI reports the cache age rather than implying a new
  audit ran.

- **AC-38-18.** Every action surfaces its failure in the palette or its host view
  via the existing `ErrorBanner`/`useAction` error path; a failed action never
  closes silently as if it succeeded. A 401 routes to `LoginGate`
  (`isUnauthorized`), not to a generic error.
  *Verify:* force `POST /api/dreams/{id}/promote` to 500 → error visible and
  attributable; expire the session then sign out → login gate.

## 7. Performance and polling discipline

- **AC-38-19.** Opening the palette issues **zero** network requests. It consumes
  data already on screen (`useResource` state); it never triggers a sweep. A full
  registry sweep is ~30 subprocesses and must not be caused by a keystroke.
  *Verify:* network log clean across 20 open/close cycles and 200 keystrokes.

- **AC-38-20.** Filtering is synchronous against an in-memory index: keystroke →
  updated list is under 16 ms with 150 entries, measured on the dev machine.
  *Verify:* instrument `performance.now()` around the filter over 150 synthetic
  entries; p95 < 16 ms.

- **AC-38-21.** Open latency is under 100 ms with 100+ panels on warm data (the
  index may be built once and memoised on `panels` identity, not rebuilt per
  keystroke).
  *Verify:* p95 open-to-visible < 100 ms across 20 opens.

## 8. Degraded behaviour (the palette must not be the one silent surface)

- **AC-38-22.** If the registry is unavailable or errored, the palette still opens
  and still offers tabs, views and actions, with an explicit line stating that
  subsystems cannot be searched right now. It must not render an empty,
  unexplained list — that would be the exact blank-panel failure #39 exists to
  kill.
  *Verify:* kill the backend, press ⌘K → palette opens, tabs and actions present,
  subsystems section says unavailable with the error's own message.

- **AC-38-23.** While `sweeping: true` / a cold start is in progress, subsystem
  results are labelled as not-yet-probed (e.g. `status: starting`) rather than
  omitted or shown as `ok`.
  *Verify:* press ⌘K during cold start; subsystem rows carry the starting
  treatment.

- **AC-38-24.** An empty result set is stated, not implied: "No matches for
  `<query>`" with the active scope named, and no fallback navigation. `Enter` on
  an empty list does nothing.
  *Verify:* query `zzzzz`, press `Enter` → palette stays open, message shown,
  focus unchanged.

## 9. Reviewer's test matrix

| # | Scenario | Expected |
|---|---|---|
| T1 | ⌘K / Ctrl+K from each of the 5 tabs | opens consistently, focus in input |
| T2 | Query a subsystem name | that panel ranks first, with its live status pill |
| T3 | Query `dns` | DNS view ranks above scattered subsequence hits |
| T4 | `status:unreachable` | exactly the unreachable panels |
| T5 | Activate `websites/logs` | Websites tab + Logs sub-tab, identical to clicking |
| T6 | Activate a dream lineage | Review sub-tab, detail for that id, 1 detail request |
| T7 | "Start a dream run" + cancel | no POST |
| T8 | "Start a dream run" + confirm | exactly 1 POST |
| T9 | Backend down, ⌘K | opens; tabs/actions work; subsystems explicitly unavailable |
| T10 | Cold start, ⌘K | subsystem rows labelled starting |
| T11 | 200 keystrokes | 0 network requests |
| T12 | `zzzzz` + Enter | "No matches", no navigation |
| T13 | Esc twice from a form | focus restored to the form field |
| T14 | Every empty-query entry activated | all navigate or have a visible effect |

## 10. Failure modes that are automatic fails

1. Any action executing without explicit activation (close/Esc/highlight firing
   it) — especially a paid dream run.
2. Firing `/api/registry` or the CLI audit per keystroke or on open.
3. A result that navigates nowhere (dead entry).
4. Palette hard-coded to today's tabs, requiring edits when a tab is added.
5. Green/`ok` treatment for a non-`ok` or absent status (§1.1 AC-V1).
6. Silent empty list on backend failure — the #39 failure reproducing inside #38.
7. Divergent navigation semantics from the mouse path (two ways to reach a view
   that disagree).
8. Keyboard trap: focus lost to `body` on close, or Tab escaping the dialog.

## 11. Out of scope

- Fuzzy **frecency** ranking (learned ordering) — a reasonable v2; v1 must be
  deterministic and testable (AC-38-10) so regressions are visible.
- Natural-language command execution ("restart the forge") — needs the auth and
  blast-radius design that #37 §8 defers.
- Global (OS-level) hotkey — the palette is an in-window affordance.
- Server-side search — the index is small (150 entries), so client-side is
  correct and keeps AC-38-19 trivially true.
