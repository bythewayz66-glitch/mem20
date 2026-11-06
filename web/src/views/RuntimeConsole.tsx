/* Surface 5 — Agent runtime & observability console.
 *
 * For: operators. Shows: live runs, steps, budgets, traces.
 * Why: 311 tools with no window into them.
 *
 * The console reads the bridge's real status and metrics endpoints, and shows
 * a labelled sample run so the step/budget/trace rendering is demonstrable
 * without a live agent. The distinction is carried in the header pill: a run
 * read from the bridge is marked live, a sample is marked sample.
 */
import React, { useEffect, useState } from 'react';
import { Notice, Panel, Pill, Stat } from '../components/ui';
import { bridge, isOk, reasonOf, type BridgeStatus } from '../lib/backend';
import { SAMPLE_RUN } from '../lib/sample';

export default function RuntimeConsole() {
  const [status, setStatus] = useState<BridgeStatus | null>(null);
  const [statusErr, setStatusErr] = useState('');
  const [metrics, setMetrics] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const s = await bridge.status();
    if (isOk(s)) {
      setStatus(s.data);
      setStatusErr('');
    } else {
      setStatus(null);
      setStatusErr(reasonOf(s));
    }
    const m = await bridge.metrics();
    setMetrics(isOk(m) ? JSON.stringify(m.data, null, 2).slice(0, 1200) : reasonOf(m));
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const run = SAMPLE_RUN;
  const usedSteps = run.steps.length;
  const usedTokens = run.steps.reduce((a, s) => a + s.tokens, 0);
  const totalMs = run.steps.reduce((a, s) => a + s.ms, 0);

  return (
    <div className="page wide">
      <p className="lede">
        A window into the runtime: what the bridge reports about itself, and what an agent run looks
        like step by step with its budget accounted. The bridge panel is live; the run below is a
        labelled sample, because no agent run is currently being served over HTTP.
      </p>

      <div className="grid g4" style={{ marginBottom: 16 }}>
        <Stat
          k="bridge"
          v={loading ? '…' : status ? 'up' : 'down'}
          sub={status ? status.bridge : 'unreachable'}
        />
        <Stat
          k="engine"
          v={status ? (status.engine_available ? 'available' : 'absent') : '—'}
          sub="import memory"
        />
        <Stat k="steps in run" v={usedSteps} sub={`budget ${run.budget.steps}`} />
        <Stat k="tokens used" v={usedTokens} sub={`budget ${run.budget.tokens}`} />
      </div>

      {statusErr && (
        <div style={{ marginBottom: 14 }}>
          <Notice tone="warn" title="Bridge not reachable">
            {statusErr} The run below is a labelled sample. Point the shell at a running bridge in{' '}
            <strong>Connection</strong> to see live status.
          </Notice>
        </div>
      )}

      <div className="grid g2" style={{ alignItems: 'start' }}>
        <Panel
          title="Bridge status"
          right={
            <div style={{ display: 'flex', gap: 6 }}>
              <Pill tone={status ? 'green' : 'red'} dot>
                {status ? 'live' : 'down'}
              </Pill>
              <button className="btn sm" onClick={load} disabled={loading}>
                {loading ? <span className="spin" /> : 'refresh'}
              </button>
            </div>
          }
        >
          {status ? (
            <dl className="kv">
              <dt>bridge</dt>
              <dd>{status.bridge}</dd>
              <dt>engine</dt>
              <dd>{status.engine_available ? 'available' : 'absent'}</dd>
              <dt>mcp</dt>
              <dd style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(status.mcp, null, 2).slice(0, 500)}</dd>
            </dl>
          ) : (
            <div className="empty">No status — the bridge did not answer.</div>
          )}
        </Panel>

        <Panel title="Metrics" right={<Pill mono>/api/metrics</Pill>}>
          {metrics ? (
            <div className="pg-out" style={{ maxHeight: 240 }}>
              {metrics}
            </div>
          ) : (
            <div className="empty">No metrics.</div>
          )}
        </Panel>
      </div>

      <div style={{ marginTop: 16 }}>
        <Panel
          title={`Run — ${run.goal}`}
          right={
            <div className="rt-budget">
              <Pill tone="amber" mono>
                sample
              </Pill>
              <span>
                {usedSteps}/{run.budget.steps} steps
              </span>
              <span>
                {usedTokens}/{run.budget.tokens} tok
              </span>
              <span>{totalMs}ms</span>
            </div>
          }
        >
          <div className="rt-run">
            {run.steps.map((s) => (
              <div className="rt-step" key={s.n}>
                <span className="ld-idx">{s.n}</span>
                <span className={`rt-kind ${s.kind}`}>{s.kind}</span>
                <span style={{ color: 'var(--ink-1)' }}>{s.detail}</span>
                <span className="ld-hash">{s.ms}ms{s.tokens ? ` · ${s.tokens} tok` : ''}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div style={{ marginTop: 16 }}>
        <Notice tone="warn" title="No live run stream exists yet">
          There is no HTTP route in <span className="mono">bridge/server.py</span> that streams agent
          runs, so this console cannot show a live one. The run above is a fixed sample that
          demonstrates the step, budget and trace rendering. When a run endpoint lands, this panel
          reads it and the pill changes from <span className="mono">sample</span> to{' '}
          <span className="mono">live</span>.
        </Notice>
      </div>
    </div>
  );
}
