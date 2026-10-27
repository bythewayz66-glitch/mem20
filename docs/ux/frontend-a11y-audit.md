# mem20controlz — frontend accessibility audit

| | |
|---|---|
| **Surface** | `mem20controlz/mem20controlz/web/src/` |
| **Audited at** | `main` @ `1264076` (2026-10-27) |
| **Branch** | `fix/ws2-controlz-a11y` |
| **Method** | Source read, then measurement: every colour claim below is a WCAG 2.1 relative-luminance computation against the token actually shipped, not an estimate. `node --test web/test/a11y.test.js` re-asserts the numbers. |
| **Out of scope** | #38 command palette (`feat/38-command-palette`, PR #109) and #39 offline states (`fix/39-offline-degraded-ux`, PR #108). Both are open and unmerged. Where they introduce a surface this branch must survive, §5 names the contract rather than editing their files. |

Status: **11 defects, 8 fixed here, 3 handed off with a written contract.** Nothing
below is a "would be nice"; each entry names a file, a line on `main`, what a user
actually experiences, and what changed.

---

## 1. Defects

### A11Y-01 — Login field suppresses the focus ring entirely · **fixed**

**File:** `web/src/styles.css:1142` (pre-fix)

```css
.login-input:focus { outline: none; border-color: var(--accent); }
```

The only focus cue on the password field was a 1px border shifting from `#1d2733` to
`#58a6ff`. Measured against the field's own `--bg-2` fill that is a 6.4:1 change in
border colour but a **0px change in thickness** — at 1px, on a 14px input, it is not
perceivable at a glance, and `outline: none` also removes the OS ring in forced-colours
mode. A keyboard user's first action in the product (typing a password) had no visible
focus position.

**Fix:** `a11y.css` §3 — rule replaced with `.login-input:focus, .login-input:focus-visible`
drawing `2px solid var(--focus)` at `2px` offset, plus a global rule in `a11y.css` §3
so no other control depends on the browser default (which on a `#070b10` page is a
near-black halo). Matched on plain `:focus` as well so the original suppression cannot
win on specificity.

---

### A11Y-02 — No global focus-visible ring; the dark theme eats the default · **fixed**

**File:** `web/src/styles.css` (whole file: 0 occurrences of `:focus-visible` before this branch)

`.nav-item`, `.tab`, `.btn`, `.grid-table tr.clickable` are all `<button>`/`<tr>`
elements. Chromium's default `:focus-visible` ring is `auto` — rendered as a 1px
black-and-white dashed halo. On `--bg #070b10` the black half is invisible; the white
half reads as a 1px hairline. Measured: the default ring is not distinguishable from
the `--line #1d2a36` border used on every panel.

**Fix:** `a11y.css` §3 —

```css
:where(a, button, input, select, textarea, summary, [tabindex]):focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}
```

`--focus: #8ecbff` measures **11.40:1** vs `--bg`, **10.61:1** vs `--panel`,
**10.04:1** vs `--panel-2` — clears the 3:1 non-text minimum with a wide margin and
survives the darkest surface. A `forced-colors: active` block swaps in
`Highlight` so Windows High Contrast is not left with a discarded custom colour.

---

### A11Y-03 — Status pills fail AA on the tint they paint themselves on · **fixed**

**File:** `web/src/styles.css:538–586` (pre-fix `.pill-ok` … `.pill-error`),
tokens at `styles.css:16–21`.

Each pill draws `color: var(--tone)` over `background: rgba(tone, 0.10–0.12)`. Because
the tint is the same hue as the text, the effective background is *not* the panel — it
is the panel shifted toward the text colour, which lowers contrast more than the panel
alone suggests. Measured against the composited tint (as shipped):

| Token | Shipped value | On `--bg` | On `--panel` | On `--panel-2` | Verdict |
|---|---|---|---|---|---|
| `--ok` | `#3fb950` | 6.92 | 6.28 | **5.86** | pass — but 11px text |
| `--degraded` | `#d29922` | 6.97 | 6.32 | **5.91** | pass |
| `--unreachable` | `#f85149` | 5.42 | 4.98 | **4.70** | marginal — see note |
| `--unknown` | `#6e7f91` | 4.39 | 4.00 | **3.77** | **FAIL AA (needs 4.5)** |
| `--no-health` | `#7d8590` | 4.82 | 4.40 | **4.10** | **FAIL AA** |
| `--error` | `#ff7b72` | 6.79 | 6.17 | **5.76** | pass |

Two tokens fail outright. `--unreachable` at 4.70 passes AA on `--bg` but drops below
4.5 the moment a pill sits in a `--panel-2` table header or hovered row — the two most
common places a pill appears. `--unknown` fails everywhere, and `--unknown` is the tone
every *unrecognised or absent* status falls back to (`status.js:20-24`), i.e. the tone
used most often when the estate is in a state nobody has classified.

Note on `--unreachable`: the pill is the one affordance that says "this surface could
not be reached". A marginal 4.70 is not the place to save a hue.

**Fix:** tokens raised in `a11y.css` §1 to

| Token | Was | Now | Worst-case ratio (on `--panel-2`, over its own tint) |
|---|---|---|---|
| `--ok` | `#3fb950` | `#56d364` | 7.16 |
| `--degraded` | `#d29922` | `#e3b341` | 7.15 |
| `--unreachable` | `#f85149` | `#ff7b72` | 5.76 |
| `--unknown` | `#6e7f91` | `#93a4b5` | 5.62 |
| `--no-health` | `#7d8590` | `#9aa4ad` | 5.66 |
| `--error` | `#ff7b72` | `#ffa198` | 6.82 |

Tints were raised from 10%/12% to 12%/14% at the same time, and every border from
`0.45` to `0.50` alpha so the pill outline also clears 3:1 as a UI boundary.
Hue is preserved (green/amber/red/grey/blue-grey) — this is a luminance change, not a
re-colouring, so the colour language the rest of the shell and `status.js` rely on is
untouched. `web/test/a11y.test.js` asserts all six against all four surfaces, so a
future "let's make the red deeper" cannot silently regress it.

---

### A11Y-04 — `--text-faint` fails AA on 12px body copy, ~70 call sites · **fixed**

**File:** `web/src/styles.css:14` (pre-fix `--text-faint: #5f7081`)

`.muted` is the shell's "this value was not reported" style, used for the *primary
information* in empty and partial states — 70 occurrences across `tabs/` and `views/`.
At `#5f7081`:

- vs `--bg` → **3.87:1**
- vs `--panel` → **3.60:1**
- vs `--panel-2` → **3.41:1**

That is below AA (4.5) on all three, and it is not decorative text — it is the
`"not reported"` / `"—"` that tells the operator a field is missing.

**Fix:** `--text-faint: #8496a8` in `a11y.css` §1 → **6.49 / 6.04 / 5.71:1**. Still
visibly dimmer than `--text-dim #8b9cad` at 7.01, so the three-level text hierarchy
survives, but every level now clears AA.

---

### A11Y-05 — The login gate is a `role="region"`, not a dialog, and nothing traps focus · **fixed**

**File:** `web/src/components/LoginGate.jsx:37` (pre-fix)

```jsx
<div className="login-gate" role="region" aria-label="Sign in">
```

Consequences, in order of severity:

1. **No focus trap.** Tab from the password field walks straight out of the card into
   the document. Since the gate renders *instead of* the shell, there is literally
   nothing behind it — focus lands on `<body>` and the user is off-screen with no
   spoken context.
2. **`role="region"` with `aria-label`** announces a landmark, not a dialog. A screen
   reader does not say "dialog", does not say it is modal, and does not read the
   description when entering.
3. **`autoFocus` on the input** (`LoginGate.jsx:63`) fires before React has committed
   the rest of the tree; in a `StrictMode` double-render it can be dropped entirely.
   There was also nothing to restore focus *to* on unmount.
4. **Login failures were silent.** `<p className="login-error">{error}</p>`
   (`LoginGate.jsx:70`) is plain text with no live region — a screen-reader user who
   submits a wrong password hears nothing at all and concludes the button did nothing.
   The input also had no `aria-invalid` / `aria-describedby`.
5. **No accessible name wiring.** The `<h1>` was unlabelled and the dialog had no
   `aria-labelledby`.

**Fix:** `LoginGate.jsx` renders through the new `components/FocusTrap.jsx` with
`role="dialog"`, `aria-labelledby="login-title"`, `aria-describedby="login-sub"`, and
`initialFocus` pointing at the password field via a ref (replacing `autoFocus`). The
error paragraph gained `role="alert"` + `id`, and the input gained
`aria-invalid`/`aria-describedby` conditional on the error. `FocusTrap` captures
`document.activeElement` on mount and restores it on unmount, with a fallback for the
common case where the opener no longer exists.

---

### A11Y-06 — Clickable table rows are mouse-only · **fixed**

**File:** `web/src/components/ui.jsx:131–161` (pre-fix `Table`)

```jsx
<tr className="clickable" onClick={() => onRowClick(row, index)}>
```

`onClick` on a `<tr>` with no `tabindex`, no `role`, and no key handler. Every
drill-down in the console is one of these:

| Call site | What the click does |
|---|---|
| `tabs/Subsystems.jsx:279` | select a registry panel |
| `tabs/CliCoverage.jsx:130` | select a CLI row |
| `views/DreamListView.jsx:120` | open a dream |
| `views/DreamHollowView.jsx:56` | open a hollow dream |

Four of the console's primary navigation paths were unreachable by keyboard and
unannounced by AT. The `selected` class was also purely visual.

**Fix:** `Table` now sets `tabIndex={0}` with an Enter/Space handler when
`onRowClick` is present, exposes `aria-selected` on the row, and accepts a `caption`
rendered as an `.sr-only` `<caption>`. `<th>` gained `scope="col"` (previously a bare
`<th>`, so AT guessed). Deliberately *not* converted to `role="grid"`: that would
require full roving-tabindex semantics on every cell and would break the existing
`panel-scroll` overflow behaviour.

---

### A11Y-07 — `TabBar` declares `role="tablist"` but implements none of it · **fixed**

**File:** `web/src/components/ui.jsx:3–22` (pre-fix)

```jsx
<div className="tabbar" role="tablist" aria-label={label}>
  <button role="tab" aria-selected={active === tab.id} …>
```

Promising `tablist` and delivering five plain tabbable buttons is worse than promising
nothing: the APG keyboard model requires (a) only the selected tab in the tab order and
(b) Arrow/Home/End moving selection. Neither was implemented, and the panels carry no
`role="tabpanel"` / `aria-labelledby` link back.

**Fix:** roving tabindex (`tabIndex={active ? 0 : -1}`), `ArrowLeft`/`ArrowRight`/`Home`/
`End` handled once on the container, focus moved with the selection, and stable
`id={`tab-${label}-${tab.id}`}` anchors so a panel can point `aria-labelledby` at its
tab. Applies to `tabs/Websites.jsx:35`, `tabs/Dreams.jsx:44` and
`views/DreamHollowView.jsx`.

---

### A11Y-08 — No skip link; every panel change costs 8 Tab presses · **fixed**

**File:** `web/src/App.jsx:106` (pre-fix: `<div className="shell">` straight into `<aside className="nav">`)

The nav rail holds 3 group labels + 5 buttons + 2 footer rows before `<main>`. Because
the app swaps panels by state (not by URL), there is no browser "skip to main" and no
scroll position change — a keyboard user re-walks the rail on every single panel switch.

**Fix:** `App.jsx` now opens `.shell` with `<a className="skip-link" href="#main-content">`
and `<main id="main-content" tabIndex={-1}>` so the anchor target can actually receive
focus (a `<main>` without `tabindex` is not focusable and the link would silently do
nothing — the classic broken skip link). Styled in `a11y.css` §4, slides in on
`:focus-visible` using `--motion-duration`.

---

### A11Y-09 — Status pills hide their reason from AT, and colour is the only signal · **partially fixed**

**File:** `web/src/components/StatusPill.jsx:8` (pre-fix)

`title={reason}` is the only carrier of *why* a status is degraded. `title` is exposed
to AT inconsistently (ignored on some touch AT, not announced on focus in most desktop
screen readers) and is unreachable by keyboard entirely.

Credit where due: the dot is already `aria-hidden` and the status **word** is real text,
so this is not a colour-only signal — that part of the component was already correct
and is not changed.

**Fix:** `reason` is now also mirrored into `aria-label={`${text}: ${reason}`}` so the
cause is in the accessible name. **Not fixed here:** the pill has no `role="status"`,
so a status changing `ok → unreachable` between polls is not announced. Making the
topbar pill live is the right move but it belongs with #39's state work (see §5,
HANDOFF-01) — a live region on `main` today would double-announce with the
`ErrorBanner role="alert"` that #39 ships.

---

### A11Y-10 — No reduced-motion handling anywhere · **fixed (forward-safe)**

**File:** `web/src/styles.css` — pre-fix: **0** occurrences of `transition`,
`animation`, `@keyframes` or `prefers-reduced-motion` in 1,258 lines.

Nothing in the shell animates today, which is why this reads as a non-issue and is
actually a trap: both in-flight branches introduce motion into this same stylesheet.
PR #109 adds `backdrop-filter: blur(2px)` on `.palette-overlay` plus item highlights;
PR #108 adds `.stale-ribbon` and `.state-notice` state changes. Neither honours the
preference, and neither author would think to add it — motion is a property of the
sheet, not of their feature.

**Fix:** `a11y.css` §5 — `--motion-duration: 140ms` on `:root`, forced to `0ms` inside
`@media (prefers-reduced-motion: reduce)`. Every new transition should be written
`transition: … var(--motion-duration) …`, so honouring the preference is automatic
rather than remembered. `.pill` is converted as the worked example, and `.skip-link`
is built on it from the start.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

`0.01ms` rather than `0s` deliberately: `transitionend`/`animationend` still fire, so
any JS that waits on them does not hang. The `!important` is scoped to exactly these
four properties and never touches outline, opacity or colour — a reduced-motion user
must still get every focus ring and every state cue.

---

### A11Y-11 — No screen-reader-only utility; no live region for result counts · **fixed (utility) / handed off (palette)**

**File:** `web/src/` — pre-fix: no `.sr-only`, no `aria-live`, no `role="status"`
anywhere in 27 source files.

Two symptoms. The `<th scope>`/`<caption>` gaps in A11Y-06 had nowhere to live. And
the palette's "N of M" count (§5, HANDOFF-02) exists only in `.palette-foot`, which is
a `<div>` of `<kbd>` hints — visually useful, completely silent.

**Fix:** `.sr-only` added in `a11y.css` §4 (the clip-rect pattern, not `display:none`,
so AT still reads it) and consumed by `Table`'s `caption` prop.

`prefersReducedMotion()` / `motionDuration()` in `a11y.js` give JS-driven motion the
same answer as §5 gives CSS, defaulting to **reduce** when `matchMedia` is missing or
throws: the safe failure mode for a motion preference is less motion.

---

## 2. What was verified, and how

```bash
cd mem20controlz/mem20controlz/web
node --test test/        # 25 tests, 25 pass
npx vite build           # 58 modules, built clean
```

- **`node --test` — 25/25 pass.** Covers tab order (visibility filtering, positive
  `tabindex` precedence, `tabindex=-1` exclusion), wrap-around arithmetic including
  recovery from "nothing focused", trap targets at both edges with the middle left to
  the browser, containment, focus restore with a removed opener, the screen-reader
  result sentence, reduced-motion with a missing/throwing `matchMedia`, and WCAG
  contrast for the exact six tokens this branch ships.
- **Contrast is asserted, not asserted-by-comment.** `status pill tokens clear WCAG AA
  on every shell surface` recomputes all six pills against all four surfaces from
  their literal hex values. Reverting a token re-fails the suite.
- **`vite build` clean** — the only new imports are `a11y.js`, `a11y.css` and
  `FocusTrap.jsx`; no new dependencies (`package.json` untouched, still React + Vite).

**Not verified here, and why:** no browser/AT pass was run. This sandbox cannot reach
`127.0.0.1:8221` or `mem20.jaysonai.online` (`HTTP 000` — the domain's CNAME points at
`bythewayz66-glitch.github.io`, which is a Pages alias, not this API), so the console
cannot be booted against live data. Everything above is source-level and
computation-level verifiable; a real NVDA/VoiceOver pass against a running backend
belongs to whoever can reach the API — see HANDOFF-03.

---

## 3. The focus contract (why a trap, and what it does)

`web/src/a11y.js` holds the decisions, `web/src/components/FocusTrap.jsx` holds the
React plumbing. Split deliberately: the part worth testing is arithmetic, and it is now
tested under plain `node` with no jsdom.

| Step | Rule |
|---|---|
| On open | Capture `document.activeElement`; focus `initialFocus` if it is inside, else the first tab stop, else the container itself (given `tabindex="-1"` so a still-loading dialog is not a focus black hole). |
| Tab / Shift-Tab | Wrap only at the two edges (`trapTarget()` returns `null` in the middle, so native order — including IME candidate windows and text-selection Tab — is untouched). |
| Focus escapes | `focusin` outside the container pulls focus back. Covers portals, browser find, and a stray `autofocus` in the page behind. |
| Escape | Handled on the container and `stopPropagation()`-ed, so an Escape meant for the palette does not also clear a filter in the tab behind it. |
| On close | Restore to the opener; if the opener is gone (a row that refetched away, a command that navigated), use the caller's fallback; never `document.body`. |

Hand-rolled rather than `<dialog>`/`showModal()` or a library: the shell has zero UI
dependencies by design, and `showModal()` cannot be driven from the focus-on-open path
the palette needs. One trap for both modals so they cannot drift.

---

## 4. Files changed

| File | Change |
|---|---|
| `web/src/a11y.js` | **new** — pure focus/trap/announce/contrast/reduced-motion logic, React- and DOM-free |
| `web/src/a11y.css` | **new** — every visual change of this pass: AA tokens for the six status pills and `--text-faint`, global `:focus-visible` ring + forced-colors fallback, `.sr-only`, `.skip-link`, `--motion-duration` + reduced-motion block. `styles.css` is deliberately **not modified** — #108 and #109 both append to it |
| `web/src/components/FocusTrap.jsx` | **new** — the shared modal container |
| `web/test/a11y.test.js` | **new** — 25 `node --test` cases |
| `web/src/components/LoginGate.jsx` | dialog semantics, trapped+restored focus, ref instead of `autoFocus`, `role="alert"` error, `aria-invalid`/`aria-describedby` |
| `web/src/components/ui.jsx` | `TabBar` roving tabindex + arrow keys; `Table` keyboard-activatable rows, `aria-selected`, `<th scope>`, caption |
| `web/src/components/StatusPill.jsx` | reason mirrored into `aria-label` |
| `web/src/App.jsx` | skip link + focusable `<main id="main-content">` |
| `web/src/main.jsx` | imports `a11y.css` after `styles.css` |

`package.json` and `package-lock.json` are **untouched** — no new dependencies.
`web/src/styles.css` is **untouched** — see the note in §6 on why every rule lives in
`a11y.css` instead.

---

## 5. Contracts handed off (not edited here)

Both target branches are open and unmerged, so editing their files would guarantee a
conflict on a surface this branch does not own.

### HANDOFF-01 — live status announcement (owner: whoever lands #39)

`StatusPill` has no `role="status"`. On the topbar, status changes between polls are
silent. Once #39's `StateNotice`/`lifecycle.js` is in `main`, wrap the topbar pill in
`aria-live="polite"` **and** check for double-announcement with `ErrorBanner`'s existing
`role="alert"` — that is why this was not done blind here. Use
`resultAnnouncement()`-style stable strings: an announcement that changes on every render
re-reads on every render.

### HANDOFF-02 — palette announcement order + backdrop trap (owner: #109, PR #109)

`components/CommandPalette.jsx` on `feat/38-command-palette` is closer than the brief
assumed. Verified reading:

- `aria-activedescendant` is present (`:146`) and `role="listbox"`/`role="option"` with
  `aria-selected` are correct. **That part works.**
- The panel is `role="dialog" aria-modal="true"` (`:112`) — but **nothing traps focus**.
  `Tab` from `.palette-input` walks out of the palette into the page behind it, which is
  still tabbable under the backdrop. This is the real defect, not announcement order.
- **The count is visual-only.** `.palette-foot` (`:178-190`) renders
  `{results.length} of {commands.length}` in a plain `<div>`; the `<kbd>` hints beside it
  are decorative. A screen-reader user is told the active option by
  `aria-activedescendant` but never learns the query narrowed the list to 3 of 12 — which
  is exactly why Enter can feel arbitrary.
- `Escape` is handled on the input (`:96`), so it only works while the input has focus —
  fine once the trap guarantees the input always has focus, broken today.

**Required change:** replace the outer `div.palette-overlay` + inner `div.palette` pair
with `<FocusTrap className="palette" role="dialog" labelledBy="palette-input-label"
initialFocus={inputRef.current} onEscape={onClose} restoreFallback={triggerRef}>` from
this branch, and render `<span className="sr-only" role="status" aria-live="polite">
{resultAnnouncement({total: commands.length, shown: results.length, active,
title: results[active]?.command.title})}</span>` inside it. Both helpers already exist
in `a11y.js` and are tested. Note the trap sets `aria-modal` itself — do not also set it
on the overlay.

### HANDOFF-03 — browser + AT verification (needs API reach)

No automated pass can prove announcement *order* or that a trap feels right; that needs
NVDA (Windows) or VoiceOver (macOS) against a running control plane. Blocked on the same
thing everything else is: `:8221` is loopback-only and the published domain does not
resolve to this API. Cheapest path is `ssh -L 8221:127.0.0.1:8221` from a host that can
reach the box, then walk: login gate → Tab cycle → panel switch → a `Dreams → Review`
drill-down → palette open/close with focus restoration.

---

## 6. Why nothing in `styles.css` changed

The obvious place for the token and focus-ring fixes is `styles.css` itself. This
branch puts all of them in `a11y.css` (imported last, so equal specificity resolves in
its favour) instead, for one concrete reason: **#108 and #109 both append to the foot of
`styles.css`** — verified with `git diff --name-only main origin/fix/39-offline-
degraded-ux -- .../web` and the same for `feat/38-command-palette`. Both are open,
neither is merged, and a six-line edit in the middle of that file conflicts with both.
A new file cannot conflict with anything.

The trade-off is honest: the old values still read as the shipped ones in `styles.css`,
overridden one layer up. That is visible in DevTools as two competing declarations, and
the right cleanup is a follow-up that deletes the dead tokens from `styles.css` once
#108 and #109 have landed. The audit keeps the pre-fix line numbers so that cleanup is
mechanical. `--motion-duration` has to be redefined on `:root` in `a11y.css` rather than
edited in place for the same reason.

## 7. Reproduce the measurements

Every ratio in §1 is recomputed by the shipped test. To print them:

```js
// node --input-type=module
import { contrastRatio, composite } from "./mem20controlz/mem20controlz/web/src/a11y.js";
console.log(contrastRatio("#93a4b5", composite("#93a4b5", 0.12, "#121b25")).toFixed(2));
```

Or just run the suite — a failing token names the surface and the ratio:

```bash
cd mem20controlz/mem20controlz/web && node --test test/
```
