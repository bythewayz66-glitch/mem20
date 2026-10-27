# mem20controlz — UX acceptance specs

**Written:** 2026-10-26 · **Surface:** `mem20controlz/` @ `main` · **Owner:** UX research
**All paths below are repository-root-relative** (this file lives at `docs/ux/`).
**Scope:** the four UX-shaped issues in the 8-issue backlog — #37, #38, #39, #40.

Each document below is written to be **implementable** (every criterion names a
concrete surface, trigger, timeout or string an engineer can build against) and
**verifiable** (every criterion names an observation a reviewer can make, and how
to make it fail). Criteria use only vocabulary and endpoints that already exist
in the tree — no new backend contract is introduced here.

| Issue | Title | Label | Spec |
|---|---|---|---|
| #37 | System tray, fleet-health glyph and native notifications | `enhancement`, `severity:medium` | [issue-37-tray-and-notifications.md](./issue-37-tray-and-notifications.md) |
| #38 | Command palette (Cmd-K) across panels, CLI audit and dream | `enhancement`, `severity:medium` | [issue-38-command-palette.md](./issue-38-command-palette.md) |
| #39 | Offline / degraded UX pass using the backend's status vocab | `enhancement`, `severity:medium` | [issue-39-offline-degraded-ux.md](./issue-39-offline-degraded-ux.md) |
| #40 | Desktop install, code-signing, auto-update — first run, the update prompt, and every failure state | `enhancement`, `severity:medium` | [issue-40-install-update-ux.md](./issue-40-install-update-ux.md) |

Source of all four: [`docs/audit/mem20controlz-desktop-overhaul-plan.md`](../audit/mem20controlz-desktop-overhaul-plan.md)
clauses **C5** (#37), **C6** (#38), **C8** (#39), **C7** (#40).

---

## 1. The shared contract — status vocabulary

All three issues are the same problem wearing three hats: **the desktop shell has
to render what the backend already knows.** So the vocabulary is defined once
here and cited, not restated, by each spec. Everything below is read from the
working tree, not proposed.

### 1.1 The five subsystem statuses

Emitted by `registry.registry()` in `mem20controlz/mem20controlz/registry.py` and
mirrored in `mem20controlz/mem20controlz/web/src/status.js`.

| Status | Meaning (verbatim intent from source) | Where the backend sets it |
|---|---|---|
| `ok` | A verified surface answered. | REST probe reachable with status < 500, **or** CLI `--json health` exit 0 |
| `degraded` | Reachable but failing / not verified against the contract. | CLI exposes a `health` verb but health exits non-zero; or health failed with no verified surface |
| `unreachable` | The probe could not reach the surface at all. | REST probe unreachable **and** CLI probe timed out (`"timed_out": true`) |
| `no-health` | The CLI runs but exposes no health verb — a probe gap, not a fault. | CLI runs, no `health` in its verb list |
| `unknown` | No verified surface — the API could not confirm anything. | Probe raised an error, or no probe surface at all |

`status.js` states the invariant that matters to every acceptance criterion below:

> Nothing is ever mapped to the "ok" tone unless the API literally reported the ok status.

The corollary is the hard rule for the desktop shell:

> **AC-V1.** No shell surface may render a positive/healthy affordance for a
> status other than the literal string `ok`. Absent, `null` and unrecognised
> statuses fall through to `unknown` — never to `ok`.
> **Verify:** feed the glyph/copy/notifier a panel whose `status` is `undefined`,
> `null`, `""` and `"OK"` (wrong case). All four must render the `unknown`
> treatment. Any one rendering the `ok` treatment is a fail.

### 1.2 The freshness triple

Every `/api/registry` response carries `cached`, `age_s` and `stale`
(`app.py::_registry_cached`). These are not decoration — they are the difference
between an operations tool and a liar.

| Field | Type | Semantics |
|---|---|---|
| `cached` | bool | True when served from the sweep cache |
| `age_s` | float | Seconds since the payload was actually probed (`0.0` on a fresh sweep) |
| `stale` | bool | `age_s > REGISTRY_TTL_S`, default TTL **45 s** (`MEM20_CONTROL_REGISTRY_TTL`) |
| `sweeping` | bool | **Only present on the cold-start path** (`_registry_cached` concurrent-sweep branch), where `panels: []`, `total: 0`, `stale: true` |

> **AC-V2.** `age_s` is the age of the *evidence*, not of the *poll*. A shell that
> shows the time it last called `/api/registry` is showing the wrong number —
> `useResource().updatedAt` is the request clock, `age_s` is the probe clock, and
> the two diverge by exactly the cache age.
> **Verify:** warm the cache, wait 20 s, poll. `age_s` must read ≈20 higher than
> the previous response while the request clock advances by 10 s (one poll of
> `POLL_MS = 10000`).

### 1.3 Lifecycle states the shell adds (not backend statuses)

The shell has three facts the registry cannot express, because they are facts
about *the shell*, not about a subsystem. They are additive and must never be
confused with the five above:

| Shell state | Trigger | Must never be rendered as |
|---|---|---|
| `starting` | Sidecar spawned, first `/api/health` not yet answered | A spinner with no text; a blank panel |
| `backend unreachable` | `/api/health` request failed (`ApiError`, incl. `timedOut`) | A blank panel; `unreachable` on *every* subsystem |
| `store missing` | The backend reports the store absent (see 1.4) | An empty-but-valid list ("you have no dreams") |

### 1.4 Honesty note on `store missing` — read before writing tests

The `dreams` and `websites` modules distinguish *absent* from *empty* (e.g.
`websites.py` sets `result["active"] = bool(result.get("exists")) and …`, and
names a unit missing rather than inferring it from a dead status). But there is
**no single top-level "store is missing" field** in `/api/registry` today.

So AC-39 splits in two, and the split is deliberate:

- **`store missing` is in scope** wherever the backend already discriminates
  absent-vs-empty (the websites `exists`/`active` pair, and the empty-registry
  `total: 0` case).
- **`store missing` for the dream store requires one additive backend field.**
  If that field is not shipped, the dream surface must fall back to the
  *unavailable* treatment (`unknown` tone + `status_reason`) rather than
  inventing an empty state. A criterion that demands a field which does not
  exist would be a spec that cannot pass — this one does not.

### 1.5 Status copy is sourced, never authored

Every `status_reason` string the backend already produces (`"REST http://… not
reachable"`, `"CLI <bin> --json health exit 0"`, `"CLI <bin> runs but exposes no
health verb (exposes: …)"`) is the copy the shell should surface, verbatim, as
the `title`/detail of a pill, a notification body or a degraded-state banner.

> **AC-V3.** No shell string may paraphrase a status into a claim the backend did
> not make — e.g. rendering a `no-health` panel as "service down" or a `degraded`
> panel as "outage". The existing `TONE_DESCRIPTIONS` map in `status.js` is the
> approved wording for tooltips.
> **Verify:** for each of the five statuses, compare the rendered detail copy to
> `TONE_DESCRIPTIONS[status]` (or the panel's `status_reason`). Any copy asserting
> a fault for `no-health`/`unknown` is a fail — those two exist specifically to
> *avoid* a false accusation.

---

## 2. Shared platform constraints (apply to all three specs)

- **Auth is fail-closed.** Every route except `/api/health` and `/api/auth/*` is
  behind `_authenticated`. A tray poller or a palette action that hits a protected
  route without a session gets a 401, and a 401 is **not** an outage — the shell
  must route it to the existing `LoginGate`, not to a degraded banner. `App.jsx`
  already does this via `isUnauthorized(...)`.
- **Only `/api/health` is unauthenticated.** It is therefore the only endpoint a
  tray may poll before login. Its shape (`app.py::health`) is
  `{"status": "ok", "service": "mem20-control", "version": <__version__>, "uptime_s": N}`
  — i.e. `service` is `mem20-control` and the uptime key is **`uptime_s`**, not
  `uptime_seconds`, so a shell that guesses key names will read nothing.
- **`/api/health` `status` is a hardcoded literal `"ok"`.** It means "this service
  answered", not "the fleet is healthy". Nothing may treat it as a fleet claim —
  that is exactly what `/api/registry` is for.
- **A full registry sweep is expensive** (`~30 subprocesses`, some importing heavy
  ML stacks; `docs/desktop.md` and `app.py` both say so). Shells must not create a
  new poll frequency; they consume the existing cache contract (TTL 45 s).
- **The sidecar is not wired yet.** `src-tauri/src/lib.rs` is a bare
  `tauri::Builder::default().run(...)` — no spawn, no port handshake (that is
  issue #36). Every spec below therefore states its preconditions in terms of
  "a reachable base URL", so it can be tested against `cargo tauri dev` today and
  against the bundled sidecar once #36 lands, without rewriting the criteria.
- **Success is not "it renders".** Each spec's final section is a negative test.
  The status vocabulary exists to stop the shell from lying; a test suite that
  only checks the happy path does not test the thing these issues are about.

---

## 3. Instrumentation each spec asks for

Reviewers cannot verify "the tray feels right", but they can verify counters.
Each spec names the minimum set it needs; the shared minimum is:

| Counter | Emitted by | Used by |
|---|---|---|
| `tray_state_changes{from,to}` | shell | #37 |
| `notifications_emitted{status}` / `notifications_suppressed{reason}` | shell | #37 |
| `palette_open{trigger}` / `palette_select{kind}` / `palette_empty{query_len}` | web UI | #38 |
| `shell_lifecycle{state}` / `panels_treated_stale` | shell | #39 |

`notifications_suppressed{reason}` must carry `reason ∈ {unchanged, cached, stale, authenticated_out, muted}` — the reason is what makes "we did not nag" auditable instead of accidental.
