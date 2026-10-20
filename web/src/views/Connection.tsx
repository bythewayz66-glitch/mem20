/* Connection — where this shell reads from.
 *
 * One auth model: the shell has none of its own. Access is whatever the origin
 * enforces (mem20controlz' own login gate) and whatever the door enforces on
 * loopback. This page only decides WHERE the two upstreams live.
 */
import React, { useEffect, useState } from 'react';
import {
  DEFAULT_DOOR,
  control,
  door,
  getControlBase,
  getDoorBase,
  setControlBase,
  setDoorBase,
} from '../lib/api';
import { Notice, Panel, Pill } from '../components/ui';

export default function Connection({ onProbe }: { onProbe: () => Promise<boolean> }) {
  const [doorBase, setDB] = useState(getDoorBase());
  const [ctlBase, setCB] = useState(getControlBase());
  const [doorOk, setDoorOk] = useState<boolean | null>(null);
  const [ctl, setCtl] = useState<{ ok: boolean; detail: string } | null>(null);
  const [saved, setSaved] = useState('');

  const test = async () => {
    setSaved('');
    const d = await door.healthy();
    setDoorOk(d);
    setCtl(await control.health());
    await onProbe();
  };

  useEffect(() => {
    test();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="page">
      <p className="lede">
        One API client, two upstreams. Nothing is bundled into this page — the shell is static, so it reads the kanban door and the
        control plane at runtime.
      </p>

      <div className="grid g2" style={{ alignItems: 'start' }}>
        <Panel
          title="Kanban door"
          right={<Pill tone={doorOk ? 'green' : doorOk === false ? 'red' : ''} dot mono>{doorOk === null ? 'checking' : doorOk ? 'up' : 'down'}</Pill>}
        >
          <div style={{ display: 'grid', gap: 9 }}>
            <input className="input" value={doorBase} onChange={(e) => setDB(e.target.value)} spellCheck={false} />
            <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>
              default <span className="mono">{DEFAULT_DOOR}</span> — the door is loopback-only, so from another machine use{' '}
              <span className="mono">ssh -L 8221:127.0.0.1:8221</span> and keep this value.
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn primary"
                onClick={async () => {
                  setDoorBase(doorBase.trim() || DEFAULT_DOOR);
                  setDB(getDoorBase());
                  await test();
                  setSaved('door base saved');
                }}
              >
                save &amp; test
              </button>
              <button
                className="btn"
                onClick={() => {
                  setDoorBase(DEFAULT_DOOR);
                  setDB(DEFAULT_DOOR);
                  test();
                }}
              >
                reset
              </button>
            </div>
          </div>
        </Panel>

        <Panel
          title="Control plane"
          right={<Pill tone={ctl?.ok ? 'green' : ctl ? 'red' : ''} dot mono>{ctl === null ? 'checking' : ctl.ok ? 'up' : 'down'}</Pill>}
        >
          <div style={{ display: 'grid', gap: 9 }}>
            <input
              className="input"
              value={ctlBase}
              placeholder="(empty = this page's own origin)"
              onChange={(e) => setCB(e.target.value)}
              spellCheck={false}
            />
            <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>
              mem20controlz serves its own frontend same-origin, so empty means “wherever this page was loaded from”. Set it only
              if the API lives elsewhere.
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn primary"
                onClick={async () => {
                  setControlBase(ctlBase.trim());
                  setCB(getControlBase());
                  await test();
                  setSaved('control base saved');
                }}
              >
                save &amp; test
              </button>
              <button
                className="btn"
                onClick={() => {
                  setControlBase('');
                  setCB('');
                  test();
                }}
              >
                reset
              </button>
            </div>
            {ctl && (
              <div style={{ fontSize: 11.5, color: ctl.ok ? 'var(--green-0)' : 'var(--red-0)' }} className="mono">
                {ctl.detail}
              </div>
            )}
          </div>
        </Panel>
      </div>

      {saved && (
        <div style={{ marginTop: 14 }}>
          <Notice tone="ok" title={saved} />
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <Panel title="Auth" right={<Pill mono>one model</Pill>}>
          <div className="grid g3">
            <div className="proof"><span className="pk">door</span><span>no auth — loopback only, so the network boundary is the control</span></div>
            <div className="proof"><span className="pk">control</span><span><span className="mono">/api/auth/login</span> sets the session; every other route is behind it</span></div>
            <div className="proof"><span className="pk">shell</span><span>carries no credentials of its own and stores no token</span></div>
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: 'var(--ink-3)' }}>
            The shell deliberately does not cache an API key in localStorage. A static page that holds a credential is a credential
            leak with a stylesheet.
          </div>
        </Panel>
      </div>

      <div style={{ marginTop: 16 }}>
        <Panel title="Build provenance">
          <dl className="kv">
            <dt>shell</dt>
            <dd>mem20-web · one shell over the teamz base</dd>
            <dt>tool catalog</dt>
            <dd>src/data/tools.json — AST extraction of mcp/tools/*.py</dd>
            <dt>door client</dt>
            <dd>src/lib/api.ts — transcribed from mem20kanbanz/door.py</dd>
            <dt>control routes</dt>
            <dd>26 routes from mem20controlz/mem20controlz/app.py</dd>
          </dl>
        </Panel>
      </div>
    </div>
  );
}
