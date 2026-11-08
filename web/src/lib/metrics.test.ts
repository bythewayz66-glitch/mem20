import { describe, expect, it } from 'vitest';
import {
  recallAtK,
  reciprocalRank,
  ndcgAtK,
  dcgAtK,
  idealDcgAtK,
  scoreRun,
  diffRuns,
  fmt,
  type QueryCase,
} from './metrics';

const q = (retrieved: string[], relevant: string[], grades?: Record<string, number>): QueryCase => ({
  query: 'q',
  retrieved,
  relevant,
  grades,
});

describe('recallAtK', () => {
  it('is 1 when every relevant item is in the top k', () => {
    expect(recallAtK(q(['a', 'b', 'c'], ['a', 'b']), 3)).toBe(1);
  });

  it('is 0.5 when half the relevant items are retrieved', () => {
    expect(recallAtK(q(['a', 'x'], ['a', 'b']), 2)).toBe(0.5);
  });

  it('respects the k cutoff', () => {
    expect(recallAtK(q(['x', 'y', 'a'], ['a']), 2)).toBe(0);
    expect(recallAtK(q(['x', 'y', 'a'], ['a']), 3)).toBe(1);
  });

  it('is 0 for an empty relevant set rather than NaN', () => {
    expect(recallAtK(q(['a'], []), 5)).toBe(0);
  });
});

describe('reciprocalRank', () => {
  it('is 1 when the first result is relevant', () => {
    expect(reciprocalRank(q(['a', 'b'], ['a']))).toBe(1);
  });

  it('is 1/3 when the third result is the first relevant one', () => {
    expect(reciprocalRank(q(['x', 'y', 'a'], ['a']))).toBeCloseTo(1 / 3, 10);
  });

  it('is 0 when nothing relevant is retrieved', () => {
    expect(reciprocalRank(q(['x', 'y'], ['a']))).toBe(0);
  });
});

describe('nDCG', () => {
  it('is 1 for the ideal ordering', () => {
    expect(ndcgAtK(q(['a', 'b'], ['a', 'b']), 10)).toBeCloseTo(1, 10);
  });

  it('is less than 1 when a relevant item is ranked below an irrelevant one', () => {
    expect(ndcgAtK(q(['x', 'a'], ['a']), 10)).toBeLessThan(1);
  });

  it('is 0 when there is nothing relevant to rank', () => {
    expect(ndcgAtK(q(['x'], []), 10)).toBe(0);
  });

  it('honours graded relevance: a grade-3 item outranks a grade-1 item', () => {
    const graded = q(['a', 'b'], ['a', 'b'], { a: 3, b: 1 });
    const swapped = q(['b', 'a'], ['a', 'b'], { a: 3, b: 1 });
    expect(ndcgAtK(graded, 10)).toBeGreaterThan(ndcgAtK(swapped, 10));
  });

  it('idealDcg is at least the achieved dcg', () => {
    const c = q(['x', 'a'], ['a', 'b']);
    expect(idealDcgAtK(c, 10)).toBeGreaterThanOrEqual(dcgAtK(c, 10));
  });
});

describe('scoreRun', () => {
  it('averages across queries', () => {
    const m = scoreRun([q(['a'], ['a']), q(['x'], ['a'])]);
    expect(m.queries).toBe(2);
    expect(m.recallAt5).toBeCloseTo(0.5, 10);
    expect(m.mrr).toBeCloseTo(0.5, 10);
  });

  it('skips queries with no ground truth instead of scoring them zero', () => {
    const m = scoreRun([q(['a'], ['a']), q(['x'], [])]);
    expect(m.queries).toBe(2);
    expect(m.skipped).toBe(1);
    // The scored query is perfect, so the mean must be 1, not 0.5.
    expect(m.recallAt5).toBe(1);
  });

  it('reports zeroes for an empty run without dividing by zero', () => {
    const m = scoreRun([]);
    expect(m.queries).toBe(0);
    expect(m.recallAt5).toBe(0);
    expect(Number.isFinite(m.mrr)).toBe(true);
  });
});

describe('diffRuns', () => {
  it('reports a negative delta as a regression, not hidden', () => {
    const before = scoreRun([q(['a'], ['a'])]);
    const after = scoreRun([q(['x'], ['a'])]);
    const d = diffRuns(before, after);
    const recall = d.find((x) => x.key === 'recallAt5')!;
    expect(recall.delta).toBeLessThan(0);
    expect(recall.material).toBe(true);
  });

  it('marks a sub-1% change as immaterial', () => {
    const before = scoreRun([q(['a'], ['a'])]);
    const after = { ...before, recallAt5: before.recallAt5 - 0.001 };
    const d = diffRuns(before, after).find((x) => x.key === 'recallAt5')!;
    expect(d.material).toBe(false);
  });
});

describe('fmt', () => {
  it('formats a real number to three places', () => {
    expect(fmt(0.5)).toBe('0.500');
  });

  it('renders a non-finite value as an em dash, never as 0', () => {
    expect(fmt(NaN)).toBe('\u2014');
    expect(fmt(Infinity)).toBe('\u2014');
  });
});
