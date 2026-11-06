import { describe, expect, it } from 'vitest';
import {
  buildChain,
  canonical,
  detectTruncation,
  expectedHash,
  sha256Hex,
  verifyChain,
  type LedgerEntry,
} from './ledger';

describe('canonical', () => {
  it('sorts object keys so two implementations agree on the bytes', () => {
    expect(canonical({ b: 1, a: 2 })).toBe(canonical({ a: 2, b: 1 }));
  });

  it('preserves array order, which is meaningful', () => {
    expect(canonical([1, 2])).not.toBe(canonical([2, 1]));
  });

  it('handles nested structures', () => {
    expect(canonical({ x: { b: 1, a: [1, { z: 1, y: 2 }] } })).toBe(
      '{"x":{"a":[1,{"y":2,"z":1}],"b":1}}',
    );
  });

  it('handles null and primitives', () => {
    expect(canonical(null)).toBe('null');
    expect(canonical('s')).toBe('"s"');
  });
});

describe('sha256Hex', () => {
  it('matches the known digest of the empty string', async () => {
    expect(await sha256Hex('')).toBe(
      'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    );
  });

  it('matches the known digest of "abc"', async () => {
    expect(await sha256Hex('abc')).toBe(
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
    );
  });
});

describe('buildChain + verifyChain', () => {
  it('builds a chain that verifies', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }, { c: 3 }]);
    const check = await verifyChain(chain);
    expect(check.ok).toBe(true);
    expect(check.verified).toBe(3);
    expect(check.firstBadIndex).toBeNull();
  });

  it('links each entry to the previous hash', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }]);
    expect(chain[0].prevHash).toBe('');
    expect(chain[1].prevHash).toBe(chain[0].hash);
  });

  it('detects an edited payload and names it a content break', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }, { c: 3 }]);
    chain[1] = { ...chain[1], data: { b: 999 } };
    const check = await verifyChain(chain);
    expect(check.ok).toBe(false);
    expect(check.firstBadIndex).toBe(1);
    expect(check.detail).toMatch(/Content break/i);
    expect(check.detail).toMatch(/edited after/i);
  });

  it('detects a removed entry and names it a linkage break', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }, { c: 3 }]);
    const spliced = [chain[0], chain[2]];
    const check = await verifyChain(spliced);
    expect(check.ok).toBe(false);
    expect(check.firstBadIndex).toBe(1);
    expect(check.detail).toMatch(/Linkage break/i);
    expect(check.detail).toMatch(/removed, reordered or inserted/i);
  });

  it('detects a reordered pair', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }, { c: 3 }]);
    const swapped = [chain[0], chain[2], chain[1]];
    const check = await verifyChain(chain.length ? swapped : swapped);
    expect(check.ok).toBe(false);
  });

  it('reports an empty chain as trivially ok, not as a failure', async () => {
    const check = await verifyChain([]);
    expect(check.ok).toBe(true);
    expect(check.total).toBe(0);
  });

  it('honours a non-empty genesis value', async () => {
    const chain = await buildChain([{ a: 1 }], 'genesis-hash');
    expect(chain[0].prevHash).toBe('genesis-hash');
    expect((await verifyChain(chain, 'genesis-hash')).ok).toBe(true);
    expect((await verifyChain(chain, '')).ok).toBe(false);
  });
});

describe('expectedHash', () => {
  it('is stable for the same entry and prev', async () => {
    const e: LedgerEntry = { index: 0, data: { a: 1 }, hash: '', prevHash: '' };
    expect(await expectedHash(e, '')).toBe(await expectedHash(e, ''));
  });

  it('changes when the prev hash changes', async () => {
    const e: LedgerEntry = { index: 0, data: { a: 1 }, hash: '', prevHash: '' };
    expect(await expectedHash(e, 'x')).not.toBe(await expectedHash(e, 'y'));
  });
});

describe('detectTruncation', () => {
  it('reports truncation when the ledger ends before the recorded head', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }, { c: 3 }]);
    const head = { index: 2, hash: chain[2].hash };
    const short = chain.slice(0, 2);
    const r = detectTruncation(short, head);
    expect(r.truncated).toBe(true);
    expect(r.detail).toMatch(/1 entries are missing/i);
  });

  it('reports a rewritten tail when the head hash differs', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }]);
    const r = detectTruncation(chain, { index: 1, hash: 'deadbeef' });
    expect(r.truncated).toBe(true);
    expect(r.detail).toMatch(/rewritten/i);
  });

  it('reports no truncation when the head matches', async () => {
    const chain = await buildChain([{ a: 1 }, { b: 2 }]);
    const r = detectTruncation(chain, { index: 1, hash: chain[1].hash });
    expect(r.truncated).toBe(false);
  });

  it('says truncation is undetectable without a recorded head', async () => {
    const chain = await buildChain([{ a: 1 }]);
    const r = detectTruncation(chain, null);
    expect(r.truncated).toBe(false);
    expect(r.detail).toMatch(/cannot be detected/i);
  });

  it('flags an empty ledger against a recorded head', () => {
    const r = detectTruncation([], { index: 5, hash: 'x' });
    expect(r.truncated).toBe(true);
  });
});
