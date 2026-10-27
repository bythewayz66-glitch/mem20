// Unit coverage for src/a11y.js — the pure focus/contrast logic behind the modal
// trap, the reduced-motion switch and the status-pill colours.
//
// Run with:  node --test mem20controlz/mem20controlz/web/test/
//
// No jsdom: tabbables()/isVisible() take any object with the few DOM members they
// read, so each test builds the smallest stub that answers the question. That keeps
// the suite dependency-free and fast, which is the point — an a11y regression has
// to be cheap to catch or it will not be run.

import test from "node:test";
import assert from "node:assert/strict";

import {
  tabbables,
  isVisible,
  nextFocusIndex,
  trapTarget,
  isInside,
  restoreTarget,
  resultAnnouncement,
  activeOptionId,
  prefersReducedMotion,
  motionDuration,
  relativeLuminance,
  contrastRatio,
  composite,
  AA_NORMAL_TEXT,
  FOCUSABLE_SELECTOR,
} from "../src/a11y.js";

/* ---------------------------------------------------------------- test doubles */

function el(attrs = {}, { visible = true } = {}) {
  const node = {
    isConnected: true,
    hidden: Boolean(attrs.hidden),
    hasAttribute: (name) => Object.prototype.hasOwnProperty.call(attrs, name),
    getAttribute: (name) => (Object.prototype.hasOwnProperty.call(attrs, name) ? String(attrs[name]) : null),
    focus: () => {
      node.focused = true;
    },
    contains: () => false,
    getClientRects: () => (visible ? [{ width: 10, height: 10 }] : []),
    getBoundingClientRect: () => ({ width: visible ? 10 : 0, height: visible ? 10 : 0 }),
  };
  return node;
}

/** Minimal container: querySelectorAll returns the given nodes. */
function container(nodes) {
  return { querySelectorAll: () => nodes };
}

/* ------------------------------------------------------------- focus order */

test("tabbables keeps DOM order and drops invisible nodes", () => {
  const a = el({ tabindex: 0 });
  const b = el({ tabindex: 0 }, { visible: false });
  const c = el({ tabindex: 0 });
  const stops = tabbables(container([a, b, c]));
  assert.deepEqual(stops, [a, c], "the display:none node must not be a tab stop");
});

test("tabbables honours positive tabindex ahead of document order", () => {
  const plain = el({ tabindex: 0 });
  const late = el({ tabindex: 3 });
  const early = el({ tabindex: 1 });
  assert.deepEqual(tabbables(container([plain, late, early])), [early, late, plain]);
});

test("FOCUSABLE_SELECTOR excludes tabindex=-1 (the palette's option rows)", () => {
  // The exclusion lives in the selector string, not in JS: in a real document it is
  // querySelectorAll that drops the rows. tabbables only sees what the selector
  // returned, so the contract under test is the selector itself plus pass-through.
  assert.ok(FOCUSABLE_SELECTOR.includes('[tabindex]:not([tabindex="-1"])'));
  assert.ok(FOCUSABLE_SELECTOR.includes('button:not([disabled])'));
  const input = el({ tabindex: 0 });
  assert.deepEqual(tabbables(container([input])), [input]);
});

test("tabbables tolerates a missing container", () => {
  assert.deepEqual(tabbables(null), []);
  assert.deepEqual(tabbables({}), []);
});

test("isVisible rejects aria-hidden and zero-size nodes", () => {
  assert.equal(isVisible(el({ tabindex: 0 })), true);
  assert.equal(isVisible(el({ tabindex: 0, "aria-hidden": "true" })), false);
  assert.equal(isVisible(el({ tabindex: 0 }, { visible: false })), false);
  assert.equal(isVisible(null), false);
});

/* --------------------------------------------------------- wrap-around move */

test("nextFocusIndex wraps in both directions", () => {
  assert.equal(nextFocusIndex(0, -1, 3), 2);
  assert.equal(nextFocusIndex(2, 1, 3), 0);
  assert.equal(nextFocusIndex(1, 1, 3), 2);
});

test("nextFocusIndex recovers when nothing is focused", () => {
  assert.equal(nextFocusIndex(-1, 1, 4), 0);
  assert.equal(nextFocusIndex(-1, -1, 4), 3);
  assert.equal(nextFocusIndex(9, 1, 4), 0, "out-of-range index restarts the list");
});

test("nextFocusIndex returns -1 for an empty list", () => {
  assert.equal(nextFocusIndex(0, 1, 0), -1);
  assert.equal(nextFocusIndex(0, 1, null), -1);
});

/* ------------------------------------------------------------- trap target */

test("trapTarget only claims the two edges", () => {
  assert.equal(trapTarget({ count: 3, index: 2, shift: false }), 0, "Tab on last wraps to first");
  assert.equal(trapTarget({ count: 3, index: 0, shift: true }), 2, "Shift-Tab on first wraps to last");
  assert.equal(trapTarget({ count: 3, index: 1, shift: false }), null, "middle: browser keeps control");
  assert.equal(trapTarget({ count: 3, index: 1, shift: true }), null);
});

test("trapTarget handles an empty or unknown focus position", () => {
  assert.equal(trapTarget({ count: 0, index: -1, shift: false }), null);
  assert.equal(trapTarget({ count: 2, index: -1, shift: false }), 0);
  assert.equal(trapTarget({ count: 2, index: -1, shift: true }), 1);
});

/* ------------------------------------------------------------- containment */
test("isInside recognises the container itself and descendants", () => {
  const child = el();
  const node = { contains: (n) => n === child };
  assert.equal(isInside(node, node), true);
  assert.equal(isInside(node, child), true);
  assert.equal(isInside(node, el()), false);
  assert.equal(isInside(null, child), false);
});

/* --------------------------------------------------------- focus restore */

test("restoreTarget prefers the opener while it is still in the document", () => {
  const opener = el();
  assert.equal(restoreTarget(opener, el(), () => true), opener);
});

test("restoreTarget falls back when the opener was removed", () => {
  const opener = el();
  const fallback = el();
  const isConnected = (n) => n === fallback;
  assert.equal(restoreTarget(opener, fallback, isConnected), fallback);
});

test("restoreTarget returns null rather than a detached node", () => {
  assert.equal(restoreTarget(el(), el(), () => false), null);
  assert.equal(restoreTarget(null, null), null, "default isConnected rejects stubs");
});

/* --------------------------------------------------- screen-reader output */

test("resultAnnouncement names the count when nothing matches", () => {
  assert.equal(resultAnnouncement({ total: 0, shown: 0, active: 0 }), "no results for an empty query");
  assert.equal(resultAnnouncement({ total: 12, shown: 0, active: 0 }), "no results for this query");
});

test("resultAnnouncement includes position and the active row title", () => {
  assert.equal(
    resultAnnouncement({ total: 12, shown: 3, active: 1, title: "Dreams" }),
    "3 of 12 results, 2 of 3: Dreams",
  );
  assert.equal(resultAnnouncement({ total: 5, shown: 5, active: 9 }), "5 of 5 results");
});

test("activeOptionId is stable and undefined for no selection", () => {
  assert.equal(activeOptionId("palette", 2), "palette-opt-2");
  assert.equal(activeOptionId("palette", -1), undefined);
  assert.equal(activeOptionId("palette", null), undefined);
});

/* --------------------------------------------------------- reduced motion */

test("prefersReducedMotion reads matchMedia and defaults to reduce", () => {
  const reduce = { matchMedia: () => ({ matches: true }) };
  const allow = { matchMedia: () => ({ matches: false }) };
  assert.equal(prefersReducedMotion(reduce), true);
  assert.equal(prefersReducedMotion(allow), false);
  assert.equal(prefersReducedMotion(undefined), true, "no window => the safe answer is less motion");
  assert.equal(
    prefersReducedMotion({
      matchMedia: () => {
        throw new Error("blocked");
      },
    }),
    true,
  );
});

test("motionDuration zeroes the duration only when reduced", () => {
  assert.equal(motionDuration(true, 180), 0);
  assert.equal(motionDuration(false, 180), 180);
  assert.equal(motionDuration(false, undefined), 0);
  assert.equal(motionDuration(false, -50), 0);
});

/* -------------------------------------------------------------- contrast */

test("relativeLuminance matches the WCAG reference values", () => {
  assert.equal(relativeLuminance("#000000"), 0);
  assert.equal(relativeLuminance("#ffffff"), 1);
  assert.equal(relativeLuminance("not-a-colour"), null);
});

test("contrastRatio reproduces the WCAG anchors", () => {
  assert.equal(Math.round(contrastRatio("#000000", "#ffffff") * 10) / 10, 21);
  assert.equal(contrastRatio("#ffffff", "#ffffff"), 1);
  assert.equal(contrastRatio("#000000", "#fff"), null, "3-digit shorthand is rejected, not guessed");
});

test("composite lays a translucent tint over its backdrop", () => {
  assert.equal(composite("#ffffff", 0, "#000000"), "#000000");
  assert.equal(composite("#ffffff", 1, "#000000"), "#ffffff");
  assert.equal(composite("#3fb950", 0.1, "#070b10"), "#0d1c16");
});

/*
 * The regression guard for docs/ux/frontend-a11y-audit.md §3. These are the
 * literal tokens shipped in a11y.css; the pill text is 11px, so every one of them
 * has to clear AA for normal text (4.5:1) against the tint it is drawn on, which is
 * itself 12% of the same colour over each of the four shell surfaces.
 */
test("status pill tokens clear WCAG AA on every shell surface", () => {
  const surfaces = { bg: "#070b10", panel: "#0e151d", panel2: "#121b25", bg2: "#0c1218" };
  const tints = {
    ok: ["#56d364", 0.12],
    degraded: ["#e3b341", 0.12],
    unreachable: ["#ff7b72", 0.12],
    unknown: ["#93a4b5", 0.12],
    "no-health": ["#9aa4ad", 0.12],
    error: ["#ffa198", 0.14],
  };
  for (const [name, [fg, alpha]] of Object.entries(tints)) {
    for (const [surface, bg] of Object.entries(surfaces)) {
      const effective = composite(fg, alpha, bg);
      const ratio = contrastRatio(fg, effective);
      assert.ok(ratio !== null, `${name} on ${surface}: unparseable colour`);
      assert.ok(
        ratio >= AA_NORMAL_TEXT,
        `${name} on ${surface} is ${ratio.toFixed(2)}:1, below AA ${AA_NORMAL_TEXT}:1`,
      );
    }
  }
});

test("the muted text token clears AA on the densest surface", () => {
  // --text-faint is used for 12px body copy ~70 times across the tabs; it shipped at
  // #5f7081, which measures 3.41:1 on --panel-2 and is the reason that token moved.
  assert.ok(contrastRatio("#8496a8", "#121b25") >= AA_NORMAL_TEXT);
});

test("the focus ring token is visible against every surface", () => {
  for (const bg of ["#070b10", "#0e151d", "#121b25", "#0c1218"]) {
    assert.ok(contrastRatio("#8ecbff", bg) >= 3, `focus ring vanishes on ${bg}`);
  }
});
