# #37 — System tray, fleet-health glyph and native notifications

| | |
|---|---|
| **Issue** | [#37](https://github.com/bythewayz66-glitch/mem20/issues/37) — `enhancement`, `severity:medium` |
| **Surface** | Tauri 2 shell (`mem20controlz/src-tauri/`) + React UI (`mem20controlz/mem20controlz/web/src/`) |
| **Source clause** | `docs/audit/mem20controlz-desktop-overhaul-plan.md` **C5** |
| **Depends on** | #35 (shell scaffold, landed), #39 (shares this vocabulary — see `README.md` §1) |
| **Blocked by** | Nothing. Testable in `cargo tauri dev` against an already-running backend; the bundled sidecar (#36) is a later wiring change, not an AC precondition. |
| **Precondition for every AC** | A reachable API base URL. In dev that is `http://127.0.0.1:8741` per `tauri.conf.json.build.devUrl`. |

## 1. What "done" means

The window is no longer the only place fleet health exists. Closing the window
leaves a tray icon whose glyph is a truthful aggregate of `/api/registry`, and a
subsystem that genuinely flips to `unreachable` (or `degraded`) raises **exactly
one** native notification — while a cached or stale reading raises **none and
never has**.

The failure this issue exists to prevent is specific and worth stating plainly:
a tray that alerts on cached data is worse than no tray, because it manufactures
outages out of its own polling cache. Every suppression rule below exists for
that.

## 2. Contract consumed (already shipped — do not extend)

`GET /api/registry` → `{ panels[], counts{}, total, cached, age_s, stale, probe_timeouts{}, contract{} }`

- `panels[i]` → `{ id, name, kind, status, status_reason, binary?, rest?, cli? }`
- `status ∈ {ok, degraded, unreachable, no-health, unknown}` (§1.1 of `README.md`)
- `sweeping: true` appears **only** on the cold-start concurrent-sweep path, with
  `panels: []`, `total: 0`, `stale: true` (`app.py::_registry_cached`).
- `GET /api/health` is the **only unauthenticated** route:
  `{status, service, version, uptime_s}` (`app.py::health`) — note `uptime_s`, not
  `uptime_seconds`. Its `status` is a **hardcoded literal `"ok"`**: it asserts only
  that this service answered, never that the fleet is healthy. Use it for
  pre-login liveness only.

**No backend change is required by this issue.** If an implementer finds
themselves adding a route, the aggregate is being computed in the wrong place.

> `counts` in a `/api/registry` payload is the **backend-ready bucket shape** and
> is not orderable against a glyph rank as values (e.g. `ok` may outnumber
> `no-health`). Match on `panels[].status`, which is both orderable and
> attributable. `counts` is for the Overview tab's summary numbers.

## 3. State model to implement

### 3.1 Aggregate glyph state — a pure function, unit-tested

Export `aggregateFleetHealth(payload)` and cover it with table-driven tests. It
returns exactly one of `starting | unreachable | degraded | unknown | no-health | ok`.

Evaluate in this order; **first match wins**:

| # | Condition | Returns | Rationale |
|---|---|---|---|
| 1 | `payload.sweeping === true` | `starting` | The backend is telling us a sweep is in flight and has no panels yet. This is the only honest "wait" signal available. |
| 2 | Any panel `status === "unreachable"` | `unreachable` | Worst actionable state. |
| 3 | Any panel `status === "degraded"` | `degraded` | Reachable but failing. |
| 4 | Any panel `status === "unknown"` | `unknown` | We could not confirm — never silently green. |
| 5 | Any panel `status === "no-health"` | `no-health` | A probe gap, *not* a fault; ranked last among non-ok so it never masquerades as an outage. |
| 6 | `total > 0` and every panel `ok` | `ok` | Verified fleet. |
| 7 | otherwise (`total === 0`, all statuses absent/unrecognised) | `unknown` | Never `ok` by absence (§1.1 AC-V1). |

- **AC-37-01.** The glyph resolves through `aggregateFleetHealth` and through no
  other path. A reviewer can grep for the function and see both the tray and the
  Overview badge consume it.
  *Verify:* with `counts = {ok: 3, "no-health": 7}`, glyph is `no-health`, not
  `ok`. With `counts = {ok: 3, unknown: 1}`, glyph is `unknown`. With
  `{panels: [], total: 0}` (no `sweeping`), glyph is `unknown`, not `ok`.

- **AC-37-02.** `starting` is transient and self-clearing: it must disappear on
  the first response where `sweeping` is absent, in the same 10 s poll tick.
  *Verify:* block the backend long enough to trigger a concurrent sweep; the glyph
  reads `starting`, then resolves to a normal state without a restart.

### 3.2 Freshness is part of the glyph, not a tooltip afterthought

| `stale` | `age_s` | Required presentation |
|---|---|---|
| `false` | any | Solid glyph in the status tone |
| `true` | `> 45` | **Stale overlay**: glyph visibly hollowed/reduced (not a colour change alone — see AC-37-12), tooltip leads with "last probed Ns ago" |

- **AC-37-03.** A stale reading is never presented as a live one. The staleness
  indicator is present in the tray state itself, not only inside a tooltip that a
  user must hover to see.
  *Verify:* pin `MEM20_CONTROL_REGISTRY_TTL` low (e.g. `5`) and stop the
  refresher; within ~45 s the glyph enters the stale presentation while
  `status` is unchanged.

- **AC-37-04.** The tooltip reports **`age_s`**, not the time of the last
  successful request. These differ by the cache age (§1.2 AC-V2).
  *Verify:* hover after one cached response; the "last probed" figure must equal
  `age_s`, which is strictly greater than 0, while the UI's own refresh clock
  shows a fresher timestamp.

## 4. Notifications

Only **two** statuses are notification-worthy: `unreachable` and `degraded`.
`no-health`, `unknown` and `ok` never notify (§1.3 AC-V3 — those two exist to
avoid a false accusation, and `no-health` in particular is a probe gap).

### 4.1 Confirmation — cached readings do not count as evidence

- **AC-37-05.** A notification fires only after **two consecutive fresh sweeps**
  (`cached === false`) report the same non-ok status for the same panel. A
  cached response never increments the confirmation counter.
  *Verify:* with TTL at default 45 s, force a panel to fail and watch: the first
  fresh sweep sets the counter to 1 and emits nothing; the cached sweeps in
  between change nothing; the second fresh sweep emits one notification. Under no
  polling cadence may a single fresh observation produce a notification.

- **AC-37-06.** `stale === true` suppresses emission entirely, for any status.
  *Verify:* freeze the refresher so every response is stale; flip a panel to
  `unreachable` in the underlying data; zero notifications arrive.

### 4.2 Dedupe — one notification per transition

- **AC-37-07.** The dedupe key is `(panel_id, status, transition_sequence)`.
  Repeated sweeps confirming an already-notified state emit **nothing**. A panel
  that recovers and later re-fails is a new transition and notifies again, once.
  *Verify:* hold a panel `unreachable` across ≥6 fresh sweeps → exactly 1
  notification. Restore it, then break it again → exactly 1 more, for a total of 2.

- **AC-37-08.** Distinct panels notified in the same sweep are coalesced into one
  notification naming the count and up to 3 ids, not N separate toasts.
  *Verify:* break 5 panels in one sweep → 1 notification, body lists 3 ids and
  indicates 5 total.

- **AC-37-09.** Every suppression is counted, with a reason from
  `{unchanged, cached, stale, authenticated_out, muted}` (`README.md` §3).
  *Verify:* the counters account for every observation — `emitted + suppressed`
  equals the number of qualifying observations. No observation is silently
  dropped.

### 4.3 Copy

- **AC-37-10.** Notification text is derived from the panel's own
  `status_reason`, verbatim where it fits (e.g. `REST http://127.0.0.1:8799/health
  not reachable`). It may prefix context (`mem20 · <panel name>`) but must not
  assert a cause the backend did not state — no "crashed", "OOM", "restarting".
  *Verify:* compare body to `status_reason` for a real failing panel; the
  reason string appears intact.

### 4.4 Control

- **AC-37-11.** Notifications can be muted from the tray without disabling the
  glyph, and the mute persists across restarts. A muting action is itself
  visible (tray menu checkmark reflects state on relaunch).
  *Verify:* mute → relaunch → menu still checked, glyph still updates, zero
  notifications over a forced failure.

## 5. Presence, auth and platform behaviour

- **AC-37-12.** The glyph conveys state by **shape and accessible name**, not hue
  alone: each of the six aggregate states has a distinct accessible name
  (`"Fleet: unreachable"`, `"Fleet: degraded"`, …). A user with no colour
  perception can still read the fleet state.
  *Verify:* an accessibility inspection of the tray item exposes the name; a
  greyscale screenshot of all six states remains discriminable.

- **AC-37-13.** Polling survives window close. Closing the window hides it; the
  tray keeps polling; reopening restores the last state within one tick.
  *Verify:* close window, break a subsystem, observe the notification arrives with
  the window hidden.

- **AC-37-14.** A 401 is not an outage. If the session lapses while the window is
  hidden, the tray must not render `unreachable` and must not notify; it records
  `authenticated_out` and shows a neutral "signed out" tray state.
  *Verify:* expire the session cookie, wait two sweeps → zero notifications, tray
  state neutral, `notifications_suppressed{authenticated_out}` increments.

- **AC-37-15.** Pre-login, the tray polls only `/api/health` (the single
  unauthenticated route) and reports liveness — never a fleet claim it has not
  verified.
  *Verify:* start signed out; tray shows a liveness-only state; `/api/registry`
  is not called (no 401s in the network log).

- **AC-37-16.** Quit is explicit and unambiguous: the tray menu has a Quit item
  that terminates the shell and, once #36 lands, its sidecar. It must not orphan
  a child process.
  *Verify:* Quit, then check for a live sidecar pid — none remains.

## 6. Reviewer's test matrix

| # | Scenario | Injection | Expected |
|---|---|---|---|
| T1 | Healthy fleet | normal startup | glyph `ok`, solid, zero notifications |
| T2 | One panel unreachable | stop a probed service | 1 notification after 2nd fresh sweep |
| T3 | Same panel still down | wait 6 sweeps | **0 further notifications** |
| T4 | Cached-only readings | freeze refresher | 0 notifications; glyph enters stale overlay |
| T5 | Cold start | kill+restart backend | glyph `starting` → resolves; no false `unreachable` |
| T6 | Probe gap | a binary with no `health` verb | glyph `no-health`; **no notification** |
| T7 | Unconfirmable panel | force a probe exception | glyph `unknown`; **no notification** |
| T8 | Session lapses | expire cookie | tray neutral; 0 notifications |
| T9 | 5 panels fail together | mass stop | 1 coalesced notification |
| T10 | Recovery then re-failure | restore, then break | 2 notifications total, not 3+ |

## 7. Failure modes that are automatic fails

1. Notifying from a **cached** response (the exact false-alarm the issue names).
2. Notifying for `no-health` or `unknown` — a probe gap reported as an outage.
3. Glyph green when `total === 0` or `status` is absent.
4. Glyph or tooltip showing request time where probe age belongs.
5. Notification asserting a root cause ("crashed") the backend never stated.
6. Colour-only state encoding.
7. A 401 surfacing as an outage or a notification.

## 8. Out of scope

- Packaging, signing, auto-update (**#40 / C7**), sidecar spawn and port handshake
  (**#36**) — the tray must be testable without them (§ "Precondition").
- Tray-side **remediation** (restart a subsystem from the tray). Attractive, and
  deliberately deferred: it turns an observability surface into a control surface
  with its own auth question, and this issue is scoped to presence.

## 9. Open questions for the implementer (decide, don't block)

1. **Recovery notifications** — allowed, off by default. If enabled, obey
   AC-37-07's dedupe exactly. Default off because a recovery toast trains users to
   ignore the channel.
2. **Per-panel mute granularity** — global mute is required (AC-37-11); per-panel
   is a reasonable stretch.
3. **Re-confirmation window after a mute ends** — recommend requiring two fresh
   sweeps again, so unmuting cannot replay a stale backlog.
