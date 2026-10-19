/**
 * Kanban transport — the door REST contract, plus a capture adapter.
 *
 * ── Ground truth ────────────────────────────────────────────────────────────
 * `mem20kanbanz/mem20kanbanz/door.py` is the only client the estate ships, and
 * this module mirrors it exactly:
 *
 *   GET    /api/boards                       → [{id, name, ...}]
 *   POST   /api/boards                       → {name, projectGoal, columns, landingColumnPosition}
 *   DELETE /api/boards/{id}                  → {success: true}
 *   POST   /api/boards/{id}/done-column      → {column: "<name>"}
 *   GET    /api/boards/{id}                  → {board, columns:[{...tasks}]}
 *   POST   /api/tasks                        → {boardId, title, content, metadata, columnId?}
 *   GET    /api/tasks/{id}                   → the full card, body included
 *   PUT    /api/tasks/{id}                   → {content}
 *   POST   /api/tasks/{id}/move              → {targetColumnId, reason}
 *   PATCH  /api/tasks/{id}/metadata          → {patch}
 *   DELETE /api/tasks/{id}                   → {success, taskId}
 *
 * The door's own quirks are preserved rather than papered over:
 *   • a bodyless request must carry no Content-Type — Fastify answers 400 for an
 *     empty JSON body and 415 for a form-encoded one, which is why DELETE broke
 *     twice (door.py:99-108);
 *   • a WIP overflow is 422, not a generic failure;
 *   • an unreachable door must raise, never return an empty board.
 *
 * ── Why there are two shapes ───────────────────────────────────────────────
 * The door nests tasks inside columns. `kanban_3.db` stores them flat. Both are
 * normalised here into `Board`/`Column`/`Card` so no component ever has to know
 * which one it got.
 */

import { DOOR_BASE, SNAPSHOT_META, SOURCE_MODE } from './config';
import snapshotRaw from '../data/snapshot.kanban.json';
import type {
  Board,
  Card,
  Column,
  ColumnSpec,
  KanbanSnapshot,
  Loaded,
  RawTaskRow,
} from './types';

const snapshot = snapshotRaw as unknown as KanbanSnapshot;

/* ------------------------------------------------------------------ errors */

export class DoorError extends Error {
  readonly kind: 'unreachable' | 'not-found' | 'capacity' | 'refused';
  constructor(kind: DoorError['kind'], message: string) {
    super(message);
    this.name = 'DoorError';
  }
}

/* --------------------------------------------------------------- transport */

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  payload?: unknown;
  timeoutMs?: number;
}

/** One HTTP call, with the door's content-type rules applied. */
async function doorFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', payload, timeoutMs = 8000 } = opts;
  const body = payload === undefined ? undefined : JSON.stringify(payload);

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${DOOR_BASE}${path}`, {
      method,
      signal: controller.signal,
      // Crucially: no headers at all when there is no body.
      ...(body ? { headers: { 'Content-Type': 'application/json' }, body } : {}),
    });

    const text = await res.text();
    let parsed: unknown = null;
    if (text) {
      try {
        parsed = JSON.parse(text);
      } catch {
        parsed = text;
      }
    }

    if (res.ok) return parsed as T;

    const detail =
      parsed && typeof parsed === 'object' && 'message' in parsed
        ? String((parsed as { message: unknown }).message)
        : '';

    if (res.status === 404)
      throw new DoorError('not-found', `404 ${path}${detail ? `: ${detail}` : ''}`);
    if (res.status === 422)
      throw new DoorError('capacity', `Column is at capacity${detail ? `: ${detail}` : ''}`);
    throw new DoorError(
      'refused',
      `HTTP ${res.status} ${method} ${path}${detail ? `: ${detail}` : ''}`,
    );
  } catch (err) {
    if (err instanceof DoorError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new DoorError('unreachable', `The door did not answer within ${timeoutMs}ms.`);
    }
    throw new DoorError(
      'unreachable',
      err instanceof Error ? err.message : 'The door is unreachable.',
    );
  } finally {
    window.clearTimeout(timer);
  }
}

/* ----------------------------------------------------------------- shaping */

function parseMetadata(raw: string | null | undefined): Record<string, unknown> {
  if (!raw) return {};
  if (typeof raw !== 'string') return raw as Record<string, unknown>;
  try {
    const decoded = JSON.parse(raw);
    return decoded && typeof decoded === 'object' ? decoded : {};
  } catch {
    return {};
  }
}

function asStringList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String).filter(Boolean);
  if (typeof value === 'string')
    return value
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  return [];
}

/** Build a normalised card from a flat task row plus its column context. */
function cardFromRow(row: RawTaskRow, columnName: string, isDone: boolean): Card {
  const meta = parseMetadata(row.metadata);
  return {
    id: row.id,
    title: row.title,
    content: row.content ?? '',
    status: columnName,
    assignee: typeof meta.assignee === 'string' ? meta.assignee : '',
    tags: asStringList(meta.tags),
    metadata: meta,
    position: Number(row.position) || 0,
    createdAt: row.created_at ?? null,
    updatedAt: row.updated_at ?? null,
    updateReason: row.update_reason ?? null,
    done: isDone || Boolean(meta.is_done_column),
  };
}

/** Board assembled from the door's nested detail response. */
interface DoorBoardDetail {
  board?: { id?: string; name?: string; goal?: string; landingColumnId?: string };
  columns?: {
    id: string;
    name: string;
    position?: number;
    wipLimit?: number;
    isDoneColumn?: boolean;
    isLanding?: boolean;
    tasks?: {
      id: string;
      title: string;
      content?: string;
      position?: number;
      metadata?: unknown;
      createdAt?: string;
      updatedAt?: string;
    }[];
  }[];
}

function boardFromDoor(raw: DoorBoardDetail, fallbackName: string): Board {
  const columns: Column[] = (raw.columns ?? []).map((c) => {
    const isDone = Boolean(c.isDoneColumn);
    const cards: Card[] = (c.tasks ?? []).map((t) => {
      const meta =
        typeof t.metadata === 'string'
          ? parseMetadata(t.metadata)
          : ((t.metadata as Record<string, unknown>) ?? {});
      return {
        id: t.id,
        title: t.title,
        // The door's board listing omits the body on purpose (door.py:305-312).
        content: t.content ?? '',
        status: c.name,
        assignee: typeof meta.assignee === 'string' ? meta.assignee : '',
        tags: asStringList(meta.tags),
        metadata: meta,
        position: Number(t.position) || 0,
        createdAt: t.createdAt ?? null,
        updatedAt: t.updatedAt ?? null,
        updateReason: null,
        done: isDone,
      };
    });
    return {
      id: c.id,
      name: c.name,
      position: c.position ?? 0,
      wipLimit: c.wipLimit ?? 0,
      isDone,
      isLanding: Boolean(c.isLanding),
      cards: cards.sort((a, b) => a.position - b.position),
    };
  });

  return {
    id: raw.board?.id ?? '',
    name: raw.board?.name ?? fallbackName,
    goal: raw.board?.goal ?? '',
    landingColumnId: raw.board?.landingColumnId ?? null,
    createdAt: null,
    columns: columns.sort((a, b) => a.position - b.position),
  };
}

/** Boards assembled from the captured database dump. */
export function boardsFromSnapshot(): Board[] {
  return snapshot.boards.map((b) => {
    const cols = snapshot.columns
      .filter((c) => c.board_id === b.id)
      .sort((a, b2) => a.position - b2.position);

    const columns: Column[] = cols.map((c) => {
      const isDone = Boolean(c.is_done_column);
      const cards = snapshot.tasks
        .filter((t) => t.column_id === c.id)
        .map((t) => cardFromRow(t, c.name, isDone))
        .sort((x, y) => x.position - y.position);
      return {
        id: c.id,
        name: c.name,
        position: c.position,
        wipLimit: c.wip_limit,
        isDone,
        isLanding: b.landing_column_id === c.id,
        cards,
      };
    });

    return {
      id: b.id,
      name: b.name,
      goal: b.goal,
      landingColumnId: b.landing_column_id,
      createdAt: b.created_at,
      columns,
    };
  });
}

/* --------------------------------------------------------------- read side */

/**
 * Read every board.
 *
 * Live path costs one request per board for the detail (the list endpoint has
 * no columns), exactly like `Door.board()`. On any transport failure the capture
 * is used and the envelope says why.
 */
export async function loadBoards(): Promise<Loaded<Board[]>> {
  const started = performance.now();
  try {
    const list = await doorFetch<{ id: string; name: string }[]>('/api/boards');
    if (!Array.isArray(list))
      throw new DoorError('refused', 'Door did not return a board list.');

    const boards = await Promise.all(
      list.map(async (b) => {
        const detail = await doorFetch<DoorBoardDetail>(`/api/boards/${b.id}`);
        return boardFromDoor(detail, b.name);
      }),
    );
    return {
      data: boards,
      source: 'live',
      at: new Date().toISOString(),
      latencyMs: Math.round(performance.now() - started),
    };
  } catch (err) {
    if (SOURCE_MODE === 'live') throw err;
    return {
      data: boardsFromSnapshot(),
      source: 'snapshot',
      at: SNAPSHOT_META.capturedAt,
      note:
        err instanceof DoorError
          ? `Door unreachable at ${DOOR_BASE} — showing the capture taken ${SNAPSHOT_META.capturedAt.slice(0, 10)} from ${SNAPSHOT_META.capturedFrom}.`
          : 'Live read failed — showing the capture.',
    };
  }
}

/** Health probe that never throws, for the connection strip. */
export async function probeDoor(): Promise<{ ok: boolean; detail: string; latencyMs: number }> {
  const started = performance.now();
  try {
    await doorFetch<unknown>('/api/boards', { timeoutMs: 3500 });
    return {
      ok: true,
      detail: 'Door answered /api/boards.',
      latencyMs: Math.round(performance.now() - started),
    };
  } catch (err) {
    return {
      ok: false,
      detail: err instanceof Error ? err.message : 'Unreachable.',
      latencyMs: Math.round(performance.now() - started),
    };
  }
}

/* -------------------------------------------------------------- write side */

export async function createCard(input: {
  boardId: string;
  boardName: string;
  columnId?: string;
  title: string;
  content?: string;
  assignee?: string;
  tags?: string[];
}): Promise<Card> {
  const payload: Record<string, unknown> = {
    boardId: input.boardId,
    title: input.title,
    content: input.content ?? '',
    metadata: {
      assignee: input.assignee ?? '',
      tags: [...new Set(input.tags ?? [])].sort(),
    },
  };
  if (input.columnId) payload.columnId = input.columnId;

  const res = await doorFetch<{ success?: boolean; task?: RawTaskRow }>('/api/tasks', {
    method: 'POST',
    payload,
  });
  if (!res?.success || !res.task) throw new DoorError('refused', 'The door refused the card.');
  return cardFromRow(res.task, '', false);
}

export async function moveCard(input: {
  taskId: string;
  targetColumnId: string;
  reason?: string;
}): Promise<void> {
  const res = await doorFetch<{ success?: boolean }>(`/api/tasks/${input.taskId}/move`, {
    method: 'POST',
    payload: { targetColumnId: input.targetColumnId, reason: input.reason ?? '' },
  });
  if (!res?.success) throw new DoorError('refused', 'The door refused the move.');
}

export async function updateCardContent(taskId: string, content: string): Promise<void> {
  const res = await doorFetch<{ success?: boolean }>(`/api/tasks/${taskId}`, {
    method: 'PUT',
    payload: { content },
  });
  if (!res?.success) throw new DoorError('refused', 'The door refused the content update.');
}

/** Merge semantics: a key set to `null` is removed (how a claim is released). */
export async function patchCardMetadata(
  taskId: string,
  patch: Record<string, unknown>,
): Promise<void> {
  const res = await doorFetch<{ success?: boolean }>(`/api/tasks/${taskId}/metadata`, {
    method: 'PATCH',
    payload: { patch },
  });
  if (!res?.success) throw new DoorError('refused', 'The door refused the metadata patch.');
}

export async function deleteCard(taskId: string): Promise<void> {
  const res = await doorFetch<{ success?: boolean; taskId?: string }>(
    `/api/tasks/${taskId}`,
    { method: 'DELETE' },
  );
  if (!res?.success) throw new DoorError('refused', 'The door refused the delete.');
  if (res.taskId && res.taskId !== taskId) {
    throw new DoorError(
      'refused',
      `The door confirmed deleting ${res.taskId} but ${taskId} was requested.`,
    );
  }
}

export async function createBoard(input: {
  name: string;
  goal?: string;
  columns?: ColumnSpec[];
}): Promise<void> {
  const columns =
    input.columns && input.columns.length
      ? input.columns
      : [
          { name: 'todo', wipLimit: 0 },
          { name: 'in_progress', wipLimit: 0 },
          { name: 'done', wipLimit: 0, isDoneColumn: true },
        ];
  await doorFetch<unknown>('/api/boards', {
    method: 'POST',
    payload: {
      name: input.name,
      projectGoal: input.goal || 'created via mem20frontendz',
      columns,
      landingColumnPosition: 0,
    },
  });
}

export async function setDoneColumn(boardId: string, columnName: string): Promise<void> {
  const res = await doorFetch<{ success?: boolean }>(`/api/boards/${boardId}/done-column`, {
    method: 'POST',
    payload: { column: columnName },
  });
  if (!res?.success) {
    throw new DoorError('not-found', `No column named ${columnName} on this board.`);
  }
}

export async function deleteBoard(boardId: string): Promise<void> {
  const res = await doorFetch<{ success?: boolean }>(`/api/boards/${boardId}`, {
    method: 'DELETE',
  });
  if (!res?.success) throw new DoorError('refused', 'The door refused the board delete.');
}

/* ------------------------------------------------------------- analytics */

export interface BoardStats {
  total: number;
  done: number;
  open: number;
  unclaimed: number;
  assignees: { name: string; count: number }[];
  tags: { name: string; count: number }[];
  overWip: { column: string; count: number; limit: number }[];
}

export function boardStats(board: Board): BoardStats {
  const cards = board.columns.flatMap((c) => c.cards);
  const assignees = new Map<string, number>();
  const tags = new Map<string, number>();

  for (const card of cards) {
    if (card.assignee) assignees.set(card.assignee, (assignees.get(card.assignee) ?? 0) + 1);
    for (const tag of card.tags) tags.set(tag, (tags.get(tag) ?? 0) + 1);
  }

  return {
    total: cards.length,
    done: cards.filter((c) => c.done).length,
    open: cards.filter((c) => !c.done).length,
    unclaimed: cards.filter((c) => !c.done && !c.assignee).length,
    assignees: [...assignees.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count),
    tags: [...tags.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count),
    overWip: board.columns
      .filter((c) => c.wipLimit > 0 && c.cards.length > c.wipLimit)
      .map((c) => ({ column: c.name, count: c.cards.length, limit: c.wipLimit })),
  };
}

/**
 * Read one card in full.
 *
 * The board listing deliberately omits `content` (door.py:305-312), so a card's
 * body only ever comes from `/api/tasks/{id}`. Returns `readable: false` when
 * the door is unreachable, which the panel renders as "could not read the body"
 * rather than as an empty body — those are different facts.
 */
export async function fetchCardBody(
  taskId: string,
): Promise<{ content: string; readable: boolean }> {
  try {
    const raw = await doorFetch<{ content?: string }>(
      `/api/tasks/${encodeURIComponent(taskId)}`,
      { timeoutMs: 6000 },
    );
    return { content: raw?.content ?? '', readable: true };
  } catch {
    return { content: '', readable: false };
  }
}
