/* Kanban — the real surface.
 *
 * Contract, read out of mem20kanbanz/mem20kanbanz/door.py:
 *   GET  /api/boards                      -> [{id,name,...}]
 *   GET  /api/boards/:id                  -> {board:{...}, columns:[{id,name,position,wipLimit,isDoneColumn,tasks:[...]}]}
 *   POST /api/tasks/:id/move              -> {targetColumnId, reason}
 *   PATCH/api/tasks/:id/metadata          -> {patch:{...}}, a key set to null is REMOVED
 *   POST /api/boards/:id/done-column      -> {column}
 *   POST /api/tasks                       -> {boardId,title,content,metadata,columnId?}
 *   DELETE /api/tasks/:id                 -> {success, taskId}
 *
 * WIP: the door enforces it and answers HTTP 422 when a column is full. That
 * 422 is surfaced as CapacityFull and rendered against the column that
 * refused the move — never swallowed, never retried silently.
 *
 * Done is a FLAG on the column (isDoneColumn), not a column name. Boards in
 * this estate disagree on naming (dev/in_progress, Fleet HQ/in progress), so
 * nothing here ever compares a column name to "done".
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  CapacityFull,
  DoorUnreachable,
  DoorNotFound,
  door,
  type DoorBoard,
  type DoorCard,
  type DoorColumn,
} from '../lib/api';
import { Empty, Notice, Panel, Pill, Stat } from '../components/ui';

type Props = { doorUp: boolean | null; onProbe: () => Promise<boolean> };

type Status = { kind: 'idle' | 'ok' | 'err' | 'busy'; msg: string };

const short = (id: string) => (id.length > 10 ? `${id.slice(0, 8)}` : id);
const errMsg = (e: unknown) => (e instanceof Error ? e.message : String(e));

export default function Kanban({ doorUp, onProbe }: Props) {
  const [boards, setBoards] = useState<Array<{ id: string; name: string }> | null>(null);
  const [boardName, setBoardName] = useState<string>('');
  const [board, setBoard] = useState<DoorBoard | null>(null);
  const [loadErr, setLoadErr] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<Status>({ kind: 'idle', msg: '' });

  // view controls
  const [query, setQuery] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('');
  const [swimlanes, setSwimlanes] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // panels
  const [card, setCard] = useState<DoorCard | null>(null);
  const [sargeOpen, setSargeOpen] = useState(false);
  const [boardCtlOpen, setBoardCtlOpen] = useState(false);

  // drag
  const [dragging, setDragging] = useState<string>('');
  const [dropLane, setDropLane] = useState<string>('');

  const loadBoards = useCallback(async () => {
    setLoadErr('');
    try {
      const list = await door.boards();
      setBoards(list);
      if (list.length && !list.some((b) => b.name === boardName)) {
        setBoardName(list[0].name);
      }
      return list;
    } catch (e) {
      setBoards(null);
      setLoadErr(errMsg(e));
      return [];
    }
  }, [boardName]);

  const loadBoard = useCallback(async (name: string) => {
    if (!name) return;
    setLoadErr('');
    try {
      const b = await door.board(name);
      setBoard(b);
      setSelected(new Set());
    } catch (e) {
      setBoard(null);
      setLoadErr(errMsg(e));
    }
  }, []);

  useEffect(() => {
    loadBoards();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (boardName) loadBoard(boardName);
  }, [boardName, loadBoard]);

  const refresh = async () => {
    setBusy(true);
    await onProbe();
    await loadBoards();
    await loadBoard(boardName);
    setBusy(false);
  };

  /* ------------------------------------------------------------- filtering */

  const allTags = useMemo(() => {
    const s = new Set<string>();
    (board?.cards || []).forEach((c) => c.tags.forEach((t) => s.add(t)));
    return [...s].sort();
  }, [board]);

  const allAssignees = useMemo(() => {
    const s = new Set<string>();
    (board?.cards || []).forEach((c) => c.assignee && s.add(c.assignee));
    return [...s].sort();
  }, [board]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (board?.cards || []).filter((c) => {
      if (q && !(c.title.toLowerCase().includes(q) || c.id.toLowerCase().includes(q))) return false;
      if (tagFilter && !c.tags.includes(tagFilter)) return false;
      if (assigneeFilter === '__none__' && c.assignee) return false;
      if (assigneeFilter && assigneeFilter !== '__none__' && c.assignee !== assigneeFilter) return false;
      return true;
    });
  }, [board, query, tagFilter, assigneeFilter]);

  /* ---------------------------------------------------------------- writes */

  async function moveTo(colId: string, colName: string, taskId: string) {
    const target = board?.columns.find((c) => c.id === colId);
    // Pre-flight WIP check so an over-capacity drop reads as a live refusal
    // locally too. The door's 422 remains the authority — this never replaces it.
    const inCol = (board?.cards || []).filter((c) => c.status === colName && c.id !== taskId).length;
    if (target && target.wipLimit > 0 && inCol >= target.wipLimit) {
      setStatus({
        kind: 'err',
        msg: `CapacityFull — "${colName}" is at its WIP limit (${inCol}/${target.wipLimit}). Move or finish a card first.`,
      });
      setDropLane('');
      return;
    }
    setBusy(true);
    try {
      await door.moveToColumnId(taskId, colId, `moved via mem20 web shell`);
      setStatus({ kind: 'ok', msg: `moved ${short(taskId)} → ${colName}` });
      await loadBoard(boardName);
    } catch (e) {
      if (e instanceof CapacityFull) {
        setStatus({ kind: 'err', msg: `HTTP 422 CapacityFull — the door refused the move: ${e.detail || 'column at capacity'}` });
      } else {
        setStatus({ kind: 'err', msg: `move failed — ${errMsg(e)}` });
      }
    } finally {
      setBusy(false);
      setDragging('');
      setDropLane('');
    }
  }

  async function bulkMove(colId: string, colName: string) {
    if (!selected.size) return;
    const ids = [...selected];
    let ok = 0;
    const failures: string[] = [];
    for (const id of ids) {
      try {
        await door.moveToColumnId(id, colId, 'bulk move via mem20 web shell');
        ok += 1;
      } catch (e) {
        failures.push(e instanceof CapacityFull ? 'capacity' : errMsg(e));
      }
    }
    setStatus({
      kind: failures.length ? 'err' : 'ok',
      msg: `bulk move → ${colName}: ${ok}/${ids.length} moved${failures.length ? ` · refused: ${[...new Set(failures)].join(', ')}` : ''}`,
    });
    await loadBoard(boardName);
  }

  async function bulkDelete() {
    if (!selected.size) return;
    if (!window.confirm(`Delete ${selected.size} card(s)? This is not undoable.`)) return;
    let ok = 0;
    for (const id of [...selected]) {
      try {
        await door.deleteCard(id);
        ok += 1;
      } catch {
        /* counted by omission */
      }
    }
    setStatus({ kind: ok === selected.size ? 'ok' : 'err', msg: `deleted ${ok}/${selected.size}` });
    await loadBoard(boardName);
  }

  async function bulkRelease() {
    let ok = 0;
    for (const id of [...selected]) {
      try {
        await door.patchMetadata(id, { assignee: null });
        ok += 1;
      } catch {
        /* ignore */
      }
    }
    setStatus({ kind: 'ok', msg: `released ${ok}/${selected.size} — assignee removed via metadata merge` });
    await loadBoard(boardName);
  }

  async function openCard(id: string) {
    try {
      setCard(await door.card(id));
      setStatus({ kind: 'idle', msg: '' });
    } catch (e) {
      if (e instanceof DoorNotFound) setStatus({ kind: 'err', msg: `no such card: ${id}` });
      else setStatus({ kind: 'err', msg: errMsg(e) });
    }
  }

  /* -------------------------------------------------------------- rendering */

  const totals = useMemo(() => {
    const cards = board?.cards || [];
    const done = cards.filter((c) => c.isDone).length;
    const claimed = cards.filter((c) => c.assignee && !c.isDone).length;
    const atCap = (board?.columns || []).filter(
      (c) => c.wipLimit > 0 && cards.filter((k) => k.status === c.name).length >= c.wipLimit,
    ).length;
    return { total: cards.length, done, open: cards.length - done, claimed, atCap };
  }, [board]);

  /* ---------------------------------------------------------- unreachable */

  if (loadErr && !board) {
    const unreachable = loadErr.includes('unreachable') || doorUp === false;
    return (
      <div className="page">
        <div style={{ display: 'grid', gap: 16 }}>
          <Notice
            tone="bad"
            title={
              <>
                Kanban door is <strong>unreachable</strong> — {door.base()}
              </>
            }
          >
            {unreachable
              ? 'The shell will not draw an empty board for a door it cannot reach. An empty board would read as "no work", which is a different fact from "no answer". Start the door (systemctl status mem20-kanban), or point this shell at one from Connection.'
              : `Load failed: ${loadErr}`}
          </Notice>
          <div className="grid g3">
            <Panel title="What the shell tried">
              <dl className="kv">
                <dt>GET</dt>
                <dd>{door.base()}/api/boards</dd>
                <dt>timeout</dt>
                <dd>8000ms</dd>
                <dt>result</dt>
                <dd style={{ color: 'var(--red-0)' }}>{loadErr || 'connection refused'}</dd>
              </dl>
            </Panel>
            <Panel title="The one store">
              <dl className="kv">
                <dt>store</dt>
                <dd>/opt/mem20/kanban/kanban_3.db</dd>
                <dt>writer</dt>
                <dd>mem20-kanban.service only</dd>
                <dt>note</dt>
                <dd>this UI never opens sqlite</dd>
              </dl>
            </Panel>
            <Panel title="Next">
              <div style={{ display: 'grid', gap: 9 }}>
                <button className="btn primary" onClick={refresh} disabled={busy}>
                  {busy ? <span className="spin" /> : null} retry door
                </button>
                <button className="btn" onClick={() => (window.location.hash = 'door')}>
                  open Door Sync
                </button>
              </div>
            </Panel>
          </div>
        </div>
      </div>
    );
  }

  const lanes: DoorColumn[] = board?.columns || [];
  const laneCards = (name: string) => visible.filter((c) => c.status === name);

  return (
    <div className="page wide">
      {/* board bar */}
      <div className="board-bar">
        <select className="select" value={boardName} onChange={(e) => setBoardName(e.target.value)}>
          {(boards || []).map((b) => (
            <option key={b.id} value={b.name}>
              {b.name}
            </option>
          ))}
        </select>
        <input
          className="input"
          style={{ width: 220 }}
          placeholder="filter title or id…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select className="select" value={tagFilter} onChange={(e) => setTagFilter(e.target.value)}>
          <option value="">all tags</option>
          {allTags.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select className="select" value={assigneeFilter} onChange={(e) => setAssigneeFilter(e.target.value)}>
          <option value="">all assignees</option>
          <option value="__none__">unclaimed</option>
          {allAssignees.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <button
          className={`btn ${swimlanes ? 'primary' : ''}`}
          onClick={() => setSwimlanes((v) => !v)}
          title="group cards by assignee"
        >
          swimlanes
        </button>
        <span className="spacer" />
        <button className="btn" onClick={() => setBoardCtlOpen((v) => !v)}>
          board control
        </button>
        <button className="btn" onClick={() => setSargeOpen((v) => !v)}>
          Sarge
        </button>
        <button className="btn" onClick={refresh} disabled={busy}>
          {busy ? <span className="spin" /> : null} refresh
        </button>
      </div>

      {/* stats */}
      <div className="grid g4" style={{ marginBottom: 14 }}>
        <Stat k="cards" v={totals.total} />
        <Stat k="open" v={totals.open} sub={`/ ${totals.total}`} />
        <Stat k="claimed" v={totals.claimed} />
        <Stat k="columns at WIP" v={totals.atCap} sub={`/ ${lanes.length}`} />
      </div>

      {status.msg && (
        <div style={{ marginBottom: 12 }}>
          <Notice tone={status.kind === 'err' ? 'bad' : 'ok'} title={status.msg} />
        </div>
      )}

      {loadErr && board && (
        <div style={{ marginBottom: 12 }}>
          <Notice tone="warn" title={`last read failed: ${loadErr}`}>
            Showing the board as of the previous successful read.
          </Notice>
        </div>
      )}

      {/* bulk bar */}
      {selected.size > 0 && (
        <div className="bulkbar">
          <strong style={{ color: 'var(--ink-0)' }}>{selected.size} selected</strong>
          <span style={{ color: 'var(--ink-3)' }}>·</span>
          <button className="btn sm" onClick={bulkRelease}>
            release (drop assignee)
          </button>
          <select
            className="select"
            style={{ height: 26, fontSize: 12 }}
            value=""
            onChange={(e) => {
              const col = lanes.find((c) => c.id === e.target.value);
              if (col) bulkMove(col.id, col.name);
            }}
          >
            <option value="">move to…</option>
            {lanes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
                {c.wipLimit > 0 ? ` (wip ${c.wipLimit})` : ''}
              </option>
            ))}
          </select>
          <button className="btn sm" onClick={bulkDelete}>
            delete
          </button>
          <span className="spacer" />
          <button className="btn ghost sm" onClick={() => setSelected(new Set())}>
            clear
          </button>
        </div>
      )}

      {/* panels */}
      {sargeOpen && <SargePanel boardName={boardName} lanes={lanes} onDone={refresh} />}
      {boardCtlOpen && board && (
        <BoardControl board={board} onDone={refresh} onStatus={setStatus} />
      )}

      {/* board */}
      {swimlanes ? (
        <Swimlanes
          board={board!}
          cards={visible}
          onOpen={openCard}
          selected={selected}
          toggle={(id) =>
            setSelected((prev) => {
              const n = new Set(prev);
              n.has(id) ? n.delete(id) : n.add(id);
              return n;
            })
          }
        />
      ) : (
        <div className="lanes">
          {lanes.map((col) => {
            const cards = laneCards(col.name);
            const total = (board?.cards || []).filter((c) => c.status === col.name).length;
            const over = col.wipLimit > 0 && total >= col.wipLimit;
            return (
              <div
                key={col.id}
                className={`lane ${dropLane === col.id ? 'drop' : ''} ${over ? 'at-cap' : ''} ${col.isDoneColumn ? 'is-done' : ''}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDropLane(col.id);
                }}
                onDragLeave={() => setDropLane((v) => (v === col.id ? '' : v))}
                onDrop={(e) => {
                  e.preventDefault();
                  const id = e.dataTransfer.getData('text/plain') || dragging;
                  if (id) moveTo(col.id, col.name, id);
                }}
              >
                <div className="lane-head">
                  <div className="lane-name">
                    <span className="nm">{col.name}</span>
                    {col.isDoneColumn && (
                      <Pill tone="green" mono>
                        done
                      </Pill>
                    )}
                    {col.isLanding && (
                      <Pill tone="violet" mono>
                        landing
                      </Pill>
                    )}
                  </div>
                  <span className="spacer" />
                  <span className={`count ${over ? 'over' : ''}`}>
                    {total}
                    {col.wipLimit > 0 ? `/${col.wipLimit}` : ''}
                  </span>
                </div>

                <div className="lane-body">
                  {cards.length === 0 && <div className="empty">no cards</div>}
                  {cards.map((c) => (
                    <div
                      key={c.id}
                      className={`card ${selected.has(c.id) ? 'sel' : ''} ${dragging === c.id ? 'dragging' : ''} ${c.isDone ? 'done-card' : ''} ${c.assignee && !c.isDone ? 'claimed' : ''}`}
                      draggable
                      onDragStart={(e) => {
                        e.dataTransfer.setData('text/plain', c.id);
                        e.dataTransfer.effectAllowed = 'move';
                        setDragging(c.id);
                      }}
                      onDragEnd={() => {
                        setDragging('');
                        setDropLane('');
                      }}
                      onClick={(e) => {
                        if (e.metaKey || e.ctrlKey) {
                          setSelected((prev) => {
                            const n = new Set(prev);
                            n.has(c.id) ? n.delete(c.id) : n.add(c.id);
                            return n;
                          });
                        } else {
                          openCard(c.id);
                        }
                      }}
                      title={`${c.id} — click to open · ⌘/ctrl-click to select`}
                    >
                      <div className="card-title">{c.title || '(untitled)'}</div>
                      <div className="card-meta">
                        <span className="card-id">{short(c.id)}</span>
                        {c.assignee && <span className="assignee">{c.assignee}</span>}
                        {c.tags.slice(0, 3).map((t) => (
                          <span key={t} className="tag">
                            {t}
                          </span>
                        ))}
                        {c.tags.length > 3 && <span className="tag">+{c.tags.length - 3}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {card && <CardDrawer card={card} board={board!} onClose={() => setCard(null)} onMoved={refresh} />}
    </div>
  );
}

/* ------------------------------------------------------------- swimlanes */

function Swimlanes({
  board,
  cards,
  onOpen,
  selected,
  toggle,
}: {
  board: DoorBoard;
  cards: DoorCard[];
  onOpen: (id: string) => void;
  selected: Set<string>;
  toggle: (id: string) => void;
}) {
  const groups = useMemo(() => {
    const m = new Map<string, DoorCard[]>();
    cards.forEach((c) => {
      const k = c.assignee || '— unclaimed —';
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(c);
    });
    return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [cards]);

  return (
    <div style={{ display: 'grid', gap: 18 }}>
      {groups.map(([who, list]) => (
        <div key={who}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 8 }}>
            <span style={{ fontWeight: 600, color: 'var(--ink-0)', fontSize: 13 }}>{who}</span>
            <span className="count">{list.length}</span>
          </div>
          <div className="lanes" style={{ minHeight: 0 }}>
            {board.columns.map((col) => {
              const inLane = list.filter((c) => c.status === col.name);
              return (
                <div key={col.id} className={`lane ${col.isDoneColumn ? 'is-done' : ''}`} style={{ minHeight: 74 }}>
                  <div className="lane-head">
                    <div className="lane-name">
                      <span className="nm">{col.name}</span>
                    </div>
                    <span className="spacer" />
                    <span className="count">{inLane.length}</span>
                  </div>
                  <div className="lane-body">
                    {inLane.map((c) => (
                      <div
                        key={c.id}
                        className={`card ${selected.has(c.id) ? 'sel' : ''} ${c.isDone ? 'done-card' : ''}`}
                        onClick={(e) => {
                          if (e.metaKey || e.ctrlKey) toggle(c.id);
                          else onOpen(c.id);
                        }}
                      >
                        <div className="card-title">{c.title}</div>
                        <div className="card-meta">
                          <span className="card-id">{short(c.id)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ----------------------------------------------------------- card drawer */

function CardDrawer({
  card,
  board,
  onClose,
  onMoved,
}: {
  card: DoorCard;
  board: DoorBoard;
  onClose: () => void;
  onMoved: () => void;
}) {
  const [err, setErr] = useState('');
  const [note, setNote] = useState('');
  const [assignee, setAssignee] = useState(card.assignee);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,7,14,0.72)',
        backdropFilter: 'blur(3px)',
        display: 'grid',
        placeItems: 'center',
        zIndex: 50,
        padding: 24,
      }}
      onClick={onClose}
    >
      <div
        className="panel"
        style={{ width: 'min(720px, 100%)', maxHeight: '86vh', overflow: 'auto', boxShadow: 'var(--shadow-3)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-head">
          <h3 style={{ fontSize: 14 }}>{card.title || '(untitled)'}</h3>
          <span className="spacer" />
          {card.isDone ? (
            <Pill tone="green" mono dot>
              done
            </Pill>
          ) : (
            <Pill tone="cyan" mono>
              {card.status}
            </Pill>
          )}
          <button className="btn ghost sm" onClick={onClose}>
            close
          </button>
        </div>
        <div className="panel-body" style={{ display: 'grid', gap: 16 }}>
          <dl className="kv">
            <dt>id</dt>
            <dd>{card.id}</dd>
            <dt>column</dt>
            <dd>{card.status}</dd>
            <dt>assignee</dt>
            <dd>{card.assignee || '—'}</dd>
            <dt>tags</dt>
            <dd>{card.tags.length ? card.tags.join(', ') : '—'}</dd>
            <dt>isDoneColumn</dt>
            <dd>{String(card.isDone)}</dd>
          </dl>

          {card.content && (
            <div>
              <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)', marginBottom: 6 }}>
                content
              </div>
              <pre
                style={{
                  margin: 0,
                  padding: 12,
                  background: 'var(--bg-0)',
                  border: '1px solid var(--line-1)',
                  borderRadius: 8,
                  color: 'var(--ink-1)',
                  fontFamily: 'var(--mono)',
                  fontSize: 11.5,
                  whiteSpace: 'pre-wrap',
                  maxHeight: 240,
                  overflow: 'auto',
                }}
              >
                {card.content}
              </pre>
            </div>
          )}

          <div style={{ display: 'grid', gap: 8 }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)' }}>
              move
            </div>
            <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
              {board.columns
                .filter((c) => c.name !== card.status)
                .map((c) => (
                  <button
                    key={c.id}
                    className="btn sm"
                    onClick={async () => {
                      setErr('');
                      if (!note.trim()) {
                        setErr('a move needs a reason — the door records update_reason on every move');
                        return;
                      }
                      try {
                        await door.moveToColumnId(card.id, c.id, note.trim());
                        onMoved();
                        onClose();
                      } catch (e) {
                        setErr(e instanceof CapacityFull ? `HTTP 422 CapacityFull — ${e.detail}` : errMsg(e));
                      }
                    }}
                  >
                    → {c.name}
                    {c.wipLimit > 0 ? <span className="tag">wip {c.wipLimit}</span> : null}
                  </button>
                ))}
            </div>
            <input
              className="input"
              placeholder="reason for the move (recorded on the card)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gap: 8 }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)' }}>
              assignee — merged into metadata, never replaced
            </div>
            <div style={{ display: 'flex', gap: 7 }}>
              <input
                className="input"
                style={{ width: 200 }}
                value={assignee}
                onChange={(e) => setAssignee(e.target.value)}
                placeholder="agent name"
              />
              <button
                className="btn sm"
                onClick={async () => {
                  try {
                    await door.patchMetadata(card.id, { assignee });
                    onMoved();
                    onClose();
                  } catch (e) {
                    setErr(errMsg(e));
                  }
                }}
              >
                claim
              </button>
              <button
                className="btn sm"
                onClick={async () => {
                  try {
                    await door.patchMetadata(card.id, { assignee: null });
                    onMoved();
                    onClose();
                  } catch (e) {
                    setErr(errMsg(e));
                  }
                }}
              >
                release (null)
              </button>
            </div>
          </div>

          {err && <Notice tone="bad" title={err} />}
        </div>
      </div>
    </div>
  );
}

/* --------------------------------------------------------- Sarge panel */

function SargePanel({
  boardName,
  lanes,
  onDone,
}: {
  boardName: string;
  lanes: DoorColumn[];
  onDone: () => Promise<void> | void;
}) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [assignee, setAssignee] = useState('');
  const [tags, setTags] = useState('');
  const [column, setColumn] = useState('');
  const [err, setErr] = useState('');
  const [ok, setOk] = useState('');

  const landing = lanes.find((c) => c.isLanding) || lanes[0];

  return (
    <div style={{ marginBottom: 16 }}>
      <Panel
        title={
          <>
            Sarge <span style={{ color: 'var(--ink-3)', fontWeight: 400 }}>— decomposer, writes a real card back to the door</span>
          </>
        }
        right={<Pill tone="violet" mono>mem20-sarge</Pill>}
      >
        <div className="lede" style={{ marginBottom: 12 }}>
          Sarge turns a roadmap phase into a card and writes the card id back as <span className="mono">jobid</span>, which is
          what stops the same phase being decomposed twice on the next pass. This panel creates the card through the same REST
          door every other tool uses — it does not shell out to the roadmap files, so a card made here carries no{' '}
          <span className="mono">jobid</span> until Sarge sees the phase.
        </div>
        <div style={{ display: 'grid', gap: 9 }}>
          <input className="input" placeholder="card title (required)" value={title} onChange={(e) => setTitle(e.target.value)} />
          <textarea
            className="input"
            style={{ height: 74, paddingTop: 8, resize: 'vertical', fontFamily: 'var(--mono)', fontSize: 11.5 }}
            placeholder="content / brief"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input className="input" placeholder="assignee" value={assignee} onChange={(e) => setAssignee(e.target.value)} style={{ width: 160 }} />
            <input className="input" placeholder="tags, comma separated" value={tags} onChange={(e) => setTags(e.target.value)} style={{ width: 220 }} />
            <select className="select" value={column} onChange={(e) => setColumn(e.target.value)}>
              <option value="">landing column ({landing?.name || '—'})</option>
              {lanes.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
            <button
              className="btn primary"
              disabled={!title.trim()}
              onClick={async () => {
                setErr('');
                setOk('');
                try {
                  await door.addCard(boardName, title.trim(), {
                    content,
                    assignee: assignee.trim(),
                    tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
                    column: column || undefined,
                  });
                  setOk(`card created on "${boardName}"`);
                  setTitle('');
                  setContent('');
                  setTags('');
                  await onDone();
                } catch (e) {
                  setErr(e instanceof CapacityFull ? `HTTP 422 CapacityFull — ${e.detail}` : errMsg(e));
                }
              }}
            >
              create card
            </button>
          </div>
          {err && <Notice tone="bad" title={err} />}
          {ok && <Notice tone="ok" title={ok} />}
        </div>
      </Panel>
    </div>
  );
}

/* ----------------------------------------------------- board control panel */

function BoardControl({
  board,
  onDone,
  onStatus,
}: {
  board: DoorBoard;
  onDone: () => Promise<void> | void;
  onStatus: (s: Status) => void;
}) {
  const doneCols = board.columns.filter((c) => c.isDoneColumn);
  const [pick, setPick] = useState(doneCols[0]?.name || '');
  const [err, setErr] = useState('');

  return (
    <div style={{ marginBottom: 16 }}>
      <Panel
        title="Board control"
        right={<Pill mono>{board.id}</Pill>}
      >
        <div className="grid g2">
          <div>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)', marginBottom: 7 }}>
              done column — exactly one column carries the flag
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <select className="select" value={pick} onChange={(e) => setPick(e.target.value)}>
                {board.columns.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
              <button
                className="btn"
                disabled={!pick}
                onClick={async () => {
                  setErr('');
                  try {
                    const ok = await door.setDoneColumn(board.name, pick);
                    if (!ok) throw new Error('door answered without success — did the board have that column?');
                    onStatus({ kind: 'ok', msg: `done column on "${board.name}" is now "${pick}"` });
                    await onDone();
                  } catch (e) {
                    setErr(errMsg(e));
                  }
                }}
              >
                set done column
              </button>
            </div>
            <div style={{ marginTop: 9, fontSize: 12, color: 'var(--ink-3)' }}>
              Current: {doneCols.length ? doneCols.map((c) => c.name).join(', ') : 'none — nothing can be completed'}
            </div>
            {err && <div style={{ marginTop: 9 }}><Notice tone="bad" title={err} /></div>}
          </div>

          <div>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)', marginBottom: 7 }}>
              columns &amp; wip limits
            </div>
            <table className="tbl">
              <thead>
                <tr>
                  <th>name</th>
                  <th>pos</th>
                  <th>wip</th>
                  <th>done</th>
                  <th>landing</th>
                  <th>id</th>
                </tr>
              </thead>
              <tbody>
                {board.columns.map((c) => (
                  <tr key={c.id}>
                    <td>{c.name}</td>
                    <td className="mono">{c.position}</td>
                    <td className="mono">{c.wipLimit || '—'}</td>
                    <td>{c.isDoneColumn ? <Pill tone="green" mono>yes</Pill> : '—'}</td>
                    <td>{c.isLanding ? <Pill tone="violet" mono>yes</Pill> : '—'}</td>
                    <td className="mono">{short(c.id)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <hr className="sep" />
        <div style={{ fontSize: 12, color: 'var(--ink-2)' }}>
          <strong style={{ color: 'var(--ink-0)' }}>board goal</strong> — {board.goal || 'the door reported no goal for this board'}
        </div>
      </Panel>
    </div>
  );
}
