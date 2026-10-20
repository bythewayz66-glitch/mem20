/* Agent Builder — built on the REAL tool catalog.
 *
 * src/data/tools.json is not hand-written: it was extracted by AST-parsing the
 * estate's own mcp/tools/*.py, reading every mt.Tool(name=, title=,
 * description=, inputSchema=) call. So the domain list and counts below are the
 * estate's actual registered tools, not a marketing number.
 */
import React, { useMemo, useState } from 'react';
import raw from '../data/tools.json';
import { Notice, Panel, Pill } from '../components/ui';

type Tool = { name: string; title: string; description: string; domain: string; params: string[] };
const CATALOG = raw as unknown as { count: number; domains?: number; tools: Tool[]; files_scanned: number };

const LIFECYCLE = ['draft', 'provisioned', 'active', 'paused', 'retired'];
const SCOPES = [
  { id: 'user', label: 'user', note: 'durable facts about the operator' },
  { id: 'project', label: 'project', note: 'state of the work in flight' },
  { id: 'session', label: 'session', note: 'this conversation only' },
  { id: 'none', label: 'none', note: 'no recall — tools only' },
];

export default function AgentBuilder() {
  const [name, setName] = useState('');
  const [prompt, setPrompt] = useState('');
  const [scope, setScope] = useState('project');
  const [stage, setStage] = useState('draft');
  const [q, setQ] = useState('');
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [domFilter, setDomFilter] = useState('');

  const domains = useMemo(() => {
    const m = new Map<string, number>();
    CATALOG.tools.forEach((t) => m.set(t.domain, (m.get(t.domain) || 0) + 1));
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, []);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    return CATALOG.tools.filter((t) => {
      if (domFilter && t.domain !== domFilter) return false;
      if (!term) return true;
      return (
        t.name.toLowerCase().includes(term) ||
        t.title.toLowerCase().includes(term) ||
        t.description.toLowerCase().includes(term)
      );
    });
  }, [q, domFilter]);

  return (
    <div className="page wide">
      <p className="lede">
        Five fields decide what an agent is: identity, prompt, tools, memory scope, lifecycle. The tool list is the estate's
        real catalog — {CATALOG.count} tools across {domains.length} domains, extracted by parsing{' '}
        <span className="mono">mcp/tools/*.py</span> ({CATALOG.files_scanned} files) for every <span className="mono">mt.Tool(…)</span>{' '}
        registration.
      </p>

      <div className="grid" style={{ gridTemplateColumns: 'minmax(0, 380px) 1fr', alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 14 }}>
          <Panel title="Identity">
            <div style={{ display: 'grid', gap: 9 }}>
              <input className="input" placeholder="agent name (e.g. crewbot)" value={name} onChange={(e) => setName(e.target.value)} />
              <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>
                the name an agent claims work under on the board — <span className="mono">patch_metadata.assignee</span>
              </div>
            </div>
          </Panel>

          <Panel title="Prompt">
            <textarea
              className="input"
              style={{ width: '100%', height: 130, paddingTop: 9, resize: 'vertical', lineHeight: 1.55 }}
              placeholder="system prompt — what this agent is for, and what it must refuse"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </Panel>

          <Panel title="Memory scope">
            <div style={{ display: 'grid', gap: 7 }}>
              {SCOPES.map((s) => (
                <label
                  key={s.id}
                  style={{
                    display: 'flex',
                    gap: 9,
                    alignItems: 'flex-start',
                    padding: '7px 10px',
                    borderRadius: 6,
                    cursor: 'pointer',
                    background: scope === s.id ? 'var(--violet-glow)' : 'transparent',
                    border: `1px solid ${scope === s.id ? 'rgba(139,124,248,0.35)' : 'transparent'}`,
                  }}
                >
                  <input type="radio" checked={scope === s.id} onChange={() => setScope(s.id)} style={{ marginTop: 3 }} />
                  <span>
                    <span style={{ color: 'var(--ink-0)', fontWeight: 500 }}>{s.label}</span>
                    <span style={{ display: 'block', fontSize: 11.5, color: 'var(--ink-3)' }}>{s.note}</span>
                  </span>
                </label>
              ))}
            </div>
          </Panel>

          <Panel title="Lifecycle">
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {LIFECYCLE.map((s) => (
                <button
                  key={s}
                  className={`btn sm ${stage === s ? 'primary' : ''}`}
                  onClick={() => setStage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
            <div style={{ marginTop: 10, fontSize: 11.5, color: 'var(--ink-3)' }}>
              only <span className="mono">active</span> agents may claim cards; retired names stay resolvable in history
            </div>
          </Panel>

          <Notice tone="warn" title="Provisioning is not wired yet">
            This panel composes the five fields and shows the real tool catalog, but there is no write route for agent
            definitions in the control plane yet — <span className="mono">app.py</span> exposes dreams, websites and registry
            reads only. Creating an agent still goes through the CLI. Flagged rather than faked: no agent is saved by this screen.
          </Notice>
        </div>

        <Panel
          title="Tools"
          right={
            <>
              <Pill mono>{picked.size} selected</Pill>
              <Pill mono>{filtered.length} shown</Pill>
            </>
          }
          bodyStyle={{ padding: 0 }}
        >
          <div style={{ display: 'flex', gap: 8, padding: '12px 16px', borderBottom: '1px solid var(--line-1)' }}>
            <input className="input" style={{ flex: 1 }} placeholder="search name, title or description…" value={q} onChange={(e) => setQ(e.target.value)} />
            <select className="select" value={domFilter} onChange={(e) => setDomFilter(e.target.value)}>
              <option value="">all {domains.length} domains</option>
              {domains.map(([d, n]) => (
                <option key={d} value={d}>
                  {d} ({n})
                </option>
              ))}
            </select>
            <button className="btn sm" onClick={() => setPicked(new Set())}>
              clear
            </button>
          </div>

          <div style={{ maxHeight: 'calc(100vh - 330px)', overflowY: 'auto' }}>
            {filtered.slice(0, 400).map((t) => {
              const on = picked.has(t.name);
              return (
                <div
                  key={t.name}
                  onClick={() =>
                    setPicked((prev) => {
                      const n = new Set(prev);
                      n.has(t.name) ? n.delete(t.name) : n.add(t.name);
                      return n;
                    })
                  }
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '20px 1fr auto',
                    gap: 10,
                    padding: '9px 16px',
                    borderBottom: '1px solid rgba(27,39,64,0.55)',
                    cursor: 'pointer',
                    background: on ? 'rgba(109,92,240,0.08)' : 'transparent',
                  }}
                >
                  <span
                    style={{
                      width: 14,
                      height: 14,
                      marginTop: 2,
                      borderRadius: 4,
                      border: `1px solid ${on ? 'var(--violet-0)' : 'var(--line-3)'}`,
                      background: on ? 'var(--violet-1)' : 'transparent',
                    }}
                  />
                  <span>
                    <span className="mono" style={{ color: 'var(--ink-0)', fontSize: 12 }}>
                      {t.name}
                    </span>
                    <span style={{ display: 'block', fontSize: 11.5, color: 'var(--ink-3)', marginTop: 2 }}>
                      {t.description || t.title}
                    </span>
                    {t.params.length > 0 && (
                      <span style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 5 }}>
                        {t.params.slice(0, 6).map((p) => (
                          <span key={p} className="tag">
                            {p}
                          </span>
                        ))}
                        {t.params.length > 6 && <span className="tag">+{t.params.length - 6}</span>}
                      </span>
                    )}
                  </span>
                  <span className="tag" style={{ alignSelf: 'start' }}>
                    {t.domain}
                  </span>
                </div>
              );
            })}
            {filtered.length === 0 && <div className="empty">no tool matches “{q}”</div>}
          </div>
        </Panel>
      </div>
    </div>
  );
}
