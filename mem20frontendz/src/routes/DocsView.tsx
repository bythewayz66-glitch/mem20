/**
 * Docs / FAQ.
 *
 * Every statement here traces to source read in this build, not to a marketing
 * summary: the door contract from `mem20kanbanz/door.py`, the dream routes from
 * `mem20controlz/app.py`, the store paths from `mem20dreamz/lineage.py`, the
 * tool counts from a live `tools/list`, and the task/board counts from
 * `kanban_3.db` itself.
 *
 * The FAQ deliberately includes the uncomfortable answers — the missing door
 * listener, the absent kanban MCP tools, the no-CORS MCP transport, the empty
 * dream store — because those are the questions an integrator hits first.
 */

import { useMemo, useState } from 'react';
import { domainLabel, groupByDomain, loadTools } from '../api/mcp';
import { useAsync } from '../lib/useAsync';
import snapshotRaw from '../data/snapshot.kanban.json';
import type { KanbanSnapshot } from '../api/types';
import {
  Chip,
  EmptyState,
  IconBook,
  IconSearch,
  LoadingState,
  Notice,
  Provenance,
  Stat,
  plural,
} from '../components/ui';

const snap = snapshotRaw as unknown as KanbanSnapshot;

/** Card count for one board, derived from the dump rather than typed in. */
function boardCardCount(name: string): number {
  const board = snap.boards.find((b) => b.name === name);
  if (!board) return 0;
  const columnIds = new Set(snap.columns.filter((c) => c.board_id === board.id).map((c) => c.id));
  return snap.tasks.filter((t) => columnIds.has(t.column_id)).length;
}

interface FaqEntry {
  q: string;
  a: React.ReactNode;
  tags: string[];
}

const FAQ: FaqEntry[] = [
  {
    q: 'Why does the kanban board say "Capture" instead of "Live"?',
    a: (
      <>
        Because nothing is listening on <code>:8221</code>. The door's systemd unit does not exist on{' '}
        <code>sidney</code>, <code>ss -tulpn</code> shows no socket, and a direct{' '}
        <code>curl http://127.0.0.1:8221/</code> is refused. The board you see is a read-only dump of{' '}
        <code>kanban_3.db</code> taken on 2026-10-19. Once the door is installed, the same screens
        read it live and the badge turns green with a latency figure.
      </>
    ),
    tags: ['kanban', 'door', 'troubleshooting'],
  },
  {
    q: 'Can I write to the board from here?',
    a: (
      <>
        Only when the door answers. Every write path in the UI (<code>POST /api/tasks</code>,{' '}
        <code>PATCH /api/tasks/:id/metadata</code>, <code>POST /api/tasks/:id/move</code>) is the
        door's own contract, and a refusal surfaces verbatim rather than being swallowed. On a
        capture, the buttons are present but the write fails fast and says the door is unreachable —
        the UI never pretends a card was filed.
      </>
    ),
    tags: ['kanban', 'door', 'writes'],
  },
  {
    q: 'Why is there no kanban_* MCP tool?',
    a: (
      <>
        Because the registry has none. A live <code>tools/list</code> returns 257 tools across 36
        namespaces and not one of them starts with <code>kanban_</code>, <code>board_</code>,{' '}
        <code>dream_</code> or <code>agent_</code>. Kanban is REST-only. Anything that told you
        otherwise would be inventing a tool name.
      </>
    ),
    tags: ['mcp', 'kanban', 'tools'],
  },
  {
    q: 'Why does the MCP endpoint need a proxy?',
    a: (
      <>
        <code>:8082</code> answers a JSON-RPC <code>POST /</code> correctly, but sends no{' '}
        <code>Access-Control-Allow-*</code> headers and does not answer a preflight. A browser
        therefore cannot call it cross-origin at all. This app routes it through{' '}
        <code>/api/mcp</code>, which is same-origin — that is why the tool browser works.
      </>
    ),
    tags: ['mcp', 'cors', 'deployment'],
  },
  {
    q: 'Where do dreams come from, and why is the store empty?',
    a: (
      <>
        A dream is a lineage under <code>/opt/mem20/store/dreams</code>, and a promotion writes a
        pack under <code>/opt/mem20/store/promotions</code>. Neither directory existed on{' '}
        <code>sidney</code> when this was captured, so there are zero lineages. Creating one is free
        (<code>POST /api/dreams</code> calls no model); <em>running</em> one is not, which is why run
        is a separate, bounded action.
      </>
    ),
    tags: ['dreams', 'store', 'cost'],
  },
  {
    q: 'What does "hollow" mean?',
    a: (
      <>
        A hollow lineage recorded provider errors rather than work. It is still listed — hiding it
        would be worse — but it is flagged, promotion refuses it, and running it is refused too. Its
        signatures may still verify: a signature proves the bytes are intact, not that a dream
        happened.
      </>
    ),
    tags: ['dreams', 'epistemics', 'hollow'],
  },
  {
    q: 'Is "promoted" read from the ledger?',
    a: (
      <>
        No. It is derived from the promotions directory on disk, and the API says so in{' '}
        <code>derived_from</code> / <code>not_derived_from</code>. A pack written elsewhere would not
        appear. The UI repeats that limitation rather than implying braid provenance it did not
        check.
      </>
    ),
    tags: ['dreams', 'provenance', 'honesty'],
  },
  {
    q: 'What exactly is Sarge?',
    a: (
      <>
        A roadmap decomposer, not a chat agent. He scans <code>/opt/mem20/roadmaps/*.json</code>,
        creates one card per eligible phase, and writes the card id back into the phase as{' '}
        <code>jobid</code>. A phase that already has a <code>jobid</code> is skipped — that single
        field is what makes him safe to run on a loop. On this host his watermark file was absent, so
        he has never been activated.
      </>
    ),
    tags: ['kanban', 'sarge', 'roadmap'],
  },
  {
    q: `Why does the board hold ${snap.counts.tasks} cards when the README mentions 16?`,
    a: (
      <>
        Both can be true at different times. The README describes <em>Fleet HQ</em> at merge time (16
        tasks). The live store holds three boards — <em>dev</em> ({boardCardCount('dev')}),{' '}
        <em>pipelines</em> ({boardCardCount('pipelines')}) and <em>Fleet HQ</em> (
        {boardCardCount('Fleet HQ')}) — for {snap.counts.tasks} tasks total. Counts in prose go
        stale; the store does not.
      </>
    ),
    tags: ['kanban', 'data'],
  },
  {
    q: 'How do I run this against a real host?',
    a: (
      <>
        Point the three env vars at reachable services and put the three prefixes behind one reverse
        proxy: <code>MEM20_DOOR_URL</code>, <code>MEM20_CONTROL_URL</code>, <code>MEM20_MCP_URL</code>.
        The dev server proxies them already. Set <code>VITE_SOURCE_MODE=live</code> to forbid the
        snapshot fallback entirely.
      </>
    ),
    tags: ['deployment', 'configuration'],
  },
  {
    q: 'Is this the whole mem20 surface?',
    a: (
      <>
        No — it is the whole <em>frontend</em> surface. The control plane also exposes websites, DNS,
        fleet health, logs and the subsystem registry; those are reachable but not yet given a view
        here. Naming that gap is more useful than a half-built tab, so it is listed as the next
        milestone rather than faked.
      </>
    ),
    tags: ['scope', 'roadmap'],
  },
];

export default function DocsView() {
  const [query, setQuery] = useState('');
  const tools = useAsync(loadTools, []);
  const [open, setOpen] = useState<number | null>(0);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return FAQ;
    return FAQ.filter(
      (f) =>
        f.q.toLowerCase().includes(q) ||
        f.tags.some((t) => t.includes(q)) ||
        String(f.a).toLowerCase().includes(q),
    );
  }, [query]);

  const domains = useMemo(() => (tools.data ? groupByDomain(tools.data.data) : []), [tools.data]);

  return (
    <>
      <div className="spread" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div className="flex">
          <Chip tone="accent">{plural(FAQ.length, 'answer')}</Chip>
          <Chip>{plural(domains.length, 'tool namespace')}</Chip>
        </div>
        <div className="search" style={{ maxWidth: 320 }}>
          <IconSearch className="search-icon" />
          <input
            className="input"
            placeholder="Search the docs…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search documentation"
          />
        </div>
      </div>

      <div
        className="grid-2"
        style={{ gridTemplateColumns: 'minmax(0, 1.6fr) minmax(280px, 1fr)' }}
      >
        <div className="stack">
          <div className="card">
            <header className="card-header">
              <IconBook size={15} />
              <h2>FAQ</h2>
            </header>
            {matches.length === 0 ? (
              <EmptyState title="No answer matches" icon={<IconSearch size={20} />}>
                Try “door”, “hollow”, “cors” or “sarge”.
              </EmptyState>
            ) : (
              <div>
                {matches.map((entry, i) => (
                  <div key={entry.q} style={{ borderBottom: '1px solid var(--line-soft)' }}>
                    <button
                      type="button"
                      aria-expanded={open === i}
                      onClick={() => setOpen(open === i ? null : i)}
                      style={{
                        display: 'flex',
                        gap: 10,
                        width: '100%',
                        padding: '12px 16px',
                        textAlign: 'left',
                        alignItems: 'flex-start',
                      }}
                    >
                      <span
                        className="mono"
                        style={{ fontSize: 10.5, color: 'var(--text-mute)', marginTop: 3 }}
                      >
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span style={{ fontSize: 13, fontWeight: 600, flex: 1 }}>{entry.q}</span>
                      <span className="muted" aria-hidden="true">
                        {open === i ? '\u2212' : '+'}
                      </span>
                    </button>
                    {open === i ? (
                      <div
                        style={{
                          padding: '0 16px 14px 42px',
                          fontSize: 12.5,
                          lineHeight: 1.7,
                          color: 'var(--text-dim)',
                        }}
                      >
                        {entry.a}
                        <div className="flex" style={{ gap: 4, marginTop: 9, flexWrap: 'wrap' }}>
                          {entry.tags.map((t) => (
                            <Chip key={t}>{t}</Chip>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card card-pad">
            <div className="stat-label" style={{ marginBottom: 8 }}>
              Endpoints, in full
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>Surface</th>
                  <th>Method + path</th>
                  <th>What it does</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['door', 'GET /api/boards', 'board list'],
                  ['door', 'GET /api/boards/{id}', 'columns + nested tasks'],
                  ['door', 'POST /api/boards', 'create board'],
                  ['door', 'POST /api/boards/{id}/done-column', 'flag the done column'],
                  ['door', 'POST /api/tasks', 'create card'],
                  ['door', 'GET /api/tasks/{id}', 'full card, body included'],
                  ['door', 'PUT /api/tasks/{id}', 'replace body'],
                  ['door', 'POST /api/tasks/{id}/move', 'move by column id'],
                  ['door', 'PATCH /api/tasks/{id}/metadata', 'merge metadata; null removes'],
                  ['door', 'DELETE /api/tasks/{id}', 'delete card'],
                  ['control', 'GET /api/dreams', 'lineage list, light rows'],
                  ['control', 'GET /api/dreams/{id}', 'one lineage, artifact included'],
                  ['control', 'GET /api/dreams/{id}/chain', 'braid chain'],
                  ['control', 'POST /api/dreams/{id}/verify', 're-prove every node'],
                  ['control', 'POST /api/dreams/{id}/promote', 'promote, or refuse with a reason'],
                  ['control', 'GET /api/dreams/runs', 'in-memory run jobs'],
                  ['control', 'GET /api/dreams/idle-stats', 'idle inventory + lock'],
                  ['control', 'GET /api/dreams/hollow', 'read-only hollow census'],
                  ['mcp', 'POST / (tools/list)', '257 tools'],
                ].map(([surface, path, what]) => (
                  <tr key={`${surface}-${path}`}>
                    <td>
                      <Chip
                        tone={surface === 'mcp' ? 'dream' : surface === 'door' ? 'accent' : 'green'}
                      >
                        {surface}
                      </Chip>
                    </td>
                    <td className="mono" style={{ fontSize: 11 }}>
                      {path}
                    </td>
                    <td className="dim" style={{ fontSize: 11.5 }}>
                      {what}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="stack">
          <div className="card card-pad">
            <div className="stat-label" style={{ marginBottom: 8 }}>
              Concepts
            </div>
            <div
              className="stack"
              style={{ gap: 10, fontSize: 12, lineHeight: 1.65, color: 'var(--text-dim)' }}
            >
              <div>
                <strong style={{ color: 'var(--text)' }}>Grounded vs simulated</strong>
                <div>
                  Grounded memory came from something that happened. Simulated came from generation.
                  The partition is hard, and promotion is the only bridge.
                </div>
              </div>
              <div>
                <strong style={{ color: 'var(--text)' }}>Braid</strong>
                <div>
                  The append-only, origin-tagged ledger. A dream's chain is a set of CIDs; verifying
                  re-reads and re-proves every node.
                </div>
              </div>
              <div>
                <strong style={{ color: 'var(--text)' }}>Promotion</strong>
                <div>
                  A reviewed artefact becomes portable. It refuses on a hollow lineage and on a chain
                  that does not verify — two different facts with two different remedies.
                </div>
              </div>
              <div>
                <strong style={{ color: 'var(--text)' }}>Door</strong>
                <div>
                  One store, one writer. Everything that touches kanban goes through the REST door;
                  nothing issues an INSERT against <code>kanban_3.db</code>.
                </div>
              </div>
            </div>
          </div>

          <div className="card card-pad">
            <div className="spread" style={{ marginBottom: 8 }}>
              <div className="stat-label">Tool namespaces</div>
              {tools.data ? <Provenance loaded={tools.data} what="Registry" /> : null}
            </div>
            {tools.loading ? (
              <LoadingState rows={2} label="Reading namespaces" />
            ) : (
              <div className="flex" style={{ gap: 4, flexWrap: 'wrap' }}>
                {domains.map((d) => (
                  <Chip key={d.id} title={domainLabel(d.id)}>
                    {d.id} · {d.count}
                  </Chip>
                ))}
              </div>
            )}
          </div>

          <div className="card card-pad">
            <div className="stat-label" style={{ marginBottom: 8 }}>
              This capture
            </div>
            <div className="stat-row" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <Stat label="Boards" value={snap.counts.boards} />
              <Stat label="Cards" value={snap.counts.tasks} />
              <Stat label="Columns" value={snap.counts.columns} />
              <Stat label="Tools" value={tools.data?.data.length ?? '—'} />
            </div>
            <p className="muted" style={{ fontSize: 11, marginTop: 10, lineHeight: 1.6 }}>
              Read from <code>kanban_3.db</code> and a live <code>tools/list</code> on{' '}
              <code>sidney</code>, 2026-10-19.
            </p>
          </div>

          <Notice>
            <strong>Not built yet:</strong> websites/DNS, fleet health, logs and the subsystem
            registry all exist on the control plane and are reachable — they just do not have a view
            here. That is the next milestone, not a hidden feature.
          </Notice>
        </div>
      </div>
    </>
  );
}
