# mem20 design system — "Solid / Dashed"

One shared system for **mem20.com** (`docs/index.html`) and **shop.mem20.com**
(`mem20shopz/mem20shopz/static/`). Vanilla HTML/CSS/JS, no build step, no external images.
This document is opinionated on purpose. If a choice isn't covered here, pick the louder
option that is still honest.

---

## 1. Brand personality

**A gleeful auditor.** mem20 has the energy of an arcade lobby and the conscience of a
ledger. It's loud about what it can prove and quiet about what it can't.

| We are | We are not |
|---|---|
| Energetic: big type, saturated accents, things that move when you touch them | Corporate-grey, "enterprise-ready" filler |
| Playful with *form*: tilt, glow, marquee, confetti on a real event | Playful with *facts*: fake urgency, invented numbers, "Hot!" badges |
| Precise: mono labels, tabular numbers, sources linked | Vague: "thousands of", "best-in-class" |

**What we borrowed, and how we changed it**

- **goatspins.com** (social-casino lobby): deep indigo night background, gold display
  headings, chunky glowing primary buttons, game tiles that show an info strip (volatility, RTP)
  *on the tile*, category lobbies. → We use the **tile-with-facts-strip** layout for products
  and domains. The "jackpot ticker" becomes a **counter driven by real data** (`surface.json`,
  `/api/*`), never a made-up figure.
- **bestbuy.com**: a deal banner at the top ("Black Friday Doorbusters"), badge-heavy product
  cards, yellow price tags, category chips, a cart button that always feels close. → We keep the
  **badge-rich card** and **chip filters**. Badges can only state facts the API returns
  (Buyable / Price not set / Checkout paused). There's no cart, so we don't fake one; the Buy
  button gets the "cart-feel" micro-interactions instead.
- **linear.app**: a live product UI as the hero (an issue with an activity feed), numbered
  figure captions ("Fig 0.1"). → Each page's hero is a **working diagram of the product**.
  Sections get `FIG 01…` mono kickers.
- **gumroad.com**: one huge counter ("$1,931,244 earned last week"), a chip cloud of
  categories, bold flat color blocks. → The big counter on the "surface, measured" section,
  plus the domain chip cloud and marquee.
- **vercel.com / stripe.com**: infinite marquee strips, soft animated gradient meshes behind
  the hero. → The domain marquee and the hero glow.

### The signature: Solid = real, Dashed = not (yet) real

This is the brand's one rule ("grounded facts and simulated hypotheses never mix"), turned into
a visual grammar used **everywhere, on both sites**:

| Meaning | Treatment |
|---|---|
| **Solid / grounded**: observed, priced, live, verified | Solid 1px border, filled tag, **filled** dot `●`, check glyph `✓`, teal `--grounded` |
| **Dashed / simulated**: inferred, unpriced, dry-run, in development | 1.5px **dashed** border, 45° hatch background, **hollow** ring `○`, tilde glyph `~`, amber `--simulated`, text at `--text-2` |

Rules:
1. Only use dashed styling for things that aren't real or working yet. Never use it as
   decoration.
2. Something can only become solid when a source backs it: a live API field, `surface.json`,
   or copy that is already on the page.
3. **Pulse = polled.** An animated pulse only appears on something JS actually checks on a
   timer (the shop's live dot). The static "Live" cards on mem20.com get a solid dot that
   doesn't pulse.
4. Decorative animation (hero lattice, pipeline) never shows numbers. Every number on screen is
   real.

Concrete mappings: shop **dry-run provisioning** = dashed (nothing is created, so it's
simulated). **Price not set** = dashed ghost price. mem20.com **"In development" domains
note** = dashed callout. The **simulated panel** in "The one rule" = dashed and hatched.

---

## 2. Color

Dark is the default. Light follows `prefers-color-scheme` and can be overridden with
`html[data-theme]`. Both sites use the same localStorage key, `mem20-theme`.

| Token | Dark | Light | Use |
|---|---|---|---|
| `--bg` | `#090A14` | `#F6F6FB` | page |
| `--bg-2` | `#0E1020` | `#EEEEF7` | bands, footer, code |
| `--surface` | `#141730` | `#FFFFFF` | cards |
| `--surface-2` | `#1B1F3D` | `#F3F3FA` | nested, chips |
| `--line` | `#262B4F` | `#DCDDEB` | borders |
| `--line-2` | `#3A4170` | `#C3C5DA` | hover borders |
| `--text` | `#F1F3FF` | `#12142B` | body |
| `--text-2` | `#C3C8E6` | `#3D4266` | secondary |
| `--muted` | `#8E95BD` | `#5A6088` | labels (≥4.5:1 on surface) |
| `--grounded` | `#2FD4C4` | `#0B7A70` | grounded / brand primary |
| `--simulated` | `#F5B841` | `#9A6200` | simulated / dry-run / unpriced |
| `--pop` | `#FF5C8A` | `#D6336C` | energy accent: highlights, focus glow, marquee dots |
| `--violet` | `#8B7CFF` | `#5B4BE0` | secondary accent, gradients |
| `--gold` | `#FFD84D` | `#8A6A00` | display highlight (goatspins nod), counters |
| `--ok` | `#3DDC97` | `#0F7A4C` | status ok |
| `--warn` | `#FF9A3D` | `#A8540A` | status warn |
| `--bad` | `#FF6B6B` | `#C02B2B` | status bad |

`--grounded` doubles as the brand color, since grounded is what we sell. Use `--simulated`
amber **only** for things that are simulated or absent. Status warnings get orange `--warn`
so the two meanings never collide.

Signature gradient `--grad-hero: linear-gradient(100deg, var(--grounded), var(--violet) 55%, var(--pop))`
goes on hero headline highlights and primary-button hover glow. Nowhere else.

Contrast was checked for both themes. Light-theme accents are darkened so they reach 4.5:1 or
better on white (teal 5.2, amber 5.1, pop 4.6). Text on filled `--grounded` buttons uses
`#04181A` in dark and `#FFFFFF` in light.

---

## 3. Type, spacing, radii, shadows

**Fonts (Google Fonts, a single request, `display=swap`):**
- Display: **Bricolage Grotesque** 600–800. Quirky and confident, with an optical-size axis.
  This replaces Space Grotesk, which is the main source of the "bland" feel.
- Body: **Inter** 400–700.
- Mono: **JetBrains Mono** 400–600, used for labels, chips, numbers and code.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Inter:wght@400..700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```
Fallbacks are in the tokens. If the shop server ever adds a CSP that blocks Google Fonts, the
system stacks still look intentional, because weight and size carry the hierarchy.

**Scale** (fluid, 1.25 ratio):
| Token | Value | Use |
|---|---|---|
| `--fs-hero` | `clamp(2.6rem, 6.4vw, 5rem)` | h1, display 800, `-0.04em` |
| `--fs-h2` | `clamp(1.8rem, 3.6vw, 2.75rem)` | section titles, display 700 |
| `--fs-h3` | `1.25rem` | card titles, display 700 |
| `--fs-stat` | `clamp(2.75rem, 6vw, 4.5rem)` | counters, display 800, tabular |
| `--fs-lede` | `clamp(1.05rem, 1.5vw, 1.25rem)` | |
| `--fs-body` | `1rem` / 1.65 | |
| `--fs-sm` | `.875rem` | card copy |
| `--fs-label` | `.72rem`, mono, `.12em` tracking, uppercase | kickers, badges |

**Spacing:** a 4px base, `--s-1`…`--s-10` = 4, 8, 12, 16, 24, 32, 48, 64, 96, 128. Sections get
`--s-9` vertical padding (`--s-8` on mobile). Card padding is `--s-5`. Grid gap is `--s-4`
on mobile and `--s-5` on desktop.
**Radii:** `--r-sm 8px` (chips, inputs), `--r 16px` (cards), `--r-lg 24px` (hero panels, big
tiles), `--r-pill 999px`.
**Shadows:** tinted, never pure black. `--sh-1` is resting, `--sh-2` is hover lift, and
`--sh-glow` is a colored halo for the primary CTA and the focused card.

---

## 4. Tokens — paste this block

Each site keeps its own identical copy at the top of its stylesheet (no shared CDN):
- mem20.com: new file `docs/assets/mem20-ds.css`
- shop: top of `static/style.css`

Edit both copies together. This section is the source of truth.

```css
:root{
  color-scheme: dark light;
  --bg:#090A14; --bg-2:#0E1020; --surface:#141730; --surface-2:#1B1F3D;
  --line:#262B4F; --line-2:#3A4170;
  --text:#F1F3FF; --text-2:#C3C8E6; --muted:#8E95BD;
  --grounded:#2FD4C4; --simulated:#F5B841; --pop:#FF5C8A; --violet:#8B7CFF; --gold:#FFD84D;
  --ok:#3DDC97; --warn:#FF9A3D; --bad:#FF6B6B;
  --on-grounded:#04181A;
  --grounded-soft:color-mix(in srgb,var(--grounded) 12%,transparent);
  --simulated-soft:color-mix(in srgb,var(--simulated) 10%,transparent);
  --hatch:repeating-linear-gradient(45deg,var(--simulated-soft) 0 6px,transparent 6px 12px);
  --grad-hero:linear-gradient(100deg,var(--grounded),var(--violet) 55%,var(--pop));
  --glow-bg:radial-gradient(60% 50% at 20% 0%,color-mix(in srgb,var(--violet) 22%,transparent),transparent 70%),
            radial-gradient(50% 40% at 90% 10%,color-mix(in srgb,var(--grounded) 16%,transparent),transparent 70%);

  --font-display:'Bricolage Grotesque','Inter',ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;
  --font-body:'Inter',ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --font-mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --fs-hero:clamp(2.6rem,6.4vw,5rem); --fs-h2:clamp(1.8rem,3.6vw,2.75rem); --fs-h3:1.25rem;
  --fs-stat:clamp(2.75rem,6vw,4.5rem); --fs-lede:clamp(1.05rem,1.5vw,1.25rem);
  --fs-body:1rem; --fs-sm:.875rem; --fs-label:.72rem;

  --s-1:4px; --s-2:8px; --s-3:12px; --s-4:16px; --s-5:24px; --s-6:32px;
  --s-7:48px; --s-8:64px; --s-9:96px; --s-10:128px;
  --r-sm:8px; --r:16px; --r-lg:24px; --r-pill:999px;
  --maxw:1200px; --nav-h:64px;

  --sh-1:0 1px 0 rgba(255,255,255,.04) inset,0 10px 30px -18px rgba(3,4,20,.9);
  --sh-2:0 1px 0 rgba(255,255,255,.06) inset,0 24px 48px -20px rgba(3,4,20,.95);
  --sh-glow:0 0 0 1px color-mix(in srgb,var(--grounded) 50%,transparent),
            0 10px 40px -8px color-mix(in srgb,var(--grounded) 55%,transparent);

  --ease-out:cubic-bezier(.2,.8,.2,1); --ease-spring:cubic-bezier(.34,1.56,.64,1);
  --t-fast:120ms; --t:200ms; --t-slow:320ms; --t-reveal:600ms;
}
@media (prefers-color-scheme: light){ :root:not([data-theme="dark"]){
  --bg:#F6F6FB; --bg-2:#EEEEF7; --surface:#FFFFFF; --surface-2:#F3F3FA;
  --line:#DCDDEB; --line-2:#C3C5DA; --text:#12142B; --text-2:#3D4266; --muted:#5A6088;
  --grounded:#0B7A70; --simulated:#9A6200; --pop:#D6336C; --violet:#5B4BE0; --gold:#8A6A00;
  --ok:#0F7A4C; --warn:#A8540A; --bad:#C02B2B; --on-grounded:#FFFFFF;
  --sh-1:0 1px 2px rgba(18,20,43,.06),0 10px 24px -16px rgba(18,20,43,.25);
  --sh-2:0 2px 4px rgba(18,20,43,.06),0 22px 40px -18px rgba(18,20,43,.35);
}}
:root[data-theme="light"]{ /* same values as the light block above — duplicate them here */ }
```

---

## 5. Components

The class names below are the shared vocabulary. Wherever possible, mem20.com keeps its existing
class names (`nav`, `.nav-links`, `.foot-links` are **required**, because `series/analytics.js`
uses them to classify clicks).

**5.1 Nav with status dot.** Sticky, 64px, `backdrop-filter: blur(14px)` over 80% `--bg`. The
logo mark is a 28px rounded square with `--grad-hero` and a lowercase "m". On hover it rotates
-8° with a spring. The shop logo reads `mem20` plus a pill reading `.shop`. Both navs carry a
cross-link to the other site, so the two finally feel like one place.
- **Status pill** (`.live` + `.dot`): mono 12px, pill, `--surface` background.
  - Shop: the existing `#live/#dot/#live-text`, polled, so `.dot.ok` pulses (2.4s ring).
  - mem20.com: a new pill that reports how the `surface.json` fetch went: `● surface.json
    pinned` (solid, no pulse) if it loaded, `○ static fallback` (hollow) if it didn't.
- Scroll state: once `scrollY > 8`, add `.is-scrolled`. That gives a hairline bottom border and
  `--sh-1`.
- Mobile (<760px): links go into a slide-down sheet behind a 44px burger button
  (`aria-expanded`). The status pill stays visible.

**5.2 Buttons.** Height 44px (40 for `-sm`), `--r-sm`+2, display font 600.
- `.btn-primary`: filled `--grounded`, text `--on-grounded`. On hover it lifts 2px, gains
  `--sh-glow`, and a gradient sheen sweeps across once (a `::after` with a 120% wide
  transparent→white 25%→transparent band, translateX over 600ms). On `:active` it goes to
  `scale(.97)` over 80ms.
- `.btn-ghost`: 1px `--line-2`. On hover the border turns `--grounded` and the text turns
  `--text`.
- `.btn.is-off` / `[disabled]`: **dashed** border, `--muted` text, hatch background,
  `cursor: not-allowed`, no hover motion. This is the motif applied to buttons.
- Arrow links (`.go`): the trailing `→` moves 4px right on hover.

**5.3 Badges / tags** (`.badge`, mono `--fs-label`, pill, 4px/10px padding):
- `.badge.g` grounded: `--grounded-soft` background, solid border, `✓` prefix.
- `.badge.s` simulated: transparent background, **dashed** border, `~` prefix.
- `.badge.live`: solid `●` dot. It only gets `.pulse` when polled (rule 3).
- `.badge.ok / .warn / .bad`: for status.
- `.badge.kind`: neutral, for the shop SKU kind.
Allowed shop card badges: **Buyable**, **Price not set**, **Checkout paused**, plus the API
`kind`. Banned anywhere: "Best seller", "Popular", "Hot", "Limited time", "Only N left", "Sale",
star ratings, strikethrough prices. None of those is backed by data.

**5.4 Hero with an animated visual.** A two-column grid (1.1fr copy, 0.9fr visual). Below
900px it stacks, with the visual under the CTAs and capped at 280px tall. The background is
`--glow-bg` plus a 28px dot-grid (`radial-gradient` 1px dots, 6% opacity), masked to fade at
the bottom. The h1 highlight uses `--grad-hero` text, with a slow `background-position` drift
(12s, alternate).
- **mem20.com: "memory lattice" canvas** (`<canvas aria-hidden="true">`, about 2KB of JS). It
  shows 14–18 nodes on a soft force layout. **Grounded nodes** are filled teal discs with solid
  edges. **Simulated nodes** are hollow amber rings with dashed edges (`setLineDash([4,4])`).
  Every 2.5s a "retrieval" pulse (a `--pop` comet) travels from a query node along edges. Nodes
  it touches flash, but simulated nodes **stay** hollow, so the two never merge. Small labels
  read `grounded` and `simulated` only. No numbers. Pointer movement nudges the nodes (parallax
  of 6px or less). It pauses when off-screen (IntersectionObserver) and on `document.hidden`.
  Under reduced motion it draws one static frame.
- **Shop: "order pipeline" SVG** (inline, about 1.5KB). Four stations in a row:
  `Checkout → Stripe confirms → Signed webhook → Provisioning`. A dot travels the path on a 3s
  loop, using CSS `offset-path`. The last station reflects the real readiness state (see 7.2):
  solid teal with `✓` when the shop can provision, dashed amber with `~ dry-run` when it can't.

**5.5 Stat counters** (`.stat`, `[data-count]`).
- Real numbers stay **hard-coded in the HTML**. The no-JS fallback and the doc-count drift gate
  depend on them. Keep `id="tile-tools"` and the others as they are.
- `count.js`: when the stat enters view, it animates from 0 to the element's *current*
  `textContent` (after `surface.json` has filled it) over 900ms using easeOutExpo, with
  `font-variant-numeric: tabular-nums` and a fixed `min-width` in `ch` so nothing shifts.
- The element gets `aria-label` set to the final value, and the animating text is
  `aria-hidden`. Screen readers never hear a number that is only on its way to the real one.
- Under reduced motion there's no animation: the final value just shows.
- Non-numeric tiles (`v4.0.0`, `Apache-2.0`) don't count. They "stamp" in instead (scale 1.15→1
  with the spring).

**5.6 Cards: hover, tilt, spotlight.** Base: `--surface`, 1px `--line`, `--r`, `--sh-1`.
- On hover: lift 4px, border turns `--line-2`, shadow goes to `--sh-2`, and a **spotlight**
  appears: a `::before` radial gradient of 240px, `--grounded` at 10%, at
  `(var(--mx), var(--my))`.
- **Tilt** (shared `fx.js`): rotateX/Y up to **4°**, `perspective: 900px`, eased back on leave.
  It's enabled only under `(hover:hover) and (pointer:fine)` and without reduced motion. Use
  **one delegated `pointermove` listener on the container**, so cards the shop re-renders keep
  working. Writes go through `requestAnimationFrame`, and only CSS vars are set (`--rx --ry --mx
  --my`).
- `.card.is-sim` (dashed motif): dashed 1.5px `--simulated` border at 60%, hatch on the top
  strip, no tilt. It shouldn't feel solid.
- **Lobby tile** (goatspins nod), used for Running products and shop SKUs: a 6px colored top
  band (`--grounded` live, hatched when not), a kicker row, the title, the copy, and a **facts
  strip** at the bottom (`.tile-facts`, mono, `--surface-2`, separated by `·`) that holds only
  existing facts (for example `port 8891`, `Live`).

**5.7 Marquee / ticker of domains** (`.marquee`).
- One or two rows of real domain chips taken from the estate copy (for example `memory`,
  `cognitive`, `world`, `kilnz`, `braid`, `irc`, …). The second row runs in reverse.
- Pure CSS: the track holds the list twice (the duplicate gets `aria-hidden="true"`) and
  animates `translateX(-50%)` over 40s linear infinite. Edges fade with
  `mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent)`.
- It pauses on hover and on `:focus-within`. Chips are separated by a `--pop` `◆`.
- Under reduced motion: no animation, and the row becomes a horizontally scrollable strip.
- It's decorative, so the first copy has `role="list"` with the label "Sample of domains". The
  full list stays in the Estate section.

**5.8 Scroll reveal.** Elements with `.reveal` start at `opacity:0; translateY(16px)`, **but only
under `html.js`**. An inline `<head>` snippet sets `document.documentElement.classList.add('js')`,
so without JS everything is visible. An IntersectionObserver (threshold .15, rootMargin `0 0 -10%`)
adds `.is-in`. That runs `--t-reveal` with `--ease-out`, and children stagger by 60ms via
`--i`. The observer fires once per element, then unobserves. Under reduced motion everything is
visible immediately.

**5.9 Sticky CTA.**
- mem20.com: a bottom-docked bar, shown after the hero scrolls out and hidden near the footer.
  It holds `Read the source` (primary) and `Install from PyPI` (ghost). It's a frosted pill,
  centered, with a 12px gap above the safe-area inset (`env(safe-area-inset-bottom)`). It's
  dismissible (×, remembered in sessionStorage).
- Shop: on mobile only, a bottom bar with a compact copy of the live pill (mirrored from
  `#live-text` with a MutationObserver) and `Browse the catalog`. It's hidden while `#catalog`
  is on screen.

**5.10 FAQ accordions** (`details/summary`, no JS).
Each item is a card with `--r` and 18px/20px padding. The summary is display font 600, with a
custom `+` icon (a CSS cross from two pseudo bars) that rotates 45° into `×` when `[open]`. The
default marker is hidden. As progressive enhancement, open/close animates with
`:root{interpolate-size:allow-keywords}` and `details::details-content{block-size:0;
overflow:clip; transition:block-size var(--t-slow), content-visibility var(--t-slow)
allow-discrete}` / `[open]::details-content{block-size:auto}`. Browsers without support toggle
instantly. The open item gets a 3px `--grounded` left rail.

**5.11 Chips & filter chips.** `.chip` is mono 12px, `--surface-2`, `--r-sm`. A filter chip is
a `<button aria-pressed>`. Pressed means filled `--grounded` with `--on-grounded` text, and
pressing it plays a small spring scale (1→1.06→1). Each chip carries a count badge, and the
**count is computed from the DOM**, never typed in by hand.

**5.12 Callouts.** `.note` (grounded, solid left rail) and `.note.is-sim` (dashed outline,
hatch, `~` icon) for anything about non-working or not-yet-real things.

**5.13 Toast** (shop `#notice`): see 7.2.

**5.14 Code / terminal.** A window frame with three dots (pop, gold, grounded), the title
`bash`, and a copy button (`navigator.clipboard`, label swaps to "Copied ✓" for 1.6s,
`aria-live`). Comments in `--muted`, commands in `--text`, the prompt in `--grounded`.

**5.15 Theme toggle.** A 40px icon button in the nav (sun/moon inline SVG). It sets
`html[data-theme]` and stores the choice in localStorage `mem20-theme`. An inline head script
applies the theme before first paint, to avoid a flash.

---

## 6. Motion rules

1. **Durations:** micro 120ms (press, color), UI 200ms (hover, chips), panels 320ms
   (accordion, sheet), reveals 600ms. Nothing longer than 900ms except ambient loops.
2. **Easing:** `--ease-out` for entering and hover, `--ease-spring` only for small "stamps"
   (chips, badges, the logo, the Buy press). Use `linear` only for marquees and the pipeline dot.
3. **Only animate `transform`, `opacity` and `filter`.** No layout properties. The accordion
   `block-size` animation is the one sanctioned exception.
4. **Ambient loops** (lattice, marquee, gradient drift, pipeline, live pulse): at most 3 visible
   at once. All of them pause when off-screen or the tab is hidden.
5. **Animate on first appearance only.** Re-renders don't replay entrances (this matters for the
   shop's 10s poll; see 7.2).
6. **Motion carries meaning.** Pulse means polled. Confetti means a real state change to "open".
   A shake means a real failure.
7. **Reduced motion.** Put this block at the end of each stylesheet. JS also checks
   `matchMedia('(prefers-reduced-motion: reduce)')` before starting the canvas, counters, tilt
   and confetti.
```css
@media (prefers-reduced-motion: reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;
    transition-duration:.001ms!important}
  .reveal{opacity:1!important;transform:none!important}
  .marquee-track{animation:none!important;transform:none!important}
  .marquee{overflow-x:auto}
}
```

---

## 7. Page plans

Rule for both pages: **every existing sentence, link, number and ID stays**. We re-skin and
re-stage the content. We add no new claims. Any new microcopy is either structural (button
labels like "Copy" or "All") or derived at runtime from real data.

### 7.1 mem20.com (`docs/index.html`)

Files: `docs/assets/mem20-ds.css` (tokens plus components, target under 22KB unminified) and
`docs/assets/mem20-fx.js` (reveal, counters, tilt, lattice, marquee pause, sticky CTA, theme,
chip filter; target under 9KB). **Stop loading `series/series.css` on the landing page only.**
The series pages keep it untouched. Keep the analytics, Plausible and gh-exp-001 scripts, and the
inline `surface.json` loader, exactly as they are.

Must-keep IDs: `tile-tools, tile-domains, big-tools, big-domains, big-unwired, crosscheck,
largest-domains, docs`. Keep the crosscheck sentence on a single line (the drift gate reads it).

| # | Section | Treatment / delight |
|---|---|---|
| 0 | Nav | 5.1, with the surface.json status pill, a theme toggle, a GitHub primary button, and a `Shop ↗` link |
| 1 | Hero | Eyebrow as a mono badge. H1 at `--fs-hero`, with "prove what it knows." in the drifting gradient. Lattice canvas on the right. The three CTAs. The four facts become **stat tiles**: 527 and 135 count up, `v4.0.0` and `Apache-2.0` stamp in. Each tile has a 2px teal top line that draws in from left to right. |
| 2 | Domain marquee | Two reversed rows of real domain chips (5.7), in a full-bleed `--bg-2` band. |
| 3 | The one rule (`FIG 01`) | The signature moment. The two panels sit side by side with a 2px vertical **seam** between them that glows `--pop` on hover. The grounded panel is solid with a `✓ grounded` badge. The simulated panel is dashed and hatched with a `~ simulated` badge, and its heading text is set at `--text-2`. On hover a panel lifts, but they **never overlap or blend**. On mobile they stack, and the seam becomes horizontal. |
| 4 | The surface, measured (`FIG 02`) | Left: the three big numbers as Gumroad-scale counters (`--fs-stat`, gold for tools, violet for domains, simulated-amber for "0 unwired", which the current page already shows). Right: the largest-domains table keeps `<table>` semantics. Each row gets a CSS bar (`td::before`, width = `count / max`, computed in JS after `surface.json` fills the rows) that grows in on reveal. The source line becomes a mono receipt strip with a `✓` stamp. |
| 5 | Three layers (`FIG 03`) | Three cards in dependency order, connected by an animated dashed→solid line (an SVG `stroke-dashoffset` draw on reveal). Big outlined numerals `01 02 03` (text-stroke) sit behind each card. |
| 6 | The estate (`FIG 04`) | **Filter chips** for the 9 families plus "All", each with a DOM-computed count, and a small search input that highlights matching domain chips and dims the rest. Family cards become lobby tiles, each with its own accent band (cycling grounded, violet, pop, gold). Domain chips are clickable with no destination: hovering one shows its full name. The "Two different counts" note stays a grounded callout. The "In development" note becomes **`.note.is-sim`** (dashed), with the three domain names shown as dashed chips. |
| 7 | Running products (`FIG 05`) | **Lobby tiles** in a 4-column grid (2 on tablet, 1 on mobile). Each has a solid `● Live` badge (no pulse) and a facts strip with the port from the copy. Control plane and Shop get a "Visit ↗" button that uses the existing link. The others have no link, as today. |
| 8 | Docs & plans (`#docs`) | A 3×3 grid of cards, each with a colored kicker and a 32px inline-SVG glyph per category (pricing tag, chart, megaphone, slides, briefcase, book ×2, gauge, braces). Hover: tilt plus spotlight, and the arrow nudges. |
| 9 | Run it | The terminal window (5.14) with a copy button. On first reveal, lines type in at 18ms per character, then the full static text is in place. Under reduced motion and without JS, the text is just there. "On the numbers" becomes a grounded callout. |
| 10 | Two series | Two big art cards with CSS-only art. The comic card gets a halftone (`radial-gradient` dots), an ink frame and amber-to-orange. The chronicles card gets a blueprint grid with teal and blue. On hover the art pans 8px. Copy is unchanged. |
| 11 | Footer | `.foot-links` unchanged, the logo, a theme toggle, and the existing foot note. |
| — | Sticky CTA | 5.9 |

Performance: this is a single HTML page. CSS and JS are loaded as files (`defer`). The canvas
holds at most 18 nodes, renders at 30fps or less, and stops when off-screen. Total page weight
excluding fonts should stay under 90KB. Don't use `will-change` on more than the hero and the
marquee.

### 7.2 shop.mem20.com (`static/index.html`, `style.css`, `app.js`)

**Contract that must not break:** the IDs `live, dot, live-text, main, status-link, status,
mode-pill, status-body, notice, activity, activity-total, activity-list, catalog, catalog-note,
groups`. The classes app.js writes: `dot ok|warn|bad`, `pill ok|warn`, `check on|off`, `checks`,
`reasons`, `card`, `kind`, `desc`, `why`, `card-foot`, `price`, `price none`, `btn btn-primary`,
`btn is-off`, `group`, `group-head`, `cards`, `when outcome-ok|outcome-bad`, `muted small`. The
endpoints: `/api/readiness`, `/api/catalog`, `/api/webhooks/status`, `/api/checkout`,
`/api/health`. Keep the 10s poll and the hidden-tab behavior as they are.

**Allowed app.js changes (additive only):** in `skuCard`, set
`card.dataset.state = buyable ? "buyable" : sku.configured ? "paused" : "unpriced"`,
`card.dataset.kind = sku.kind || "product"`, and `card.dataset.sku = sku.id`. Then prepend a
`.badge` derived from `state`. Everything else lives in a new `static/fx.js` (loaded after
app.js), which **observes** the DOM and never fetches.

**Important: `#groups` is rebuilt every 10s.** That means:
- Entrance animation runs only once. fx.js sets `#groups[data-ready]` after the first render,
  and the stagger CSS is scoped to `.groups:not([data-ready]) .card`.
- Filter state lives on `#groups` (`data-filter-state`, `data-filter-group`), which survives
  `replaceChildren()`. CSS hides cards that don't match. Chip counts are recomputed in a
  MutationObserver callback (debounced with rAF).
- Tilt uses a delegated listener on `#groups` (5.6).
- Price change flash: fx.js keeps a `Map(sku → price text)`. When a card's price text differs
  from the last render, that card gets a one-shot `.flash` (a background pulse in `--gold`, 600ms).
  That's honest: it only happens when the server really changed the price.

| # | Section | Treatment / delight |
|---|---|---|
| 0 | Topbar | Same component as the mem20.com nav (5.1): logo `mem20` + `.shop` pill, a link to `mem20.com`, the theme toggle, and the existing `#live` pill (polled, pulsing). When `.dot.bad`, the pill border turns `--bad` and the dot does a single 4px shake. |
| 1 | Hero | Two columns. Copy on the left (unchanged; "not a promise of one." in the hero gradient). Order pipeline SVG on the right (5.4). fx.js watches `#mode-pill`'s class and sets `body[data-shop="open"\|"closed"]`, and the pipeline's last station switches solid/dashed through CSS. This doubles as the **deal-banner slot** à la Best Buy: a full-width strip above the hero that says "Shop open — products below are buyable" (solid teal) or "Not selling yet — see why ↓" (dashed amber), built only from the readiness state. |
| 2 | Readiness `#status` | A **scoreboard**. `.checks` becomes a 4-column grid of big tiles (2×2 on mobile). `.check.on` is a solid tile with a big `✓`, a teal top band and the label in display font. `.check.off` is a dashed hatched tile with `~` (and `dry-run` shown in amber for Provisioning, since that is simulated). `#mode-pill` is an oversized pill. `.reasons` is a list with a dashed left rail and a mono `→` bullet. When a check flips, that tile gets the spring "stamp" once (diffed in fx.js). |
| 3 | `#notice` | Styled as a **toast**: fixed bottom-right (bottom on mobile, above the sticky bar), slide-up and fade over 320ms, with a close button that fx.js injects. It keeps `hidden` semantics, and fx.js just observes `hidden`. Tone comes from the heading text: "The shop is open" gets ok plus a **one-shot confetti burst** (a canvas of 40 particles at most, 1.2s, skipped under reduced motion). "Lost contact" and "could not start" get bad, and "New payment activity" gets gold. It also stays in flow under the hero for screen readers (`aria-live` on `#status` is unchanged). |
| 4 | `#activity` | A **ticker card**. Each `li` is a pill row. When `×count` increases, the number rolls up (a translateY swap). |
| 5 | `#catalog` | Section head with `#catalog-note` unchanged, rendered as a mono receipt line. **Filter chips:** State (All · Buyable · Price not set · Checkout paused) and Group (built from `.group-head h3` text). All counts come from the DOM. Groups get sticky sub-headers (`top: var(--nav-h)`) with a colored accent bar. **Product cards are lobby tiles:** the kind badge plus the state badge in the top row, the name, the description, then the `.why` block (dashed amber, `~` icon, since it explains an absence), then a `.card-foot` facts strip. A real `.price` is set in display 800 at 1.5rem inside a **yellow price tag** (a Best Buy nod: `--gold` background, `#12142B` text, a notched left edge made with `clip-path`). `.price.none` is a dashed ghost tag with muted text. Cards with `data-state="unpriced"` or `"paused"` get `.is-sim`-style dashed borders and no tilt. |
| 6 | Buy button: cart-feel | On hover: lift plus glow, and the label slides to reveal `→`. On press: `scale(.95)` with a spring back. While app.js shows "Starting…", fx.js (watching the text) adds `.is-busy` (a shimmer sweep plus `aria-busy`). On "Try again" it gets `.is-error` (a single 4px shake, `--bad` ring). The disabled state is the dashed `.is-off` from 5.2. |
| 7 | FAQ "Straight answers" | Accordions (5.10). Copy unchanged. |
| 8 | Footer | Shared footer look: the existing tagline, the `health` link, plus `mem20.com` and the GitHub link (both exist on the main site). |
| — | Sticky mobile bar | 5.9 |

Performance: style.css stays under 20KB and fx.js under 7KB. No canvas runs except the one-shot
confetti. Every observer callback is batched with rAF.

---

## 8. Layout & mobile rules

- Container is `width: min(var(--maxw), 100% - 2*var(--s-5))`. The shop moves from 1120px up to
  1200px so the two sites match.
- Breakpoints: **≤480** (phone), **≤760** (large phone and nav collapse), **≤1024** (tablet).
  Mobile-first CSS uses `min-width` queries.
- Grids: product and lobby tiles use `repeat(auto-fill, minmax(260px, 1fr))`. Stat tiles go 4→2
  columns at ≤760. The split panels and the hero stack at ≤900.
- Tap targets are at least 44×44px. Chip rows scroll horizontally (`overflow-x:auto;
  scroll-snap-type:x proximity`) instead of wrapping into five lines.
- Tilt, spotlight and cursor parallax are off on touch. The lattice canvas renders half the
  nodes below 760px.
- Sticky elements never stack more than two deep: the nav plus one of (group header or bottom
  bar). Pad the bottom bar with `env(safe-area-inset-bottom)`.
- Hero h1 is at least 2.4rem on phones. Long domain names (`mem20productionplanning…`) get
  `overflow-wrap:anywhere` inside chips.

---

## 9. Accessibility floor (non-negotiable)

- **WCAG 2.2 AA:** body text 4.5:1 or better, large text and UI borders 3:1 or better, in both
  themes. Check every new pairing. Gold `#FFD84D` text is allowed on the dark `--bg/--surface`
  only. In light, gold appears only as a background, under `#12142B` text.
- **Meaning is never color-only:** grounded vs simulated is carried by border style (solid or
  dashed), a glyph (✓ or ~) **and** a text label. The same goes for check on/off (✓/~ plus
  "yes"/"no", which app.js already writes).
- Focus: `:focus-visible { outline: 2px solid var(--pop); outline-offset: 3px; }` on every
  interactive element. Never remove it.
- Keep the skip link (the shop already has one; add it to mem20.com). There's one `h1` per page
  and the heading order doesn't skip levels (the shop's `h4` cards sit under `h3` groups, which
  is fine).
- Filter chips are `<button aria-pressed>` inside `role="group"` with an `aria-label`. When
  filtering, update a visually hidden live region ("Showing 6 of 14 products"), with the counts
  taken from the DOM.
- Decorative canvases and SVGs get `aria-hidden="true"`, as does the duplicated marquee track.
- Counters: the final value goes in `aria-label` (5.5).
- The toast doesn't steal focus. It has a labelled close button and doesn't auto-dismiss errors.
- Everything works without JS: content and numbers are present, accordions are native
  `details`, reveal is gated on `html.js`.
- Honor `prefers-reduced-motion`, `prefers-color-scheme`, and `forced-colors: active` (where the
  dashed vs solid borders survive by design; give hatch backgrounds `forced-color-adjust:auto`).

---

## 10. Honesty checklist (run before every merge)

1. Is every number on the page from the HTML as it stands today, `surface.json`, or a live API
   field?
2. Do all dashed, hollow and `~` styles mark only simulated, unpriced, dry-run or in-development
   things?
3. Are pulse animations only on polled data?
4. Are there no banned badges (5.3), no fake urgency, no testimonials, and no logos of customers
   we don't have?
5. Does the shop never show a price that `skuCard` didn't render, and does it never make an
   unbuyable card look buyable?
6. Is every original sentence, link and ID still present? (Diff the text content before and
   after.)
