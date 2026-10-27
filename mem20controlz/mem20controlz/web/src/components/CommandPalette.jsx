import React, { useEffect, useMemo, useRef, useState } from "react";
import { buildCommands, rankCommands, nextIndex } from "../commandPalette.js";

const GROUP_LABELS = {
  go: "go to",
  do: "do",
  subsystems: "subsystems",
  cli: "cli coverage",
  dreams: "dreams",
};

/**
 * Cmd-K / Ctrl-K command palette.
 *
 * Two things make this more than a second sidebar:
 *   - it reaches *entities*, not just tabs (a specific registry panel, a CLI row
 *     with gaps, a named dream), which is where the clicks actually are;
 *   - it is built only from payloads App.jsx already fetched, so opening it costs
 *     no requests.
 *
 * Keyboard: type to filter, Up/Down (or Ctrl-N/P) to move, Enter to run, Esc to
 * close. The list is a listbox with an active descendant so a screen reader
 * announces the highlighted row rather than only the query.
 */
export default function CommandPalette({ open, onClose, commands, onRun }) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  const results = useMemo(() => rankCommands(commands, query), [commands, query]);

  // Reset the cursor whenever the query changes, so Enter never runs a row the
  // user has not looked at.
  useEffect(() => {
    setActive(0);
  }, [query]);

  // Focus the field on open; clear it on close so the next open starts clean.
  useEffect(() => {
    if (open) {
      const t = setTimeout(() => inputRef.current && inputRef.current.focus(), 0);
      return () => clearTimeout(t);
    }
    setQuery("");
    setActive(0);
    return undefined;
  }, [open]);

  // Keep the highlighted row in view when moving with the keyboard.
  useEffect(() => {
    if (!open || !listRef.current) return;
    const node = listRef.current.querySelector('[data-active="true"]');
    if (node && typeof node.scrollIntoView === "function") {
      node.scrollIntoView({ block: "nearest" });
    }
  }, [active, open, results.length]);

  if (!open) return null;

  function run(entry) {
    if (!entry) return;
    onRun(entry.command);
    onClose();
  }

  function onKeyDown(event) {
    if (event.key === "ArrowDown" || (event.ctrlKey && event.key === "n")) {
      event.preventDefault();
      setActive((i) => nextIndex(i, 1, results.length));
      return;
    }
    if (event.key === "ArrowUp" || (event.ctrlKey && event.key === "p")) {
      event.preventDefault();
      setActive((i) => nextIndex(i, -1, results.length));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      run(results[active]);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
    }
  }

  // group the ranked results while preserving rank order within each group
  const grouped = [];
  results.forEach((entry, index) => {
    const key = entry.command.group;
    const last = grouped[grouped.length - 1];
    if (!last || last.key !== key) grouped.push({ key, items: [] });
    grouped[grouped.length - 1].items.push({ entry, index });
  });

  return (
    <div
      className="palette-overlay"
      role="presentation"
      onMouseDown={(event) => {
        // click on the backdrop closes; clicks inside the panel do not
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="palette" role="dialog" aria-modal="true" aria-label="command palette">
        <input
          ref={inputRef}
          className="palette-input"
          type="text"
          value={query}
          placeholder="search panels, subsystems, cli rows, dreams, or an action…"
          aria-label="command"
          aria-controls="palette-results"
          aria-activedescendant={results.length ? `palette-opt-${active}` : undefined}
          autoComplete="off"
          spellCheck="false"
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
        />

        <ul className="palette-results" id="palette-results" role="listbox" ref={listRef}>
          {results.length === 0 ? (
            <li className="palette-empty" role="presentation">
              nothing matches <span className="mono">{query}</span>. A palette that showed unrelated commands here would be
              worse than an empty list.
            </li>
          ) : null}

          {grouped.map((group) => (
            <li key={group.key} role="presentation">
              <div className="palette-group-title">{GROUP_LABELS[group.key] || group.key}</div>
              <ul role="presentation">
                {group.items.map(({ entry, index }) => (
                  <li
                    key={entry.command.id}
                    id={`palette-opt-${index}`}
                    role="option"
                    aria-selected={index === active}
                    data-active={index === active ? "true" : undefined}
                    className={`palette-item${index === active ? " palette-item-active" : ""}`}
                    onMouseEnter={() => setActive(index)}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      run(entry);
                    }}
                  >
                    <span className="palette-item-title">
                      {highlight(entry.command.title, entry.positions)}
                    </span>
                    {entry.command.subtitle ? (
                      <span className="palette-item-sub">{entry.command.subtitle}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>

        <div className="palette-foot">
          <span>
            <kbd>↑</kbd>
            <kbd>↓</kbd> move
          </span>
          <span>
            <kbd>↵</kbd> run
          </span>
          <span>
            <kbd>esc</kbd> close
          </span>
          <span className="palette-count mono">
            {results.length} of {commands.length}
          </span>
        </div>
      </div>
    </div>
  );
}

/** Wrap the matched characters so the ranking is visible, not just asserted. */
function highlight(text, positions) {
  if (!positions || positions.length === 0) return text;
  const marks = new Set(positions);
  return String(text)
    .split("")
    .map((ch, i) => (marks.has(i) ? <mark key={i}>{ch}</mark> : <React.Fragment key={i}>{ch}</React.Fragment>));
}

export { buildCommands };
