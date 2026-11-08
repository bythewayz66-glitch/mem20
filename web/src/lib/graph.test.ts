import { describe, expect, it } from 'vitest';
import {
  applyFilter,
  asOf,
  changePoints,
  fromRecords,
  layout,
  summarise,
  EMPTY_FILTER,
  type Graph,
} from './graph';

const G: Graph = {
  nodes: [
    { id: 'a', label: 'A', epistemic: 'grounded', origin: 'user', store: 'memory', at: '2026-01-01T00:00:00Z', tags: ['x'] },
    { id: 'b', label: 'B', epistemic: 'grounded', origin: 'tool', store: 'memory', at: '2026-01-02T00:00:00Z', tags: ['x', 'y'] },
    { id: 'c', label: 'C', epistemic: 'simulated', origin: 'dream', store: 'imaginated', at: '2026-01-03T00:00:00Z', tags: ['y'] },
  ],
  edges: [
    { id: 'e1', from: 'a', to: 'b', kind: 'supports', at: '2026-01-02T00:00:00Z' },
    { id: 'e2', from: 'b', to: 'c', kind: 'contradicts', at: '2026-01-03T00:00:00Z', retractedAt: '2026-01-04T00:00:00Z' },
  ],
};

describe('asOf', () => {
  it('excludes nodes that did not exist yet', () => {
    const g = asOf(G, '2026-01-01T12:00:00Z');
    expect(g.nodes.map((n) => n.id)).toEqual(['a']);
  });

  it('includes a node that existed at T even if later retracted', () => {
    const g = asOf(G, '2026-01-03T12:00:00Z');
    expect(g.nodes.map((n) => n.id)).toContain('c');
  });

  it('keeps an edge that was still live at T', () => {
    const g = asOf(G, '2026-01-03T12:00:00Z');
    expect(g.edges.map((e) => e.id)).toContain('e2');
  });

  it('drops an edge after its retraction instant', () => {
    const g = asOf(G, '2026-01-05T00:00:00Z');
    expect(g.edges.map((e) => e.id)).not.toContain('e2');
  });

  it('never returns an edge whose endpoints are absent', () => {
    const g = asOf(G, '2026-01-01T12:00:00Z');
    expect(g.edges).toHaveLength(0);
  });

  it('returns the full graph at the end of time', () => {
    const g = asOf(G, '2030-01-01T00:00:00Z');
    expect(g.nodes).toHaveLength(3);
    expect(g.edges).toHaveLength(1); // e2 was retracted
  });
});

describe('changePoints', () => {
  it('includes node times, edge times and retraction times', () => {
    const pts = changePoints(G);
    expect(pts).toContain('2026-01-01T00:00:00Z');
    expect(pts).toContain('2026-01-03T00:00:00Z');
    expect(pts).toContain('2026-01-04T00:00:00Z');
  });

  it('is sorted ascending', () => {
    const pts = changePoints(G);
    expect([...pts].sort()).toEqual(pts);
  });
});

describe('applyFilter', () => {
  it('filters by epistemic partition', () => {
    const g = applyFilter(G, { ...EMPTY_FILTER, epistemic: 'simulated' });
    expect(g.nodes.map((n) => n.id)).toEqual(['c']);
  });

  it('filters by free text over label and tags', () => {
    expect(applyFilter(G, { ...EMPTY_FILTER, q: 'b' }).nodes.map((n) => n.id)).toEqual(['b']);
    expect(applyFilter(G, { ...EMPTY_FILTER, q: 'y' }).nodes.map((n) => n.id)).toEqual(['b', 'c']);
  });

  it('requires every requested tag', () => {
    expect(applyFilter(G, { ...EMPTY_FILTER, tags: ['x', 'y'] }).nodes.map((n) => n.id)).toEqual(['b']);
  });

  it('drops edges whose endpoints were filtered out', () => {
    const g = applyFilter(G, { ...EMPTY_FILTER, epistemic: 'simulated' });
    expect(g.edges).toHaveLength(0);
  });

  it('returns everything for the empty filter', () => {
    expect(applyFilter(G, EMPTY_FILTER).nodes).toHaveLength(3);
  });
});

describe('layout', () => {
  it('is deterministic - the same graph gives the same picture', () => {
    const a = layout(G, 800, 600);
    const b = layout(G, 800, 600);
    expect(a.map((p) => [p.x, p.y])).toEqual(b.map((p) => [p.x, p.y]));
  });

  it('places every node', () => {
    expect(layout(G, 800, 600)).toHaveLength(3);
  });

  it('keeps grounded nodes inside the simulated ring', () => {
    const placed = layout(G, 800, 600);
    const dist = (p: { x: number; y: number }) => Math.hypot(p.x - 400, p.y - 300);
    const grounded = placed.filter((p) => p.node.epistemic === 'grounded').map(dist);
    const simulated = placed.filter((p) => p.node.epistemic === 'simulated').map(dist);
    expect(Math.max(...grounded)).toBeLessThan(Math.min(...simulated));
  });

  it('handles an empty graph without dividing by zero', () => {
    expect(layout({ nodes: [], edges: [] }, 800, 600)).toEqual([]);
  });
});

describe('summarise', () => {
  it('counts nodes, edges and partitions', () => {
    const s = summarise(G);
    expect(s.nodes).toBe(3);
    expect(s.edges).toBe(2);
    expect(s.grounded).toBe(2);
    expect(s.simulated).toBe(1);
  });

  it('counts contradictions', () => {
    expect(summarise(G).contradictions).toBe(1);
  });

  it('counts orphans', () => {
    const orphan: Graph = { nodes: [{ ...G.nodes[0], id: 'z' }], edges: [] };
    expect(summarise(orphan).orphans).toBe(1);
  });

  it('counts distinct origins', () => {
    expect(summarise(G).origins).toBe(3);
  });
});

describe('fromRecords', () => {
  it('maps bridge records to nodes', () => {
    const g = fromRecords([
      { id: 'r1', topic: 'T1', text: 'body', origin: 'user', store: 'memory', tags: ['a'], created_at: '2026-01-01T00:00:00Z' },
    ]);
    expect(g.nodes[0].id).toBe('r1');
    expect(g.nodes[0].label).toBe('T1');
    expect(g.nodes[0].epistemic).toBe('grounded');
  });

  it('marks a simulated record as simulated', () => {
    const g = fromRecords([{ id: 'r1', epistemic_status: 'simulated' }]);
    expect(g.nodes[0].epistemic).toBe('simulated');
  });

  it('derives edges from shared tags, since the bridge returns none', () => {
    const g = fromRecords([
      { id: 'r1', tags: ['shared'] },
      { id: 'r2', tags: ['shared'] },
    ]);
    expect(g.edges).toHaveLength(1);
    expect(g.edges[0].kind).toBe('shares:shared');
  });

  it('produces no edges when no tags are shared', () => {
    const g = fromRecords([{ id: 'r1', tags: ['a'] }, { id: 'r2', tags: ['b'] }]);
    expect(g.edges).toHaveLength(0);
  });

  it('handles an empty record list', () => {
    expect(fromRecords([])).toEqual({ nodes: [], edges: [] });
  });
});
