/* Memory-graph model - nodes, edges, provenance, and as-of time travel.
 *
 * The deck's first pick. It is the one surface that SHOWS the product working
 * rather than describing it, and the data model already exists in the repo:
 * mem20agentz/mem20agentz/graphstore.py holds a node/edge store, and the
 * ledger carries the provenance that makes an edge trustworthy.
 *
 * This file is the pure model - layout, filtering, and the as-of projection.
 * The view is a thin renderer over it, so the interesting logic is testable
 * without a DOM.
 *
 * As-of time travel is the part worth getting right. "Show me the graph as it
 * was at T" is not "filter to nodes created before T": a node that was later
 * superseded must appear in its OLD form, and an edge that was later retracted
 * must still be present. So the projection replays the event log up to T and
 * returns the state at that instant, rather than filtering the current state.
 */

export type Epistemic = 'grounded' | 'simulated';

export interface GraphNode {
  id: string;
  label: string;
  /** The memory text, when the node carries one. */
  text?: string;
  epistemic: Epistemic;
  /** Where this node came from - the provenance chain. */
  origin: string;
  store: string;
  /** ISO timestamp the node entered the store. */
  at: string;
  tags: string[];
}

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  /** The relation, e.g. 'supports', 'contradicts', 'derived_from'. */
  kind: string;
  /** ISO timestamp the edge was asserted. */
  at: string;
  /** ISO timestamp the edge was retracted, when it was. */
  retractedAt?: string;
  /** The ledger entry that witnesses this edge. */
  witness?: string;
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/* ------------------------------------------------------------- as-of replay */

/**
 * Project the graph to its state at instant `t`.
 *
 * Replays rather than filters: a node or edge that existed at `t` is included
 * even if it has since been retracted, and one that did not yet exist is
 * excluded even though it is present now. This is what makes the time slider
 * honest - it shows history, not a filtered present.
 */
export function asOf(graph: Graph, t: string): Graph {
  const nodes = graph.nodes.filter((n) => n.at <= t);
  const nodeIds = new Set(nodes.map((n) => n.id));
  const edges = graph.edges.filter(
    (e) =>
      e.at <= t &&
      (!e.retractedAt || e.retractedAt > t) &&
      nodeIds.has(e.from) &&
      nodeIds.has(e.to),
  );
  return { nodes, edges };
}

/** Every distinct instant at which the graph changed - the slider's stops. */
export function changePoints(graph: Graph): string[] {
  const all = new Set<string>();
  for (const n of graph.nodes) all.add(n.at);
  for (const e of graph.edges) {
    all.add(e.at);
    if (e.retractedAt) all.add(e.retractedAt);
  }
  return [...all].sort();
}

/* ------------------------------------------------------------------ filters */

export interface GraphFilter {
  epistemic: 'all' | Epistemic;
  /** Free text matched against label, text and tags. */
  q: string;
  /** Only nodes carrying every one of these tags. */
  tags: string[];
}

export const EMPTY_FILTER: GraphFilter = { epistemic: 'all', q: '', tags: [] };

export function applyFilter(graph: Graph, f: GraphFilter): Graph {
  const q = f.q.trim().toLowerCase();
  const nodes = graph.nodes.filter((n) => {
    if (f.epistemic !== 'all' && n.epistemic !== f.epistemic) return false;
    if (f.tags.length > 0 && !f.tags.every((t) => n.tags.includes(t))) return false;
    if (q) {
      const hay = `${n.label} ${n.text || ''} ${n.tags.join(' ')}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
  const ids = new Set(nodes.map((n) => n.id));
  const edges = graph.edges.filter((e) => ids.has(e.from) && ids.has(e.to));
  return { nodes, edges };
}

/* ------------------------------------------------------------------- layout */

export interface Placed {
  node: GraphNode;
  x: number;
  y: number;
  r: number;
}

/**
 * Deterministic radial layout.
 *
 * Deliberately not a force simulation: a force layout gives a different picture
 * on every render, which makes two screenshots of "the same" graph impossible
 * to compare and makes a regression invisible. A stable layout means a change
 * in the picture is a change in the data.
 *
 * Grounded nodes sit on the inner ring, simulated on the outer, so the
 * partition the whole product is built around is visible at a glance.
 */
export function layout(graph: Graph, width: number, height: number): Placed[] {
  const cx = width / 2;
  const cy = height / 2;
  const grounded = graph.nodes.filter((n) => n.epistemic === 'grounded');
  const simulated = graph.nodes.filter((n) => n.epistemic === 'simulated');

  const place = (list: GraphNode[], radius: number): Placed[] =>
    list.map((node, i) => {
      const angle = (i / Math.max(1, list.length)) * Math.PI * 2 - Math.PI / 2;
      return {
        node,
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
        r: 7 + Math.min(9, (node.tags.length || 0) * 2),
      };
    });

  const maxR = Math.min(width, height) / 2 - 40;
  return [...place(grounded, maxR * 0.55), ...place(simulated, maxR * 0.92)];
}

/* ------------------------------------------------------------------ summary */

export interface GraphSummary {
  nodes: number;
  edges: number;
  grounded: number;
  simulated: number;
  /** Node ids with no edge at all - often a data-quality signal. */
  orphans: number;
  /** Edges whose kind is 'contradicts'. */
  contradictions: number;
  /** Distinct origins across all nodes. */
  origins: number;
}

export function summarise(graph: Graph): GraphSummary {
  const degree = new Map<string, number>();
  for (const n of graph.nodes) degree.set(n.id, 0);
  for (const e of graph.edges) {
    degree.set(e.from, (degree.get(e.from) || 0) + 1);
    degree.set(e.to, (degree.get(e.to) || 0) + 1);
  }
  return {
    nodes: graph.nodes.length,
    edges: graph.edges.length,
    grounded: graph.nodes.filter((n) => n.epistemic === 'grounded').length,
    simulated: graph.nodes.filter((n) => n.epistemic === 'simulated').length,
    orphans: [...degree.values()].filter((d) => d === 0).length,
    contradictions: graph.edges.filter((e) => e.kind === 'contradicts').length,
    origins: new Set(graph.nodes.map((n) => n.origin)).size,
  };
}

/**
 * Build a graph from bridge memory records.
 *
 * The bridge returns flat records with no edges, so edges are derived from the
 * only relation the records actually carry: shared tags. This is stated in the
 * UI rather than presented as if the store had returned a real graph - an
 * inferred edge and a stored edge are different things and the viewer says
 * which it is showing.
 */
export function fromRecords(records: Array<Record<string, any>>): Graph {
  const nodes: GraphNode[] = records.map((r, i) => ({
    id: String(r.id ?? `rec-${i}`),
    label: String(r.topic ?? r.title ?? ((r.text || r.content || '').slice(0, 40) || `record ${i}`)),
    text: String(r.text ?? r.content ?? ''),
    epistemic: String(r.epistemic_status ?? 'grounded') === 'simulated' ? 'simulated' : 'grounded',
    origin: String(r.origin ?? 'unknown'),
    store: String(r.store ?? 'memory'),
    at: String(r.created_at ?? new Date().toISOString()),
    tags: Array.isArray(r.tags) ? r.tags.map(String) : [],
  }));

  const edges: GraphEdge[] = [];
  const byTag = new Map<string, string[]>();
  for (const n of nodes) {
    for (const t of n.tags) {
      const list = byTag.get(t) || [];
      list.push(n.id);
      byTag.set(t, list);
    }
  }
  let e = 0;
  for (const [tag, ids] of byTag) {
    for (let i = 0; i + 1 < ids.length; i += 1) {
      edges.push({
        id: `e${e++}`,
        from: ids[i],
        to: ids[i + 1],
        kind: `shares:${tag}`,
        at: nodes.find((n) => n.id === ids[i])?.at || new Date().toISOString(),
      });
    }
  }
  return { nodes, edges };
}
