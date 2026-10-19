/**
 * The mem20 shell.
 *
 * One nav, one theme, one design system, one place where "which backend am I
 * talking to" is visible. Every surface is a route inside this frame — nothing
 * is a bolted-on page, which is the whole point of the exercise.
 *
 * The teamz application lives at `src/teamz/` and is mounted at `/teamz`; it
 * supplies the token block and the workspace store that Kanban, Dreams, Agents,
 * Tools and Docs all render against.
 */

import { Suspense, lazy, useEffect, useState } from 'react';
import { useRoute, useScrollReset, type RouteId } from './lib/router';
import { usePersisted } from './lib/useAsync';
import { SOURCE_MODE } from './api/config';
import {
  Chip,
  IconBoard,
  IconBook,
  IconCube,
  IconDream,
  IconLink,
  IconMenu,
  IconMoon,
  IconSun,
  IconUsers,
  IconWarn,
  IconX,
  LoadingState,
} from './components/ui';

// Code-split per surface: the tool registry and kanban capture are the two
// biggest payloads, and neither should be in the first paint of a chat screen.
const KanbanView = lazy(() => import('./routes/KanbanView'));
const DreamsView = lazy(() => import('./routes/DreamsView'));
const AgentsView = lazy(() => import('./routes/AgentsView'));
const TeamView = lazy(() => import('./routes/TeamView'));
const ToolsView = lazy(() => import('./routes/ToolsView'));
const DocsView = lazy(() => import('./routes/DocsView'));
const StatusView = lazy(() => import('./routes/StatusView'));

interface NavEntry {
  id: RouteId;
  label: string;
  icon: (p: { size?: number; className?: string }) => JSX.Element;
  title: string;
  blurb: string;
  group: string;
}

const NAV: NavEntry[] = [
  {
    id: 'kanban',
    label: 'Kanban',
    icon: IconBoard,
    title: 'Kanban',
    blurb: 'Boards, cards, WIP limits, Sarge and board configuration',
    group: 'Operate',
  },
  {
    id: 'dreams',
    label: 'Dreams',
    icon: IconDream,
    title: 'Dreams',
    blurb: 'Lineages, promotion, provenance and the hollow census',
    group: 'Operate',
  },
  {
    id: 'agents',
    label: 'Agents',
    icon: IconCube,
    title: 'Agent builder',
    blurb: 'Identity, endpoint, model, prompt and tool scopes',
    group: 'Operate',
  },
  {
    id: 'teamz',
    label: 'Team',
    icon: IconUsers,
    title: 'Team workspace',
    blurb: 'Rooms, members, @mention routing and shared context',
    group: 'Operate',
  },
  {
    id: 'tools',
    label: 'Tools',
    icon: IconLink,
    title: 'Tool surface',
    blurb: 'Every registered tool, with its real input schema',
    group: 'Understand',
  },
  {
    id: 'docs',
    label: 'Docs & FAQ',
    icon: IconBook,
    title: 'Docs & FAQ',
    blurb: 'Concepts, endpoints and the answers to the awkward questions',
    group: 'Understand',
  },
  {
    id: 'status',
    label: 'Connection',
    icon: IconWarn,
    title: 'Connection',
    blurb: 'What is reachable right now, and what a capture is',
    group: 'Understand',
  },
];

export default function App() {
  const [route, navigate] = useRoute();
  const [theme, setTheme] = usePersisted<'dark' | 'light'>('mem20.theme', 'dark');
  const [navOpen, setNavOpen] = useState(false);

  useScrollReset(route.id);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setNavOpen(false);
  }, [route.id]);

  const entry = NAV.find((n) => n.id === route.id) ?? NAV[0];

  const groups = NAV.reduce<Record<string, NavEntry[]>>((acc, item) => {
    (acc[item.group] ??= []).push(item);
    return acc;
  }, {});

  return (
    <div className="shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>

      {navOpen ? (
        <div className="nav-scrim" onClick={() => setNavOpen(false)} aria-hidden="true" />
      ) : null}

      <nav className="nav" data-open={navOpen} aria-label="Primary">
        <div className="nav-brand">
          <span className="nav-mark" aria-hidden="true">
            m20
          </span>
          <span className="nav-brand-text">
            <strong>mem20</strong>
            <span>unified console</span>
          </span>
          <button
            type="button"
            className="btn btn-ghost btn-sm nav-toggle"
            style={{ marginLeft: 'auto' }}
            onClick={() => setNavOpen(false)}
            aria-label="Close navigation"
          >
            <IconX size={15} />
          </button>
        </div>

        {Object.entries(groups).map(([group, items]) => (
          <div key={group}>
            <div className="nav-group-label">{group}</div>
            {items.map((item) => {
              const Icon = item.icon;
              const active = route.id === item.id;
              return (
                <a
                  key={item.id}
                  href={`#/${item.id}`}
                  className="nav-item"
                  aria-current={active ? 'page' : undefined}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(item.id);
                  }}
                >
                  <Icon size={17} className="nav-item-icon" />
                  <span className="nav-item-label">{item.label}</span>
                </a>
              );
            })}
          </div>
        ))}

        <div className="nav-foot">
          <a
            className="nav-item"
            href="https://github.com/bythewayz66-glitch/mem20"
            target="_blank"
            rel="noreferrer noopener"
          >
            <IconLink size={16} className="nav-item-icon" />
            <span className="nav-item-label">Canonical repo</span>
          </a>
          <div className="flex" style={{ padding: '2px 8px 0' }}>
            <Chip tone={SOURCE_MODE === 'live' ? 'green' : 'amber'} title="VITE_SOURCE_MODE">
              {SOURCE_MODE}
            </Chip>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              style={{ marginLeft: 'auto' }}
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            >
              {theme === 'dark' ? <IconSun size={15} /> : <IconMoon size={15} />}
            </button>
          </div>
        </div>
      </nav>

      <div className="workspace">
        <header className="topbar">
          <button
            type="button"
            className="btn btn-ghost btn-sm nav-toggle"
            onClick={() => setNavOpen(true)}
            aria-label="Open navigation"
          >
            <IconMenu size={17} />
          </button>
          <div className="topbar-title">
            <h1>{entry.title}</h1>
            <p>{entry.blurb}</p>
          </div>
        </header>

        <main className="content" id="main">
          <div className="content-inner">
            <Suspense fallback={<LoadingState rows={4} label={`Opening ${entry.title}`} />}>
              {route.id === 'kanban' ? (
                <KanbanView
                  param={decodeURIComponent(route.param)}
                  onNavigate={(name) => navigate('kanban', encodeURIComponent(name))}
                />
              ) : null}
              {route.id === 'dreams' ? (
                <DreamsView param={decodeURIComponent(route.param)} />
              ) : null}
              {route.id === 'agents' ? <AgentsView /> : null}
              {route.id === 'teamz' ? <TeamView /> : null}
              {route.id === 'tools' ? <ToolsView /> : null}
              {route.id === 'docs' ? <DocsView /> : null}
              {route.id === 'status' ? <StatusView /> : null}
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  );
}
