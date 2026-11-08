/* Surface 4 — Retrieval / recall evaluation dashboard.
 *
 * For: ML engineers. Shows: recall@k, MRR, nDCG per run, diffed.
 * Why: turns a claim into a CI number.
 *
 * The deck's point about this surface is that mem20's README makes retrieval
 * claims that no number backs. So the dashboard's job is to be the place a
 * number WOULD live, and to be honest that it currently has no measured run to
 * show. It computes real metrics over a labelled sample run so the arithmetic
 * is demonstrable, and it labels that run as a sample in the header.
 *
 * The diff panel is the part that matters for CI: a regression is shown in red
 * with its magnitude, and a change under 1% is marked immaterial rather than
 * presented as a win.
 */
import React, { useMemo, useState } from 'react';
import { Notice, Panel, Pill, Stat } from '../components/ui';
import { diffRuns, fmt, scoreRun, type QueryCase } from '../lib/metrics';
import { SAMPLE_RUNS } from '../lib/sample';

const LABELS: Record<string, string> = {
  recallAt5: 'recall@5',
  recallAt10: 'recall@10',
  mrr: 'MRR',
  ndcgAt10: 'nDCG@10',
};

export default function EvalDashboard() {
  const [which, setWhich] = useState<'before' | 'after'>('after');

  const before = useMemo(() => scoreRun(SAMPLE_RUNS.before as QueryCase[]), []);
  const after = useMemo(() => scoreRun(SAMPLE_RUNS.after as QueryCase[]), []);
  const deltas = useMemo(() => diffRuns(before, after), [before, after]);

  const current = which === 'before' ? before : after;
  const cases = (which === 'before' ? SAMPLE_RUNS.before : SAMPLE_RUNS.after) as QueryCase[];

  return (
    <div className="page wide">
      <p className="lede">
        Retrieval quality as a number a CI job can fail on. The metrics below are computed in the
        browser from a labelled sample run — the arithmetic is real, the run is a sample, and the
        header says which. There is no measured run of the real store yet, and this view will not
        invent one.
      </p>

      <div style={{ marginBottom: 14 }}>
        <Notice tone="warn" title="No measured run of the real store exists yet">
          mem20's README makes retrieval claims that no committed number backs. This dashboard is
          where that number would live. Until a run is recorded, it shows a labelled sample so the
          metric definitions and the diff logic are demonstrable — not so the numbers can be quoted.
        </Notice>
      </div>

      <div className="grid g4" style={{ marginBottom: 16 }}>
        <Stat k="queries scored" v={current.queries - current.skipped} sub={`${current.skipped} skipped`} />
        <Stat k="recall@5" v={fmt(current.recallAt5)} />
        <Stat k="MRR" v={fmt(current.mrr)} />
        <Stat k="nDCG@10" v={fmt(current.ndcgAt10)} />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <button className={`btn ${which === 'before' ? 'primary' : ''}`} onClick={() => setWhich('before')}>
          run A (before)
        </button>
        <button className={`btn ${which === 'after' ? 'primary' : ''}`} onClick={() => setWhich('after')}>
          run B (after)
        </button>
      </div>

      <div className="grid g2" style={{ alignItems: 'start' }}>
        <Panel title="Run diff — A → B" right={<Pill mono>Δ</Pill>}>
          <div>
            {deltas.map((d) => {
              const cls = d.delta > 0 ? 'up' : d.delta < 0 ? 'down' : 'flat';
              return (
                <div className="ev-metric" key={d.key}>
                  <span className="k">{LABELS[d.key] || d.key}</span>
                  <span className="v">{fmt(d.before)}</span>
                  <span className="v">{fmt(d.after)}</span>
                  <span className={`d ${cls}`}>
                    {d.delta > 0 ? '+' : ''}
                    {fmt(d.delta)}
                    {d.material ? '' : ' ·'}
                  </span>
                </div>
              );
            })}
          </div>
          <div style={{ padding: '10px 12px', borderTop: '1px solid var(--line-1)' }}>
            <span style={{ fontSize: 11, color: 'var(--ink-3)' }}>
              A trailing <span className="mono">·</span> marks a change under 1% — immaterial, and not
              presented as a win.
            </span>
          </div>
        </Panel>

        <Panel title="Per-query detail" right={<Pill mono>{cases.length} queries</Pill>}>
          <table className="tbl">
            <thead>
              <tr>
                <th>query</th>
                <th style={{ width: 60 }}>rel</th>
                <th style={{ width: 60 }}>top-5</th>
                <th style={{ width: 70 }}>RR</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => {
                const top5 = c.retrieved.slice(0, 5);
                const hits = c.relevant.filter((r) => top5.includes(r)).length;
                const rr = (() => {
                  for (let i = 0; i < c.retrieved.length; i += 1) {
                    if (c.relevant.includes(c.retrieved[i])) return 1 / (i + 1);
                  }
                  return 0;
                })();
                return (
                  <tr key={c.query}>
                    <td>{c.query}</td>
                    <td className="mono">{c.relevant.length}</td>
                    <td className="mono">
                      {hits}/{c.relevant.length}
                    </td>
                    <td className="mono">{fmt(rr, 2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>
      </div>

      <div style={{ marginTop: 16 }} className="grid g2">
        <Panel title="Metric definitions">
          <dl className="kv" style={{ gridTemplateColumns: '110px 1fr' }}>
            <dt>recall@k</dt>
            <dd style={{ fontFamily: 'var(--sans)', fontSize: 12 }}>
              of the relevant items, the fraction appearing in the top k. Binary relevance.
            </dd>
            <dt>MRR</dt>
            <dd style={{ fontFamily: 'var(--sans)', fontSize: 12 }}>
              1 / rank of the first relevant item, averaged over queries. 0 when none is retrieved.
            </dd>
            <dt>nDCG@k</dt>
            <dd style={{ fontFamily: 'var(--sans)', fontSize: 12 }}>
              DCG@k / IDCG@k with 2^rel − 1 gain and log2(rank + 1) discount. 1.0 is ideal.
            </dd>
            <dt>skipped</dt>
            <dd style={{ fontFamily: 'var(--sans)', fontSize: 12 }}>
              queries with an empty relevant set are excluded from the means, not scored as zero —
              counting them would drag every metric down for a reason unrelated to retrieval.
            </dd>
          </dl>
        </Panel>

        <Panel title="How this becomes a CI gate">
          <div style={{ display: 'grid', gap: 10 }}>
            <p className="lede" style={{ marginBottom: 0 }}>
              The metrics are pure functions in <span className="mono">src/lib/metrics.ts</span> with
              their own tests, so a CI job can import them and fail a build on a regression:
            </p>
            <code className="code">{`import { scoreRun, diffRuns } from './src/lib/metrics';

const before = scoreRun(baseline);
const after  = scoreRun(current);
const regressions = diffRuns(before, after)
  .filter(d => d.material && d.delta < 0);

if (regressions.length) {
  console.error('retrieval regressed:', regressions);
  process.exit(1);
}`}</code>
            <Notice tone="warn" title="Not wired into CI yet">
              This is the shape the gate would take. No workflow runs it today, and this view does not
              claim one does.
            </Notice>
          </div>
        </Panel>
      </div>
    </div>
  );
}
