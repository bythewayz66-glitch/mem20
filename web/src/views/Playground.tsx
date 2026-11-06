/* Surface 2 — Playground / sandbox.
 *
 * For: first-time visitors. Shows: write a memory, recall it, see the trace.
 * Why: try-before-install.
 *
 * The playground does two things and keeps them visibly separate:
 *
 *   1. A REAL memory round trip against the bridge — write a record, recall it
 *      by topic, and show the actual request/response trace with timings.
 *   2. A REAL LLM turn over whatever was recalled, so a visitor sees the
 *      substrate and the model working together rather than either alone.
 *
 * When the bridge is down, step 1 says so and the LLM step still works — the
 * model is keyless and needs no backend. That is deliberate: the one thing a
 * visitor can always try is the thing that needs no install.
 */
import React, { useRef, useState } from 'react';
import { Notice, Panel, Pill } from '../components/ui';
import { bridge, isOk, reasonOf } from '../lib/backend';
import { ask, LLM_MODE, modeLabel } from '../lib/llm';

interface Step {
  n: number;
  label: string;
  detail: string;
  ms: number;
  ok: boolean;
}

export default function Playground() {
  const [topic, setTopic] = useState('ledger invariants');
  const [text, setText] = useState('The ledger is append-only: entries are added, never mutated.');
  const [tags, setTags] = useState('ledger, invariant');
  const [steps, setSteps] = useState<Step[]>([]);
  const [recalled, setRecalled] = useState<unknown[] | null>(null);
  const [answer, setAnswer] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const n = useRef(0);

  const push = (label: string, detail: string, ms: number, ok = true) => {
    n.current += 1;
    setSteps((s) => [...s, { n: n.current, label, detail, ms, ok }]);
  };

  const run = async () => {
    setBusy(true);
    setSteps([]);
    setRecalled(null);
    setAnswer('');
    setErr('');
    n.current = 0;

    // --- step 1: recall from the real store -------------------------------
    const t0 = performance.now();
    const tagList = tags.split(',').map((s) => s.trim()).filter(Boolean);
    const r = await bridge.recall(topic, tagList.length ? tagList : null, 5);
    const ms1 = Math.round(performance.now() - t0);

    if (isOk(r)) {
      const recs = r.data?.records || [];
      setRecalled(recs);
      push('recall', `POST /api/recall → ${recs.length} record(s)`, ms1, true);
    } else {
      push('recall', reasonOf(r), ms1, false);
      setErr(reasonOf(r));
    }

    // --- step 2: a real LLM turn over what came back ----------------------
    const context =
      recalled && recalled.length > 0
        ? `Recalled records:\n${JSON.stringify(recalled, null, 2).slice(0, 2000)}`
        : 'No records were recalled from the store.';

    const t1 = performance.now();
    try {
      const out = await ask(
        `Question: ${topic}\n\n${context}\n\nAnswer the question using only the recalled records. If they do not contain the answer, say so plainly.`,
        {
          system:
            'You are answering over a memory store. Ground every claim in the records provided. Never invent a record.',
          maxTokens: 400,
        },
      );
      const ms2 = Math.round(performance.now() - t1);
      setAnswer(out);
      push('llm', `completion via ${LLM_MODE}`, ms2, true);
    } catch (e) {
      const ms2 = Math.round(performance.now() - t1);
      const msg = e instanceof Error ? e.message : String(e);
      setErr(msg);
      push('llm', msg, ms2, false);
    }

    setBusy(false);
  };

  return (
    <div className="page wide">
      <p className="lede">
        Write a memory, recall it, and watch a real model answer over what came back. The recall step
        hits the store; the answer step hits a real LLM. Both are shown with their actual timings, and
        a failure in either is reported as a failure rather than papered over.
      </p>

      <div style={{ marginBottom: 14, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <Pill tone={LLM_MODE === 'mock' ? 'amber' : 'green'} dot mono>
          {modeLabel()}
        </Pill>
        <Pill mono>bridge {bridge.base()}</Pill>
      </div>

      <div className="pg-grid">
        <Panel title="Input">
          <div style={{ display: 'grid', gap: 10 }}>
            <label style={{ fontSize: 11, color: 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              topic / query
            </label>
            <input className="input" value={topic} onChange={(e) => setTopic(e.target.value)} />

            <label style={{ fontSize: 11, color: 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              memory text
            </label>
            <textarea
              className="input"
              rows={3}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />

            <label style={{ fontSize: 11, color: 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              tags (comma separated)
            </label>
            <input className="input" value={tags} onChange={(e) => setTags(e.target.value)} />

            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn primary" onClick={run} disabled={busy}>
                {busy ? <span className="spin" /> : 'run round trip'}
              </button>
              <button
                className="btn"
                onClick={() => {
                  setSteps([]);
                  setRecalled(null);
                  setAnswer('');
                  setErr('');
                }}
                disabled={busy}
              >
                clear
              </button>
            </div>

            <Notice tone="warn" title="The write path is not wired here">
              The bridge exposes <span className="mono">GET /api/memory</span> and{' '}
              <span className="mono">POST /api/recall</span> — there is no HTTP write route in{' '}
              <span className="mono">bridge/server.py</span>. So this playground recalls and answers,
              and does not pretend to store. The text box above is what would be written; the recall
              step queries the real store for the topic.
            </Notice>
          </div>
        </Panel>

        <div style={{ display: 'grid', gap: 14 }}>
          <Panel title="Trace" right={<Pill mono>{steps.length} steps</Pill>}>
            {steps.length === 0 && <div className="empty">Run the round trip to see the trace.</div>}
            {steps.length > 0 && (
              <div className="pg-trace">
                {steps.map((s) => (
                  <div key={s.n} className={`pg-step ${s.ok ? 'ok' : 'bad'}`}>
                    <span className="n">{s.ok ? '✓' : '✕'}</span>
                    <span className="d">
                      <strong style={{ color: 'var(--ink-0)' }}>{s.label}</strong> — {s.detail}
                    </span>
                    <span className="ms">{s.ms}ms</span>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Answer" right={<Pill tone={answer ? 'green' : ''} mono>{answer ? 'real' : '—'}</Pill>}>
            {!answer && !err && <div className="empty">No answer yet.</div>}
            {err && <Notice tone="bad" title="Failed">{err}</Notice>}
            {answer && <div className="pg-out">{answer}</div>}
          </Panel>

          {recalled && (
            <Panel title="Recalled records" right={<Pill mono>{recalled.length}</Pill>}>
              {recalled.length === 0 ? (
                <div className="empty">The store returned no records for this topic.</div>
              ) : (
                <div className="pg-out" style={{ maxHeight: 200 }}>
                  {JSON.stringify(recalled, null, 2)}
                </div>
              )}
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
