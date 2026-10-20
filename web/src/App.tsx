/* The unified shell: one app, one nav, one auth model, one API client.
 *
 * Every surface is a view under `src/views/`. The nav below is the ONLY
 * navigation in the product — no per-surface tabs, no second auth flow.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { Pill } from './components/ui';
import { getDoorBase, door } from './lib/api';
import Kanban from './views/Kanban';
import Dreams from './views/Dreams';
import AgentBuilder from './views/AgentBuilder';
import Teamily from './views/Teamily';
import DocsFaq from './views/DocsFaq';
import Sales from './views/Sales';
import MemoryModel from './views/MemoryModel';
import DoorSync from './views/DoorSync';
import Connection from './views/Connection';

export type Route =
  | 'kanban'
  | 'dreams'
  | 'agents'
  | 'teamily'
  | 'docs'
  | 'sales'
  | 'memory'
  | 'door'
  | 'connection';

const NAV: Array<{ id: Route; label: string; group: string; icon: string }> = [
  { id: 'kanban', label: 'Kanban', group: 'Operate', icon: 'M3 4h5v16H3zM10 4h5v10h-5zM17 4h4v7h-4z' },
  { id: 'dreams', label: 'Dreams', group: 'Operate', icon: 'M12 3a9 9 0 100 18 9 9 0 000-18zM8 12a4 4 0 018 0' },
  { id: 'agents', label: 'Agent Builder', group: 'Operate', icon: 'M12 3v3M12 18v3M4.2 7.5l2.6 1.5M17.2 15l2.6 1.5M4.2 16.5l2.6-1.5M17.2 9l2.6-1.5M12 8a4 4 0 100 8 4 4 0 000-8z' },
  { id: 'teamily', label: 'Teamily', group: 'Operate', icon: 'M9 11a3.5 3.5 0 100-7 3.5 3.5 0 000 7zM2.5 20a6.5 6.5 0 0113 0M16 11.5a3 3 0 100-6M17.5 20a5.5 5.5 0 00-2-4.3' },
  { id: 'docs', label: 'Docs / FAQ', group: 'Understand', icon: 'M5 3h9l5 5v13H5zM14 3v5h5M8 13h8M8 17h6' },
  { id: 'sales', label: 'Sales', group: 'Sell', icon: 'M4 20V9M10 20V4M16 20v-7M22 20H2' },
  { id: 'memory', label: 'Memory model', group: 'Trust', icon: 'M12 3l8 4.5v9L12 21l-8-4.5v-9zM12 12l8-4.5M12 12v9M12 12L4 7.5' },
  { id: 'door', label: 'Door Sync', group: 'Trust', icon: 'M5 3h14v18H5zM12 12h.01M9 21v-2h6v2' },
  { id: 'connection', label: 'Connection', group: 'Trust', icon: 'M9 15l6-6M7.5 10.5l-1.9 1.9a3.5 3.5 0 004.9 4.9l1.9-1.9M16.5 13.5l1.9-1.9a3.5 3.5 0 00-4.9-4.9L11.6 8.6' },
];

const TITLES: Record<Route, { title: string; sub: string }> = {
  kanban: { title: 'Kanban', sub: 'the one board — mem20-kanban door, REST :8221' },
  dreams: { title: 'Dreams', sub: 'promotion and provenance, evidence-gated' },
  agents: { title: 'Agent Builder', sub: 'identity · prompt · tools · memory scope · lifecycle' },
  teamily: { title: 'Teamily', sub: 'members · roles · groups · activity' },
  docs: { title: 'Docs / FAQ', sub: 'searchable, tool reference from source' },
  sales: { title: 'Sales', sub: 'positioning · proof · pricing' },
  memory: { title: 'Memory model', sub: 'the five hard invariants, enforced at the store layer' },
  door: { title: 'Door Sync', sub: 'the real door contract, reported honestly' },
  connection: { title: 'Connection', sub: 'where this shell reads from' },
};

export default function App() {
  const [route, setRoute] = useState<Route>(() => {
    const h = window.location.hash.replace('#', '') as Route;
    return NAV.some((n) => n.id === h) ? h : 'kanban';
  });
  const [doorUp, setDoorUp] = useState<boolean | null>(null);
  const [doorLabel, setDoorLabel] = useState(getDoorBase());

  useEffect(() => {
    const onHash = () => {
      const h = window.location.hash.replace('#', '') as Route;
      if (NAV.some((n) => n.id === h)) setRoute(h);
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const go = (r: Route) => {
    window.location.hash = r;
    setRoute(r);
  };

  const probe = useCallback(async () => {
    const ok = await door.healthy();
    setDoorUp(ok);
    setDoorLabel(getDoorBase());
    return ok;
  }, []);

  useEffect(() => {
    probe();
    const t = setInterval(probe, 30000);
    return () => clearInterval(t);
  }, [probe]);

  const t = TITLES[route] ?? TITLES.kanban;

  return (
    <div className="app">
      <aside className="rail">
        <div className="rail-brand">
          <div className="glyph">20</div>
          <div>
            <div className="brand-name">mem20</div>
            <div className="brand-sub">auditable memory</div>
          </div>
        </div>

        <nav className="rail-nav">
          {['Operate', 'Understand', 'Sell', 'Trust'].map((group) => (
            <div key={group}>
              <div className="nav-group-label">{group}</div>
              {NAV.filter((n) => n.group === group).map((n) => (
                <button
                  key={n.id}
                  className={`nav-item ${route === n.id ? 'active' : ''}`}
                  onClick={() => go(n.id)}
                  title={n.label}
                >
                  <svg className="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                    <path d={n.icon} />
                  </svg>
                  {n.label}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="rail-foot">
          <div className="authbar">
            <Pill tone={doorUp === null ? '' : doorUp ? 'green' : 'red'} dot>
              door {doorUp === null ? '…' : doorUp ? 'up' : 'down'}
            </Pill>
            <button className="btn ghost sm" style={{ marginLeft: 'auto' }} onClick={() => go('connection')}>
              config
            </button>
          </div>
          <div style={{ marginTop: 8, color: 'var(--ink-3)', fontSize: 10.5, fontFamily: 'var(--mono)' }}>
            {doorLabel}
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <h1>{t.title}</h1>
          <span className="sub">{t.sub}</span>
          <span className="spacer" />
          <Pill tone="violet" mono>
            v0.1.0
          </Pill>
        </header>

        <div className="content">
          {route === 'kanban' && <Kanban doorUp={doorUp} onProbe={probe} />}
          {route === 'dreams' && <Dreams />}
          {route === 'agents' && <AgentBuilder />}
          {route === 'teamily' && <Teamily />}
          {route === 'docs' && <DocsFaq />}
          {route === 'sales' && <Sales onOpenApp={() => go('kanban')} />}
          {route === 'memory' && <MemoryModel />}
          {route === 'door' && <DoorSync doorUp={doorUp} onProbe={probe} />}
          {route === 'connection' && <Connection onProbe={probe} />}
        </div>
      </main>
    </div>
  );
}
