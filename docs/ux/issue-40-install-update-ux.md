# #40 — Install, update and failure UX for the desktop build

| | |
|---|---|
| **Issue** | #40 — desktop packaging, code-signing, auto-update |
| **Surface** | `mem20controlz/src-tauri/` (shell), `mem20controlz/mem20controlz/web/src/` (in-window copy), `packaging/` (artifacts) |
| **Source clause** | `docs/audit/mem20controlz-desktop-overhaul-plan.md` **C7** |
| **Depends on** | `README.md` §1 (shared status vocabulary) and §1.3 (`starting` / `backend unreachable` / `store missing`); the `deriveLifecycleState` function specified in #39 |
| **Blocks** | Nothing. This is the last UX gap in the desktop chain. |
| **Blocked by** | #36 (sidecar) for §7 only, and by release infrastructure that does not exist for all of §4–§6. **Both are marked per-criterion below.** |

This is the surface where a product loses a user before that user ever sees it work.
Every other UX issue in this backlog assumes the app is already running. This one is
about the four moments before and between runs: the first launch, the nag, the failed
update, and the process that died halfway.

---

## 1. The rule this document is built on

The house invariant (§1.1 of `README.md`) is that **no surface may render a positive
affordance for a status the system did not actually confirm.** Install and update are
where that invariant is easiest to break and most expensive to break, because both
involve claims about *the future* ("this will work", "this is current", "this is the
real file").

So there is one sentence to hold on to for the rest of this document:

> **An updater never knows something is current. It only knows that a check succeeded
> and said so. Absence of a successful check is `unknown`, never "up to date".**

Applied concretely: no network, a 500 from the release feed, a TLS failure, a rate
limit, a mirror that answered with HTML — every one of those is `check failed` or
`unknown`, and none of them may render the sentence "you're on the latest version."
That single rule is worth more than the prompt's visual design.

### 1.1 The four install/update states

These are **shell** states, additive to the five backend statuses, and they must be
rendered on the same chrome as the lifecycle model in #39. They do not replace it.

| State | Trigger | Must never be rendered as |
|---|---|---|
| `unverified build` | The running binary has no valid signature / notarization ticket | A warning the user can dismiss once and never see again |
| `update available` | A check **succeeded** and the feed's version is newer than the running one | A modal dialog; a badge with no version numbers |
| `update failed` | Any stage of download / verify / apply / re-verify failed | A single generic "update failed"; a success state; a retry loop with no exit |
| `update interrupted` | The process died with an apply in flight (marker present on next launch) | A crash report; a silent fall-back to the old version with no message |

### 1.2 One version authority, or the comparison is a guess

An update decision is a comparison between **the version that is running** and **the
version that is offered**. The repo currently has five numbers for that first term and
they disagree:

| Source | Version | Where |
|---|---|---|
| `VERSION` (repo root) | `3.0.0` | `VERSION` |
| control-plane package metadata | `0.1.0` | `mem20controlz/pyproject.toml` `project.version` |
| Tauri bundle metadata | `0.1.0` | `mem20controlz/src-tauri/tauri.conf.json` `version` |
| the running sidecar's own report | `0.1.0` | `/api/health` → `version`, from `mem20controlz/__init__.py` `__version__` |
| the only installer committed to the tree | `2.1.0~rc2` | `packaging/deb/mem20_2.1.0~rc2_amd64.deb` |

> **AC-40-01. [specifiable now]** The *installed* version is defined as the `version`
> string returned by the running sidecar's `/api/health`. Nothing else is the installed
> version — not a build-time constant baked into the shell, not a filename, not
> `VERSION`. If `/api/health` cannot be read, the installed version is **unknown** and
> no update decision may be made.
> **Verify:** with the sidecar stopped, the About panel reports the version as unknown
> and the update control is disabled with the reason — it does not fall back to a
> compiled-in number.

> **AC-40-02. [specifiable now]** The offered version comes only from a feed response
> that parsed as the expected schema. A response that is HTML, empty, or missing the
> version field is a failed check.
> **Verify:** point the feed at a URL returning `200` with an HTML body. The UI must
> read `check failed`, and must not read `up to date` or `update available`.

> **AC-40-03. [blocked: release infra]** Comparing `3.0.0` (release) against `0.1.0`
> (running) will report an update on every launch forever, and comparing `0.1.0`
> against `0.1.0` will hide a real `3.0.0` release. **Until the five numbers above are
> reconciled to one, this feature must not ship enabled.** Shipping it against the
> current tree produces a permanently-wrong answer, which is worse than no updater.
> **Verify:** the release checklist for enabling the updater includes a single
> reconciled version, and the four stale sources are retired in the same change.

> **AC-40-04. [specifiable now]** The update comparison is `offered > installed` using
> pre-release-aware ordering, and an offered version *equal to or older than* the
> installed one renders `up to date` **only after a successful check**. A downgrade
> must be refused, not offered. If ordering cannot be determined, the state is
> `unknown`, not `update available`.
> **Verify:** offer `0.1.0` to a `0.1.0` install → `up to date`. Offer `0.0.9` → `up to
> date`, no update, no downgrade. Offer `not-a-version` → `unknown` with a reason.

---

## 2. What exists today (measured, not assumed)

Everything in this section was read from the tree at the baseline commit. It is here
so that no reader mistakes the specifications below for a description of current
behaviour.

| Capability | Status today | Evidence |
|---|---|---|
| Tauri shell scaffold | **exists** | `mem20controlz/src-tauri/{Cargo.toml,tauri.conf.json,src/main.rs,src/lib.rs}` |
| Native window | **exists** | `tauri.conf.json` → `app.windows[]`, 1280×800, title `mem20 control plane` |
| Bundle icon | **not implemented** | `tauri.conf.json` → `bundle.icon` is `[]` |
| Updater plugin | **not implemented** | `Cargo.toml` has no `tauri-plugin-updater`; `grep -c updater` = `0` |
| Updater endpoint / pubkey | **not implemented** | `tauri.conf.json` has no `plugins` key at all |
| Any update UI | **not implemented** | `web/src/` contains `App.jsx api.js auth.js components hooks.js main.jsx status.js styles.css tabs views` — no update surface |
| macOS `.dmg` + notarization | **not implemented** | `packaging/README.md` lists four channels: pip, docker, npm, apt |
| Windows `.msi` + Authenticode | **not implemented** | same |
| Linux `.AppImage` | **not implemented** | same |
| `.deb` build | **partial** | `packaging/deb/build-deb.sh` builds from package metadata; no signature, no checksum step |
| Sidecar spawn / port handshake | **not implemented** | `src-tauri/src/lib.rs` is a bare `Builder::default().run(...)`; main.rs comment defers sidecar to #36 and signing to #40 |
| Rollback / previous-version retention | **not implemented** | nothing staged; `cargo tauri build` output is unsigned and unretained |

Two of these deserve to be stated as findings rather than gaps, because they are
already user-visible defects today:

1. **A committed `.deb` from a previous release is sitting in the tree**
   (`packaging/deb/mem20_2.1.0~rc2_amd64.deb`, ~3.9 MB) while the repo's `VERSION` is
   `3.0.0`. Anyone who finds it and installs it gets an old, unsigned build with no way
   to know it is old. A committed artifact is a distribution channel whether or not it
   was meant to be one.
2. **`bundle.icon` is empty.** An installed app with no icon renders as a generic
   blank/parent placeholder in the Dock, the taskbar, and the Applications list. This
   happens at precisely the moment the user is deciding whether to trust the thing —
   and "anonymous blank icon" reads as malware. Filling this in is a five-minute change
   with outsized trust value.

---

## 3. First run on an unsigned binary

### 3.1 What the OS actually says

This is not something we control, so it must be described accurately — support copy
that misquotes the OS is how users conclude the product is broken.

| OS | What the user sees | What it means | Can they proceed in-window? |
|---|---|---|---|
| macOS 10.15–14, downloaded build | *"mem20controlz" can't be opened because Apple cannot check it for malicious software.* The alert offers only **OK**. | Not signed, or signed but not notarized. | No. The only routes are the version-specific Privacy & Security path, a right-click-Open, or nothing. |
| macOS 15+ | Same class of alert, but **the Control-click → Open bypass was removed**. The route is System Settings → Privacy & Security → **Open Anyway**, and it re-prompts. | Same cause; the workaround changed. | No. |
| Windows 10/11, downloaded build | *Windows protected your PC — Microsoft Defender SmartScreen prevented an unrecognized app from starting.* Plus, on launch as an installer, **Unknown publisher** in the elevation prompt. | No Authenticode signature, or too few installs to have reputation. | No, until **More info → Run anyway**. |
| Linux, `.deb` | Installs without a signature check; `apt` may warn only if a repo is unsigned. | No signing concept enforced by default. | Yes — and this is the problem: the platform does not warn, so the absence of a warning is mistaken for a trust signal. |
| Linux, `.AppImage` | Nothing, if it is executable; *Permission denied* if it is not. | File mode, not trust. | Yes. |

### 3.2 What we tell the user — the honest default

The honest default is **not** "here is how to get past the dialog." It is: name the
state, give the user a way to verify the file is ours, and point at the channel that
does not have this problem.

The first run must present, in-product, in this order:

1. **The state, plainly.** `This build is not signed or notarized. macOS/Windows cannot
   verify who made it.` No reassurance, no euphemism ("beta", "development build" is
   only allowed if it is literally true).
2. **The provenance.** The SHA-256 of the artifact, and a link to the place that
   publishes the same digest, so the two can be compared. A digest the user cannot
   check against an independent copy is decoration, not verification.
3. **The better channel, named.** Today the honest recommendation is the channel with
   no OS trust prompt at all — the pip package, the container image, or the `.deb` from
   the distribution path — or building from source. This is a real, available answer,
   not a deflection.
4. **What we will not do:** *(see §3.4 — and the copy says so explicitly, so the user
   is not left hunting for a bypass we deliberately did not publish.)*

Copy, written to be used as-is:

> **This build isn't signed.**
> We couldn't verify this copy of mem20controlz, so your system couldn't either.
> If you downloaded it from somewhere other than our release page, delete it.
>
> **Check it matches** — SHA-256 `‹digest›` should match the digest on the release page.
>
> **No signing prompts** — the pip package, the container image and the `.deb` install
> without an OS trust prompt, because they don't launch a downloaded binary.
>
> We don't recommend turning off your system's protection to run this. If that's the
> only way it will open, the right fix is a signed build, and that's on us.

> **AC-40-05. [specifiable now]** The first-run unsigned notice is shown **once per
> build**, and its dismissed state is keyed to the build digest — a new build re-shows
> it. It is a banner in the main window, not a modal, and it never blocks the fleet
> view.
> **Verify:** dismiss, quit, relaunch → no banner. Install a different digest →
> banner returns.

> **AC-40-06. [specifiable now]** The notice is reachable again after dismissal from
> About → build provenance. It is a suppressed notice, not a deleted one.
> **Verify:** after dismissal, the About panel still shows the unsigned state and the
> digest.

> **AC-40-07. [blocked: release infra]** The digest shown in-window must equal the
> digest published beside the artifact. Until a release publishes digests, this
> criterion cannot pass, and the provenance block must render `no published digest to
> compare` rather than showing a digest with nothing to check it against.
> **Verify:** with no published digest, the copy explicitly says there is nothing to
> compare it to.

### 3.3 Trust presentation details that are cheap and load-bearing

- **Icon present (§2 finding 2).** An app with no icon reads as untrustworthy at the
  moment trust is being decided. Required, not cosmetic.
- **Publisher string matches across the stack.** The product name in the window, the
  bundle, and the OS-level publisher field must be the same words. Divergence ("mem20
  control plane" in the title bar, "mem20controlz" in the bundle, "Unknown publisher"
  in the prompt) reads as three different things.
- **No countdown, no urgency, no dark pattern on the dismiss.** The user is being asked
  to accept risk; manufacturing pressure to hurry is the opposite of informed consent.

### 3.4 What we refuse to do

This list is a product decision and belongs in the acceptance criteria, not only in a
style guide. Each item is a thing the product **must not** do, in copy, docs, tooltips,
installer scripts, or error messages.

| Refused | Why |
|---|---|
| Tell the user to disable Gatekeeper, or run `spctl --master-disable` | It is a machine-wide security downgrade to work around one app's missing signature. |
| Publish `xattr -d com.apple.quarantine` as *the* fix | A per-file security bypass dressed as a one-liner; it moves the risk to every future download of that file and teaches a habit that outlives us. |
| Tell users to click through SmartScreen **before** giving them a digest to compare | "Run anyway" with no verification is just "trust me" with an OS dialog's authority attached. |
| Instruct running an installer as root / Administrator to get past a failure | Escalating privileges to work around a bug converts a UX failure into a security incident. |
| Present a curator's assurance ("we tested this") as verification | It is a claim, not evidence; it is exactly what the shared vocabulary exists to prevent. |
| Apply an update silently, or without an explicit accept | This tool holds a local store and can be mid-run; a silent swap is a data-loss path. |
| Render "up to date" (or a green check) after a check that did not succeed | The core invariant, §1. |
| Keep retrying a failed update with no exit | A retry loop against a broken feed is how a support ticket becomes a crash loop. |
| Republish the stale committed `.deb` as if it were current | §2 finding 1. An old artifact with no date is a lie by omission. |

> **AC-40-08. [specifiable now]** A reviewer can grep the shipped copy and docs for the
> refused patterns and find none.
> **Verify:** search the built bundle, `docs/`, and `packaging/` for the Gatekeeper
> bypass, the quarantine-attribute removal, and any "run as Administrator/root to fix"
> instruction. Any hit is a fail — including in a comment that gets bundled.

> **AC-40-09. [specifiable now]** Where the unsigned state exists, the product says
> which channels avoid it (§3.2 item 3) rather than leaving the user to infer that the
> desktop build is the only option.
> **Verify:** the notice names at least one working alternative channel.

---

## 4. The update-available prompt and its dismiss states

### 4.1 Placement

The prompt is a **non-modal banner in the window chrome**, plus an entry point in
About. It is not a modal dialog and it does not steal focus. An operations console is
often open *because* something is on fire; a modal that interrupts an operator mid
incident to talk about version numbers has its priorities backwards.

One suppression rule, borrowed from the shared state function:

> **AC-40-10. [specifiable now]** The prompt is suppressed unless the lifecycle state is
> `ready` or `degraded`. It never appears in `starting`, `backend unreachable`,
> `signed out`, or while a region is rendering `store missing` — asking someone to
> restart an app that cannot currently reach its own backend is noise.
> **Verify:** kill the sidecar with an update staged; the prompt does not appear; the
> `backend unreachable` banner does, per #39.

### 4.2 What the prompt must say

Four facts, all of them checkable, no adjectives:

```
Update available — 3.1.0  (you have 3.0.0)
Released <date>.  <n> changes, including <one line of substance>.
[ Install and restart ]   [ Later ]   [ Skip this version ]
```

- Both version numbers, always. A prompt that says "an update is available" without
  naming versions is unverifiable by the user.
- The **installed** number comes from `/api/health` (AC-40-01), not the bundle.
- Nothing about how important it is beyond a factual severity, and no "critical" unless
  the feed marked it critical for a named reason.

### 4.3 Dismiss states — exact semantics

The distinction between "later" and "skip" is the whole of this section. Collapsing
them means a user who wanted five more minutes gets bothered forever, or a user who
never wants this build gets asked at every launch.

| Action | Persisted | Re-prompt rule | Reversible |
|---|---|---|---|
| **Install and restart** | `installed_version` = new | — | n/a |
| **Later** | snoozed until `now + 24h` for this offered version | One re-prompt after the snooze, then it waits for the next launch day | Yes — About → Check now |
| **Skip this version** | `skipped = <exact offered version>` | Never offered again **for that exact version**; a newer version prompts normally | Yes — About → Check for updates clears the skip |
| **Esc / close / click outside** | Identical to **Later** | As *Later* | Yes |

> **AC-40-11. [specifiable now]** `Skip this version` suppresses only the exact version
> skipped. Offering `3.1.1` after skipping `3.1.0` prompts normally.
> **Verify:** skip `3.1.0`, feed `3.1.1` → prompt appears.

> **AC-40-12. [specifiable now]** Escape and window-close are **not** a skip. They
> snooze. A user who presses Esc out of habit must not silently lose updates for that
> version forever.
> **Verify:** press Esc; relaunch after the snooze → prompt returns for the same
> version.

> **AC-40-13. [specifiable now]** Both snooze and skip survive a restart and are
> visible in About ("Skipped 3.1.0", "Remind after <time>"), with a control to clear
> them. A hidden sticky setting is a bug even when its behaviour is correct.
> **Verify:** skip a version, quit, relaunch → About states the skip; clearing it
> re-enables the prompt.

> **AC-40-14. [specifiable now]** Dismissing the prompt never changes the region's
> underlying state (§AC-39-25 applied here): the banner hides, the About panel still
> reports `update available`.
> **Verify:** dismiss; About still shows the offered version.

### 4.4 Checking

- Automatic check on launch **and** at most once per 24 h while running. Not more.
- **Manual check is always available** and is the escape hatch for every suppressed
  state — skip, snooze, and failed check alike.
- Checking is a network call to a third party; it must be off-able in settings, and the
  setting must say what it does ("check for updates on launch") rather than hiding
  behind "telemetry".

> **AC-40-15. [specifiable now]** With automatic checking off, no update network call is
> made on launch, and About still allows a manual check.
> **Verify:** network log with the setting off → zero calls to the feed until manual.

> **AC-40-16. [specifiable now]** `check failed` is a distinct, visible state with the
> reason and a retry. It is never silent, and it never degrades into `up to date`.
> **Verify:** 500 from the feed → "Couldn't check for updates — <reason>" + retry, and
> no green state anywhere.

---

## 5. A failed update and the rollback path

### 5.1 Stages, named

An update is six ordered stages, and a failure must name the one it happened in. This
is the difference between a user who can act and a user who files "update broken".

| Stage | What it means | Failure is |
|---|---|---|
| `download` | Fetching the artifact | Network/disk. Nothing changed. |
| `verify` | Digest (and signature, when there is one) matches the published value | **Refuse and stop.** Nothing changed. |
| `stage` | Artifact placed beside the install, not yet active | Disk/permissions. Nothing changed. |
| `apply` | New artifact becomes the active one | The dangerous one — see §5.3. |
| `restart` | Old process exits, new one starts | Old version may or may not be running. |
| `re-verify` | New sidecar answers `/api/health` with the expected `version`, and the store is readable | Installed but unproven. |

> **AC-40-17. [specifiable now]** Every failure message names the stage in the user's
> words — "downloading", "checking the file", "installing", "starting the new version",
> "confirming it works" — plus one sentence on the current machine state. Never a bare
> "update failed".
> **Verify:** force a failure at each of the six stages; six distinct, correct messages.

> **AC-40-18. [specifiable now]** The verify stage is fail-closed: a digest mismatch
> stops the update before anything is applied and recommends re-downloading. A mismatch
> is never a warning to be ignored.
> **Verify:** corrupt the staged artifact → refusal, old version untouched, message
> names the digest mismatch.

### 5.2 The three machine states after a failure

Every failure must resolve to exactly one of these, and say which:

1. **Unchanged** — still on the old version, everything works. (Any failure through
   `stage`.)
2. **Installed but unverified** — the new version is active but did not pass
   `re-verify`. This is the state that must never be reported as success.
3. **Unknown** — we could not determine what is running. This is a legitimate answer
   and must be available; forcing a guess between (1) and (2) is how a user ends up
   trusting a broken install.

> **AC-40-19. [specifiable now]** Success is declared **only** after `re-verify` passes:
> the new sidecar reports the expected version on `/api/health` *and* the store reads.
> Anything less renders as `installed but unverified` with a "go back" action.
> **Verify:** make the new build report the old version on health → no success state;
> rollback offered.

### 5.3 Rollback

The honest default for rollback is a **retained previous artifact**, not a reinstall
from the network. If the fix for a broken update requires connectivity and a correct
download, then it fails exactly when the update failed.

Required behaviour, when there is something to roll back to:

- The previous version's artifact is retained through the whole update and deleted only
  after `re-verify` succeeds.
- `go back to <old version>` is a first-class button in the failure state and in About —
  not a documentation link, not a support instruction.
- Rolling back is itself verified: after it, `/api/health` must report the old version,
  and *that* success is stated plainly.

> **AC-40-20. [blocked: no staged install exists]** Today there is no staged install, no
> retained artifact, and no `re-verify`, so **rollback is not implemented.** The truthful
> current behaviour is: the previous build survives only because nothing was ever
> replaced. Manual recovery means reinstalling the prior package by hand.
> **Do not** write copy promising an automatic rollback until the retention exists.
> **Verify:** at the baseline commit, the failure path offers no rollback control and
> the docs do not claim one.

> **AC-40-21. [specifiable now — buildable before the updater]** The *decision* logic is
> testable today with a fake updater: given an injected stage failure, the UI must
> produce the correct one of the three states, name the stage, and offer the correct
> actions. This is the part that should land first, because it is independent of
> signing infrastructure.
> **Verify:** a test double drives all six stages × 3 outcomes; 18 assertions.

### 5.4 Copy for the failure state

> **The update to 3.1.0 didn't finish.**
> It stopped while *checking the new version*. **You're still on 3.0.0 and it's
> working normally** — nothing was replaced.
> [ Try again ]  [ Details ]
>
> — or, in the unverified case —
>
> **3.1.0 is installed but didn't confirm it started correctly.**
> We couldn't get a healthy response from the new version.
> [ Go back to 3.0.0 ]  [ Try again ]  [ Details ]

"Nothing was replaced" is the single most reassuring true sentence available, and it is
only allowed when it is literally true. That is the point of the three-state model.

---

## 6. When the sidecar dies mid-update

This is the worst case and the easiest to get silently wrong, because a death during an
update looks exactly like a crash to anything that is not told otherwise.

### 6.1 Status today

**Not implemented — and in a specific, checkable way.**

- There is no sidecar lifecycle to interrupt: `src-tauri/src/lib.rs` is
  `tauri::Builder::default().run(...)`, with no spawn, no port handshake, no supervision.
- The sidecar branch is not merged and does not compile standalone (module references
  that are not committed on that branch), so "mid-update" is not a reachable state yet.
- Consequence for today's UX: a desktop window with no sidecar has nothing to show. This
  is #39's `backend unreachable` state and nothing more. **No update-specific copy should
  be written or shipped for a lifecycle that does not exist.**

### 6.2 The behaviours that must be specified now anyway

These are written now so that #36 and the updater are built against them, not retrofitted.

**(a) An update must refuse to start while a dream run holds the lock.**

`/api/dreams/runs` starts background jobs and the engine's CLI owns the run lock;
`/api/dreams/idle-stats` already reports who holds it. Applying an update restarts the
sidecar, which kills a run in flight. That is data loss caused by a version bump.

> **AC-40-22. [blocked: #36]** If a dream run is active, an update is **refused**, not
> queued silently. The copy names the run and offers to wait, or to admit that cancelling
> is the user's decision. The updater never kills a run to proceed.
> **Verify:** start a run, offer an update → refusal naming the run; no restart occurs.

**(b) A staged-but-unapplied update is abandoned when the sidecar dies.**

> **AC-40-23. [blocked: #36]** If the sidecar dies after `stage` and before `apply`, the
> staged artifact is **not** applied on next launch. It is discarded, the new launch
> reports `the update didn't start`, and the running version is stated. A staged file is
> not consent to install it later.
> **Verify:** kill the sidecar between stage and apply; relaunch → old version running,
> message says the update did not start, no auto-apply.

**(c) An intentional restart must be distinguishable from a crash.**

The shell must write an intent marker *before* it stops the sidecar as part of an
update, and read it on the next launch. Without this, every successful update produces
a crash report and every crash during an update looks intentional.

> **AC-40-24. [blocked: #36]** An interrupted apply produces **one** `update
> interrupted` state on next launch — not a crash report, not a silent fallback — with
> `retry` and `stop trying`. It resolves after one resolution; it does not reappear on
> every subsequent launch.
> **Verify:** kill the app mid-apply; relaunch → single `update interrupted` notice;
> resolve it; relaunch again → no notice. Instrumentation (§7) shows the exit recorded
> with intent `update`, not `crash`.

**(d) Never show progress that outlives the thing doing the work.**

> **AC-40-25. [blocked: #36]** If the process that owns the download/apply is gone, no
> progress indicator may keep animating. A progress bar is a claim that work is
> happening.
> **Verify:** kill the sidecar mid-download → the progress affordance is replaced by a
> terminal failure state within one poll interval, per #39's bounded-state rule.

---

## 7. Instrumentation

Reviewers cannot verify "the update flow feels honest", but they can verify counters.
Minimum set, alongside the shared counters in `README.md` §3:

| Counter | Labels | Why |
|---|---|---|
| `install_first_run` | `unsigned=true/false`, `channel=deb/pip/docker/source` | Is anyone actually hitting the unsigned path? |
| `update_check` | `result=ok/failed/unknown`, `trigger=launch/manual` | Proves `failed` is not being rendered as `ok`. |
| `update_prompt_shown` / `_dismissed` | `action=install/later/skip/escape` | Tells you whether Esc is being mistaken for skip (§4.3). |
| `update_apply` | `stage`, `result=ok/failed` | Which stage actually breaks in the field. |
| `update_outcome` | `state=unchanged/unverified/unknown/rolled_back` | Verifies the three-state model is the one users see. |
| `sidecar_exit` | `intent=update/crash/quit` | **Must** exist before AC-40-24 can be tested. |
| `update_refused` | `reason=dream_run_active/offline/dev_build` | Proves refusals happen for the stated reason. |

> **AC-40-26. [specifiable now]** `update_check` has no `ok` label reachable from a
> failed network call. If a failed check can be counted as `ok`, the honesty invariant is
> being violated somewhere the UI cannot see.
> **Verify:** force failures; the counter records `failed`, never `ok`.

---

## 8. Reviewer's matrix

Five install/update states, three platforms, plus the two lifecycle interactions. Every
cell must render a named state with text; zero blank cells, zero bare spinners.

| State | macOS (unsigned, ≤14 / 15+) | Windows (unsigned) | Linux (`.deb` / AppImage) |
|---|---|---|---|
| **First run** | OS alert with the version-correct bypass path; in-product unsigned banner + digest + better channel | SmartScreen; in-product banner + digest | No OS warning — so the in-product banner carries the whole trust burden and must not be skipped |
| **Update available** | Non-modal banner, both versions, three actions | same | same |
| **Later / Skip / Esc** | snooze ≠ skip; visible & clearable in About | same | same |
| **Failed update** | stage named + one of `unchanged` / `unverified` / `unknown` | same | same |
| **Sidecar died mid-update** | `update interrupted`, once, retry/stop | same | same |
| **Lifecycle `backend unreachable`** | no update prompt (§AC-40-10) | same | same |
| **Lifecycle `starting`** | no update prompt; `starting` per #39 with text | same | same |

> **AC-40-27.** The matrix is an automated test where the surface exists, and an explicit
> `not implemented` assertion where it does not — so the doc cannot silently rot into
> fiction. At the baseline, the six "not implemented" rows of §2 are asserted as absent.
> **Verify:** the test fails if an updater is claimed but `Cargo.toml` has no updater
> dependency.

---

## 9. Automatic fails

1. "Up to date" (or any green check) after a check that did not succeed. *(§1)*
2. Instructing the user to disable Gatekeeper, remove the quarantine attribute as the
   standard fix, or click "Run anyway" with no digest to compare. *(§3.4)*
3. Esc / close rendering as a permanent skip. *(AC-40-12)*
4. A modal update dialog that steals focus from an operations console. *(§4.1)*
5. An update prompt shown while the app cannot reach its own backend. *(AC-40-10)*
6. Declaring success before `re-verify`: new version installed, never health-checked,
   reported as done. *(AC-40-19)*
7. Rollback promised in copy with no retained artifact behind it. *(AC-40-20)*
8. An update that kills an in-flight dream run. *(AC-40-22)*
9. Every successful update reported to the user as a crash, because the restart was not
   marked as intentional. *(AC-40-24)*
10. A progress indicator that outlives the process doing the work. *(AC-40-25)*
11. Shipping the update comparison against four disagreeing version numbers. *(AC-40-03)*
12. Publishing the stale committed `.deb` as a current artifact. *(§2 finding 1)*
13. An installed app with no icon presenting itself at the moment trust is decided.
    *(§2 finding 2)*

---

## 10. Out of scope

- **Delta/binary-diff updates.** A correct full-artifact update is the prerequisite.
- **Silent background installation.** Explicitly excluded in §3.4.
- **Update channels beyond stable** (beta/nightly) — a later setting, and it must not
  arrive before the single-version-authority problem (AC-40-03) is solved.
- **License/entitlement checks at update time.** Not a UX concern and not consented to
  here.
- **Auto-update on a host running the systemd service.** That is the service lifecycle,
  not the desktop shell; restarting the unit under a running fleet is its own problem.
- **Windows/Linux equivalents of notarization policy.** Named as gaps in §2, not designed
  here.

---

## 11. Implementation status — the honest ledger

Every row is either buildable now or explicitly absent. Nothing in this document should
be read as describing behaviour that exists.

| Behaviour | Status | Blocked on | Can be specified now |
|---|---|---|---|
| Single version authority (AC-40-01/03) | **not implemented** — five disagreeing numbers (§1.2) | release infra | yes |
| Unsigned first-run notice + refusal list (§3) | **not implemented** — no such copy in the tree | nothing | yes |
| Bundle icon (§2 finding 2) | **not implemented** — `bundle.icon: []` | nothing | yes |
| Update prompt + Later/Skip/Esc semantics (§4) | **not implemented** — no update UI in `web/src` | updater plugin | yes |
| Check-failed ≠ up-to-date (§1, AC-40-16) | **not implemented** | updater plugin | yes |
| Six-stage failure model + three machine states (§5.1–5.2) | **not implemented** | updater plugin | yes — and this is the piece to build first (AC-40-21) |
| Rollback / N−1 retention (§5.3) | **not implemented** | updater plugin + release infra | rules only, not copy |
| Refuse update during a dream run (AC-40-22) | **not implemented** | #36 | yes |
| Interrupted-update marker (AC-40-24) | **not implemented** — no sidecar lifecycle | #36 | yes |
| Sidecar spawn at all | **not implemented** — `lib.rs` is a bare builder | #36 | no |
| Signed/notarized macOS, Authenticode Windows, AppImage | **not implemented** — `packaging/` has pip/docker/npm/apt only | certs + CI | no |
| `.deb` signing | **not implemented** — `build-deb.sh` has no signing step | release infra | no |

The shape of that table is the message: **the parts that can be built without
certificates are the parts that protect the user from being lied to**, and they are also
the parts that are still missing. Signing is a procurement problem; honest copy is not.

---

**Written:** 2026-10-27 · **Baseline:** `main` @ `1264076698a00878acc3adacf7bf1d51eea315cc`
**Owner:** UX research · **Branch:** `docs/ws1-issue-40-update-ux`
**Predecessors:** `issue-37-tray-and-notifications.md`, `issue-38-command-palette.md`,
`issue-39-offline-degraded-ux.md` — this document shares their vocabulary and cites
§1 of `README.md` rather than restating it.
