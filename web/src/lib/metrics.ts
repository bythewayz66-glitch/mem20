/* Retrieval metrics - recall@k, MRR, nDCG - as pure functions.
 *
 * The deck's surface 4 exists to turn "our retrieval is good" into a number a
 * CI job can fail on. That only works if the arithmetic is right and testable,
 * so it lives here as pure functions with no I/O, and the dashboard is a thin
 * renderer over them.
 *
 * Definitions used (stated, because "nDCG" means different things to different
 * people and a dashboard that does not say which one it computed is not
 * evidence):
 *
 *   recall@k  - of the relevant items, what fraction appears in the top k.
 *               Binary relevance. Denominator is the number of relevant items.
 *
 *   MRR       - 1 / rank of the FIRST relevant item, averaged over queries.
 *               0 when no relevant item is retrieved.
 *
 *   nDCG@k    - DCG@k / IDCG@k with graded relevance and the standard
 *               2^rel - 1 gain, log2(rank + 1) discount. 1.0 is ideal.
 *
 * All three return 0 for an empty relevant set rather than NaN, and the
 * dashboard labels that case explicitly so a 0 is never read as a measurement
 * when it is really an absence of ground truth.
 */

export interface RankedResult {
  /** The retrieved item's id. */
  id: string;
  /** Graded relevance, when the run carries it. Defaults to binary. */
  relevance?: number;
}

export interface QueryCase {
  query: string;
  /** Ids that are relevant, in no particular order. */
  relevant: string[];
  /** Graded relevance per id, when the run carries it. */
  grades?: Record<string, number>;
  /** The ranked list the retriever returned, best first. */
  retrieved: string[];
}

/** Fraction of relevant items present in the top k. */
export function recallAtK(c: QueryCase, k: number): number {
  if (c.relevant.length === 0) return 0;
  const top = new Set(c.retrieved.slice(0, k));
  let hit = 0;
  for (const id of c.relevant) if (top.has(id)) hit += 1;
  return hit / c.relevant.length;
}

/** Reciprocal rank of the first relevant item; 0 when none is retrieved. */
export function reciprocalRank(c: QueryCase): number {
  const rel = new Set(c.relevant);
  for (let i = 0; i < c.retrieved.length; i += 1) {
    if (rel.has(c.retrieved[i])) return 1 / (i + 1);
  }
  return 0;
}

function gain(c: QueryCase, id: string): number {
  if (c.grades && typeof c.grades[id] === 'number') return c.grades[id];
  return c.relevant.includes(id) ? 1 : 0;
}

/** DCG@k with 2^rel - 1 gain and log2(rank + 1) discount. */
export function dcgAtK(c: QueryCase, k: number): number {
  let sum = 0;
  const top = c.retrieved.slice(0, k);
  for (let i = 0; i < top.length; i += 1) {
    const g = gain(c, top[i]);
    if (g > 0) sum += (Math.pow(2, g) - 1) / Math.log2(i + 2);
  }
  return sum;
}

/** The DCG of the ideal ordering - the denominator of nDCG. */
export function idealDcgAtK(c: QueryCase, k: number): number {
  const grades = c.relevant.map((id) => gain(c, id)).sort((a, b) => b - a).slice(0, k);
  let sum = 0;
  for (let i = 0; i < grades.length; i += 1) {
    if (grades[i] > 0) sum += (Math.pow(2, grades[i]) - 1) / Math.log2(i + 2);
  }
  return sum;
}

/** nDCG@k. 0 when there is no relevant item to rank. */
export function ndcgAtK(c: QueryCase, k: number): number {
  const ideal = idealDcgAtK(c, k);
  if (ideal === 0) return 0;
  return dcgAtK(c, k) / ideal;
}

export interface RunMetrics {
  queries: number;
  recallAt5: number;
  recallAt10: number;
  mrr: number;
  ndcgAt10: number;
  /** Queries whose relevant set was empty - excluded from the means. */
  skipped: number;
}

const mean = (xs: number[]): number => (xs.length === 0 ? 0 : xs.reduce((a, b) => a + b, 0) / xs.length);

/**
 * Aggregate a whole run.
 *
 * Queries with an empty relevant set are SKIPPED, not counted as zero. Counting
 * them as zero would drag every metric down for a reason that has nothing to do
 * with retrieval quality, and the count of skipped queries is reported so the
 * reader can see how much of the run was actually scored.
 */
export function scoreRun(cases: QueryCase[]): RunMetrics {
  const scored = cases.filter((c) => c.relevant.length > 0);
  return {
    queries: cases.length,
    skipped: cases.length - scored.length,
    recallAt5: mean(scored.map((c) => recallAtK(c, 5))),
    recallAt10: mean(scored.map((c) => recallAtK(c, 10))),
    mrr: mean(scored.map(reciprocalRank)),
    ndcgAt10: mean(scored.map((c) => ndcgAtK(c, 10))),
  };
}

export interface MetricDelta {
  key: string;
  before: number;
  after: number;
  delta: number;
  /** True when the change is large enough to be worth a human's attention. */
  material: boolean;
}

/** Diff two runs. A negative delta is a regression and is never hidden. */
export function diffRuns(before: RunMetrics, after: RunMetrics): MetricDelta[] {
  const keys: Array<keyof RunMetrics> = ['recallAt5', 'recallAt10', 'mrr', 'ndcgAt10'];
  return keys.map((k) => {
    const b = before[k] as number;
    const a = after[k] as number;
    const delta = a - b;
    return { key: String(k), before: b, after: a, delta, material: Math.abs(delta) >= 0.01 };
  });
}

/** Format a metric for display. Never rounds a real value to a fake zero. */
export function fmt(v: number, digits = 3): string {
  if (!Number.isFinite(v)) return '-';
  return v.toFixed(digits);
}
