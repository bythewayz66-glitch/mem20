import React, { useCallback, useEffect, useMemo, useState } from "react";
import StatusPill from "./components/StatusPill.jsx";
import LoginGate from "./components/LoginGate.jsx";
import { ErrorBanner, NoticeBanner } from "./components/Banner.jsx";
import { StateNotice, StaleRibbon } from "./components/StateNotice.jsx";
import CommandPalette from "./components/CommandPalette.jsx";
import { buildCommands } from "./commandPalette.js";
import { KNOWN_STATUSES } from "./status.js";
import { LIFECYCLE, lifecycleFor, ageSecondsOf, formatAge } from "./lifecycle.js";
import { useResource, formatClock } from "./hooks.js";
import { fetchAuthStatus, isUnauthorized } from "./auth.js";
import Overview from "./tabs/Overview.jsx";
import Subsystems from "./tabs/Subsystems.jsx";
import CliCoverage from "./tabs/CliCoverage.jsx";
import Websites from "./tabs/Websites.jsx";
import Dreams from "./tabs/Dreams.jsx";

const POLL_MS = 10000;

const NAV = [
  {
    group: "control",
    items: [
      { id: "overview", label: "Overview", hint: "service + registry census" },
      { id: "subsystems", label: "Subsystems", hint: "registry panels + probes" },
      { id: "cli", label: "CLI coverage", hint: "fleet CLI contract audit" },
    ],
  },
  {
    group: "fleet / web",
    items: [{ id: "websites", label: "Websites", hint: "sites · DNS · health · logs · pages" }],
  },
  {
    group: "imagination",
    items: [{ id: "dreams", label: "Dreams", hint: "review · keep · run" }],
  },
];

function NavBadge({ id, registry }) {
  const data = registry.data;
  if (id === "subsystems") {
    return data && Array.isArray(data.panels) ? <span className="nav-badge">{data.panels.length}</span> : null;
  }
  if (id === "overview" && data && data.counts && typeof data.counts === "object") {
    const degraded = KNOWN_STATUSES.filter((key) => key !== "ok" && data.counts[key] > 0).reduce(
      (sum, key) => sum + data.counts[key],
      0,
    );
    return degraded > 0 ? <span className="nav-badge nav-badge-warn">{degraded}</span> : null;
  }
  return null;
}

export default function App() {
  const [view, setView] = useState("overview");
  const [authStatus, setAuthStatus] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Cmd-K state. `paletteSeen` gates the one fetch the palette needs, so opening
  // the app still issues the same requests it did before #38 — the dream list is
  // only fetched once someone actually reaches for the palette or the tab.
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteSeen, setPaletteSeen] = useState(false);
  const [focusRequest, setFocusRequest] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      const status = await fetchAuthStatus();
      setAuthStatus(status);
      return status;
    } catch {
      setAuthStatus(null);
      return null;
    } finally {
      setAuthChecked(true);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Two long-lived polls live at the top so switching tabs never restarts them.
  const health = useResource("/api/health", { pollMs: POLL_MS });
  const registry = useResource("/api/registry", { pollMs: POLL_MS });
  const manifest = useResource("/api/websites/manifest", { enabled: view === "websites" || view === "overview" });
  const coverage = useResource("/api/cli/coverage", { enabled: view === "cli" || view === "subsystems" });
  const dreams = useResource("/api/dreams", { enabled: paletteSeen || view === "dreams" });

  // A 401 on any protected route means the session lapsed, so show the gate
  // rather than leaving four red "unauthorized" banners on screen.
  const unauthorized = isUnauthorized(registry.error) || isUnauthorized(manifest.error) || isUnauthorized(coverage.error);
  const locked = authChecked && (unauthorized || authStatus?.authenticated === false);

  useEffect(() => {
    if (unauthorized) checkAuth();
  }, [unauthorized, checkAuth]);

  function refreshAll() {
    health.refresh();
    registry.refresh();
    manifest.refresh();
    coverage.refresh();
    dreams.refresh();
  }

  // Cmd-K / Ctrl-K opens the palette; Esc inside it closes it. Registered once at
  // the document level because the palette must be reachable from any panel
  // without every panel wiring its own listener.
  useEffect(() => {
    function onKey(event) {
      const isPalette = (event.metaKey || event.ctrlKey) && (event.key === "k" || event.key === "K");
      if (isPalette) {
        event.preventDefault();
        setPaletteSeen(true);
        setPaletteOpen((open) => !open);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const commands = useMemo(
    () => buildCommands({ nav: NAV, registry, coverage, dreams }),
    [registry, registry.data, coverage, coverage.data, dreams, dreams.data],
  );

  // A palette entry can name an entity *inside* a panel, so hand the target down
  // rather than only switching the tab — otherwise "open panel X" lands the user
  // on a list they still have to search.
  function runCommand(command) {
    const action = command && command.action ? command.action : {};
    if (action.type === "refresh") {
      refreshAll();
      return;
    }
    if (action.type === "retry") {
      health.refresh();
      registry.refresh();
      return;
    }
    if (action.type === "copy") {
      const path = action.path || "/api/registry";
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(new URL(path, window.location.origin).toString()).catch(() => {});
      }
      return;
    }
    if (action.type === "nav") {
      setView(action.view);
      if (action.select !== undefined) {
        setFocusRequest({ view: action.view, select: action.select, sub: action.sub, nonce: Date.now() });
      }
    }
  }

  function handleAuthenticated() {
    checkAuth();
    refreshAll();
  }

  const healthData = health.data;

  // The shell's own lifecycle, separate from the fleet's status vocabulary.
  // `backendDown` means we have never received a usable /api/health response, so
  // there is nothing honest to render inside the content area.
  const backendState = lifecycleFor(health);
  const backendDown = backendState === LIFECYCLE.UNREACHABLE;

  if (locked) {
    return <LoginGate status={authStatus} onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div className="shell">
      {/* The nav is a 248px rail of buttons before the content, and panels are swapped
          by state rather than by URL, so there is no browser "skip to main" to lean
          on: without this every panel change costs ~8 Tab presses. */}
      <a className="skip-link" href="#main-content">
        skip to content
      </a>
      <aside className="nav">
        <div className="nav-brand">
          <span className="nav-brand-name">mem20</span>
          <span className="nav-brand-sub">control plane</span>
        </div>
        {NAV.map((section) => (
          <nav className="nav-group" key={section.group}>
            <span className="nav-group-title">{section.group}</span>
            {section.items.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`nav-item${view === item.id ? " nav-item-active" : ""}`}
                onClick={() => setView(item.id)}
                aria-current={view === item.id ? "page" : undefined}
              >
                <span className="nav-item-label">{item.label}</span>
                <NavBadge id={item.id} registry={registry} />
                <span className="nav-item-hint">{item.hint}</span>
              </button>
            ))}
          </nav>
        ))}
        <div className="nav-foot">
          <div className="nav-foot-row">
            <span>api</span>
            <span className="mono">same-origin /api</span>
          </div>
          <div className="nav-foot-row">
            <span>poll</span>
            <span className="mono">{POLL_MS / 1000}s · timeout 20s</span>
          </div>
        </div>
      </aside>

      {/* tabIndex={-1} is what makes the skip link work: a <main> without it is not
          focusable, so the anchor scrolls but focus stays on the link. */}
      <main className="main" id="main-content" tabIndex={-1}>
        <header className="topbar">
          <div className="topbar-left">
            <h1>mem20 control plane</h1>
            <span className="topbar-sub">
              {view === "overview"
                ? "service + registry census"
                : view === "subsystems"
                  ? "registry panels, probes and CLI output"
                  : view === "cli"
                    ? "fleet CLI contract coverage"
                    : view === "dreams"
                      ? "review a dream, keep the good ones"
                      : "sites, DNS, systemd health, journals, Pages"}
            </span>
          </div>
          <div className="topbar-right">
            {healthData ? (
              <span className="topbar-service">
                <span className="mono">{healthData.service || "service not reported"}</span>
                <span className="mono muted">v{healthData.version || "?"}</span>
              </span>
            ) : null}
            <StatusPill
              status={healthData ? healthData.status : null}
              reason={health.error ? health.error.message : undefined}
              label={healthData ? undefined : health.error ? "api unreachable" : "not checked"}
            />
            <span className="topbar-clock mono" title="last /api/registry response">
              {formatClock(registry.updatedAt)}
            </span>
            <button type="button" className="btn btn-primary" onClick={refreshAll}>
              refresh
            </button>
            <button
              type="button"
              className="btn btn-ghost palette-trigger"
              onClick={() => {
                setPaletteSeen(true);
                setPaletteOpen(true);
              }}
              title="open the command palette (Cmd-K)"
              aria-keyshortcuts="Meta+K Control+K"
            >
              <kbd>⌘K</kbd>
            </button>
          </div>
        </header>

        {health.error ? (
          <div className="strip">
            <StateNotice
              state={backendState}
              context="control-plane API"
              resource={health}
              onRetry={health.refresh}
            />
          </div>
        ) : null}
        {!health.error && registry.error ? (
          <div className="strip">
            <StateNotice
              state={lifecycleFor(registry)}
              context="registry"
              resource={registry}
              onRetry={registry.refresh}
            />
          </div>
        ) : null}
        {!health.error && !registry.error ? (
          <div className="strip strip-quiet">
            <StaleRibbon resource={health} context="control-plane API" onRetry={health.refresh} />
            <StaleRibbon resource={registry} context="registry" onRetry={registry.refresh} />
          </div>
        ) : null}

        {authStatus?.admitted_by === "loopback" ? (
          <div className="strip">
            <NoticeBanner tone="info" title="no login required on this machine">
              This request was admitted because it arrived on a loopback socket, not because a password was
              checked. That trust stops applying the moment the panel is reached from elsewhere — including
              through a tunnel or reverse proxy — and the password comes back then.
            </NoticeBanner>
          </div>
        ) : null}

        <div className="content">
          {backendDown ? (
            // Never a blank pane: the backend is gone, so say so once, here,
            // instead of letting five tabs each render an empty rectangle.
            <StateNotice
              state={backendState}
              context="control plane"
              resource={health}
              onRetry={health.refresh}
            />
          ) : (
            <>
              {view === "overview" ? (
                <Overview health={health} registry={registry} manifest={manifest} onRefreshAll={refreshAll} />
              ) : null}
              {view === "subsystems" ? (
                <Subsystems registry={registry} coverage={coverage} focusRequest={focusRequest} />
              ) : null}
              {view === "cli" ? (
                <CliCoverage coverage={coverage} focusRequest={focusRequest} />
              ) : null}
              {view === "websites" ? <Websites manifest={manifest} /> : null}
              {view === "dreams" ? <Dreams focusRequest={focusRequest} /> : null}
            </>
          )}
        </div>
      </main>

      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        commands={commands}
        onRun={runCommand}
      />
    </div>
  );
}
