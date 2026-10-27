// Accessibility primitives for the mem20 control plane (issue: a11y pass).
//
// Everything here is React-free and DOM-free *except* the small focus helpers,
// which take an explicit element/container so they can be driven from a test with
// a stub tree. That split is deliberate: the rules that decide *what* gets focus
// (order, wrap-around, restore target) are pure data transforms and are covered by
// `node --test` in web/test/a11y.test.js without a browser or jsdom.
//
// Why a hand-rolled trap instead of a <dialog> or a library: this shell ships
// plain CSS + React with no UI dependencies (see package.json), and <dialog>'s
// showModal() cannot be driven from the focus-on-open path the command palette
// uses. One trap, used by both the palette and the login gate, so the two cannot
// drift apart.

/**
 * Selector for everything that can receive keyboard focus.
 *
 * `:not([tabindex="-1"])` matters: the palette keeps the listbox reachable by
 * aria-activedescendant, never by Tab, and a roving-tabindex list would otherwise
 * put 40 options in the tab order.
 */
export const FOCUSABLE_SELECTOR = [
  "a[href]",
  "area[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type=hidden])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "iframe",
  "audio[controls]",
  "video[controls]",
  "[contenteditable]:not([contenteditable=false])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

/**
 * Is this element visible enough to be focused?
 *
 * `getClientRects().length === 0` is the standard trick for "not rendered" and it
 * also catches `display:none` ancestors, which is exactly the case that matters
 * here: the palette's results list is empty on first open, so its listbox has no
 * boxes at all and must not be offered as a tab stop.
 */
export function isVisible(el) {
  if (!el) return false;
  if (el.hidden) return false;
  if (el.getAttribute && el.getAttribute("aria-hidden") === "true") return false;
  if (typeof el.getClientRects === "function") {
    try {
      if (el.getClientRects().length === 0) return false;
    } catch {
      // Detached nodes can throw; fall through to the attribute checks.
    }
  }
  if (typeof el.getBoundingClientRect === "function") {
    try {
      const rect = el.getBoundingClientRect();
      if (rect && rect.width === 0 && rect.height === 0) return false;
    } catch {
      /* ignore */
    }
  }
  return true;
}

/**
 * Tab stops inside `container`, in DOM order.
 *
 * Positive tabindex is honoured ahead of document order because that is what the
 * browser does; a trap that ignored it would move focus somewhere the user did not
 * expect.
 */
export function tabbables(container) {
  if (!container || typeof container.querySelectorAll !== "function") return [];
  const nodes = Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR)).filter(isVisible);
  const positive = nodes.filter((n) => Number(n.getAttribute("tabindex")) > 0);
  if (positive.length === 0) return nodes;
  const rest = nodes.filter((n) => positive.indexOf(n) === -1);
  positive.sort((a, b) => Number(a.getAttribute("tabindex")) - Number(b.getAttribute("tabindex")));
  return positive.concat(rest);
}

/**
 * Next focus index for a linear wrap-around move.
 *
 * `current < 0` (nothing focused yet, or the focused node was removed) resolves to
 * the first/last stop rather than throwing — the palette loses its active row every
 * time the query changes and must not fall over when Tab lands mid-render.
 */
export function nextFocusIndex(current, delta, count) {
  if (!Number.isInteger(count) || count <= 0) return -1;
  if (!Number.isInteger(current) || current < 0 || current >= count) {
    return delta > 0 ? 0 : count - 1;
  }
  return (current + delta + count) % count;
}

/**
 * Resolve where a Tab keydown should send focus, or `null` to let the browser do it.
 *
 * Wrapping is only claimed at the two edges; in the middle we return null so the
 * native order (which the trap mirrors exactly) stays in charge. Returning a target
 * unconditionally would break Shift-Tab inside a text field's selection, IME
 * candidates, and contenteditable.
 */
export function trapTarget({ count, index, shift }) {
  if (!Number.isInteger(count) || count <= 0) return null;
  if (index < 0) return shift ? count - 1 : 0;
  if (!shift && index === count - 1) return 0;
  if (shift && index === 0) return count - 1;
  return null;
}

/**
 * Elements that *are* the container, or live inside it.
 *
 * Used on focusin to yank focus back: if the active element is outside the trap
 * because something moved it (a portal, a browser find, a stray autofocus), we
 * put it back on the first stop instead of silently losing it to the document.
 */
export function isInside(container, node) {
  if (!container || !node) return false;
  if (container === node) return true;
  if (typeof container.contains === "function") return container.contains(node);
  return false;
}

/**
 * Where focus should go back to when a modal closes.
 *
 * `preferred` is the element that opened the modal. If it has been removed from
 * the document in the meantime (a row that refetched away, a nav item that
 * unmounted), falling back to `document.body` would drop focus to the top of the
 * page and the user loses their place — so we prefer `fallback`, which callers set
 * to the element that logically replaced it (the palette's trigger button, the
 * main content region).
 */
export function restoreTarget(preferred, fallback, isConnected) {
  const connected = typeof isConnected === "function" ? isConnected : (el) => Boolean(el && el.isConnected);
  if (preferred && connected(preferred)) return preferred;
  if (fallback && connected(fallback)) return fallback;
  return null;
}

/**
 * Screen-reader status text for the palette.
 *
 * A listbox read through aria-activedescendant announces the *option*, but the
 * count ("3 of 12") is only in a visual footer, so a screen-reader user never
 * learns that their query narrowed the list — the same silence that made Enter
 * feel random. This returns the live-region sentence, and it is stable between
 * identical states so React does not re-announce on every render.
 */
export function resultAnnouncement({ total, shown, active, title, noun }) {
  const t = Number.isInteger(total) ? total : 0;
  const s = Number.isInteger(shown) ? shown : 0;
  // `noun` lets a caller say "panels" or "commands" instead of "results". The
  // default keeps every pre-existing call site (and its test) byte-identical.
  const word = typeof noun === "string" && noun.trim() ? noun.trim() : "results";
  if (s <= 0) return `no ${word} for ${t ? "this query" : "an empty query"}`;
  const position = Number.isInteger(active) && active >= 0 && active < s ? `, ${active + 1} of ${s}` : "";
  const named = title ? `: ${title}` : "";
  return `${s} of ${t} ${word}${position}${named}`;
}

/** Also the visible label for the result count — one string, two consumers. */
export function activeOptionId(prefix, index) {
  if (!Number.isInteger(index) || index < 0) return undefined;
  return `${prefix}-opt-${index}`;
}

/**
 * prefers-reduced-motion, read defensively.
 *
 * Returns `true` (i.e. "reduce") when matchMedia is missing or throws, because the
 * safe failure mode for a motion preference is less motion, not more. Callers pass
 * the window in so this stays testable.
 */
export function prefersReducedMotion(win) {
  try {
    if (!win || typeof win.matchMedia !== "function") return true;
    const mq = win.matchMedia("(prefers-reduced-motion: reduce)");
    return Boolean(mq && mq.matches);
  } catch {
    return true;
  }
}

/**
 * Transition duration in ms, as the CSS should apply it.
 *
 * Every animated surface in this shell asks this question through one custom
 * property (`--motion-duration`), so honouring the preference is one line of CSS
 * and cannot be forgotten by a new component.
 */
export function motionDuration(prefersReduced, requestedMs) {
  const ms = Number.isFinite(requestedMs) ? Math.max(0, requestedMs) : 0;
  return prefersReduced ? 0 : ms;
}

/**
 * `aria-activedescendant` for a listbox whose focus stays on the search field.
 *
 * Returns `undefined` — i.e. the attribute is omitted entirely — when there is no
 * selection or the index has run past the list. That matters: an
 * `aria-activedescendant` pointing at a node that does not exist is an accessibility
 * error in every audit tool, and it is exactly what a naive `prefix + index` leaves
 * behind for one render after a query narrows the list.
 */
export function activeDescendant(prefix, index, count) {
  if (!Number.isInteger(index) || index < 0) return undefined;
  if (Number.isInteger(count) && index >= count) return undefined;
  return activeOptionId(prefix, index);
}

/**
 * The live-region sentence for a command palette.
 *
 * Two rules, both learned from how a screen reader actually behaves:
 *
 *   - **Closed means silent.** The region is mounted with the palette, so returning
 *     text while `open` is false would announce the whole result set on page load,
 *     before the user did anything. Empty string is the off switch.
 *   - **Position is included only when it is real.** `active` arrives as 0 on a
 *     freshly opened palette with no results; claiming "1 of 0" is worse than
 *     saying nothing, so an out-of-range cursor degrades to the bare count.
 */
export function paletteAnnouncement({ open, total, shown, active, title }) {
  if (!open) return "";
  return resultAnnouncement({ total, shown, active, title });
}

/**
 * Inline style that applies a motion preference to a single element.
 *
 * The stylesheet already zeroes `--motion-duration` under the media query, which
 * covers every rule written against the token. This exists for the other half:
 * components that set `transition`/`animation` in JS, or that animate a property the
 * media query cannot retarget (a transform on an overlay). Returning an object keeps
 * it assertable without a DOM.
 */
export function motionStyle(prefersReduced, requestedMs, properties = ["transitionDuration"]) {
  const ms = motionDuration(prefersReduced, requestedMs);
  const style = {};
  for (const property of properties) style[property] = `${ms}ms`;
  return style;
}

/**
 * WCAG 2.1 relative luminance, from an `#rrggbb` string.
 * Exported because the contrast test asserts the shipped token values with it.
 */
export function relativeLuminance(hex) {
  const channels = parseHex(hex);
  if (!channels) return null;
  const [r, g, b] = channels.map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** WCAG contrast ratio between two `#rrggbb` colours, or null if unparseable. */
export function contrastRatio(a, b) {
  const la = relativeLuminance(a);
  const lb = relativeLuminance(b);
  if (la === null || lb === null) return null;
  const hi = Math.max(la, lb);
  const lo = Math.min(la, lb);
  return (hi + 0.05) / (lo + 0.05);
}

/**
 * Composite a translucent foreground over an opaque background.
 *
 * The status pills draw their text colour on a 10–12% tint of *the same* colour,
 * so the effective background differs from the panel behind it. Measuring against
 * the panel instead of the tint understates nothing but overstates nothing either
 * — this is how the shipped numbers in docs/ux/frontend-a11y-audit.md were taken.
 */
export function composite(fgHex, alpha, bgHex) {
  const fg = parseHex(fgHex);
  const bg = parseHex(bgHex);
  if (!fg || !bg) return null;
  const a = Number.isFinite(alpha) ? Math.min(1, Math.max(0, alpha)) : 1;
  const mixed = fg.map((c, i) => Math.round(a * c + (1 - a) * bg[i]));
  return `#${mixed.map((c) => c.toString(16).padStart(2, "0")).join("")}`;
}

function parseHex(hex) {
  if (typeof hex !== "string") return null;
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return null;
  const n = m[1];
  return [parseInt(n.slice(0, 2), 16), parseInt(n.slice(2, 4), 16), parseInt(n.slice(4, 6), 16)];
}

/**
 * The duration a11y.css ships in `--motion-duration`, in ms.
 *
 * Declared here as a number so the stylesheet's value and the JS-side motion
 * plumbing can be asserted to match. They are read by different runtimes and there
 * is no import between them, so `web/test/a11y.test.js` parses the CSS custom
 * property and compares it to this constant: change one without the other and the
 * suite fails instead of the two drifting into subtly different timings.
 */
export const MOTION_DURATION_MS = 140;

/** AA for normal text. The pill text is 11px, so this is the bar, not 3:1. */
export const AA_NORMAL_TEXT = 4.5;
/** AA for large (>=18.66px bold / 24px) text and for UI boundaries. */
export const AA_LARGE_TEXT = 3;
