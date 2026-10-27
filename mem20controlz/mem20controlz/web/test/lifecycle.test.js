// Acceptance tests for issue #39 — offline / degraded UX.
//
//   node --test web/test/lifecycle.test.js
//
// These cover the two criteria in the issue verbatim:
//   1. "Killing the sidecar shows an explicit 'backend unreachable' state, not a
//      blank panel."
//   2. "Stale data is visibly marked stale (age shown)."
//
// lifecycle.js is imported directly — it has no React dependency precisely so
// this can run as plain node without a DOM.

import test from "node:test";
import assert from "node:assert/strict";

import {
  LIFECYCLE,
  lifecycleFor,
  toneForLifecycle,
  labelForLifecycle,
  describeLifecycle,
  formatAge,
  ageSecondsOf,
  isStale,
  reportsMissingStore,
} from "../src/lifecycle.js";

// Mirrors the shape useResource() returns.
function resource({ data = null, error = null, loading = false, updatedAt = null, everLoaded = false } = {}) {
  return { data, error, loading, updatedAt, everLoaded, requests: everLoaded ? 1 : 0 };
}

const netError = Object.assign(new Error("Network error calling GET /api/health: Failed to fetch"), {
  url: "/api/health",
  method: "GET",
});

test("sidecar killed before any successful response => backend-unreachable, never starting", () => {
  // This is the exact scenario in the issue: the sidecar process is gone, so the
  // very first fetch fails and there has never been a payload.
  const health = resource({ error: netError, loading: false, everLoaded: false });
  assert.equal(lifecycleFor(health), LIFECYCLE.UNREACHABLE);
  assert.equal(toneForLifecycle(LIFECYCLE.UNREACHABLE), "unreachable");

  const heading = labelForLifecycle(LIFECYCLE.UNREACHABLE, "control plane");
  assert.match(heading, /backend unreachable/i);

  // The message must explain the blank panel rather than apologise for it, and
  // must carry the underlying cause.
  const body = describeLifecycle(LIFECYCLE.UNREACHABLE, { context: "control plane", error: netError });
  assert.match(body, /did not answer/i);
  assert.match(body, /Failed to fetch/);
  assert.match(body, /not because there is none/i);
});

test("a resource still loading is 'starting', not 'unreachable'", () => {
  const health = resource({ loading: true, everLoaded: false });
  assert.equal(lifecycleFor(health), LIFECYCLE.STARTING);
  assert.equal(toneForLifecycle(LIFECYCLE.STARTING), "unknown");

  const body = describeLifecycle(LIFECYCLE.STARTING, { context: "registry" });
  // The distinction that matters: pending is not the same claim as failed.
  assert.match(body, /not an empty result/i);
});

test("a live payload is live", () => {
  const registry = resource({
    data: { panels: [], counts: {}, cached: false, age_s: 0, stale: false },
    everLoaded: true,
    updatedAt: Date.now(),
  });
  assert.equal(lifecycleFor(registry), LIFECYCLE.LIVE);
  assert.equal(toneForLifecycle(LIFECYCLE.LIVE), "ok");
  assert.equal(isStale(registry), false);
});

test("backend says stale => panel is stale even though the request succeeded", () => {
  // The honest-cache case: HTTP 200, real numbers, but the sweep behind them is
  // older than its TTL. The backend's own verdict must win over our optimism.
  const registry = resource({
    data: { panels: [{ id: "a" }], counts: { ok: 1 }, cached: true, age_s: 143.7, stale: true },
    everLoaded: true,
    updatedAt: Date.now(),
  });
  assert.equal(lifecycleFor(registry), LIFECYCLE.STALE);
  assert.equal(toneForLifecycle(LIFECYCLE.STALE), "degraded");
  assert.equal(isStale(registry), true);

  // "age shown" — the number in the UI comes from the backend's own measurement.
  assert.equal(ageSecondsOf(registry), 143.7);
  assert.equal(formatAge(143.7), "2 min");

  const body = describeLifecycle(LIFECYCLE.STALE, { context: "registry", ageS: ageSecondsOf(registry) });
  assert.match(body, /cached response/i);
  assert.match(body, /2 min old/);
  assert.match(body, /not current/i);
});

test("a later failure keeps the last good payload and marks it stale, not absent", () => {
  // Nothing is thrown away: the numbers stay on screen, labelled.
  const before = { panels: [{ id: "a" }], counts: { ok: 1 }, stale: false, age_s: 0 };
  const registry = resource({ data: before, error: netError, everLoaded: true, updatedAt: Date.now() - 42_000 });
  assert.equal(lifecycleFor(registry), LIFECYCLE.STALE);
  assert.equal(isStale(registry), true);
  // Falls back to how long ago the browser received it when the backend gave no age.
  const age = ageSecondsOf(registry);
  assert.ok(age >= 41 && age <= 44, `expected ~42s, got ${age}`);
});

test("a reported missing store is its own state, not 'unreachable' or 'empty'", () => {
  const manifest = resource({ data: { store_present: false, zone: "x" }, everLoaded: true, updatedAt: Date.now() });
  assert.equal(reportsMissingStore(manifest.data), true);
  assert.equal(lifecycleFor(manifest), LIFECYCLE.STORE_MISSING);

  const body = describeLifecycle(LIFECYCLE.STORE_MISSING, { context: "sites manifest" });
  assert.match(body, /no sites manifest store/i);

  // An empty array is NOT a missing store — "no rows" is not an error.
  assert.equal(reportsMissingStore({ sites: [] }), false);
  assert.equal(reportsMissingStore(null), false);
});

test("every lifecycle state has a tone and a non-empty heading", () => {
  for (const state of Object.values(LIFECYCLE)) {
    assert.ok(toneForLifecycle(state), `no tone for ${state}`);
    assert.ok(labelForLifecycle(state, "registry").length > 0, `no label for ${state}`);
    assert.ok(describeLifecycle(state, { context: "registry" }).length > 20, `no description for ${state}`);
  }
});

test("an unrecognised status is never mapped to the ok tone", () => {
  // Regression guard for the honesty rule status.js already enforces.
  assert.notEqual(toneForLifecycle("something-new"), "ok");
  assert.equal(toneForLifecycle("something-new"), "unknown");
});

test("formatAge never renders NaN or a bare undefined", () => {
  assert.equal(formatAge(null), "an unknown time");
  assert.equal(formatAge(undefined), "an unknown time");
  assert.equal(formatAge(NaN), "an unknown time");
  assert.equal(formatAge(0.4), "under a second");
  assert.equal(formatAge(45), "45s");
  assert.equal(formatAge(3600), "1 h");
  // Nothing above may contain a literal "NaN" or "undefined".
  for (const v of [null, undefined, NaN, 0.4, 45, 1440, 3600]) {
    const out = formatAge(v);
    assert.ok(!/NaN|undefined/.test(out), `formatAge(${v}) => ${out}`);
  }
});
