# #39 — Offline / degraded UX pass using the backend's status vocabulary

| | |
|---|---|
| **Issue** | [#39](https://github.com/bythewayz66-glitch/mem20/issues/39) — `enhancement`, `severity:medium` |
| **Surface** | `mem20controlz/mem20controlz/web/src/` (React UI) — every tab and view |
| **Source clause** | `docs/audit/mem20controlz-desktop-overhaul-plan.md` **C8** |
| **Depends on** | `README.md` §1 (shared vocabulary); `hooks.js` `useResource`; `status.js` |
| **Blocks** | #37 (the tray needs the same lifecycle model) — the state function is shared |
| **Blocked by** | Nothing. All states below are derivable from data the shell already receives, with one explicitly-flagged additive field (§5). |

## 1. What "done" means

There is no state of the product in which the user sees a spinner forever, or a
blank panel where a failure occurred. Every data-bearing region renders exactly
one of four things, and it says which:

1. the data,
2. **empty — verified** ("no records", and we know because the source answered),
3. **unavailable — with the reason** (and a retry),
4. **loading for the first time** (with text, and a bounded duration).

The distinction between (2) and (3) is the whole issue. "You have no dreams" and
"I could not read your dreams" are different sentences and must never collapse
into the same blank table.

The second half is honest staleness: when data is stale, it stays on screen
**marked stale with its age**, rather than being replaced by a spinner or by
nothing. Losing last-known data during a blip is a UX regression, not a safety
feature.

## 2. Current behaviour to preserve (do not rip out)

The tree already has good instincts here — the pass *extends* them, it does not
replace them:

- `useResource` keeps the last good `data` when a refresh fails and exposes
  `error`, `everLoaded`, `updatedAt`, `loading` (`hooks.js`). The comment is
  explicit: *"keeping the last good data when a refresh fails … never a blank
  UI"*.
- `App.jsx` already renders an `ErrorBanner` for `health.error` / `registry.error`
  and a `StatusPill` labelled `api unreachable` / `not checked`.
- `toneForStatus` never returns `ok` for an unrecognised status, and
  `statusLabel(null)` returns `not reported`.
- `HealthView` already refuses to paint a non-existent systemd unit red
  (*"A unit that does not exist is not a failed service … would invent an
  outage"*).

> **AC-39-00 (regression guard).** The pass must not regress any of the above.
> Specifically: a failed refresh must still keep `data`; an unrecognised status
> must still be toned `unknown`; a missing systemd unit must still not be red.
> **Verify:** re-run the existing behaviours before and after; the diff is
> additive only.

## 3. The lifecycle state function

Implement **one** pure function, `deriveLifecycleState({health, registry, auth, now})`,
returning exactly one of:

`starting | backend unreachable | signed out | degraded | ready`

Both the shell chrome (#37's tray) and the in-window banner consume it — one
model, two renderers, so the tray can never disagree with the window.

### 3.1 Evaluation order (first match wins)

| # | Condition | State |
|---|---|---|
| 1 | A protected route returned 401 (`isUnauthorized`) | `signed out` |
| 2 | `health.error` is a transport failure (`ApiError` network/`timedOut`) | `backend unreachable` |
| 3 | `health.data == null && health.error == null` (request in flight, none failed yet) | `starting` |
| 4 | `health.data` present but registry `error`, or `registry.data.stale`, or `registry.data.sweeping` | `degraded` |
| 5 | `health.data` present and registry usable | `ready` |

- **AC-39-01.** `signed out` outranks everything: a lapsed session is a login
  problem, not an outage, and must render `LoginGate` — never a red "backend
  unreachable". (401 ≠ 503. `App.jsx`'s existing `locked` path is the right
  destination.)
  *Verify:* expire the cookie → login gate; a `StatusPill` reading `unreachable`
  at the same moment is a fail.

- **AC-39-02.** `starting` is a **bounded** state, not an indefinite spinner. The
  shell may hold `starting` while no request has failed and no response has
  arrived, up to **30 s** (the 20 s `REQUEST_TIMEOUT_MS` plus one 10 s `POLL_MS`
  tick). After that it must swap to an explicit "still connecting — the control
  plane has not answered in 30 s" panel with a **retry** button, and it must still
  **not** claim `backend unreachable` — no request has actually failed, and
  asserting a failure we have not observed is the same lie in the other
  direction.
  *Verify:* point the app at a black-hole address that never answers; at 30 s the
  honest "still connecting" copy appears with retry, and the state is not
  `unreachable`.

- **AC-39-03.** The transition into `backend unreachable` requires an **observed
  failure** (network error or timeout), never elapsed time alone.
  *Verify:* kill the API; the state flips on the first failed request, not on a
  timer.

- **AC-39-04.** State is derived, never stored twice. A reviewer can find exactly
  one call site per renderer, and no component keeps its own `isOffline` flag.
  *Verify:* grep for boolean offline flags — none outside the function.

## 4. "Never blank" — the four-state data contract

Wrap every data region in one shared primitive, e.g. `<DataRegion>`, which
**requires** all four branches and fails a lint/test if one is omitted. A region
is any panel that shows registry panels, dreams, sites, DNS records, logs, pages,
or CLI coverage.

- **AC-39-05.** Every data region renders exactly one of `data` /
  `empty (verified)` / `unavailable (with reason)` / `first-load (with text)`.
  There is no fifth rendering, and no region may render nothing.
  *Verify:* the matrix in §8 — all 14 surfaces × 5 failure modes. Zero cells
  blank, zero cells showing a spinner with no accompanying text.

- **AC-39-06.** `empty (verified)` requires positive evidence: a successful
  response whose collection is empty. It may only be shown when
  `everLoaded && !error`. Copy names the collection and its scope, e.g.
  "No dream lineages in the store — checked just now".
  *Verify:* with an empty but reachable store, the region says empty/verified; the
  word "unavailable" does not appear.

- **AC-39-07.** `unavailable` always carries (a) what failed, (b) the backend's or
  client's own reason string, (c) a retry affordance. It never says merely "an
  error occurred".
  *Verify:* each unavailable region's reason traces to a `status_reason`, an
  `ApiError.message`, or the `sweeping` state — attributable, not invented.

- **AC-39-08.** A first load shows a text label ("reading registry…"), not a
  contentless spinner, and is replaced within 30 s by data or by an explicit
  state (AC-39-02). A bare spinner is a fail.
  *Verify:* throttle the network; the label is present at every moment of the
  first load.

## 5. The three named states the issue asks for

### 5.1 `starting` — the backend is coming up

Backend signal already available: **`sweeping: true`** on the cold-start
concurrent-sweep path, which returns `panels: []`, `total: 0`, `stale: true`
(`app.py::_registry_cached`).

- **AC-39-09.** When the registry reports `sweeping: true`, the UI shows a
  "starting — first fleet sweep in progress" state and **must not** render
  `total: 0` as "0 subsystems discovered" or as a healthy empty fleet (§1.1
  AC-V1; `0/0` ok is the most dangerous possible reading).
  *Verify:* cold start; for the duration of the sweep the copy is `starting`, and
  the Subsystems tab shows no "0 panels" claim.

- **AC-39-10.** Leaving `starting` does not require a manual refresh: the next
  poll (10 s) resolves it, and the state clears without a reload.
  *Verify:* cold start → resolves in ≤ 2 poll ticks with no interaction.

### 5.2 `backend unreachable` — the sidecar is gone

- **AC-39-11.** Killing the sidecar produces an explicit, page-level
  "backend unreachable" state — the issue's headline criterion — with the reason
  (`Request timed out after 20s` or the network error) and a **Retry** button.
  It is not a blank panel, not a bare spinner, and not 5 stacked red banners.
  *Verify:* kill the sidecar with the Overview tab open → one coherent page-level
  state; per-region errors are suppressed in favour of it.

- **AC-39-12.** Each of the 5 tabs and 9 sub-views, **when open at the moment of
  failure**, renders that state. No surface is exempt.
  *Verify:* §8 matrix rows.

- **AC-39-13.** Recovery is automatic: when the sidecar returns, the UI resumes
  on the next poll without a reload and without the user re-navigating. The stale
  banner clears only after a *successful* fetch.
  *Verify:* kill → restart; content returns, banner clears, and a late-failing
  retry does not clear it prematurely.

- **AC-39-14.** Retries **back off** and never stampede: 1 s, 2 s, 4 s, 8 s, capped
  at 30 s, reset on success. A dead backend must not be re-swept every poll —
  a full sweep spawns ~30 subprocesses.
  *Verify:* kill the API and count requests over 60 s; cadence widens and settles
  at ≤ 2 attempts/min.

### 5.3 `store missing` — and the honest limit of this criterion

Two distinct situations, and they must not be merged:

**(a) Already expressible — implement fully.**

- **AC-39-15.** Where the backend distinguishes *absent* from *inactive*
  (`websites.py`: `"active" = bool(result.get("exists")) and active_state ==
  "active"`, and units are *named* missing rather than inferred from a dead
  status), the UI shows a distinct **"not present on this host"** state. It is
  neither an outage (red) nor a healthy state (green): the `unknown` tone with the
  backend's own reason.
  *Verify:* query a site/unit that does not exist; copy reads "not present", tone
  is `unknown`, and no outage language appears.

- **AC-39-16.** A registry that returns `total: 0` while **not** sweeping is a
  *discovery* failure, not a healthy empty fleet. Render "no subsystems
  discovered — discovery source returned nothing" with the `contract.discovery`
  text the registry already sends, and never an `ok` aggregate.
  *Verify:* stub `/api/registry` to `{panels: [], total: 0, counts: {}}` without
  `sweeping`; the shell shows the discovery-failure state, not `ready`.

**(b) Requires one additive backend field — flagged, not assumed.**

The dream store has **no** top-level absent/empty discriminator in
`/api/registry` today (see `README.md` §1.4). So:

- **AC-39-17.** If a dream-store availability field is added (recommended:
  surface the store root and an `available` boolean alongside the existing
  `dreams.py` promotion-store logic), the UI renders `store missing` distinctly.
  **If it is not added**, the dreams region must fall back to `unavailable` with
  a reason — it must **not** invent an empty-verified state.
  *Verify:* point the dream store at a nonexistent path. With the field: distinct
  "dream store missing" state. Without: `unavailable` + reason. Under no
  configuration does the UI say "no dreams" when it could not read the store.

> **Why this is written as a conditional:** a criterion demanding a field that
> does not exist can never pass, and a reviewer would be forced to waive the
> whole document. Splitting it keeps every AC testable today and leaves the
> improvement explicit and reviewable.

## 6. Honest staleness

- **AC-39-18.** When data is stale, it stays visible and is **marked stale with a
  human age**, using the backend's `stale` and `age_s` (§1.2). Age is rendered in
  seconds under a minute, minutes under an hour, and includes the word "ago".
  *Verify:* with `stale: true, age_s: 132`, the marker reads "2m 12s ago", not
  "now" and not a spinner replacing the table.

- **AC-39-19.** Stale marking is never colour-only: it carries text (e.g.
  "stale"), and the table remains readable. A stale reading is visibly *less*
  trustworthy than a fresh one without hiding the data.
  *Verify:* greyscale screenshot; the stale marker is still legible.

- **AC-39-20.** `age_s` is always the probe age, never the request clock (the two
  differ by the cache age) — the same invariant as #37 AC-37-04.
  *Verify:* one cached response; shown age equals `age_s`, while the nav clock
  shows a later time.

- **AC-39-21.** A locally-failed poll (backend gone, so no `age_s` arrives) still
  yields a truthful age: the UI reports "last successful reading at HH:MM:SS
  (Ns ago)" from `useResource().updatedAt`, and this local age is presented as
  *local* — it must not be dressed up as a backend `age_s`.
  *Verify:* kill the API after a success; the age keeps counting up and the label
  states it is the last received reading.

## 7. Copy, tone and accessibility

- **AC-39-22.** Status copy is sourced, never authored — `status_reason` or
  `TONE_DESCRIPTIONS` verbatim (§1.5 AC-V3). No state may assert a cause:
  "stopped responding" yes, "crashed"/"out of memory" no.
  *Verify:* every rendered reason maps back to a source string.

- **AC-39-23.** State changes are announced, not just painted:
  `aria-live="polite"` on the lifecycle banner (assertive only for
  `backend unreachable`), and each region's state change updates an accessible
  name. A sighted-only cue is insufficient.
  *Verify:* screen-reader run (VoiceOver/NVDA) through the §8 matrix announces
  each transition exactly once.

- **AC-39-24.** Every state is distinguishable with no colour perception and with
  no motion: shape/icon + text, and `prefers-reduced-motion: reduce` removes any
  pulse/spinner animation while keeping the label.
  *Verify:* reduced-motion enabled; states remain fully legible, no animation.

- **AC-39-25.** No state may be dismissed into blankness: dismissing a banner
  leaves the region's state intact (dismiss hides the banner, not the truth).
  *Verify:* dismiss a degraded banner; the pill/region still reports the state.

## 8. Reviewer's matrix — 14 surfaces × 5 modes

Surfaces: `overview`, `subsystems`, `cli`, `websites/{sites,dns,health,logs,pages}`,
`dreams/{review,new,runs,hollow}`, plus the two dynamic detail views
(`DreamDetailView`, and any site detail). Modes: **S** starting · **U** unreachable
· **SM** store missing · **ST** stale data · **OK** healthy.

Every cell must render one of the four contract states (AC-39-05). Abbreviated:

| Mode | Injection | Required rendering (all surfaces) |
|---|---|---|
| **S** | cold start / `sweeping: true` | `starting` + text + no `0`-counts claim; no `ok` |
| **U** | kill sidecar | page-level `backend unreachable` + reason + retry; no blank cells |
| **SM** | missing store / `total: 0` non-sweeping | `not present` / `no subsystems discovered`, `unknown` tone, backend reason |
| **ST** | `stale: true, age_s ≥ 46` | data still visible + "stale · Ns ago"; no spinner substitution |
| **OK** | normal | data, no lifecycle banner, no stale marker |

- **AC-39-26.** The matrix is executed as an automated test (mock the two
  endpoints per mode; assert each surface's rendered state token) so it cannot
  silently rot.
  *Verify:* the test exists and fails if any cell regresses to blank.

## 9. Failure modes that are automatic fails

1. A blank panel or bare spinner in any mode — the issue's core defect.
2. "No records" shown when the source was never successfully read (empty and
   unavailable collapsed).
3. `total: 0` rendered as a healthy fleet.
4. `sweeping: true` rendered as an empty fleet rather than `starting`.
5. A 401 rendered as an outage.
6. Stale data replaced by a spinner or hidden instead of marked.
7. `age_s` replaced by the request clock.
8. Retry every poll with no backoff against a dead backend (~30 subprocesses per
   sweep).
9. Invented causes ("crashed") or invented empty states.
10. Colour-only state encoding.

## 10. Out of scope

- Offline **writes** / an outbound queue (queueing a promote while offline is a
  data-integrity question, not a UX pass).
- Service-worker/asset caching for a full offline mode — the shell is
  network-dependent by design until the sidecar bundles locally (#36).
- Retry *policy* for individual subsystem probes — that is the registry's
  `probe_timeouts` concern, already surfaced.
- Error **taxonomy** beyond distinguishing auth / transport / backend-reported.
