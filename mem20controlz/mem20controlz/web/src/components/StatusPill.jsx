import React from "react";
import { toneForStatus, statusLabel } from "../status.js";

export default function StatusPill({ status, reason, small = false, label = null }) {
  const tone = toneForStatus(status);
  const text = label ?? statusLabel(status);
  // The dot is decorative (aria-hidden), so the colour carries no meaning on its own
  // — the status word is always in the accessible name. `title` only duplicates the
  // reason text for a mouse user, so it is exposed to AT as a description instead.
  return (
    <span
      className={`pill pill-${tone}${small ? " pill-small" : ""}`}
      title={reason || undefined}
      aria-label={reason ? `${text}: ${reason}` : undefined}
    >
      <span className="pill-dot" aria-hidden="true" />
      {text}
    </span>
  );
}

export function TonePill({ tone, text, title, small = false }) {
  return (
    <span className={`pill pill-${tone}${small ? " pill-small" : ""}`} title={title || undefined}>
      <span className="pill-dot" aria-hidden="true" />
      {text}
    </span>
  );
}
