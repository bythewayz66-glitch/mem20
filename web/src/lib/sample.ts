/* Labelled sample data for surfaces that need a backend to be meaningful.
 *
 * Every surface that falls back to this data must SAY it is sample data. The
 * point of this file is to make the surfaces demonstrable without a running
 * bridge, while keeping the honesty rule intact: a reader must never mistake a
 * sample for a measurement.
 *
 * The graph below is a fixed, hand-written illustration of the memory model -
 * grounded records on the inner ring, a simulated hypothesis on the outer, and
 * one contradiction edge. It is not a fixture of real data and is not
 * presented as one.
 */
import type { Graph } from './graph';

const T = (d: number, h = 0) => new Date(Date.UTC(2026, 0, d, h)).toISOString();

export const SAMPLE_GRAPH: Graph = {
  nodes: [
    {
      id: 'sample-1',
      label: 'ledger is append-only',
      text: 'The ledger accepts new entries and never mutates or deletes an existing one.',
      epistemic: 'grounded',
      origin: 'sample',
      store: 'memory',
      at: T(1),
      tags: ['ledger', 'invariant'],
    },
    {
      id: 'sample-2',
      label: 'indexes are grounded-only',
      text: 'A simulated record reaching the vector or BM25 index raises immediately.',
      epistemic: 'grounded',
      origin: 'sample',
      store: 'memory',
      at: T(2),
      tags: ['invariant', 'index'],
    },
    {
      id: 'sample-3',
      label: 'promotion needs evidence',
      text: 'A simulated record is promoted only when it carries prediction_error_evidence.',
      epistemic: 'grounded',
      origin: 'sample',
      store: 'memory',
      at: T(3),
      tags: ['invariant', 'promotion'],
    },
    {
      id: 'sample-4',
      label: 'recall@5 = 0.82',
      text: 'A measured retrieval run over the sample corpus.',
      epistemic: 'grounded',
      origin: 'sample',
      store: 'memory',
      at: T(4),
      tags: ['eval', 'retrieval'],
    },
    {
      id: 'sample-5',
      label: 'hypothesis: decay improves precision',
      text: 'A counterfactual - if old records decayed, precision might rise. Not observed.',
      epistemic: 'simulated',
      origin: 'sample',
      store: 'imaginated',
      at: T(5),
      tags: ['hypothesis', 'retrieval'],
    },
    {
      id: 'sample-6',
      label: 'hypothesis: unbounded growth is fine',
      text: 'A counterfactual that contradicts the measured storage trend.',
      epistemic: 'simulated',
      origin: 'sample',
      store: 'imaginated',
      at: T(6),
      tags: ['hypothesis', 'ledger'],
    },
  ],
  edges: [
    { id: 'se1', from: 'sample-1', to: 'sample-2', kind: 'shares:invariant', at: T(2) },
    { id: 'se2', from: 'sample-2', to: 'sample-3', kind: 'shares:invariant', at: T(3) },
    { id: 'se3', from: 'sample-4', to: 'sample-5', kind: 'shares:retrieval', at: T(5) },
    { id: 'se4', from: 'sample-1', to: 'sample-6', kind: 'contradicts', at: T(6) },
    // A retracted edge, so the time slider has something real to replay.
    { id: 'se5', from: 'sample-3', to: 'sample-5', kind: 'shares:promotion', at: T(5), retractedAt: T(7) },
  ],
};

/** A sample ledger, built at module load so the viewer has something to verify. */
export const SAMPLE_LEDGER_PAYLOADS: unknown[] = [
  { op: 'remember', origin: 'user', store: 'memory', text: 'the ledger is append-only' },
  { op: 'remember', origin: 'tool', store: 'memory', text: 'indexes are grounded-only' },
  { op: 'simulate', origin: 'dream', store: 'imaginated', text: 'hypothesis: decay improves precision' },
  { op: 'promote', origin: 'user', store: 'memory', text: 'promotion needs prediction_error_evidence' },
  { op: 'recall', origin: 'user', store: 'memory', text: 'query: ledger invariants', k: 5 },
];

/** A sample retrieval run, so the eval dashboard is demonstrable offline. */
export const SAMPLE_RUNS = {
  before: [
    { query: 'ledger invariants', relevant: ['d1', 'd2'], retrieved: ['d1', 'x', 'd2', 'y'] },
    { query: 'promotion gate', relevant: ['d3'], retrieved: ['x', 'd3', 'y'] },
    { query: 'retrieval quality', relevant: ['d4', 'd5'], retrieved: ['d4', 'd5', 'z'] },
    { query: 'storage growth', relevant: ['d6'], retrieved: ['x', 'y', 'z'] },
  ],
  after: [
    { query: 'ledger invariants', relevant: ['d1', 'd2'], retrieved: ['d1', 'd2', 'x', 'y'] },
    { query: 'promotion gate', relevant: ['d3'], retrieved: ['d3', 'x', 'y'] },
    { query: 'retrieval quality', relevant: ['d4', 'd5'], retrieved: ['d4', 'd5', 'z'] },
    { query: 'storage growth', relevant: ['d6'], retrieved: ['d6', 'x', 'y'] },
  ],
};

/** A sample agent run, so the runtime console is demonstrable offline. */
export const SAMPLE_RUN = {
  id: 'run-sample-1',
  agent: 'atlas',
  goal: 'answer: what makes the ledger trustworthy?',
  budget: { steps: 8, tokens: 4000 },
  steps: [
    { n: 1, kind: 'plan', detail: 'decompose the question into ledger properties', ms: 120, tokens: 180 },
    { n: 2, kind: 'tool', detail: 'memory.recall(topic="ledger invariants", k=5)', ms: 340, tokens: 0 },
    { n: 3, kind: 'observe', detail: '5 records returned, 3 grounded / 2 simulated', ms: 12, tokens: 0 },
    { n: 4, kind: 'tool', detail: 'ledger.verify_chain()', ms: 210, tokens: 0 },
    { n: 5, kind: 'observe', detail: 'chain intact, 5 entries verified', ms: 8, tokens: 0 },
    { n: 6, kind: 'act', detail: 'compose the answer from grounded records only', ms: 640, tokens: 420 },
  ],
};
