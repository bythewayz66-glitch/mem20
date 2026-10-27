import React, { useCallback, useEffect, useRef } from "react";
import { tabbables, trapTarget, isInside, restoreTarget } from "../a11y.js";

/**
 * FocusTrap / Dialog — the single modal container in this shell.
 *
 * Both modal surfaces (the login gate and the #38 command palette) render through
 * this component so their keyboard behaviour cannot diverge:
 *
 *   - on mount, focus moves to the first tab stop (or the `initialFocus` node);
 *   - Tab / Shift-Tab wrap at the edges and never escape to the document;
 *   - a focusin that lands outside is pulled back in (portal/browser-find safety);
 *   - on unmount, focus is restored to whatever had it before, not to <body>.
 *
 * The decision logic lives in ../a11y.js and is unit-tested; this file is only the
 * React plumbing, which is why there is nothing clever in it.
 */
export default function FocusTrap({
  children,
  active = true,
  onEscape,
  initialFocus = null,
  restoreFallback = null,
  role = "dialog",
  labelledBy,
  label,
  describedBy,
  className = "",
  as: Tag = "div",
  ...rest
}) {
  const containerRef = useRef(null);
  // The node that had focus when the trap opened. Captured on mount, read on
  // unmount; a ref (not state) because restoring must not re-render anything.
  const openerRef = useRef(null);

  const focusFirst = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    if (initialFocus && typeof initialFocus.focus === "function" && isInside(container, initialFocus)) {
      initialFocus.focus();
      return;
    }
    const stops = tabbables(container);
    if (stops.length > 0) {
      stops[0].focus();
      return;
    }
    // Nothing focusable (a panel that is still loading): make the container itself
    // focusable for the duration, so the trap has somewhere to live and the screen
    // reader still announces the dialog.
    if (typeof container.focus === "function") {
      if (!container.hasAttribute("tabindex")) container.setAttribute("tabindex", "-1");
      container.focus();
    }
  }, [initialFocus]);

  useEffect(() => {
    if (!active) return undefined;

    const activeElement = typeof document !== "undefined" ? document.activeElement : null;
    openerRef.current = activeElement && activeElement !== document.body ? activeElement : null;

    // Focus after the paint that mounts the dialog: focusing a node that is still
    // display:none is a no-op, and the palette's input arrives in the same commit.
    const raf =
      typeof window !== "undefined" && typeof window.requestAnimationFrame === "function"
        ? window.requestAnimationFrame(focusFirst)
        : setTimeout(focusFirst, 0);

    return () => {
      if (typeof window !== "undefined" && typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(raf);
      } else {
        clearTimeout(raf);
      }

      // Restore. If the opener is gone (it often is: running a palette command
      // navigates away), use the caller's fallback and only then give up quietly.
      const target =
        restoreTarget(openerRef.current, restoreFallback, (el) =>
          Boolean(el && el.isConnected && typeof el.focus === "function"),
        ) || null;
      if (target) {
        try {
          target.focus({ preventScroll: true });
        } catch {
          try {
            target.focus();
          } catch {
            /* focus is best-effort: a removed node must not throw on unmount */
          }
        }
      }
      openerRef.current = null;
    };
  }, [active, focusFirst, restoreFallback]);

  function handleKeyDown(event) {
    if (event.key === "Escape") {
      // Escape is the dialog's, not the field's: stop it here so an Escape meant
      // for the palette does not also clear a filter in the tab behind it.
      event.stopPropagation();
      if (onEscape) {
        event.preventDefault();
        onEscape(event);
      }
      return;
    }

    if (event.key !== "Tab") return;

    const container = containerRef.current;
    if (!container) return;
    const stops = tabbables(container);
    const activeNode = typeof document !== "undefined" ? document.activeElement : null;
    const index = stops.indexOf(activeNode);
    const target = trapTarget({ count: stops.length, index, shift: Boolean(event.shiftKey) });
    if (target === null) return;
    event.preventDefault();
    const node = stops[target];
    if (node) node.focus();
  }

  function handleFocusIn(event) {
    const container = containerRef.current;
    if (!container) return;
    if (isInside(container, event.target)) return;
    // Something outside grabbed focus (browser find, a portal, an autofocus in the
    // page behind). Take it back rather than leaving the dialog with no focus.
    event.stopPropagation();
    focusFirst();
  }

  return (
    <Tag
      {...rest}
      ref={containerRef}
      className={className}
      role={role}
      aria-modal={role === "dialog" || role === "alertdialog" ? "true" : undefined}
      aria-label={labelledBy ? undefined : label}
      aria-labelledby={labelledBy}
      aria-describedby={describedBy}
      onKeyDown={handleKeyDown}
      onFocusIn={handleFocusIn}
    >
      {children}
    </Tag>
  );
}
