import React from "react";
import {
  LIFECYCLE,
  lifecycleFor,
  toneForLifecycle,
  labelForLifecycle,
  describeLifecycle,
  ageSecondsOf,
  freshnessLabel,
  isStale,
} from "../lifecycle.js";
import { TonePill } from "./StatusPill.jsx";

/**
 * The state a panel shows instead of an empty rectangle.
 *
 * This is deliberately not a spinner: a spinner claims "something is coming",
 * which is a promise we cannot keep when the backend exited. Each state names
 * itself and says what the reader can do about it.
 */
export function StateNotice({
  state,
  context = "data",
  resource = null,
  error = null,
  onRetry = null,
  compact = false,
}) {
  const ageS = resource ? ageSecondsOf(resource) : null;
  const message = describeLifecycle(state, {
    context,
    ageS,
    error: error || (resource && resource.error),
  });
  const heading = labelForLifecycle(state, context);

  return (
    <div
      className={`state-notice state-notice-${state}${compact ? " state-notice-compact" : ""}`}
      role="status"
      aria-live="polite"
    >
      <div className="state-notice-head">
        <TonePill tone={toneForLifecycle(state)} text={state} small />
        <strong className="state-notice-title">{heading}</strong>
        {onRetry ? (
          <button type="button" className="btn btn-small" onClick={onRetry}>
            retry
          </button>
        ) : null}
      </div>
      <p className="state-notice-body">{message}</p>
      {resource && resource.updatedAt ? (
        <p className="state-notice-meta mono">
          last response {freshnessLabel(resource)}
          {ageS !== null ? ` · age ${Math.round(ageS)}s` : ""}
        </p>
      ) : null}
    </div>
  );
}

/**
 * The staleness ribbon that sits above data which is real but not current.
 *
 * It renders nothing when the payload is live, so the common case stays quiet —
 * a staleness marker that is always on is a marker nobody reads.
 */
export function StaleRibbon({ resource, context = "data", onRetry = null }) {
  if (!isStale(resource)) return null;
  const ageS = ageSecondsOf(resource);
  const cached = resource && resource.data ? resource.data.cached === true : false;
  return (
    <div className="stale-ribbon" role="status">
      <TonePill tone="degraded" text="stale" small />
      <span>
        these numbers are {ageS === null ? "of unknown age" : `${Math.round(ageS)}s old`}
        {cached ? " (served from the backend's cache)" : ""} — real, but not current
      </span>
      {onRetry ? (
        <button type="button" className="btn btn-small" onClick={onRetry}>
          refresh
        </button>
      ) : null}
    </div>
  );
}

/**
 * A container that owns its own empty/failed states.
 *
 * `children` is only rendered when there is data to render; every other case
 * falls through to a StateNotice, which is what guarantees "never render an empty
 * panel where a failure occurred".
 */
export function ResourcePanel({ resource, context, children, onRetry = null }) {
  const state = lifecycleFor(resource);
  if (state === LIFECYCLE.LIVE || state === LIFECYCLE.STALE) {
    return (
      <>
        <StaleRibbon resource={resource} context={context} onRetry={onRetry} />
        {children}
      </>
    );
  }
  return <StateNotice state={state} context={context} resource={resource} onRetry={onRetry} />;
}

export { LIFECYCLE };
