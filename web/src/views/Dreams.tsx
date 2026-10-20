/* Dreams — promotion and provenance.
 *
 * Backed by mem20controlz (FastAPI) routes read out of app.py:
 *   GET  /api/dreams                         list
 *   GET  /api/dreams/{id}                    one dream
 *   GET  /api/dreams/{id}/chain              provenance chain
 *   POST /api/dreams/{id}/verify             verify
 *   POST /api/dreams/{id}/promote            promote (needs prediction_error_evidence)
 *
 * The promotion gate is the point of this screen. Invariant 4 of the memory
 * model says a simulated record becomes grounded only when it carries
 * prediction_error_evidence — so the promote button REFUSES to fire without it
 * rather than letting the server 4xx later.
 */
import React, { useEffect, useState } from 'react';
import { control, type DreamSummary } from '../lib/api';
import { Notice, Panel, Pill } from '../components/ui';

export default function Dreams() {
  const [rows, setRows] = useState<DreamSummary[] | null>(null);
  const [err, setErr] = useState('');
  const [sel, setSel] = useState<string>('');
  const [evidence, setEvidence] = useState('');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    control
      .dreams()
      .then((d) => setRows(d))
      .catch((e) => setErr(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="page">
      <p className="lede">
        A dream is simulated memory. It stays simulated — never indexed, never retrieved as fact — until it is promoted with
        evidence. This screen shows the promotion gate and the provenance chain that backs it.
      </p>

      {err && (
        <Notice tone="warn" title="Control plane not reachable from this page">
          The shell read <span className="mono">GET /api/dreams</span> from the control plane origin and got:{' '}
          <span className="mono">{err}</span>. A statically hosted shell has no FastAPI behind it — run{' '}
          <span className="mono">mem20controlz</span> and serve the shell from it, or point{' '}
          <span className="mono">Connection</span> at a reachable origin. No dream rows are shown rather than inventing them.
        </Notice>
      )}

      <div className="grid g2" style={{ marginTop: err ? 16 : 0, alignItems: 'start' }}>
        <Panel title="Dreams" right={<Pill mono>{rows ? `${rows.length} rows` : '—'}</Pill>}>
          {rows && rows.length === 0 && <div className="empty">control plane answered with an empty dream list</div>}
          {rows && rows.length > 0 && (
            <table className="tbl">
              <thead>
                <tr>
                  <th>title</th>
                  <th>status</th>
                  <th>epistemic</th>
                  <th>evidence</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((d) => (
                  <tr key={d.id} onClick={() => setSel(d.id)} style={{ cursor: 'pointer' }}>
                    <td>{d.title || <span className="mono">{d.id}</span>}</td>
                    <td className="mono">{d.status || '—'}</td>
                    <td>
                      {d.epistemic === 'grounded' ? (
                        <Pill tone="green" mono dot>
                          grounded
                        </Pill>
                      ) : (
                        <Pill tone="amber" mono dot>
                          simulated
                        </Pill>
                      )}
                    </td>
                    <td className="mono">{d.predictionErrorEvidence ? 'present' : 'absent'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!rows && !err && <div className="empty"><span className="spin" /> reading the control plane…</div>}
        </Panel>

        <Panel title="Promotion gate">
          <div className="lede" style={{ marginBottom: 12 }}>
            Invariant 4: <span className="mono">promote_simulated_to_grounded()</span> accepts a simulated record only when it
            carries <span className="mono">prediction_error_evidence</span> — a linked prior prediction resolved in its favour, or
            a registered external verifier's voucher.
          </div>
          <div style={{ display: 'grid', gap: 9 }}>
            <input
              className="input"
              placeholder="dream id"
              value={sel}
              onChange={(e) => setSel(e.target.value)}
            />
            <textarea
              className="input"
              style={{ height: 90, paddingTop: 8, resize: 'vertical', fontFamily: 'var(--mono)', fontSize: 11.5 }}
              placeholder='prediction_error_evidence — e.g. {"prediction_id":"pred_…","resolved_in_favour":true}'
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
            />
            <button
              className="btn primary"
              disabled={!sel.trim() || !evidence.trim()}
              onClick={async () => {
                setMsg('');
                try {
                  const parsed = JSON.parse(evidence);
                  await control.promote(sel.trim(), parsed);
                  setMsg('promote accepted by the control plane');
                } catch (e) {
                  setMsg(e instanceof Error ? e.message : String(e));
                }
              }}
            >
              promote with evidence
            </button>
            {!evidence.trim() && (
              <div style={{ fontSize: 11.5, color: 'var(--ink-3)' }}>
                disabled on purpose — there is no promotion without evidence
              </div>
            )}
            {msg && <Notice tone="warn" title={msg} />}
          </div>
        </Panel>
      </div>

      <div style={{ marginTop: 16 }}>
        <Panel title="Provenance &amp; audit trail">
          <p className="lede" style={{ marginBottom: 10 }}>
            Every ledger line carries <span className="mono">origin</span> and <span className="mono">store</span>, and a promotion
            stamps the status onto the original grounded line plus the deep-store markdown header. The chain endpoint is{' '}
            <span className="mono">GET /api/dreams/&#123;id&#125;/chain</span>.
          </p>
          <div className="empty">
            select a dream to read its chain — no chain is rendered while the control plane is unreachable
          </div>
        </Panel>
      </div>
    </div>
  );
}
