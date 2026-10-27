import React from "react";

export function TabBar({ tabs, active, onChange, label = "views" }) {
  // Real tablist keyboard model: only the selected tab is a tab stop, Arrow keys move
  // between tabs. Before this, every tab was tabbable and the arrows did nothing, so
  // a screen reader announced "tab, 1 of 5" five times on the way into the panel.
  const index = tabs.findIndex((tab) => tab.id === active);

  function onKeyDown(event) {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft" && event.key !== "Home" && event.key !== "End") {
      return;
    }
    event.preventDefault();
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    const target = tabs[next];
    if (!target) return;
    onChange(target.id);
    // Move focus with the selection so the next arrow press continues from here.
    const node = event.currentTarget.querySelector(`[data-tab-id="${target.id}"]`);
    if (node && typeof node.focus === "function") node.focus();
  }

  return (
    <div className="tabbar" role="tablist" aria-label={label} onKeyDown={onKeyDown}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          id={`tab-${label.replace(/\s+/g, "-")}-${tab.id}`}
          data-tab-id={tab.id}
          aria-selected={active === tab.id}
          tabIndex={active === tab.id ? 0 : -1}
          className={`tab${active === tab.id ? " tab-active" : ""}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
          {tab.badge !== undefined && tab.badge !== null ? <span className="tab-badge">{tab.badge}</span> : null}
        </button>
      ))}
    </div>
  );
}

export function Panel({ title, subtitle, actions, children, className = "", scroll = false }) {
  return (
    <section className={`panel ${className}`}>
      {(title || actions) && (
        <header className="panel-head">
          <div className="panel-titles">
            {title ? <h2>{title}</h2> : null}
            {subtitle ? <span className="panel-sub">{subtitle}</span> : null}
          </div>
          {actions ? <div className="panel-actions">{actions}</div> : null}
        </header>
      )}
      <div className={scroll ? "panel-body panel-scroll" : "panel-body"}>{children}</div>
    </section>
  );
}

export function Section({ title, children, actions }) {
  return (
    <div className="block">
      <div className="block-head">
        <h3>{title}</h3>
        {actions ? <div className="block-actions">{actions}</div> : null}
      </div>
      {children}
    </div>
  );
}

export function Row({ label, children, mono = false }) {
  return (
    <div className="row">
      <span className="row-label">{label}</span>
      <span className={`row-value${mono ? " mono" : ""}`}>{children}</span>
    </div>
  );
}

export function Grid({ items, columns = 4 }) {
  return (
    <div className="grid" style={{ "--cols": columns }}>
      {items.map((item) => (
        <div className="cell" key={item.label}>
          <span className="cell-label">{item.label}</span>
          {/* A cell is a summary line, not a data structure. Rendering a raw
              object or array here throws away the whole React tree, and the
              failure names neither the component nor the field - so values are
              stringified here, exactly as `Table` already does for its cells. */}
          <span className={`cell-value ${item.tone ? `tone-${item.tone}` : ""}`}>{cellText(item.value)}</span>
          {item.hint ? <span className="cell-hint">{item.hint}</span> : null}
        </div>
      ))}
    </div>
  );
}

function cellText(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") {
    if (Array.isArray(value)) return value.length ? `${value.length} item(s)` : "—";
    return `${Object.keys(value).length} field(s)`;
  }
  return String(value);
}

export function Chips({ values, empty = "none reported" }) {
  if (!Array.isArray(values) || values.length === 0) {
    return <span className="muted">{empty}</span>;
  }
  return (
    <span className="chips">
      {values.map((value, index) => (
        <code className="chip" key={`${String(value)}-${index}`}>
          {String(value)}
        </code>
      ))}
    </span>
  );
}

export function Mono({ value, className = "" }) {
  if (value === null || value === undefined || value === "") {
    return <span className="muted">not reported</span>;
  }
  return <span className={`mono ${className}`}>{String(value)}</span>;
}

export function YesNo({ value }) {
  // A boolean data field is not a health signal: render it neutrally. Colour here
  // would imply a fault the API never reported.
  if (value === true) return <span className="bool">yes</span>;
  if (value === false) return <span className="bool">no</span>;
  return <span className="muted">not reported</span>;
}

export function Json({ value, empty = "no data" }) {
  if (value === null || value === undefined) {
    return <pre className="json empty">{empty}</pre>;
  }
  let text;
  try {
    text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  } catch {
    text = String(value);
  }
  return <pre className="json">{text}</pre>;
}

export function Table({ columns, rows, empty = "no rows returned by the API", rowKey, onRowClick, selectedKey, caption }) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return <div className="table-empty">{empty}</div>;
  }
  return (
    <div className="table-wrap">
      <table className="grid-table">
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" style={column.width ? { width: column.width } : undefined}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const key = rowKey ? rowKey(row, index) : index;
            const selected = selectedKey !== undefined && selectedKey === key;
            return (
              <tr
                key={key}
                className={`${onRowClick ? "clickable" : ""} ${selected ? "selected" : ""}`}
                onClick={onRowClick ? () => onRowClick(row, index) : undefined}
                // A click handler on a <tr> is invisible to the keyboard. tabIndex +
                // Enter/Space makes the same row reachable and activatable without
                // turning the table into a grid (which would require aria-selected
                // on a role that the native table does not have).
                tabIndex={onRowClick ? 0 : undefined}
                onKeyDown={
                  onRowClick
                    ? (event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          onRowClick(row, index);
                        }
                      }
                    : undefined
                }
                aria-selected={onRowClick ? Boolean(selected) : undefined}
              >
                {columns.map((column) => (
                  <td key={column.key} className={column.className || ""}>
                    {column.render ? column.render(row, index) : row[column.key] === undefined ? <span className="muted">—</span> : String(row[column.key])}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
