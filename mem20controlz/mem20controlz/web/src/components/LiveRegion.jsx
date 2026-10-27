import React, { useEffect, useRef, useState } from "react";

/**
 * A polite live region that announces a sentence produced by `a11y.js`.
 *
 * Why this is not just `<div aria-live="polite">{message}</div>`:
 *
 *   - **An empty region announces nothing.** Screen readers only speak on a change
 *     to a region that was *already* in the accessibility tree, so the node is
 *     mounted for the lifetime of the panel and only its text changes. Mounting it
 *     conditionally would announce nothing at all on the first result — the exact
 *     bug this is here to fix.
 *   - **Identical text is not re-announced.** React re-renders a filtered list on
 *     every keystroke even when the count did not move; relying on the DOM to
 *     dedupe gives "3 of 154 panels" spoken on every letter. `lastRef` makes the
 *     dedupe explicit and keeps the DOM text stable between identical states.
 *   - **A zero-width space clears it.** Going from "3 of 154" to silence needs a
 *     real character change or the region keeps its old value; "\u200b" is invisible
 *     to sighted users and unvoiced by readers.
 */
export default function LiveRegion({ message, politeness = "polite", atomic = true, className = "sr-only" }) {
  const [text, setText] = useState("");
  const lastRef = useRef(null);

  useEffect(() => {
    const next = typeof message === "string" ? message : "";
    if (next === lastRef.current) return;
    lastRef.current = next;
    setText(next);
  }, [message]);

  return (
    <div className={className} aria-live={politeness} aria-atomic={atomic ? "true" : "false"} role="status">
      {text || "\u200b"}
    </div>
  );
}
