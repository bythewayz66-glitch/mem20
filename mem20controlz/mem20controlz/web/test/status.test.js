// Fleet aggregate conformance (issue #37).
//
// This table is the shared contract: the Rust side
// (mem20desktop/src/tray.rs) is tested against the same order. If someone
// "simplifies" either implementation to a plain max(), one of the two suites
// goes red -- which is the point.
import test from "node:test";
import assert from "node:assert/strict";

import {
  aggregateFleetHealth,
  fleetAccessibleName,
  FLEET_ACCESSIBLE_NAMES,
} from "../src/status.js";

const panel = (status) => ({ id: status, name: status, status });

test("sweeping wins over everything and is not an outage", () => {
  assert.equal(
    aggregateFleetHealth({ sweeping: true, panels: [], total: 0 }),
    "starting"
  );
  // Even with a broken panel listed, an in-flight sweep is "wait", not "down".
  assert.equal(
    aggregateFleetHealth({ sweeping: true, panels: [panel("unreachable")], total: 1 }),
    "starting"
  );
});

test("unreachable outranks degraded even when degraded is more numerous", () => {
  // counts{} is not orderable; panels are. One unreachable must not hide.
  assert.equal(
    aggregateFleetHealth({
      panels: [panel("degraded"), panel("degraded"), panel("degraded"), panel("unreachable")],
      total: 4,
    }),
    "unreachable"
  );
});

test("a probe gap never masquerades as an outage", () => {
  // no-health ranks BELOW ok in severity, but still non-ok.
  assert.equal(aggregateFleetHealth({ panels: [panel("no-health")], total: 1 }), "no-health");
});

test("unknown outranks no-health so a gap is not an accusation", () => {
  assert.equal(
    aggregateFleetHealth({ panels: [panel("no-health"), panel("unknown")], total: 2 }),
    "unknown"
  );
});

test("ok requires a non-empty, fully verified fleet", () => {
  assert.equal(aggregateFleetHealth({ panels: [panel("ok"), panel("ok")], total: 2 }), "ok");
});

test("an empty fleet is never ok by absence of evidence", () => {
  assert.equal(aggregateFleetHealth({ panels: [], total: 0 }), "unknown");
  assert.equal(aggregateFleetHealth({ total: 0 }), "unknown");
});

test("an unrecognised status degrades to unknown, not ok", () => {
  assert.equal(
    aggregateFleetHealth({ panels: [panel("ok"), panel("something-new")], total: 2 }),
    "unknown"
  );
});

test("a malformed payload is unknown, never ok", () => {
  for (const bad of [null, undefined, 42, "nope", {}]) {
    assert.equal(aggregateFleetHealth(bad), "unknown");
  }
});

test("total must be a real number for a verified ok", () => {
  assert.equal(aggregateFleetHealth({ panels: [panel("ok")], total: "1" }), "ok");
  assert.equal(aggregateFleetHealth({ panels: [panel("ok")], total: null }), "unknown");
  assert.equal(aggregateFleetHealth({ panels: [panel("ok")] }), "unknown");
});

test("every state has a distinct accessible name (no colour-only signalling)", () => {
  const names = Object.values(FLEET_ACCESSIBLE_NAMES);
  assert.equal(new Set(names).size, names.length, "names must be distinct");
  assert.ok(names.every((n) => n.startsWith("Fleet: ")));
  // An unknown state must not render as a green/ok label.
  assert.equal(fleetAccessibleName("not-a-state"), FLEET_ACCESSIBLE_NAMES.unknown);
});
