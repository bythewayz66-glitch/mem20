// Lifecycle states for the panel itself, kept separate from the *fleet* status
// vocabulary in ./status.js.
//
// Two different questions get two different vocabularies, and conflating them is
// how a dashboard ends up lying:
//
//   status.js  answers "what did the API say about a subsystem?"  → ok/degraded/
//              unreachable/no-health/unknown. Owned by the backend.
//   this file  answers "can this panel talk to the backend at all, and how fresh
//              is what it is showing?"  → starting / live / stale / backend-
//              unreachable / store-missing. Owned by the shell.
//
// A panel is never blank because something failed. Every combination below
// resolves to a state with a heading and a sentence a human can act on.
//
// Deliberately free of React and of every other app import: this is the one
// module the offline behaviour is decided in, so it stays a pure function of its
// inputs and can be tested without a browser.

export const LIFECYCLE = {
  STARTING: "starting",
  LIVE: "live",
  STALE: "stale",
  UNREACHABLE: "backend-unreachable",
  STORE_MISSING: "store-missing",
};

// Tone names line up with the pill classes already in styles.css so the shell
// does not invent a second colour language.
const TONE = {
  [LIFECYCLE.STARTING]: "unknown",
  [LIFECYCLE.LIVE]: "ok",
  [LIFECYCLE.STALE]: "degraded",
  [LIFECYCLE.UNREACHABLE]: "unreachable",
  [LIFECYCLE.STORE_MISSING]: "no-health",
};

export function toneForLifecycle(state) {
  return TONE[state] || "unknown";
}

/**
 * Human-readable heading for a lifecycle state.
 *
 * `context` names the thing that failed ("registry", "sites manifest") so the
 * message never reads as a generic "Something went wrong".
 */
export function labelForLifecycle(state, context = "data") {
  switch (state) {
    case LIFECYCLE.STARTING:
      return `waiting for the ${context} — first response pending`;
    case LIFECYCLE.LIVE:
      return `${context} live`;
    case LIFECYCLE.STALE:
      return `${context} is stale`;
    case LIFECYCLE.UNREACHABLE:
      return `backend unreachable — ${context} unavailable`;
    case LIFECYCLE.STORE_MISSING:
      return `store missing — ${context} has nothing to read`;
    default:
      return `${context} state unknown`;
  }
}

export function describeLifecycle(state, { context = "data", ageS = null, error = null } = {}) {
  switch (state) {
    case LIFECYCLE.STARTING:
      return `The request to /api for the ${context} has not returned yet. Nothing is shown because nothing has been fetched — this is not an empty result.`;
    case LIFECYCLE.LIVE:
      return `Showing a current response for the ${context}.`;
    case LIFECYCLE.STALE:
      return (
        `Showing a cached response for the ${context}` +
        (ageS === null || ageS === undefined ? "" : ` that is ${formatAge(ageS)} old`) +
        ". The numbers are real but they are not current, so they are marked rather than hidden. " +
        "A stale reading is never presented as a live one."
      );
    case LIFECYCLE.UNREACHABLE:
      return (
        `The control-plane API did not answer for the ${context}` +
        (error && error.message ? ` (${error.message})` : "") +
        ". The backend may still be starting, or the sidecar may have exited. This panel is empty because the data could not be fetched, not because there is none."
      );
    case LIFECYCLE.STORE_MISSING:
      return `The API answered, but reported no ${context} store on this machine. Start the service that owns it, or point the shell at a host that has one.`;
    default:
      return `The ${context} is in an unrecognised state. Treating it as unknown rather than healthy.`;
  }
}

export function formatAge(ageS) {
  if (ageS === null || ageS === undefined || Number.isNaN(Number(ageS))) return "an unknown time";
  const seconds = Number(ageS);
  if (seconds < 1) return "under a second";
  if (seconds < 90) return `${Math.round(seconds)}s`;
  const minutes = seconds / 60;
  if (minutes < 60) return `${Math.round(minutes)} min`;
  return `${Math.round(minutes / 60)} h`;
}

/**
 * Does this payload say the store it reads from is absent?
 *
 * Deliberately conservative: it only looks at keys the backend actually emits
 * (`store`, `store_present`, `store_missing`) rather than guessing from an empty
 * array, because "no rows" and "no store" are different facts and only one of
 * them is an error.
 */
export function reportsMissingStore(data) {
  if (!data || typeof data !== "object") return false;
  if (data.store_missing === true) return true;
  if (data.store_present === false) return true;
  if (typeof data.store === "string" && data.store.toLowerCase() === "missing") return true;
  return false;
}

/**
 * Resolve one resource (as returned by useResource) into a lifecycle state.
 *
 * Precedence matters: once we have ever loaded data, a later failure is
 * *staleness*, not absence — the last good payload is still on screen and must be
 * labelled rather than thrown away. Only a resource that has never loaded can be
 * `backend-unreachable`.
 */
export function lifecycleFor(resource) {
  const { data, error, loading, everLoaded } = resource || {};

  if (data && reportsMissingStore(data)) return LIFECYCLE.STORE_MISSING;

  if (error) {
    // Keep showing the last good payload, but never as current.
    return everLoaded ? LIFECYCLE.STALE : LIFECYCLE.UNREACHABLE;
  }

  if (data) {
    // The backend's own staleness verdict wins over our optimism.
    if (data.stale === true) return LIFECYCLE.STALE;
    return LIFECYCLE.LIVE;
  }

  if (loading || !everLoaded) return LIFECYCLE.STARTING;
  return LIFECYCLE.STARTING;
}

/**
 * Age in seconds of the payload currently on screen.
 *
 * When the current request failed we must measure from the last *successful*
 * response, not trust `age_s`: the backend's age describes the sweep it served,
 * which may be 0 while the connection has since been dead for a minute. Reporting
 * the backend's 0 there would label dead data "fresh", which is exactly the lie
 * this module exists to prevent.
 *
 * Otherwise the backend-reported `age_s` wins, because it timed the sweep itself.
 */
export function ageSecondsOf(resource, nowMs = Date.now()) {
  const data = resource && resource.data;
  const failedAfterSuccess = Boolean(resource && resource.error && resource.everLoaded);
  if (failedAfterSuccess) {
    return resource.updatedAt ? (nowMs - resource.updatedAt) / 1000 : null;
  }
  if (data && typeof data.age_s === "number") return data.age_s;
  if (resource && resource.updatedAt) return (nowMs - resource.updatedAt) / 1000;
  return null;
}

/** True when the payload should carry a visible "stale" marker. */
export function isStale(resource) {
  if (!resource || !resource.data) return false;
  if (resource.data.stale === true) return true;
  return Boolean(resource.error) && Boolean(resource.everLoaded);
}

/** A short clock label for the last successful response, or an honest absence. */
export function freshnessLabel(resource) {
  if (!resource || !resource.updatedAt) return "never received";
  return new Date(resource.updatedAt).toLocaleTimeString(undefined, { hour12: false });
}
