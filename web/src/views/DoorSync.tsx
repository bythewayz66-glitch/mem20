/* Door Sync — the real contract, and an honest report of reachability.
 *
 * This panel exists because the door is the single point of truth for work and
 * it fails in a way that is easy to paper over: an unreachable door looks
 * exactly like an empty board if you do not check. So the contract is printed
 * from the same constants the client uses, and the probe result is shown raw.
 */
import React, { useEffect, useState } from 'react';
import { CAPACITY_STATUS, DOOR_ROUTES, door } from '../lib/api';
import { Notice, Panel, Pill } from '../components/ui';

type Props = { doorUp: boolean | null; onProbe: () => Promise<boolean> };

export default function DoorSync({ doorUp, onProbe }: Props) {
  const [boards, setBoards] = useState<string[] | null>(null);
  const [err, setErr] = useState('');
  const [raw, setRaw] = useState<string>('');
  const [busy, setBusy] = useState(false);

  const probe = async () => {
    setBusy(true);
    setErr('');
    setBoards(null);
    const t0 = performance.now();
    try {
      const list = await door.boards();
      const ms = Math.round(performance.now() - t0);
      setBoards(list.map((b) => b.name));
      setRaw(`GET ${door.base()}/api/boards → 200 · ${list.length} boards · ${ms}ms`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setRaw(`GET ${door.base()}/api/boards → no answer`);
    } finally {
      setBusy(false);
      onProbe();
    }
  };

  useEffect(() => {
    probe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const up = boards !== null;

  return (
    <div className="page">
      <p className="lede">
        One door, one store, one writer. <span className="mono">mem20-kanban.service</span> listens on{' '}
        <span className="mono">127.0.0.1:8221</span> and owns <span className="mono">kanban_3.db</span>. Every kanban write in the
        estate — bots, CLI, this shell — goes through these routes.
      </p>

      <div className="grid g2" style={{ marginBottom: 16, alignItems: 'start' }}>
        <Panel
          title="Live probe"
          right={<Pill tone={up ? 'green' : doorUp === false ? 'red' : ''} dot mono>{up ? 'reachable' : busy ? 'probing' : 'unreachable'}</Pill>}
        >
          <dl className="kv" style={{ marginBottom: 12 }}>
            <dt>base</dt>
            <dd>{door.base()}</dd>
            <dt>request</dt>
            <dd>{raw || '—'}</dd>
            <dt>health call</dt>
            <dd>GET /api/boards (this is what Door.healthy() does — it never fabricates a list)</dd>
          </dl>
          {up ? (
            <Notice tone="ok" title={`door answered with ${boards!.length} board(s)`}>
              {boards!.join(' · ')}
            </Notice>
          ) : (
            <Notice tone="bad" title="the door did not answer">
              {err || 'no response'}
              <div style={{ marginTop: 8 }}>
                A browser can only reach the door if it is on the same machine or the door is exposed through a proxy. The door is
                loopback-only by design (<span className="mono">restart=always</span>, enabled at boot), so a remote browser will
                always see this. Use <span className="mono">ssh -L 8221:127.0.0.1:8221</span> and point Connection at{' '}
                <span className="mono">http://127.0.0.1:8221</span>.
              </div>
            </Notice>
          )}
          <div style={{ marginTop: 12 }}>
            <button className="btn primary" onClick={probe} disabled={busy}>
              {busy ? <span className="spin" /> : null} probe again
            </button>
          </div>
        </Panel>

        <Panel title="The one store" right={<Pill mono>kanban_3.db</Pill>}>
          <dl className="kv">
            <dt>path</dt>
            <dd>/opt/mem20/kanban/kanban_3.db</dd>
            <dt>owner</dt>
            <dd>mem20-kanban.service (sole writer)</dd>
            <dt>retired writers</dt>
            <dd>mcp-server (stdio), kanban-server/server.js</dd>
            <dt>migrated</dt>
            <dd>16 cards from the orphan ~/.kanban/kanban.db, source left byte-identical</dd>
            <dt>last read-only inspect</dt>
            <dd>3 boards · 10 columns · 154 cards · sha256 eab7bcee… unchanged before/after</dd>
          </dl>
          <div style={{ marginTop: 12 }}>
            <Notice tone="warn" title="Written by the door, never by this UI">
              The shell has no SQLite driver and no database URL. A second writer on one SQLite file is a second source of truth,
              and drift by construction is exactly what the four-way merge was done to end.
            </Notice>
          </div>
        </Panel>
      </div>

      <Panel
        title="Wire contract"
        right={
          <>
            <Pill mono>{DOOR_ROUTES.length} routes</Pill>
            <Pill tone="red" mono>
              {CAPACITY_STATUS} = capacity
            </Pill>
          </>
        }
        bodyStyle={{ padding: 0 }}
      >
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 70 }}>method</th>
              <th>path</th>
              <th>payload</th>
              <th>what it does</th>
            </tr>
          </thead>
          <tbody>
            {DOOR_ROUTES.map((r) => (
              <tr key={`${r.method}${r.path}`}>
                <td>
                  <Pill tone={r.method === 'GET' ? 'cyan' : r.method === 'DELETE' ? 'red' : 'violet'} mono>
                    {r.method}
                  </Pill>
                </td>
                <td className="mono" style={{ color: 'var(--ink-0)' }}>{r.path}</td>
                <td className="mono">{r.payload || '—'}</td>
                <td>{r.does}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <div style={{ marginTop: 16 }}>
        <Panel title="Sarge — decomposer">
          <p className="lede" style={{ marginBottom: 10 }}>
            <span className="mono">mem20-sarge</span> reads a roadmap phase, creates the card through this door, and writes the new
            card id back into the phase as <span className="mono">jobid</span>. That one field is what makes the loop safe to run
            forever: a phase carrying a <span className="mono">jobid</span> has already been decomposed and is skipped, so a repeat
            pass cannot drown the board in duplicates.
          </p>
          <div className="grid g3">
            <div className="proof"><span className="pk">1</span><span>roadmap phase</span></div>
            <div className="proof"><span className="pk">2</span><span>Sarge → card on the door</span></div>
            <div className="proof"><span className="pk">3</span><span>bot claims → work → verified done</span></div>
          </div>
          <div style={{ marginTop: 12, fontSize: 11.5, color: 'var(--ink-3)' }}>
            the card-creation form lives on the Kanban surface, under <span className="mono">Sarge</span> in the board bar
          </div>
        </Panel>
      </div>
    </div>
  );
}
