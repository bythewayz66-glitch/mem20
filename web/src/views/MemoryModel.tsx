/* Memory model — the five hard invariants, and the grounded/simulated split.
 *
 * Invariant text is taken from README.md § "Hard invariants enforced by the
 * store engine" — not paraphrased into something the code does not do. Each
 * carries the symbol that actually enforces it, so a reader can go look.
 */
import React from 'react';
import { Notice, Panel, Pill, Stat } from '../components/ui';

const INVARIANTS = [
  {
    n: 1,
    title: 'Indexes are grounded-only',
    body: '_add_to_vector_index() and _add_to_bm25_index() call _assert_grounded(); a simulated record reaching either index raises immediately.',
    guard: '_assert_grounded()',
  },
  {
    n: 2,
    title: 'remember() is grounded-only by default',
    body: 'The default is _allow_simulated=False. Simulated content uses its own path: remember_simulated / memory_simulate_store.',
    guard: '_allow_simulated=False',
  },
  {
    n: 3,
    title: 'Append-only ledger with validated tags',
    body: 'Every ledger entry carries origin (user, tool, simulated) and store (memory / imaginated). _validate_partition_tags() rejects mismatches at the lowest append path.',
    guard: '_validate_partition_tags()',
  },
  {
    n: 4,
    title: 'Promotion is evidence-based',
    body: 'promote_simulated_to_grounded() accepts a simulated record only when it carries prediction_error_evidence — a linked prior prediction resolved in its favour, or a registered external verifier voucher.',
    guard: 'prediction_error_evidence',
  },
  {
    n: 5,
    title: 'Epistemic status is authoritative on the record',
    body: 'set_epistemic_status() stamps the status directly onto the original grounded ledger line and the deep-store markdown header.',
    guard: 'set_epistemic_status()',
  },
];

const STORE = [
  ['ledger.jsonl', 'append-only operation log (origin/store tagged)'],
  ['embeddings.npy / index', 'vector index — grounded only'],
  ['bm25_corpus.json', 'BM25 corpus — grounded only'],
  ['records/<id>.md', 'deep-store markdown (header carries epistemic_status)'],
  ['simulated/', 'simulated partition — never indexed'],
];

export default function MemoryModel() {
  return (
    <div className="page">
      <p className="lede">
        mem20 keeps two logical partitions: <strong style={{ color: 'var(--green-0)' }}>grounded</strong> memory derived from real
        observations, statements or events, and <strong style={{ color: 'var(--amber-0)' }}>simulated</strong> memory —
        hypotheticals, imagined scenarios, counterfactuals. They are separated by code, not by convention.
      </p>

      <div className="grid g4" style={{ marginBottom: 18 }}>
        <Stat k="hard invariants" v={5} sub="enforced" />
        <Stat k="guarded index writes" v={2} sub="vector + bm25" />
        <Stat k="promotion paths" v={1} sub="evidence only" />
        <Stat k="clean contamination rate" v="0.0" sub="target" />
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <div className="panel-head">
          <h3>Hard invariants</h3>
          <span className="spacer" />
          <div className="legend">
            <span className="sw">
              <span className="sq" style={{ background: 'var(--green-0)' }} /> grounded
            </span>
            <span className="sw">
              <span className="sq" style={{ background: 'var(--amber-0)' }} /> simulated
            </span>
          </div>
        </div>
        {INVARIANTS.map((iv) => (
          <div className="invariant" key={iv.n}>
            <div className="inv-n">{iv.n}</div>
            <div>
              <div className="inv-t">{iv.title}</div>
              <div className="inv-d">{iv.body}</div>
              <div style={{ marginTop: 6 }}>
                <span className="tag">{iv.guard}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid g2" style={{ alignItems: 'start' }}>
        <Panel title="Store layout" right={<Pill mono>MEM20_STORE_PATH</Pill>}>
          <table className="tbl">
            <tbody>
              {STORE.map(([p, d]) => (
                <tr key={p}>
                  <td className="mono" style={{ width: 190, color: 'var(--ink-0)' }}>{p}</td>
                  <td>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="Promotion gate">
          <div style={{ display: 'grid', gap: 12 }}>
            <div className="proof">
              <span className="pk">simulated</span>
              <span>a dream / hypothesis / counterfactual, in its own partition, never indexed</span>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--ink-3)', fontSize: 12 }}>
              ↓ requires <span className="mono" style={{ color: 'var(--cyan-0)' }}>prediction_error_evidence</span>
            </div>
            <div className="proof" style={{ borderColor: 'rgba(52,211,153,0.3)' }}>
              <span className="pk" style={{ color: 'var(--green-0)' }}>grounded</span>
              <span>retrievable as fact; carries origin + store + epistemic_status</span>
            </div>
            <Notice tone="warn" title="There is no second path">
              No admin override, no “just this once”, no flag that skips the gate. If a promotion is attempted without evidence the
              call fails — which is the point.
            </Notice>
          </div>
        </Panel>
      </div>

      <div style={{ marginTop: 16 }}>
        <Panel title="Contamination audit" right={<Pill tone="amber" mono>live run pending</Pill>}>
          <p className="lede" style={{ marginBottom: 10 }}>
            <span className="mono">memory_audit_contamination()</span> inspects both the grounded store and the BM25 corpus for
            simulated records and reports <span className="mono">contamination_rate</span>,{' '}
            <span className="mono">violations</span> and <span className="mono">violations_simulated_in_bm25_corpus</span>. A clean
            system reports <span className="mono">0.0</span>.
          </p>
          <Notice tone="warn" title="Not run from the browser">
            The audit is a store-layer function; there is no HTTP route for it in mem20controlz yet, and this shell will not display
            a rate it did not measure. Green here must mean measured, never assumed.
          </Notice>
        </Panel>
      </div>
    </div>
  );
}
