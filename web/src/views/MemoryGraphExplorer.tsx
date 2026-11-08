/* Surface 1 — Memory-graph explorer. The deck's first pick.
 *
 * Why this one first: it is the only surface that SHOWS the product working
 * rather than describing it, and it doubles as the demo asset for every launch
 * post. The data model already exists (mem20agentz/graphstore.py), and the
 * ledger carries the provenance that makes an edge trustworthy.
 *
 * Two honesty rules this view enforces:
 *
 *   1. When the bridge is unreachable it says so and offers a clearly-labelled
 *      sample graph. It never renders an empty canvas that reads as "you have
 *      no memories".
 *   2. Edges derived from shared tags are labelled as INFERRED. The bridge
 *      returns flat records with no edges, so presenting a derived edge as a
 *      stored one would be a lie about what the store knows.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { Notice, Panel, Pill, Stat } from '../components/ui';
import { bridge, isOk, reasonOf, type MemoryRecord } from '../lib/backend';
import {
  applyFilter,
  asOf,
  changePoints,
  fromRecords,
  layout,
  summarise,
  EMPTY_FILTER,
  type Graph,
  type GraphFilter,
} from '../lib/graph';
import { SAMPLE_GRAPH } from '../lib/sample';

const W = 900;
const H = 520;

export default function MemoryGraphExplorer() {
  const [graph, setGraph] = useState<Graph | null>(null);
  const [source, setSource] = useState<'bridge' | 'sample' | null>(null);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<GraphFilter>(EMPTY_FILTER);
  const [t, setT] = useState<string>('');
  const [selected, setSelected] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    const r = await bridge.memory(200);
    if (isOk(r)) {
      const recs = (r.data?.records || []) as MemoryRecord[];
      if (recs.length > 0) {
        setGraph(fromRecords(recs as Array<Record<string, any>>));
        setSource('bridge');
        setReason('');
      } else {
        setGraph(SAMPLE_GRAPH);
        setSource('sample');
        setReason('The bridge answered but the store holds no records yet.');
      }
    } else {
      setGraph(SAMPLE_GRAPH);
      setSource('sample');
      setReason(reasonOf(r));
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const stops = useMemo(() => (graph ? changePoints(graph) : []), [graph]);
  useEffect(() => {
    if (stops.length > 0 && !t) setT(stops[stops.length - 1]);
  }, [stops, t]);

  const view = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };
    const at = t ? asOf(graph, t) : graph;
    return applyFilter(at, filter);
  }, [graph, t, filter]);

  const placed = useMemo(() => layout(view, W, H), [view]);
  const summary = useMemo(() => (graph ? summarise(graph) : null), [graph]);
  const pos = useMemo(() => new Map(placed.map((p) => [p.node.id, p])), [placed]);
  const sel = selected ? view.nodes.find((n) => n.id === selected) : null;

  const allTags = useMemo(
    () => (graph ? [...new Set(graph.nodes.flatMap((n) => n.tags))].sort() : []),
    [graph],
  );

  return (
    <div className="page wide">
      <p className="lede">
        The memory substrate, drawn. Grounded records sit on the inner ring, simulated on the outer —
        the partition the whole product is built around, visible at a glance. Drag the time slider to
        replay the graph as it was, not as it is filtered.
      </p>

      {source === 'sample' && (
        <div style={{ marginBottom: 14 }}>
          <Notice tone="warn" title="Showing a labelled sample graph — not your data">
            {reason} The graph below is a fixed sample so the surface is demonstrable; every node is
            marked <span className="mono">sample</span> in its provenance. Point the shell at a running
            bridge in <strong>Connection</strong> to see real records.
          </Notice>
        </div>
      )}

      {summary && (
        <div className="grid g4" style={{ marginBottom: 16 }}>
          <Stat k="nodes" v={summary.nodes} sub={source === 'sample' ? 'sample' : 'from bridge'} />
          <Stat k="edges" v={summary.edges} sub="inferred from tags" />
          <Stat k="grounded / simulated" v={`${summary.grounded} / ${summary.simulated}`} />
          <Stat k="contradictions" v={summary.contradictions} sub="kind=contradicts" />
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: 'minmax(0,1fr) 320px', alignItems: 'start' }}>
        <Panel
          title="Graph"
          right={
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <Pill tone={source === 'bridge' ? 'green' : 'amber'} dot>
                {source === 'bridge' ? 'live store' : 'sample'}
              </Pill>
              <button className="btn sm" onClick={load} disabled={loading}>
                {loading ? <span className="spin" /> : 'reload'}
              </button>
            </div>
          }
          bodyStyle={{ padding: 0 }}
        >
          <div className="gx-wrap">
            <svg viewBox={`0 0 ${W} ${H}`} className="gx-svg" role="img" aria-label="memory graph">
              <defs>
                <radialGradient id="gx-bg" cx="50%" cy="50%">
                  <stop offset="0%" stopColor="#0e1424" />
                  <stop offset="100%" stopColor="#070a12" />
                </radialGradient>
              </defs>
              <rect width={W} height={H} fill="url(#gx-bg)" />

              {/* ring guides make the grounded/simulated split legible */}
              <circle cx={W / 2} cy={H / 2} r={Math.min(W, H) / 2 * 0.55 - 0} className="gx-ring" />
              <circle cx={W / 2} cy={H / 2} r={Math.min(W, H) / 2 * 0.92 - 0} className="gx-ring" />

              {view.edges.map((e) => {
                const a = pos.get(e.from);
                const b = pos.get(e.to);
                if (!a || !b) return null;
                const contra = e.kind === 'contradicts';
                return (
                  <line
                    key={e.id}
                    x1={a.x}
                    y1={a.y}
                    x2={b.x}
                    y2={b.y}
                    className={`gx-edge ${contra ? 'contra' : ''}`}
                  />
                );
              })}

              {placed.map((p) => (
                <g
                  key={p.node.id}
                  className={`gx-node ${p.node.epistemic} ${selected === p.node.id ? 'sel' : ''}`}
                  onClick={() => setSelected(p.node.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle cx={p.x} cy={p.y} r={p.r} />
                  <text x={p.x} y={p.y + p.r + 12} textAnchor="middle" className="gx-label">
                    {p.node.label.length > 18 ? `${p.node.label.slice(0, 17)}…` : p.node.label}
                  </text>
                </g>
              ))}

              {placed.length === 0 && (
                <text x={W / 2} y={H / 2} textAnchor="middle" className="gx-empty">
                  no nodes match the current filter
                </text>
              )}
            </svg>
          </div>

          <div className="gx-controls">
            <div className="gx-legend">
              <span className="sw"><span className="sq grounded" /> grounded</span>
              <span className="sw"><span className="sq simulated" /> simulated</span>
              <span className="sw"><span className="ln contra" /> contradicts</span>
            </div>
            <div className="gx-slider">
              <label htmlFor="gx-t">as of</label>
              <input
                id="gx-t"
                type="range"
                min={0}
                max={Math.max(0, stops.length - 1)}
                value={Math.max(0, stops.indexOf(t))}
                onChange={(e) => setT(stops[Number(e.target.value)] || '')}
                disabled={stops.length === 0}
              />
              <span className="mono gx-tval">{t ? t.replace('T', ' ').replace('Z', '') : '—'}</span>
            </div>
          </div>
        </Panel>

        <div style={{ display: 'grid', gap: 14 }}>
          <Panel title="Filter">
            <div style={{ display: 'grid', gap: 10 }}>
              <input
                className="input"
                placeholder="search label, text, tags…"
                value={filter.q}
                onChange={(e) => setFilter({ ...filter, q: e.target.value })}
              />
              <select
                className="select"
                value={filter.epistemic}
                onChange={(e) => setFilter({ ...filter, epistemic: e.target.value as any })}
              >
                <option value="all">all partitions</option>
                <option value="grounded">grounded only</option>
                <option value="simulated">simulated only</option>
              </select>
              {allTags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {allTags.slice(0, 14).map((tag) => {
                    const on = filter.tags.includes(tag);
                    return (
                      <button
                        key={tag}
                        className={`tag ${on ? 'on' : ''}`}
                        onClick={() =>
                          setFilter({
                            ...filter,
                            tags: on ? filter.tags.filter((x) => x !== tag) : [...filter.tags, tag],
                          })
                        }
                      >
                        {tag}
                      </button>
                    );
                  })}
                </div>
              )}
              <button className="btn sm" onClick={() => setFilter(EMPTY_FILTER)}>
                clear
              </button>
            </div>
          </Panel>

          <Panel title="Provenance" right={sel ? <Pill mono>{sel.id}</Pill> : undefined}>
            {!sel && <div className="empty">Select a node to see where it came from.</div>}
            {sel && (
              <dl className="kv">
                <dt>label</dt>
                <dd>{sel.label}</dd>
                <dt>partition</dt>
                <dd>
                  <Pill tone={sel.epistemic === 'grounded' ? 'green' : 'amber'}>{sel.epistemic}</Pill>
                </dd>
                <dt>origin</dt>
                <dd>{sel.origin}</dd>
                <dt>store</dt>
                <dd>{sel.store}</dd>
                <dt>entered</dt>
                <dd>{sel.at}</dd>
                <dt>tags</dt>
                <dd>{sel.tags.length ? sel.tags.join(', ') : '—'}</dd>
                {sel.text && (
                  <>
                    <dt>text</dt>
                    <dd style={{ fontFamily: 'var(--sans)', fontSize: 12 }}>{sel.text}</dd>
                  </>
                )}
              </dl>
            )}
          </Panel>

          <Notice tone="warn" title="Edges are inferred, and labelled as such">
            The bridge returns flat records with no edges. The links drawn here are derived from shared
            tags and named <span className="mono">shares:&lt;tag&gt;</span>. A stored edge and an
            inferred one are different things, and this view does not blur them.
          </Notice>
        </div>
      </div>
    </div>
  );
}
