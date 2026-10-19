/**
 * Kanban surface.
 *
 * Wired to the door contract (see `api/kanban.ts`), which is the only writer.
 * Two design decisions worth knowing:
 *
 * 1. **A card's body is not in the board listing.** The door strips it on
 *    purpose (door.py:305-312) so a 137-card board does not ship 137 bodies to
 *    every reader. So the card panel fetches `/api/tasks/{id}` when opened, and
 *    the board itself never claims to have content it does not have.
 * 2. **Optimistic move, authoritative re-read.** A drop updates the local board
 *    immediately, then calls the door. If the door refuses (WIP cap is a 422),
 *    the board is reloaded so the UI cannot sit in a state the store disagrees
 *    with.
 *
 * Sarge is shown as what he actually is: a decomposer driven by roadmap phase
 * `jobid`s, not a chat bot. His state file (`/root/.mem20agentz/sarge.json`)
 * did not exist at capture time, so the panel says "never activated" rather
 * than inventing a watermark.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  boardStats,
  boardsFromSnapshot,
  createBoard,
  createCard,
  deleteBoard,
  deleteCard,
  fetchCardBody,
  loadBoards,
  moveCard,
  probeDoor,
  setDoneColumn,
  updateCardContent,
  DoorError,
} from '../api/kanban';
import type { Board, Card, Column } from '../api/types';
import roadmapData from '../data/snapshot.roadmaps.json';
import type { RoadmapFile } from '../api/types';
import { useAsync } from '../lib/useAsync';
import {
  CaptureNotice,
  Chip,
  EmptyState,
  ErrorState,
  IconBoard,
  IconCheck,
  IconInfo,
  IconPlus,
  IconRefresh,
  IconRoute,
  IconSearch,
  IconTrash,
  IconWarn,
  IconX,
  LoadingState,
  Modal,
  Notice,
  Provenance,
  Stat,
  plural,
  shortDate,
} from '../components/ui';

const roadmaps = roadmapData as unknown as RoadmapFile[];

interface Props {
  /** Board name from the hash route, if any. */
  param: string;
  onNavigate: (param: string) => void;
}

export default function KanbanView({ param, onNavigate }: Props) {
  const boards = useAsync(loadBoards);
  const [overrides, setOverrides] = useState<Board[] | null>(null);
  const [query, setQuery] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [hideDone, setHideDone] = useState(false);
  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [openCard, setOpenCard] = useState<Card | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [showNewCard, setShowNewCard] = useState<Column | null>(null);
  const [showBoardConfig, setShowBoardConfig] = useState(false);
  const [showNewBoard, setShowNewBoard] = useState(false);
  const [showSarge, setShowSarge] = useState(false);

  const loadedBoards = overrides ?? boards.data?.data ?? boardsFromSnapshot();
  const loaded = boards.data ?? {
    data: loadedBoards,
    source: 'snapshot' as const,
    at: '',
    note: 'Reading the local board capture.',
  };

  const board: Board | undefined = useMemo(() => {
    if (!loadedBoards.length) return undefined;
    const named = loadedBoards.find((b) => b.name === param);
    if (named) return named;
    // Default to the fullest board, not the first in the list. The estate's
    // first board held 2 of 137 cards; opening on it hid 98% of the work.
    return [...loadedBoards].sort(
      (a, b) =>
        b.columns.reduce((n, c) => n + c.cards.length, 0) -
        a.columns.reduce((n, c) => n + c.cards.length, 0),
    )[0];
  }, [loadedBoards, param]);

  const stats = useMemo(() => (board ? boardStats(board) : null), [board]);

  /** Every card in the estate, so the header can say what this board is a slice of. */
  const allBoardsTotal = useMemo(
    () => loadedBoards.reduce((n, b) => n + b.columns.reduce((m, c) => m + c.cards.length, 0), 0),
    [loadedBoards],
  );

  /** Every card, flattened — the filter bar operates on the whole board. */
  const allCards = useMemo(() => (board ? board.columns.flatMap((c) => c.cards) : []), [board]);

  const filterActive = Boolean(query || assigneeFilter || tagFilter);

  const matches = useCallback(
    (card: Card) => {
      if (query) {
        const q = query.toLowerCase();
        if (
          !card.title.toLowerCase().includes(q) &&
          !card.tags.join(' ').toLowerCase().includes(q)
        )
          return false;
      }
      if (assigneeFilter && card.assignee !== assigneeFilter) return false;
      if (tagFilter && !card.tags.includes(tagFilter)) return false;
      return true;
    },
    [query, assigneeFilter, tagFilter],
  );

  const refresh = useCallback(() => {
    setOverrides(null);
    setSelection(new Set());
    boards.reload();
  }, [boards]);

  /** Apply a functional change to the board and keep it locally authoritative. */
  const mutate = useCallback(
    (fn: (b: Board) => Board) => {
      const current = overrides ?? boards.data?.data ?? boardsFromSnapshot();
      setOverrides(current.map((b) => (board && b.id === board.id ? fn(b) : b)));
    },
    [overrides, boards.data, board],
  );

  const onDrop = async (target: Column, cardId: string) => {
    if (!board) return;
    const source = board.columns.find((c) => c.cards.some((x) => x.id === cardId));
    if (!source || source.id === target.id) return;

    const card = source.cards.find((c) => c.id === cardId)!;

    // Optimistic: move locally first so the drop feels instant.
    mutate((b) => ({
      ...b,
      columns: b.columns.map((c) => {
        if (c.id === source.id)
          return { ...c, cards: c.cards.filter((x) => x.id !== cardId) };
        if (c.id === target.id)
          return {
            ...c,
            cards: [...c.cards, { ...card, status: c.name, done: c.isDone }].sort(
              (a, b2) => a.position - b2.position,
            ),
          };
        return c;
      }),
    }));

    setBusy(true);
    setFailure(null);
    try {
      await moveCard({
        taskId: cardId,
        targetColumnId: target.id,
        reason: 'moved in mem20frontendz',
      });
    } catch (err) {
      setFailure(
        err instanceof DoorError
          ? err.kind === 'capacity'
            ? `${target.name} is at its WIP limit. ${err.message}`
            : err.message
          : 'The move failed.',
      );
      refresh();
    } finally {
      setBusy(false);
    }
  };

  const bulkMove = async (columnName: string) => {
    if (!board || selection.size === 0) return;
    const target = board.columns.find((c) => c.name === columnName);
    if (!target) return;
    setBusy(true);
    setFailure(null);
    try {
      for (const id of selection) {
        await moveCard({ taskId: id, targetColumnId: target.id, reason: 'bulk move' });
      }
      setSelection(new Set());
      refresh();
    } catch (err) {
      setFailure(err instanceof Error ? err.message : 'The bulk move failed.');
      refresh();
    } finally {
      setBusy(false);
    }
  };

  const bulkDelete = async () => {
    if (selection.size === 0) return;
    setBusy(true);
    setFailure(null);
    try {
      for (const id of selection) await deleteCard(id);
      setSelection(new Set());
      refresh();
    } catch (err) {
      setFailure(err instanceof Error ? err.message : 'The bulk delete failed.');
      refresh();
    } finally {
      setBusy(false);
    }
  };

  if (boards.loading && !overrides) return <LoadingState rows={5} label="Reading boards" />;
  if (boards.error) return <ErrorState error={boards.error} onRetry={boards.reload} />;
  if (!board) {
    return (
      <EmptyState title="No boards on this door" icon={<IconBoard size={20} />}>
        The door answered with an empty board list. Create one to start.
      </EmptyState>
    );
  }

  const showEmpty = filterActive && allCards.filter(matches).length === 0;

  return (
    <>
      <div className="spread" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div className="flex" style={{ flexWrap: 'wrap' }}>
          <Provenance loaded={loaded} what="Board" />
          <span className="chip mono">{board.name}</span>
          {stats ? (
            <>
              <Chip>{plural(stats.total, 'card')}</Chip>
              <Chip tone="green">{stats.done} done</Chip>
              {stats.unclaimed > 0 ? <Chip tone="amber">{stats.unclaimed} unclaimed</Chip> : null}
            </>
          ) : null}
        </div>
        <div className="flex" style={{ flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-sm" onClick={refresh} disabled={busy}>
            <IconRefresh size={13} /> Refresh
          </button>
          <button type="button" className="btn btn-sm" onClick={() => setShowSarge(true)}>
            <IconRoute size={13} /> Sarge
          </button>
          <button type="button" className="btn btn-sm" onClick={() => setShowBoardConfig(true)}>
            Board config
          </button>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => setShowNewCard(board.columns[0] ?? null)}
          >
            <IconPlus size={13} /> New card
          </button>
        </div>
      </div>

      <CaptureNotice loaded={loaded} />

      <div className="grid-2" style={{ gridTemplateColumns: 'minmax(0, 1fr)', marginBottom: 14 }}>
        <div className="notice" style={{ alignItems: 'flex-start' }}>
          <IconInfo className="notice-icon" size={16} />
          <div>
            <strong>{board.goal || 'No goal set on this board.'}</strong>{' '}
            <span className="muted">
              Board id <span className="mono">{board.id.slice(0, 8)}</span> · created{' '}
              {shortDate(board.createdAt)} · {plural(board.columns.length, 'column')}
            </span>
            {allBoardsTotal !== stats?.total ? (
              <div className="muted" style={{ marginTop: 4, fontSize: 11.5 }}>
                This board holds {stats?.total ?? 0} of <strong>{allBoardsTotal}</strong> cards
                across {plural(loadedBoards.length, 'board')} on the estate. Switch board below.
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {stats && stats.total > 0 ? (
        <div className="stat-row" style={{ marginBottom: 14 }}>
          <Stat label="Total" value={stats.total} hint={`${board.columns.length} columns`} />
          <Stat label="Open" value={stats.open} hint="not in a done column" />
          <Stat label="Unclaimed" value={stats.unclaimed} hint="available to take" />
          <Stat label="Assignees" value={stats.assignees.length} hint="distinct owners" />
          <Stat
            label="Done"
            value={`${Math.round((stats.done / Math.max(1, stats.total)) * 100)}%`}
            hint={`${stats.done} of ${stats.total}`}
          />
        </div>
      ) : null}

      {failure ? (
        <div className="notice" data-tone="error" style={{ marginBottom: 12 }}>
          <IconWarn className="notice-icon" size={16} />
          <div>
            <strong>The door refused that write.</strong> {failure}
          </div>
        </div>
      ) : null}

      {/* --------------------------------------------------------- filter bar */}
      <div className="flex" style={{ marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div className="search" style={{ maxWidth: 340 }}>
          <IconSearch className="search-icon" />
          <input
            className="input"
            placeholder="Filter cards, tags…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Filter cards"
          />
        </div>
        <select
          className="select"
          style={{ width: 'auto', minWidth: 150 }}
          value={assigneeFilter}
          onChange={(e) => setAssigneeFilter(e.target.value)}
          aria-label="Filter by assignee"
        >
          <option value="">All assignees</option>
          {stats?.assignees.map((a) => (
            <option key={a.name} value={a.name}>
              {a.name} ({a.count})
            </option>
          ))}
        </select>
        <select
          className="select"
          style={{ width: 'auto', minWidth: 130 }}
          value={tagFilter}
          onChange={(e) => setTagFilter(e.target.value)}
          aria-label="Filter by tag"
        >
          <option value="">All tags</option>
          {stats?.tags.slice(0, 40).map((t) => (
            <option key={t.name} value={t.name}>
              {t.name} ({t.count})
            </option>
          ))}
        </select>
        <label className="flex" style={{ fontSize: 12.5, color: 'var(--text-dim)', gap: 6 }}>
          <input
            type="checkbox"
            checked={hideDone}
            onChange={(e) => setHideDone(e.target.checked)}
          />
          Hide done
        </label>
        {filterActive || hideDone ? (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setQuery('');
              setAssigneeFilter('');
              setTagFilter('');
              setHideDone(false);
            }}
          >
            <IconX size={12} /> Clear
          </button>
        ) : null}
      </div>

      {selection.size > 0 ? (
        <div
          className="card"
          style={{
            padding: '8px 12px',
            marginBottom: 12,
            display: 'flex',
            gap: 8,
            alignItems: 'center',
            flexWrap: 'wrap',
            borderColor: 'var(--accent)',
          }}
          role="region"
          aria-label="Bulk actions"
        >
          <strong style={{ fontSize: 12.5 }}>{plural(selection.size, 'card')} selected</strong>
          <select
            className="select"
            style={{ width: 'auto', minWidth: 150 }}
            defaultValue=""
            onChange={(e) => {
              if (e.target.value) void bulkMove(e.target.value);
              e.currentTarget.value = '';
            }}
            disabled={busy}
            aria-label="Move selected to column"
          >
            <option value="">Move to…</option>
            {board.columns.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="btn btn-sm btn-danger"
            onClick={bulkDelete}
            disabled={busy}
          >
            <IconTrash size={12} /> Delete
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setSelection(new Set())}
          >
            Clear selection
          </button>
        </div>
      ) : null}

      {/* ------------------------------------------------------------- boards */}
      {showEmpty ? (
        <EmptyState title="No cards match those filters" icon={<IconSearch size={20} />}>
          The board holds {plural(allCards.length, 'card')}; none of them match. Clear the filters to
          see them all.
        </EmptyState>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${Math.max(
              1,
              board.columns.length,
            )}, minmax(246px, 1fr))`,
            gap: 12,
            alignItems: 'start',
            overflowX: 'auto',
            paddingBottom: 8,
          }}
        >
          {board.columns.map((column) => {
            const visible = column.cards.filter(matches);
            if (hideDone && column.isDone) return null;
            const over = column.wipLimit > 0 && column.cards.length > column.wipLimit;

            return (
              <section
                key={column.id}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = 'move';
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  const id = e.dataTransfer.getData('text/plain') || dragging;
                  if (id) void onDrop(column, id);
                  setDragging(null);
                }}
                aria-label={`${column.name} column`}
                style={{
                  background: 'var(--bg-panel)',
                  border: `1px solid ${over ? 'var(--red)' : 'var(--line)'}`,
                  borderRadius: 'var(--r-md)',
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 140,
                }}
              >
                <header
                  style={{
                    padding: '9px 11px',
                    borderBottom: '1px solid var(--line-soft)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span style={{ fontSize: 12.5, fontWeight: 600 }} className="truncate">
                    {column.name}
                  </span>
                  {column.isDone ? <Chip tone="green">done</Chip> : null}
                  <span style={{ marginLeft: 'auto' }} className="chip mono">
                    {column.cards.length}
                    {column.wipLimit > 0 ? `/${column.wipLimit}` : ''}
                  </span>
                </header>

                {over ? (
                  <div
                    style={{
                      padding: '5px 11px',
                      fontSize: 11,
                      color: 'var(--red)',
                      background: 'color-mix(in srgb, var(--red) 9%, transparent)',
                    }}
                  >
                    Over WIP limit by {column.cards.length - column.wipLimit}
                  </div>
                ) : null}

                <div style={{ padding: 8, display: 'grid', gap: 7 }}>
                  {visible.map((card) => {
                    const selected = selection.has(card.id);
                    return (
                      <article
                        key={card.id}
                        draggable
                        onDragStart={(e) => {
                          e.dataTransfer.setData('text/plain', card.id);
                          e.dataTransfer.effectAllowed = 'move';
                          setDragging(card.id);
                        }}
                        onDragEnd={() => setDragging(null)}
                        style={{
                          background: 'var(--bg-panel-2)',
                          border: `1px solid ${selected ? 'var(--accent)' : 'var(--line)'}`,
                          borderRadius: 'var(--r-sm)',
                          padding: '9px 10px',
                          cursor: 'grab',
                          opacity: dragging === card.id ? 0.45 : 1,
                        }}
                      >
                        <div className="flex" style={{ alignItems: 'flex-start', gap: 6 }}>
                          <input
                            type="checkbox"
                            checked={selected}
                            onChange={(e) => {
                              setSelection((prev) => {
                                const next = new Set(prev);
                                if (e.target.checked) next.add(card.id);
                                else next.delete(card.id);
                                return next;
                              });
                            }}
                            aria-label={`Select ${card.title}`}
                            style={{ marginTop: 2 }}
                          />
                          <button
                            type="button"
                            onClick={() => setOpenCard(card)}
                            style={{
                              textAlign: 'left',
                              fontSize: 12.5,
                              lineHeight: 1.45,
                              flex: 1,
                              minWidth: 0,
                            }}
                          >
                            {card.title}
                          </button>
                        </div>

                        {card.assignee || card.tags.length ? (
                          <div className="flex" style={{ flexWrap: 'wrap', gap: 4, marginTop: 7 }}>
                            {card.assignee ? (
                              <Chip tone="accent" title="Assignee">
                                {card.assignee}
                              </Chip>
                            ) : null}
                            {card.tags.slice(0, 3).map((t) => (
                              <Chip key={t} title="Tag">
                                {t}
                              </Chip>
                            ))}
                            {card.tags.length > 3 ? (
                              <Chip title={card.tags.slice(3).join(', ')}>
                                +{card.tags.length - 3}
                              </Chip>
                            ) : null}
                          </div>
                        ) : null}

                        <div
                          className="mono"
                          style={{ fontSize: 10, color: 'var(--text-mute)', marginTop: 6 }}
                          title={card.updatedAt ?? undefined}
                        >
                          {card.id.slice(0, 8)} · {shortDate(card.updatedAt)}
                        </div>
                      </article>
                    );
                  })}

                  {visible.length === 0 ? (
                    <div
                      style={{
                        padding: '14px 10px',
                        fontSize: 11.5,
                        color: 'var(--text-mute)',
                        textAlign: 'center',
                        border: '1px dashed var(--line)',
                        borderRadius: 'var(--r-sm)',
                      }}
                    >
                      {column.cards.length === 0 ? 'Empty' : 'Filtered out'}
                    </div>
                  ) : null}

                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => setShowNewCard(column)}
                    style={{ justifyContent: 'flex-start', color: 'var(--text-mute)' }}
                  >
                    <IconPlus size={12} /> Add card
                  </button>
                </div>
              </section>
            );
          })}
        </div>
      )}

      {/* -------------------------------------------------------- board switcher */}
      <div className="flex" style={{ marginTop: 18, flexWrap: 'wrap' }}>
        <span className="muted" style={{ fontSize: 12 }}>
          Boards on the door:
        </span>
        {loadedBoards.map((b) => (
          <button
            key={b.id}
            type="button"
            className={`btn btn-sm${b.id === board.id ? ' btn-primary' : ''}`}
            onClick={() => onNavigate(b.name)}
          >
            {b.name} ({b.columns.reduce((n, c) => n + c.cards.length, 0)})
          </button>
        ))}
        <button
          type="button"
          className="btn btn-sm btn-ghost"
          onClick={() => setShowNewBoard(true)}
        >
          <IconPlus size={12} /> New board
        </button>
      </div>

      {/* -------------------------------------------------------------- modals */}
      {openCard ? (
        <CardPanel
          card={openCard}
          onClose={() => setOpenCard(null)}
          onSaved={() => {
            setOpenCard(null);
            refresh();
          }}
          columns={board.columns}
        />
      ) : null}

      <Modal
        open={Boolean(showNewCard)}
        onClose={() => setShowNewCard(null)}
        title="New card"
        subtitle={`Filed on ${board.name}${showNewCard ? ` → ${showNewCard.name}` : ''}.`}
      >
        <NewCardForm
          column={showNewCard}
          board={board}
          onDone={() => {
            setShowNewCard(null);
            refresh();
          }}
          onCancel={() => setShowNewCard(null)}
        />
      </Modal>

      <Modal
        open={showNewBoard}
        onClose={() => setShowNewBoard(false)}
        title="New board"
        subtitle="Creates todo / in_progress / done with done flagged as the completion column."
      >
        <NewBoardForm
          onDone={() => {
            setShowNewBoard(false);
            refresh();
          }}
          onCancel={() => setShowNewBoard(false)}
        />
      </Modal>

      <Modal
        open={showBoardConfig}
        onClose={() => setShowBoardConfig(false)}
        title="Board configuration"
        subtitle="The door owns column order and the done flag. WIP limits are set on the door, not here."
      >
        <div className="stack">
          <Notice>
            <strong>{board.name}</strong> — {board.goal || 'no goal'}
          </Notice>
          <table className="table">
            <thead>
              <tr>
                <th>Column</th>
                <th>Position</th>
                <th>WIP</th>
                <th>Flags</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {board.columns.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td className="mono">{c.position}</td>
                  <td className="mono">{c.wipLimit || '—'}</td>
                  <td>
                    <div className="flex" style={{ gap: 4 }}>
                      {c.isDone ? <Chip tone="green">done</Chip> : null}
                      {c.isLanding ? <Chip tone="accent">landing</Chip> : null}
                    </div>
                  </td>
                  <td>
                    {!c.isDone ? (
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        disabled={busy}
                        onClick={async () => {
                          setBusy(true);
                          setFailure(null);
                          try {
                            await setDoneColumn(board.id, c.name);
                            refresh();
                          } catch (err) {
                            setFailure(err instanceof Error ? err.message : 'Failed.');
                          } finally {
                            setBusy(false);
                          }
                        }}
                      >
                        Mark done column
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="spread">
            <span className="muted" style={{ fontSize: 11.5 }}>
              Deleting a board removes its columns and cards on the door. This is not undoable.
            </span>
            <button
              type="button"
              className="btn btn-sm btn-danger"
              disabled={busy}
              onClick={async () => {
                if (!window.confirm(`Delete board "${board.name}" and all of its cards?`)) return;
                setBusy(true);
                try {
                  await deleteBoard(board.id);
                  setShowBoardConfig(false);
                  refresh();
                } catch (err) {
                  setFailure(err instanceof Error ? err.message : 'Failed.');
                } finally {
                  setBusy(false);
                }
              }}
            >
              <IconTrash size={12} /> Delete board
            </button>
          </div>
        </div>
      </Modal>

      <Modal
        open={showSarge}
        onClose={() => setShowSarge(false)}
        title="Sarge — roadmap decomposer"
        subtitle="Turns roadmap phases into cards and writes the new card id back into the phase as jobid."
      >
        <SargePanel />
      </Modal>
    </>
  );
}

/* ------------------------------------------------------------- card panel */

function CardPanel({
  card,
  columns,
  onClose,
  onSaved,
}: {
  card: Card;
  columns: Column[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // The board listing omits bodies, so pull this one card in full. The effect
  // seeds the textarea once the read lands — never during render.
  const body = useAsync(() => fetchCardBody(card.id), [card.id]);

  useEffect(() => {
    if (body.data) setContent(body.data.content);
  }, [body.data]);

  const loadingBody = body.loading;
  const bodyNote = body.data
    ? body.data.readable
      ? body.data.content
        ? null
        : 'This card has an empty body on the door.'
      : 'Could not read the card body — the door is unreachable. The save button is disabled so a write cannot overwrite a body you never saw.'
    : null;

  const save = async () => {
    setSaving(true);
    setErr(null);
    try {
      await updateCardContent(card.id, content);
      onSaved();
    } catch (error) {
      setErr(error instanceof Error ? error.message : 'Save failed.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={card.title}
      subtitle={`${card.status}${card.assignee ? ` · ${card.assignee}` : ' · unclaimed'}`}
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={save}
            disabled={saving || loadingBody || !body.data?.readable}
          >
            {saving ? 'Saving…' : 'Save body'}
          </button>
        </>
      }
    >
      <div className="stack">
        <div className="flex" style={{ flexWrap: 'wrap', gap: 5 }}>
          <Chip title="Task id">{card.id.slice(0, 8)}</Chip>
          {card.tags.map((t) => (
            <Chip key={t}>{t}</Chip>
          ))}
          {card.updateReason ? <Chip tone="amber">{card.updateReason}</Chip> : null}
        </div>

        {err ? <Notice tone="error">{err}</Notice> : null}
        {bodyNote ? <Notice>{bodyNote}</Notice> : null}

        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="card-body">Body</label>
          {loadingBody ? (
            <LoadingState rows={2} label="Reading card body" />
          ) : (
            <textarea
              id="card-body"
              className="textarea"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="The door stores this as the card body. Nothing is invented: an empty box means an empty body."
              rows={8}
            />
          )}
          <span className="field-hint">
            PUT <span className="mono">/api/tasks/{card.id.slice(0, 8)}…</span> — the door is the only
            writer, so this saves straight to <span className="mono">kanban_3.db</span>.
          </span>
        </div>

        <div>
          <div className="stat-label" style={{ marginBottom: 4 }}>
            Column
          </div>
          <div className="flex" style={{ flexWrap: 'wrap' }}>
            {columns.map((c) => (
              <button
                key={c.id}
                type="button"
                className={`btn btn-sm${c.name === card.status ? ' btn-primary' : ''}`}
                onClick={async () => {
                  try {
                    await moveCard({
                      taskId: card.id,
                      targetColumnId: c.id,
                      reason: 'moved from card panel',
                    });
                    onSaved();
                  } catch (error) {
                    setErr(error instanceof Error ? error.message : 'Move failed.');
                  }
                }}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>

        <div className="spread">
          <span className="muted mono" style={{ fontSize: 10.5 }}>
            created {shortDate(card.createdAt)} · updated {shortDate(card.updatedAt)}
          </span>
          <button
            type="button"
            className="btn btn-sm btn-danger"
            onClick={async () => {
              if (!window.confirm(`Delete "${card.title}"? This is not undoable.`)) return;
              try {
                await deleteCard(card.id);
                onSaved();
              } catch (error) {
                setErr(error instanceof Error ? error.message : 'Delete failed.');
              }
            }}
          >
            <IconTrash size={12} /> Delete
          </button>
        </div>
      </div>
    </Modal>
  );
}

/* ---------------------------------------------------------------- new card */

function NewCardForm({
  board,
  column,
  onDone,
  onCancel,
}: {
  board: Board;
  column: Column | null;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [assignee, setAssignee] = useState('');
  const [tags, setTags] = useState('');
  const [columnId, setColumnId] = useState(column?.id ?? board.columns[0]?.id ?? '');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    if (!title.trim()) return;
    setSaving(true);
    setErr(null);
    try {
      await createCard({
        boardId: board.id,
        boardName: board.name,
        columnId: columnId || undefined,
        title: title.trim(),
        content,
        assignee: assignee.trim(),
        tags: tags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      });
      onDone();
    } catch (error) {
      setErr(error instanceof Error ? error.message : 'The door refused the card.');
      setSaving(false);
    }
  };

  return (
    <>
      {err ? (
        <div style={{ marginBottom: 12 }}>
          <Notice tone="error">{err}</Notice>
        </div>
      ) : null}
      <div className="field">
        <label htmlFor="nc-title">Title</label>
        <input
          id="nc-title"
          className="input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void submit();
          }}
          placeholder="What needs doing"
          autoFocus
        />
      </div>
      <div className="field">
        <label htmlFor="nc-body">Body</label>
        <textarea
          id="nc-body"
          className="textarea"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
        />
      </div>
      <div className="field">
        <label htmlFor="nc-col">Column</label>
        <select
          id="nc-col"
          className="select"
          value={columnId}
          onChange={(e) => setColumnId(e.target.value)}
        >
          {board.columns.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="nc-assignee">Assignee</label>
        <input
          id="nc-assignee"
          className="input"
          value={assignee}
          onChange={(e) => setAssignee(e.target.value)}
          placeholder="Leave blank to keep it claimable"
        />
      </div>
      <div className="field" style={{ marginBottom: 0 }}>
        <label htmlFor="nc-tags">Tags</label>
        <input
          id="nc-tags"
          className="input"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="comma, separated"
        />
      </div>
      <div className="modal-actions">
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={submit}
          disabled={saving || !title.trim()}
        >
          {saving ? 'Filing…' : 'File card'}
        </button>
      </div>
    </>
  );
}

function NewBoardForm({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  return (
    <>
      {err ? (
        <div style={{ marginBottom: 12 }}>
          <Notice tone="error">{err}</Notice>
        </div>
      ) : null}
      <div className="field">
        <label htmlFor="nb-name">Board name</label>
        <input
          id="nb-name"
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Fleet HQ"
          autoFocus
        />
        <span className="field-hint">
          Names are how the door is addressed — ids are resolved per call.
        </span>
      </div>
      <div className="field" style={{ marginBottom: 0 }}>
        <label htmlFor="nb-goal">Goal</label>
        <input
          id="nb-goal"
          className="input"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="What this board tracks"
        />
      </div>
      <div className="modal-actions">
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
        <button
          type="button"
          className="btn btn-primary"
          disabled={saving || !name.trim()}
          onClick={async () => {
            setSaving(true);
            setErr(null);
            try {
              await createBoard({ name: name.trim(), goal: goal.trim() });
              onDone();
            } catch (error) {
              setErr(error instanceof Error ? error.message : 'The door refused the board.');
              setSaving(false);
            }
          }}
        >
          {saving ? 'Creating…' : 'Create board'}
        </button>
      </div>
    </>
  );
}

/* -------------------------------------------------------------- sarge panel */

function SargePanel() {
  const [probe, setProbe] = useState<{ ok: boolean; detail: string; latencyMs: number } | null>(
    null,
  );
  const [probing, setProbing] = useState(false);

  const totals = useMemo(() => {
    const usable = roadmaps.filter((r) => (r.phases ?? 0) > 0);
    const phases = usable.reduce((n, r) => n + (r.phases ?? 0), 0);
    const decomposed = usable.reduce(
      (n, r) => n + (r.rows ?? []).filter((p) => Boolean(p.jobid)).length,
      0,
    );
    return { files: usable.length, phases, decomposed };
  }, []);

  const eligible = useMemo(
    () =>
      roadmaps
        .filter((r) => (r.phases ?? 0) > 0)
        .flatMap((r) =>
          (r.rows ?? [])
            .filter((p) => !p.jobid && !['completed', 'done', 'blocked'].includes(p.status))
            .map((p) => ({ ...p, file: r.file })),
        )
        .slice(0, 12),
    [],
  );

  return (
    <div className="stack">
      <Notice>
        Sarge creates a card per roadmap phase and writes the card id back into that phase as{' '}
        <span className="mono">jobid</span>. The <span className="mono">jobid</span> is what makes him
        safe to run on a loop: a phase that already carries one is skipped, so a second pass cannot
        duplicate the board.
      </Notice>

      <div className="stat-row">
        <Stat label="Roadmaps" value={totals.files} hint="with phases" />
        <Stat label="Phases" value={totals.phases} hint="across those files" />
        <Stat label="Decomposed" value={totals.decomposed} hint="carrying a jobid" />
        <Stat
          label="Remaining"
          value={Math.max(0, totals.phases - totals.decomposed)}
          hint="without a card yet"
        />
      </div>

      <div className="notice" data-tone="warn">
        <IconWarn className="notice-icon" size={16} />
        <div>
          <strong>Sarge has never been activated on this host.</strong> His watermark file{' '}
          <span className="mono">/root/.mem20agentz/sarge.json</span> was absent at capture, so every
          roadmap predates him and no phase carries a card yet. Running{' '}
          <span className="mono">mem20-sarge serve</span> would create that watermark and start
          decomposing from it — a write, so it is not done from the browser.
        </div>
      </div>

      <div>
        <div className="stat-label" style={{ marginBottom: 6 }}>
          Next phases he would card
        </div>
        {eligible.length === 0 ? (
          <EmptyState title="Nothing eligible" icon={<IconCheck size={20} />}>
            Every phase is either done, blocked, or already carries a jobid.
          </EmptyState>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Phase</th>
                <th>Status</th>
                <th>Roadmap</th>
              </tr>
            </thead>
            <tbody>
              {eligible.map((p) => (
                <tr key={`${p.file}-${p.i}`}>
                  <td className="truncate" style={{ maxWidth: 260 }} title={p.title}>
                    {p.title || `Phase ${p.i + 1}`}
                  </td>
                  <td>
                    <Chip>{p.status || 'planned'}</Chip>
                  </td>
                  <td className="mono" style={{ fontSize: 11 }}>
                    {p.file}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="spread">
        <span className="muted" style={{ fontSize: 11.5 }}>
          Commands: <span className="mono">mem20-sarge scan</span>, then{' '}
          <span className="mono">mem20-sarge serve --board "Fleet HQ"</span>.
        </span>
        <button
          type="button"
          className="btn btn-sm"
          disabled={probing}
          onClick={async () => {
            setProbing(true);
            setProbe(await probeDoor());
            setProbing(false);
          }}
        >
          {probing ? 'Probing…' : 'Check door'}
        </button>
      </div>

      {probe ? (
        <Notice tone={probe.ok ? 'ok' : 'error'}>
          {probe.ok ? 'Door is up' : 'Door is down'} — {probe.detail} ({probe.latencyMs}ms).{' '}
          {probe.ok ? null : 'Sarge cannot file a card until this answers.'}
        </Notice>
      ) : null}
    </div>
  );
}
