// Command palette sources for the desktop shell (issue #38).
//
// Everything here is a pure function of the data already loaded by App.jsx, so
// the palette needs no extra API calls of its own — that matters because a
// palette that issues its own fetches turns one keystroke into five requests and
// goes stale the moment it opens.
//
// Kept React-free so the ranking and the command table can be tested under plain
// `node` (see web/test/command_palette.test.js).

/** Navigate to a top-level panel. */
export function navCommands(nav) {
  const out = [];
  for (const section of nav || []) {
    for (const item of section.items || []) {
      out.push({
        id: `nav:${item.id}`,
        group: "go",
        title: item.label,
        subtitle: item.hint,
        keywords: [item.id, section.group],
        action: { type: "nav", view: item.id },
      });
    }
  }
  return out;
}

/**
 * Actions that act on the shell itself rather than navigating.
 *
 * `available` is resolved lazily at call time by the caller, because the same
 * command is conditionally useful (refresh is pointless with a dead backend, but
 * retry is exactly what you want there).
 */
export function shellCommands() {
  return [
    {
      id: "shell:refresh",
      group: "do",
      title: "Refresh all panels",
      subtitle: "re-fetch health, registry, manifest and coverage",
      keywords: ["reload", "re-fetch", "update", "poll"],
      action: { type: "refresh" },
    },
    {
      id: "shell:retry",
      group: "do",
      title: "Retry the control-plane API",
      subtitle: "use when the shell reports the backend as unreachable",
      keywords: ["reconnect", "backend", "offline", "unreachable"],
      action: { type: "retry" },
    },
    {
      id: "shell:copy-url",
      group: "do",
      title: "Copy this panel's API URL",
      subtitle: "the same-origin path behind what is on screen",
      keywords: ["clipboard", "link", "endpoint"],
      action: { type: "copy", path: "/api/registry" },
    },
  ];
}

/**
 * One command per registry panel, so the palette reaches a *panel detail* and not
 * just its tab — which is the difference between a palette that saves you clicks
 * and one that only mirrors the sidebar.
 */
export function subsystemCommands(registry) {
  const panels = registry && registry.data && Array.isArray(registry.data.panels) ? registry.data.panels : [];
  return panels
    .filter((p) => p && (p.id || p.name))
    .map((p) => ({
      id: `sub:${p.id || p.name}`,
      group: "subsystems",
      title: p.name || p.id,
      subtitle: [p.kind, p.status].filter(Boolean).join(" · ") || "registry panel",
      keywords: [p.id, p.binary, p.status, p.kind].filter(Boolean).map(String),
      action: { type: "nav", view: "subsystems", select: p.id || p.name },
    }));
}

/** One command per CLI coverage row, landing on that row's audited detail. */
export function cliCommands(coverage) {
  const results =
    coverage && coverage.data && Array.isArray(coverage.data.results) ? coverage.data.results : [];
  return results
    .filter((r) => r && r.name)
    .map((r) => {
      const gaps = Array.isArray(r.gaps) ? r.gaps.length : 0;
      return {
        id: `cli:${r.name}`,
        group: "cli",
        title: r.name,
        subtitle: gaps ? `${r.naming || "cli"} · ${gaps} gap${gaps === 1 ? "" : "s"}` : `${r.naming || "cli"} · no gaps`,
        keywords: [r.naming, ...(Array.isArray(r.gaps) ? r.gaps : [])].filter(Boolean).map(String),
        action: { type: "nav", view: "cli", select: r.name },
      };
    });
}

/** One command per dream, landing on that dream's detail pane. */
export function dreamCommands(dreams) {
  const rows = dreams && dreams.data && Array.isArray(dreams.data.dreams) ? dreams.data.dreams : [];
  return rows
    .filter((d) => d && (d.id || d.dream_id))
    .map((d) => {
      const id = d.id || d.dream_id;
      return {
        id: `dream:${id}`,
        group: "dreams",
        title: d.title || d.summary || String(id),
        subtitle: [d.status || d.state, d.created_at ? String(d.created_at).slice(0, 10) : null]
          .filter(Boolean)
          .join(" · ") || "dream",
        keywords: [id, d.status, d.state].filter(Boolean).map(String),
        action: { type: "nav", view: "dreams", select: id, sub: "review" },
      };
    });
}

/**
 * Every command the palette can currently offer.
 *
 * `data` is the already-fetched payload set from App.jsx. Nothing is fetched here.
 */
export function buildCommands({ nav, registry, coverage, dreams } = {}) {
  return [
    ...navCommands(nav),
    ...shellCommands(),
    ...subsystemCommands(registry),
    ...cliCommands(coverage),
    ...dreamCommands(dreams),
  ];
}

/**
 * Case-insensitive subsequence match.
 *
 * Subsequence rather than substring so `ovw` finds "Overview" and `wbs` finds
 * "Websites" — the behaviour people expect from a Cmd-K field. Returns the match
 * positions so the UI can highlight them, or null when there is no match.
 */
export function fuzzyMatch(query, text) {
  const q = String(query || "").trim().toLowerCase();
  const t = String(text || "");
  if (!q) return { positions: [], score: 0 };
  if (!t) return null;

  const lower = t.toLowerCase();
  // Exact substring is always the strongest signal; prefer it and highlight the run.
  const direct = lower.indexOf(q);
  if (direct !== -1) {
    const positions = [];
    for (let i = 0; i < q.length; i += 1) positions.push(direct + i);
    // Prefer matches at a word boundary, and shorter targets.
    let bonus = 0;
    if (direct === 0 || /[\s/_:-]/.test(lower[direct - 1] || "")) bonus += 40;
    bonus += Math.max(0, 20 - lower.length / 4);
    return { positions, score: 100 + bonus };
  }

  // Fall back to subsequence.
  const positions = [];
  let ti = 0;
  for (const ch of q) {
    const found = lower.indexOf(ch, ti);
    if (found === -1) return null;
    positions.push(found);
    ti = found + 1;
  }
  // Tighter matches rank higher.
  const span = positions[positions.length - 1] - positions[0] + 1;
  const score = 50 - Math.min(45, span - q.length) + Math.max(0, 10 - lower.length / 8);
  return { positions, score };
}

/**
 * Rank commands against a query.
 *
 * Title match outranks keyword match, which outranks subtitle match: typing
 * "websites" should put the Websites panel first, not a registry panel whose
 * binary happens to contain that string.
 */
export function rankCommands(commands, query, limit = 40) {
  const q = String(query || "").trim();
  if (!q) {
    // No query: keep the caller's order, but cap it so the list stays scannable.
    return commands.slice(0, limit).map((command) => ({ command, positions: [], score: 0 }));
  }

  const scored = [];
  for (const command of commands) {
    const titleMatch = fuzzyMatch(q, command.title);
    if (titleMatch) {
      scored.push({ command, positions: titleMatch.positions, score: titleMatch.score + 30 });
      continue;
    }

    const keywordHit = (command.keywords || []).find((k) => fuzzyMatch(q, k));
    if (keywordHit) {
      scored.push({ command, positions: [], score: fuzzyMatch(q, keywordHit).score });
      continue;
    }

    const subtitleMatch = fuzzyMatch(q, command.subtitle);
    if (subtitleMatch) {
      scored.push({ command, positions: [], score: subtitleMatch.score - 20 });
    }
  }

  scored.sort((a, b) => b.score - a.score || a.command.title.localeCompare(b.command.title));
  return scored.slice(0, limit);
}

/**
 * Move the selection by `delta`, wrapping at both ends.
 *
 * Returns 0 for an empty list rather than -1 so callers never index into nothing.
 */
export function nextIndex(current, delta, length) {
  if (!length) return 0;
  if (current < 0 || current >= length) return 0;
  return (current + delta + length) % length;
}
