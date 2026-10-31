/* Docs / FAQ — searchable, with the real tool reference.
 *
 * Two corpora, both sourced rather than written:
 *   · FAQ  — answers derived from README.md's hard invariants and the kanban
 *            door contract, each annotated with the file it comes from.
 *   · Tools — the full estate catalog from src/data/tools.json (AST-extracted).
 */
import React, { useMemo, useState } from 'react';
import raw from '../data/tools.json';
import { Panel, Pill } from '../components/ui';

type Tool = { name: string; title: string; description: string; domain: string; params: string[] };
const CATALOG = raw as unknown as { count: number; tools: Tool[] };

const FAQ: Array<{ q: string; a: React.ReactNode; src: string; tags: string[] }> = [
  {
    q: 'What stops an imagined fact from being retrieved as if it were real?',
    a: (
      <>
        Three guards, all at the write path. <span className="mono">_assert_grounded()</span> runs inside{' '}
        <span className="mono">_add_to_vector_index()</span> and <span className="mono">_add_to_bm25_index()</span>, so a simulated
        record reaching either index raises immediately. <span className="mono">remember()</span> is grounded-only by default, and{' '}
        <span className="mono">_validate_partition_tags()</span> rejects an origin/store mismatch at the lowest append path.
      </>
    ),
    src: 'README.md § Memory model / Hard invariants 1–3',
    tags: ['memory', 'grounding', 'index', 'safety'],
  },
  {
    q: 'How does a dream become grounded?',
    a: (
      <>
        Only with evidence. <span className="mono">promote_simulated_to_grounded()</span> accepts a simulated record only when it
        carries <span className="mono">prediction_error_evidence</span> — a linked prior prediction resolved in its favour, or a
        voucher from a registered external verifier. There is no other promotion path.
      </>
    ),
    src: 'README.md § Hard invariant 4 · mcp/memory_tools.py § _memory_promote',
    tags: ['memory', 'promotion', 'dreams', 'evidence'],
  },
  {
    q: 'Why is there only one kanban, and what is “the door”?',
    a: (
      <>
        The estate had four kanban implementations and two SQLite files, and one real board (16 cards) lived only in the orphan
        file where no other tool could see it. The merge left one store, one writer, one door:{' '}
        <span className="mono">mem20-kanban.service</span> on <span className="mono">127.0.0.1:8221</span>, backed by{' '}
        <span className="mono">kanban_3.db</span>. Every other kanban tool is now a client of that REST door.
      </>
    ),
    src: 'mem20kanbanz/README.md § why this exists',
    tags: ['kanban', 'door', 'architecture', 'merge'],
  },
  {
    q: 'What happens when I move a card into a column that is full?',
    a: (
      <>
        The door refuses it with <strong>HTTP 422</strong>, and the client turns that into{' '}
        <span className="mono">CapacityFull</span>. Nothing is silently moved, and nothing is silently dropped — the refusal is
        shown against the column that refused it. A silent no-op here would be worse than an error, because an agent would
        believe the work had advanced.
      </>
    ),
    src: 'mem20kanbanz/door.py § _request / CapacityFull',
    tags: ['kanban', 'wip', '422', 'capacity'],
  },
  {
    q: 'How does a bot know which column means “finished”?',
    a: (
      <>
        It reads the flag, never the name. Exactly one column on a board carries{' '}
        <span className="mono">isDoneColumn</span>, and the boards disagree on naming (<span className="mono">done</span>,{' '}
        <span className="mono">Done</span>, <span className="mono">Review</span>; <span className="mono">in_progress</span> vs{' '}
        <span className="mono">in progress</span>). A hardcoded name made every claim on one board fail, which is how this got
        fixed.
      </>
    ),
    src: 'mem20kanbanz/README.md § the claim / done lifecycle',
    tags: ['kanban', 'done', 'isDoneColumn', 'bots'],
  },
  {
    q: 'What does claiming a card actually write?',
    a: (
      <>
        The assignee is written <em>before</em> the move, so a card is never sitting in the working column owned by nobody. It is
        a metadata <strong>merge</strong> (<span className="mono">PATCH /api/tasks/:id/metadata</span>), so recording an assignee
        never erases tags; a key set to <span className="mono">null</span> is removed, which is how a claim is released. A claim
        on someone else's card is refused unless forced.
      </>
    ),
    src: 'mem20kanbanz/door.py § claim / patch_metadata',
    tags: ['kanban', 'claim', 'metadata', 'assignee'],
  },
  {
    q: 'Does the web shell ever open the kanban database directly?',
    a: (
      <>
        No. It is an HTTP client and nothing else. A second writer on that SQLite file is a second source of truth — that is the
        drift the merge exists to prevent, so the browser has no file access and no ORM.
      </>
    ),
    src: 'mem20kanbanz/door.py § design rules',
    tags: ['kanban', 'architecture', 'sqlite'],
  },
  {
    q: 'Why did the site 404 at the custom domain?',
    a: (
      <>
        Because DNS is a different layer from Pages. The repo can serve perfectly on{' '}
        <span className="mono">*.github.io/mem20/</span> while{' '}
        <span className="mono">mem20.jaysonai.online</span> returns NXDOMAIN — that custom domain is now
        <strong>retired</strong> and will not be restored. GitHub only accepts a custom domain once the
        record exists, so the site is served from the Pages path only.
      </>
    ),
    src: 'docs/CNAME · GitHub Pages custom-domain behaviour',
    tags: ['deploy', 'dns', 'pages', 'cname'],
  },
  {
    q: 'What are the five memory invariants, in order?',
    a: (
      <>
        (1) indexes are grounded-only; (2) <span className="mono">remember()</span> is grounded-only by default; (3) the ledger is
        append-only with validated origin/store tags; (4) promotion is evidence-based; (5) epistemic status is stamped onto the
        original record. The Memory model surface renders all five with the guard that enforces each.
      </>
    ),
    src: 'README.md § Hard invariants enforced by the store engine',
    tags: ['memory', 'invariants'],
  },
  {
    q: 'How many tools does mem20 actually expose?',
    a: (
      <>
        {CATALOG.count}, counted from source. The docs' summary line and this shell disagree with an earlier '260'; the count
        below is produced by parsing every <span className="mono">mt.Tool(…)</span> registration in{' '}
        <span className="mono">mcp/tools/*.py</span>, so it is the number this UI stands behind.
      </>
    ),
    src: 'src/data/tools.json (AST extraction)',
    tags: ['tools', 'catalog', 'count'],
  },
];

export default function DocsFaq() {
  const [q, setQ] = useState('');
  const [mode, setMode] = useState<'faq' | 'tools'>('faq');
  const [sel, setSel] = useState(0);
  const [toolSel, setToolSel] = useState<Tool | null>(null);

  const term = q.trim().toLowerCase();

  const faqHits = useMemo(
    () =>
      FAQ.map((f, i) => ({ f, i })).filter(({ f }) => {
        if (!term) return true;
        return (
          f.q.toLowerCase().includes(term) ||
          f.tags.join(' ').includes(term) ||
          f.tags.some((t) => t.includes(term))
        );
      }),
    [term],
  );

  const toolHits = useMemo(
    () =>
      CATALOG.tools.filter((t) => {
        if (!term) return true;
        return (
          t.name.toLowerCase().includes(term) ||
          t.title.toLowerCase().includes(term) ||
          t.description.toLowerCase().includes(term) ||
          t.domain.toLowerCase().includes(term)
        );
      }),
    [term],
  );

  const current = FAQ[sel];

  return (
    <div className="page wide">
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
        <button className={`btn sm ${mode === 'faq' ? 'primary' : ''}`} onClick={() => setMode('faq')}>
          FAQ <span style={{ opacity: 0.6 }}>({FAQ.length})</span>
        </button>
        <button className={`btn sm ${mode === 'tools' ? 'primary' : ''}`} onClick={() => setMode('tools')}>
          Tool reference <span style={{ opacity: 0.6 }}>({CATALOG.count})</span>
        </button>
        <span className="spacer" />
        <input
          className="input"
          style={{ width: 300 }}
          placeholder={mode === 'faq' ? 'search questions and tags…' : 'search tool, domain or description…'}
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {mode === 'faq' ? (
        <div className="docs-grid">
          <div className="panel doc-list">
            <div style={{ padding: 8 }}>
              {faqHits.map(({ f, i }) => (
                <div
                  key={f.q}
                  className={`doc-term ${sel === i ? 'active' : ''}`}
                  onClick={() => setSel(i)}
                >
                  {f.q}
                  <span className="dom">{f.tags.slice(0, 2).map((t) => `#${t}`).join(' ')}</span>
                </div>
              ))}
              {faqHits.length === 0 && <div className="empty">nothing matches “{q}”</div>}
            </div>
          </div>

          <Panel title="Answer" right={<Pill mono>source-backed</Pill>}>
            {current && (
              <>
                <h2 style={{ fontSize: 17, color: 'var(--ink-0)', margin: '0 0 12px', lineHeight: 1.35 }}>{current.q}</h2>
                <div style={{ color: 'var(--ink-1)', fontSize: 13.5, lineHeight: 1.7 }}>{current.a}</div>
                <hr className="sep" />
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)' }}>source</span>
                  <span className="mono" style={{ fontSize: 11.5, color: 'var(--cyan-0)' }}>{current.src}</span>
                </div>
                <div style={{ display: 'flex', gap: 5, marginTop: 12, flexWrap: 'wrap' }}>
                  {current.tags.map((t) => (
                    <span key={t} className="tag">#{t}</span>
                  ))}
                </div>
              </>
            )}
          </Panel>
        </div>
      ) : (
        <div className="docs-grid">
          <div className="panel doc-list">
            <div style={{ padding: 8 }}>
              {toolHits.slice(0, 300).map((t) => (
                <div
                  key={t.name}
                  className={`doc-term ${toolSel?.name === t.name ? 'active' : ''}`}
                  onClick={() => setToolSel(t)}
                >
                  <span className="mono">{t.name}</span>
                  <span className="dom">{t.domain}</span>
                </div>
              ))}
              {toolHits.length === 0 && <div className="empty">no tool matches “{q}”</div>}
            </div>
          </div>

          <Panel title={toolSel ? toolSel.name : 'Select a tool'} right={<Pill mono>{toolHits.length} matches</Pill>}>
            {toolSel ? (
              <>
                <div style={{ fontSize: 15, color: 'var(--ink-0)', fontWeight: 600, marginBottom: 6 }}>
                  {toolSel.title || toolSel.name}
                </div>
                <div className="mono" style={{ fontSize: 11.5, color: 'var(--ink-3)', marginBottom: 14 }}>
                  {toolSel.domain} · mcp/tools/{toolSel.domain}_tools.py
                </div>
                <p style={{ color: 'var(--ink-1)', fontSize: 13.5, lineHeight: 1.65 }}>
                  {toolSel.description || 'this registration carries no description string'}
                </p>
                {toolSel.params.length > 0 && (
                  <>
                    <hr className="sep" />
                    <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)', marginBottom: 8 }}>
                      inputSchema properties
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {toolSel.params.map((p) => (
                        <span key={p} className="tag">{p}</span>
                      ))}
                    </div>
                  </>
                )}
              </>
            ) : (
              <div className="empty">
                <div>pick a tool from the list — {CATALOG.count} are registered in the estate</div>
                <div style={{ fontSize: 11.5 }}>descriptions shown verbatim from the source registration</div>
              </div>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
}
