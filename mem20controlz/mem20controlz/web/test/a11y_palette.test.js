// Screen-reader traversal + reduced-motion contract for the command palette.
//
// Run with:  node --test mem20controlz/mem20controlz/web/test/
//
// The palette's *component* lives behind its own feature branch (#38/PR #109). What
// this file pins down is the contract that component has to satisfy, expressed as the
// pure functions it is obliged to call, plus a check that the reduced-motion token in
// a11y.css and the one this module exports have not drifted apart. That combination is
// what makes the difference between "keyboard-only" and "followable by a screen
// reader": a listbox whose active option is not announced is invisible to anyone not
// looking at the highlight.
//
// No jsdom, for the same reason as a11y.test.js: every function under test is a data
// transform, so the suite stays dependency-free and runs in ~100ms.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  paletteAnnouncement,
  activeDescendant,
  motionStyle,
  MOTION_DURATION_MS,
  prefersReducedMotion,
} from "../src/a11y.js";

const here = dirname(fileURLToPath(import.meta.url));

/* --------------------------------------------------------------- traversal */

test("a closed palette says nothing at all", () => {
  // The region is mounted with the panel, not with the dialog. If it spoke while
  // closed, every page load would announce the full result set before the user
  // pressed a key.
  assert.equal(paletteAnnouncement({ open: false, total: 154, shown: 154, active: 0 }), "");
  assert.equal(paletteAnnouncement({ open: false, total: 0, shown: 0, active: -1 }), "");
});

test("an open palette announces the filtered count, not the cursor", () => {
  assert.equal(
    paletteAnnouncement({ open: true, total: 154, shown: 3, active: 0 }),
    "3 of 154 results, 1 of 3",
  );
  // Cursor moved: the position advances but the count is unchanged, which is what
  // tells a screen-reader user their ArrowDown was received.
  assert.equal(
    paletteAnnouncement({ open: true, total: 154, shown: 3, active: 2 }),
    "3 of 154 results, 3 of 3",
  );
});

test("the announced cursor never points past the list", () => {
  // Query narrowed the list and `active` has not been clamped yet. Claiming
  // "4 of 3" would be a lie the user cannot see to correct.
  assert.equal(paletteAnnouncement({ open: true, total: 154, shown: 3, active: 7 }), "3 of 154 results");
});

test("an empty result set is announced as empty, not as zero rows", () => {
  assert.equal(
    paletteAnnouncement({ open: true, total: 154, shown: 0, active: 0 }),
    "no results for this query",
  );
  assert.equal(
    paletteAnnouncement({ open: true, total: 0, shown: 0, active: 0 }),
    "no results for an empty query",
  );
});

test("the active row title is spoken after the count", () => {
  assert.equal(
    paletteAnnouncement({ open: true, total: 9, shown: 2, active: 1, title: "dreams / new" }),
    "2 of 9 results, 2 of 2: dreams / new",
  );
});

/* ------------------------------------------------------- aria-activedescendant */

test("activedescendant resolves to the same id the option renders", () => {
  // One function produces both, so the attribute and the DOM id cannot disagree.
  assert.equal(activeDescendant("palette", 0, 3), "palette-opt-0");
  assert.equal(activeDescendant("palette", 2, 3), "palette-opt-2");
});

test("activedescendant is omitted rather than dangling", () => {
  // A dangling aria-activedescendant is an a11y-tree error in every audit tool, and
  // it is exactly what a raw `prefix + index` leaves behind for one render after the
  // list shortens. undefined means React omits the attribute entirely.
  assert.equal(activeDescendant("palette", -1, 3), undefined, "no cursor yet");
  assert.equal(activeDescendant("palette", 3, 3), undefined, "cursor ran past the end");
  assert.equal(activeDescendant("palette", null, 3), undefined);
  assert.equal(activeDescendant("palette", 0, 0), undefined, "empty list has no option");
});

test("activedescendant tolerates a missing count", () => {
  // Callers that do not know the count yet still get a stable id for a valid index.
  assert.equal(activeDescendant("palette", 1, undefined), "palette-opt-1");
});

/* ----------------------------------------------------------- reduced motion */

test("reduced motion zeroes the JS-driven duration too", () => {
  // The stylesheet covers every rule written against --motion-duration. This covers
  // the components that set the duration inline, which the media query cannot reach.
  assert.deepEqual(motionStyle(true, MOTION_DURATION_MS), { transitionDuration: "0ms" });
  assert.deepEqual(motionStyle(false, MOTION_DURATION_MS), { transitionDuration: "140ms" });
});

test("motionStyle can target several properties at once", () => {
  assert.deepEqual(motionStyle(true, 140, ["transitionDuration", "animationDuration"]), {
    transitionDuration: "0ms",
    animationDuration: "0ms",
  });
});

test("the shipped CSS duration and the exported constant agree", () => {
  // a11y.css is read by the browser, this module by the bundle; neither imports the
  // other. Parsing the custom property here turns "keep these in sync" from a
  // comment into a failing test when someone tunes one of them.
  const css = readFileSync(join(here, "..", "src", "a11y.css"), "utf8");
  const match = /--motion-duration:\s*(\d+)ms/.exec(css);
  assert.ok(match, "--motion-duration is missing from a11y.css");
  assert.equal(
    Number(match[1]),
    MOTION_DURATION_MS,
    "a11y.css and a11y.js disagree about the base motion duration",
  );
});

test("the reduced-motion media query actually zeroes the token", () => {
  const css = readFileSync(join(here, "..", "src", "a11y.css"), "utf8");
  const block = /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*?)\n\}/.exec(css);
  assert.ok(block, "the prefers-reduced-motion block is missing");
  assert.match(block[1], /--motion-duration:\s*0ms/, "the token is not zeroed under reduce");
  // Focus rings and colour must survive the blanket animation reset.
  assert.doesNotMatch(block[1], /outline:\s*none/, "reduce must not remove focus rings");
});

test("a reduce preference resolves to a zero duration end to end", () => {
  const reduce = { matchMedia: () => ({ matches: true }) };
  const allow = { matchMedia: () => ({ matches: false }) };
  assert.deepEqual(motionStyle(prefersReducedMotion(reduce), MOTION_DURATION_MS), {
    transitionDuration: "0ms",
  });
  assert.deepEqual(motionStyle(prefersReducedMotion(allow), MOTION_DURATION_MS), {
    transitionDuration: "140ms",
  });
});
