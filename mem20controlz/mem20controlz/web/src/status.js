// Status vocabulary. Nothing is ever mapped to the "ok" tone unless the API
// literally reported the ok status.

export const KNOWN_STATUSES = ["ok", "degraded", "unreachable", "no-health", "unknown"];

export const TONE_DESCRIPTIONS = {
  ok: "API reported status ok (verified surface answered).",
  degraded: "reachable but failing / not verified against the contract.",
  unreachable: "probe could not reach the surface at all.",
  "no-health": "the CLI runs, but exposes no health verb — a probe gap, not a fault.",
  unknown: "no verified surface — the API could not confirm anything.",
  error: "the request itself failed.",
};

export function toneForStatus(status) {
  if (status === "ok") return "ok";
  if (status === "degraded") return "degraded";
  if (status === "unreachable") return "unreachable";
  if (status === "no-health") return "no-health";
  if (status === "unknown") return "unknown";
  // Unrecognised or absent status: never green.
  return "unknown";
}

export function statusLabel(status) {
  if (status === null || status === undefined || status === "") return "not reported";
  return String(status);
}

export function isCounted(panels, status) {
  if (!Array.isArray(panels)) return 0;
  return panels.filter((panel) => panel && panel.status === status).length;
}

// ---------------------------------------------------------------------------
// Fleet aggregate (issue #37, AC-37-01 / AC-37-12)
// ---------------------------------------------------------------------------
//
// The tray glyph and the Overview badge must resolve through THIS function, not
// through two separately-maintained "worst status" helpers. Two copies drift,
// and the day they disagree the user is told two different things about the
// same fleet by two surfaces of the same app.
//
// The Rust side mirrors this exactly (mem20desktop/src/tray.rs
// ::aggregate_fleet_health). Both are table-tested against the same order, so a
// "simplification" to a plain max() in either one turns that suite red.
//
// Order matters and is not cosmetic:
//   starting   sweeping === true. The only honest "wait" signal.
//   unreachable worst actionable state.
//   degraded   reachable but failing.
//   unknown    we could not confirm -- never silently green.
//   no-health  a probe GAP, not a fault. Ranks last among non-ok so "we could
//              not check this binary" never reads as an outage.
//   ok         total > 0 and every panel ok. Verified.
//   unknown    otherwise (empty fleet): never ok by absence of evidence.
//
// `counts{}` is never consulted. The README notes those values are not
// orderable against each other, and a single `unreachable` must not be hidden
// behind three `degraded`.
export function aggregateFleetHealth(payload) {
  if (!payload || typeof payload !== "object") return "unknown";
  if (payload.sweeping === true) return "starting";

  const panels = Array.isArray(payload.panels) ? payload.panels : [];
  const has = (status) =>
    panels.some((panel) => panel && panel.status === status);

  if (has("unreachable")) return "unreachable";
  if (has("degraded")) return "degraded";
  if (has("unknown")) return "unknown";
  if (has("no-health")) return "no-health";

  const total = Number(payload.total);
  const verified =
    Number.isFinite(total) &&
    total > 0 &&
    panels.length > 0 &&
    panels.every((panel) => panel && panel.status === "ok");
  return verified ? "ok" : "unknown";
}

// Accessible name per state (AC-37-12): state is carried by text and shape, not
// by hue alone, so a user with no colour perception can still read it.
export const FLEET_ACCESSIBLE_NAMES = {
  starting: "Fleet: starting",
  unreachable: "Fleet: unreachable",
  degraded: "Fleet: degraded",
  unknown: "Fleet: unknown",
  "no-health": "Fleet: no health check",
  ok: "Fleet: ok",
};

export function fleetAccessibleName(state) {
  return FLEET_ACCESSIBLE_NAMES[state] || FLEET_ACCESSIBLE_NAMES.unknown;
}
