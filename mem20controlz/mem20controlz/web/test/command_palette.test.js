// Acceptance tests for issue #38 — the Cmd-K command palette.
//
//   node --test web/test/command_palette.test.js
//
// The issue asks for one palette "across panels, CLI audit and dream". That is
// only worth having if it reaches *entities* — a named registry panel, a CLI row
// with gaps, a specific dream — rather than duplicating the sidebar. These tests
// pin that, plus the ranking and keyboard behaviour.

import test from "node:test";
import assert from "node:assert/strict";

import {
  navCommands,
  shellCommands,
  subsystemCommands,
  cliCommands,
  dreamCommands,
  buildCommands,
  fuzzyMatch,
  rankCommands,
  nextIndex,
} from "../src/commandPalette.js";

const NAV = [
  { group: "control", items: [{ id: "overview", label: "Overview", hint: "census" }] },
  { group: "fleet / web", items: [{ id: "websites", label: "Websites", hint: "sites" }] },
];

const REGISTRY = {
  data: {
    panels: [
      { id: "mem20agentz", name: "mem20agentz", kind: "subsystem", status: "ok", binary: "mem20agentz" },
      { id: "mem20controlz", name: "mem20controlz", kind: "manager", status: "degraded" },
    ],
  },
};

const COVERAGE = {
  data: {
    results: [
      { name: "mem20ops", naming: "python", gaps: ["--json", "--dry-run"] },
      { name: "mem20dreamz", naming: "python", gaps: [] },
    ],
  },
};

const DREAMS = {
  data: { dreams: [{ id: "d-42", title: "index drift report", status: "draft" }] },
};

const ALL = buildCommands({ nav: NAV, registry: REGISTRY, coverage: COVERAGE, dreams: DREAMS });

test("the palette spans panels, the CLI audit and dreams, as the issue asks", () => {
  const groups = new Set(ALL.map((c) => c.group));
  assert.ok(groups.has("go"), "no navigation commands");
  assert.ok(groups.has("subsystems"), "no subsystem commands");
  assert.ok(groups.has("cli"), "no CLI audit commands");
  assert.ok(groups.has("dreams"), "no dream commands");
});

test("each subsystem panel gets its own command that selects it", () => {
  const subs = subsystemCommands(REGISTRY);
  assert.equal(subs.length, 2);
  const controlz = subs.find((c) => c.id === "sub:mem20controlz");
  // Reaching the panel, not just the tab: `select` is what the panel needs.
  assert.equal(controlz.action.type, "nav");
  assert.equal(controlz.action.view, "subsystems");
  assert.equal(controlz.action.select, "mem20controlz");
});

test("CLI rows surface their gap count in the subtitle", () => {
  const cli = cliCommands(COVERAGE);
  const ops = cli.find((c) => c.title === "mem20ops");
  assert.match(ops.subtitle, /2 gaps/);
  const dreamz = cli.find((c) => c.title === "mem20dreamz");
  assert.match(dreamz.subtitle, /no gaps/);
  assert.equal(ops.action.select, "mem20ops");
});

test("dreams are addressable by id and land on the review detail", () => {
  const dreams = dreamCommands(DREAMS);
  assert.equal(dreams.length, 1);
  assert.equal(dreams[0].action.view, "dreams");
  assert.equal(dreams[0].action.select, "d-42");
  assert.equal(dreams[0].action.sub, "review");
});

test("no payload => no crash, and the static commands survive", () => {
  // The palette opens before data arrives; it must still be usable.
  const empty = buildCommands({ nav: NAV });
  assert.ok(empty.length > 0);
  assert.equal(subsystemCommands(null).length, 0);
  assert.equal(cliCommands(undefined).length, 0);
  assert.equal(dreamCommands({}).length, 0);
  // A malformed payload is not a crash either.
  assert.equal(dreamCommands({ data: { dreams: "nope" } }).length, 0);
});

test("exact substring ranks above a keyword hit", () => {
  const ranked = rankCommands(ALL, "websites");
  assert.equal(ranked[0].command.title, "Websites");
});

test("fuzzy subsequence finds targets the substring rule would miss", () => {
  assert.ok(fuzzyMatch("ovw", "Overview"), "ovw should match Overview");
  assert.ok(fuzzyMatch("wbs", "Websites"), "wbs should match Websites");
  assert.equal(fuzzyMatch("zzz", "Overview"), null);
});

test("empty query returns the list capped, in caller order", () => {
  const ranked = rankCommands(ALL, "", 5);
  assert.equal(ranked.length, 5);
  assert.equal(ranked[0].command.id, ALL[0].id);
});

test("a query with no match returns an empty list, not everything", () => {
  // A palette that falls back to showing unrelated commands is worse than an
  // empty list: Enter would then run something the user never asked for.
  assert.deepEqual(rankCommands(ALL, "qqqqzzzz"), []);
});

test("ranked results never duplicate a command", () => {
  const ranked = rankCommands(ALL, "mem20");
  const ids = ranked.map((r) => r.command.id);
  assert.equal(new Set(ids).size, ids.length);
});

test("nextIndex wraps at both ends and never returns -1", () => {
  assert.equal(nextIndex(0, -1, 3), 2);
  assert.equal(nextIndex(2, 1, 3), 0);
  assert.equal(nextIndex(1, 1, 3), 2);
  // Empty list: 0, so callers never index into nothing.
  assert.equal(nextIndex(0, 1, 0), 0);
  // Out-of-range cursor self-heals rather than throwing.
  assert.equal(nextIndex(9, 1, 3), 0);
});

test("shell commands cover refresh and retry, which is what an offline shell needs", () => {
  const shell = shellCommands();
  const types = shell.map((c) => c.action.type);
  assert.ok(types.includes("refresh"));
  assert.ok(types.includes("retry"));
  // Retry must be discoverable by the words a person would actually type.
  const retry = shell.find((c) => c.action.type === "retry");
  assert.ok(retry.keywords.includes("offline"));
  assert.ok(rankCommands(shell, "offline").some((r) => r.command.id === retry.id));
});

test("every command has a stable id, a group and an action", () => {
  for (const command of ALL) {
    assert.ok(command.id, "missing id");
    assert.ok(command.group, `missing group on ${command.id}`);
    assert.ok(command.action && command.action.type, `missing action on ${command.id}`);
    assert.ok(command.title, `missing title on ${command.id}`);
  }
  const ids = ALL.map((c) => c.id);
  assert.equal(new Set(ids).size, ids.length, "duplicate command ids");
});
