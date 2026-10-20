/* The ONE api client for the whole shell.
 *
 * Two upstreams, both real, both taken from the code in the mem20 repo:
 *
 *   1. the kanban DOOR  — mem20-kanban, REST on 127.0.0.1:8221
 *      contract read from mem20kanbanz/mem20kanbanz/door.py
 *   2. the CONTROL PLANE — mem20controlz (FastAPI). Its own frontend is served
 *      "same-origin API", so there is no third base URL to invent: it is the
 *      origin this page was loaded from.
 *
 * Design rule carried over from door.py: FAIL LOUD. An unreachable door raises
 * DoorUnreachable. It never returns an empty board, because a UI that shows
 * "no cards" when the door is down is lying to the operator about the state of
 * the work.
 */

export class DoorUnreachable extends Error {
  constructor(public readonly base: string, detail: string) {
    super(`kanban door unreachable at ${base} — ${detail}`);
    this.name = 'DoorUnreachable';
  }
}

/** A column has hit its WIP limit. The door answers HTTP 422 for this. */
export class CapacityFull extends Error {
  constructor(public readonly column: string, public readonly detail: string) {
    super(detail || `column "${column}" is at its WIP limit`);
    this.name = 'CapacityFull';
  }
}

export class DoorNotFound extends Error {
  constructor(public readonly path: string) {
    super(`not found: ${path}`);
    this.name = 'DoorNotFound';
  }
}

/* ---------------------------------------------------------------- storage */

const DOOR_KEY = 'mem20.door';
const CONTROL_KEY = 'mem20.control';

export const DEFAULT_DOOR = 'http://127.0.0.1:8221';
export const DEFAULT_CONTROL = '';

export function getDoorBase(): string {
  return localStorage.getItem(DOOR_KEY) || DEFAULT_DOOR;
}
export function setDoorBase(v: string) {
  localStorage.setItem(DOOR_KEY, v.replace(/\/$/, ''));
}
export function getControlBase(): string {
  const v = localStorage.getItem(CONTROL_KEY);
  return v === null ? DEFAULT_CONTROL : v;
}
export function setControlBase(v: string) {
  localStorage.setItem(CONTROL_KEY, v.replace(/\/$/, ''));
}

/* ------------------------------------------------------------ transport */

type Json = unknown;

async function request(
  base: string,
  path: string,
  init: { method?: string; body?: Json; timeoutMs?: number } = {},
): Promise<any> {
  const method = init.method || 'GET';
  const timeoutMs = init.timeoutMs ?? 8000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  // No body => no Content-Type. door.py learned this the hard way: an empty
  // body with a declared JSON content-type makes Fastify answer 400/415.
  const hasBody = init.body !== undefined;
  try {
    const res = await fetch(`${base}${path}`, {
      method,
      headers: hasBody ? { 'Content-Type': 'application/json' } : undefined,
      body: hasBody ? JSON.stringify(init.body) : undefined,
      credentials: 'same-origin',
      signal: controller.signal,
    });
    if (res.status === 404) throw new DoorNotFound(path);
    if (res.status === 422) {
      let detail = '';
      try {
        detail = (await res.json())?.message || '';
      } catch {
        /* body may be empty */
      }
      throw new CapacityFull('', detail || 'column at capacity');
    }
    if (!res.ok) {
      let detail = '';
      try {
        detail = (await res.json())?.message || '';
      } catch {
        /* ignore */
      }
      throw new Error(`HTTP ${res.status} ${method} ${path}${detail ? `: ${detail}` : ''}`);
    }
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  } catch (err) {
    if (err instanceof CapacityFull || err instanceof DoorNotFound) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new DoorUnreachable(base, `timed out after ${timeoutMs}ms`);
    }
    if (err instanceof TypeError) {
      // fetch rejects with TypeError on DNS failure / connection refused.
      throw new DoorUnreachable(base, (err as Error).message || 'connection refused');
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

/* ------------------------------------------------------- the kanban door */

export interface DoorColumn {
  id: string;
  name: string;
  position: number;
  wipLimit: number;
  isDoneColumn: boolean;
  isLanding: boolean;
}

export interface DoorCard {
  id: string;
  title: string;
  content: string;
  status: string;
  assignee: string;
  tags: string[];
  metadata: Record<string, unknown>;
  isDone: boolean;
}

export interface DoorBoardSummary {
  id: string;
  name: string;
  goal?: string;
}

export interface DoorBoard {
  id: string;
  name: string;
  goal: string;
  columns: DoorColumn[];
  cards: DoorCard[];
}

function parseMeta(raw: unknown): Record<string, unknown> {
  if (!raw) return {};
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw) || {};
    } catch {
      return {};
    }
  }
  return typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
}

export const door = {
  base: getDoorBase,

  /** True when the door answers. Never throws (mirrors Door.healthy). */
  async healthy(): Promise<boolean> {
    try {
      const boards = await request(getDoorBase(), '/api/boards');
      return Array.isArray(boards);
    } catch {
      return false;
    }
  },

  async boards(): Promise<DoorBoardSummary[]> {
    const rows = await request(getDoorBase(), '/api/boards');
    if (!Array.isArray(rows)) throw new Error('door returned a non-array board list');
    return rows.map((b: any) => ({ id: String(b.id), name: String(b.name), goal: b.goal ?? '' }));
  },

  async boardId(name: string): Promise<string> {
    const boards = await this.boards();
    const hit = boards.find((b) => b.name === name);
    if (!hit) throw new DoorNotFound(`board ${name}`);
    return hit.id;
  },

  /** Board detail. The done flag lives on the column as `isDoneColumn`. */
  async board(name: string): Promise<DoorBoard> {
    const id = await this.boardId(name);
    const detail = await request(getDoorBase(), `/api/boards/${id}`);
    const columns: DoorColumn[] = (detail?.columns || []).map((c: any) => ({
      id: String(c.id),
      name: String(c.name),
      position: Number(c.position ?? 0),
      wipLimit: Number(c.wipLimit ?? 0) || 0,
      isDoneColumn: Boolean(c.isDoneColumn),
      isLanding: Boolean(c.isLanding),
    }));
    const doneNames = new Set(columns.filter((c) => c.isDoneColumn).map((c) => c.name));
    const cards: DoorCard[] = [];
    for (const raw of detail?.columns || []) {
      for (const t of raw.tasks || []) {
        const meta = parseMeta(t.metadata);
        const tags = Array.isArray(meta.tags)
          ? (meta.tags as unknown[]).map(String)
          : typeof meta.tags === 'string'
            ? String(meta.tags).split(',').filter(Boolean)
            : [];
        cards.push({
          id: String(t.id),
          title: String(t.title ?? ''),
          content: String(t.content ?? ''),
          status: String(raw.name),
          assignee: String(meta.assignee ?? ''),
          tags,
          metadata: meta,
          isDone: doneNames.has(String(raw.name)),
        });
      }
    }
    return {
      id,
      name: detail?.board?.name ?? name,
      goal: detail?.board?.goal ?? '',
      columns: columns.sort((a, b) => a.position - b.position),
      cards,
    };
  },

  /** One card in full. `/api/tasks/:id` is authoritative and carries content. */
  async card(taskId: string): Promise<DoorCard> {
    const raw = await request(getDoorBase(), `/api/tasks/${taskId}`);
    const meta = parseMeta(raw?.metadata);
    return {
      id: String(raw?.id ?? taskId),
      title: String(raw?.title ?? ''),
      content: String(raw?.content ?? ''),
      status: String(raw?.status ?? ''),
      assignee: String(meta.assignee ?? ''),
      tags: Array.isArray(meta.tags) ? (meta.tags as unknown[]).map(String) : [],
      metadata: meta,
      isDone: Boolean(meta.is_done_column),
    };
  },

  /** Move a card by column NAME (callers stay name-based, as door.py does). */
  async move(taskId: string, targetColumn: string, reason = ''): Promise<void> {
    const board = await this.boardOfTask(taskId);
    const col = board.columns.find((c) => c.name === targetColumn);
    if (!col) throw new DoorNotFound(`column ${targetColumn} on ${board.name}`);
    await request(getDoorBase(), `/api/tasks/${taskId}/move`, {
      method: 'POST',
      body: { targetColumnId: col.id, reason },
    });
  },

  async moveToColumnId(taskId: string, columnId: string, reason = ''): Promise<void> {
    await request(getDoorBase(), `/api/tasks/${taskId}/move`, {
      method: 'POST',
      body: { targetColumnId: columnId, reason },
    });
  },

  /** Merge a metadata patch. A key mapped to null is REMOVED (how release works). */
  async patchMetadata(taskId: string, patch: Record<string, unknown>): Promise<void> {
    await request(getDoorBase(), `/api/tasks/${taskId}/metadata`, {
      method: 'PATCH',
      body: { patch },
    });
  },

  async setDoneColumn(boardName: string, column: string): Promise<boolean> {
    const id = await this.boardId(boardName);
    const res = await request(getDoorBase(), `/api/boards/${id}/done-column`, {
      method: 'POST',
      body: { column },
    });
    return Boolean(res?.success);
  },

  async addCard(
    boardName: string,
    title: string,
    opts: { content?: string; assignee?: string; tags?: string[]; column?: string } = {},
  ): Promise<void> {
    const board = await this.board(boardName);
    const payload: Record<string, unknown> = {
      boardId: board.id,
      title,
      content: opts.content ?? '',
      metadata: { assignee: opts.assignee ?? '', tags: opts.tags ?? [] },
    };
    if (opts.column) {
      const col = board.columns.find((c) => c.name === opts.column);
      if (!col) throw new DoorNotFound(`column ${opts.column}`);
      payload.columnId = col.id;
    }
    await request(getDoorBase(), '/api/tasks', { method: 'POST', body: payload });
  },

  async deleteCard(taskId: string): Promise<void> {
    const res = await request(getDoorBase(), `/api/tasks/${taskId}`, { method: 'DELETE' });
    const confirmed = res?.taskId;
    // A door answering 200 for a DIFFERENT card must never read as a delete.
    if (confirmed && String(confirmed) !== taskId) {
      throw new Error(`door confirmed deleting ${confirmed} but ${taskId} was asked for`);
    }
  },

  async boardOfTask(taskId: string): Promise<DoorBoard> {
    for (const b of await this.boards()) {
      const full = await this.board(b.name);
      if (full.cards.some((c) => c.id === taskId)) return full;
    }
    throw new DoorNotFound(`task ${taskId} is on no board`);
  },
};

/* ------------------------------------------------------- the door contract */

/** The status the door answers when a move would break a WIP limit. */
export const CAPACITY_STATUS = 422;

/** Every route on the door, transcribed from mem20kanbanz/door.py. */
export const DOOR_ROUTES: Array<{
  method: string;
  path: string;
  payload?: string;
  does: string;
}> = [
  { method: 'GET', path: '/api/boards', does: 'all boards — this is also the health probe' },
  { method: 'POST', path: '/api/boards', payload: '{name, projectGoal, columns[], landingColumnPosition}', does: 'create a board (idempotent by name, so a bot retry cannot duplicate it)' },
  { method: 'GET', path: '/api/boards/:boardId', does: 'board with columns and tasks; carries isDoneColumn' },
  { method: 'DELETE', path: '/api/boards/:boardId', does: 'remove a board and its cards' },
  { method: 'POST', path: '/api/boards/:boardId/done-column', payload: '{column}', does: 'declare which column means finished — moves the flag, never adds a second one' },
  { method: 'POST', path: '/api/tasks', payload: '{boardId, title, content, metadata, columnId?}', does: 'add a card, defaulting to the landing column' },
  { method: 'GET', path: '/api/tasks/:taskId', does: 'one card — authoritative, carries content' },
  { method: 'PUT', path: '/api/tasks/:taskId', payload: '{content}', does: "replace a card's content" },
  { method: 'PATCH', path: '/api/tasks/:taskId/metadata', payload: '{patch:{...}}', does: 'MERGE metadata; a key set to null is removed (this is how a claim is released)' },
  { method: 'POST', path: '/api/tasks/:taskId/move', payload: '{targetColumnId, reason}', does: 'move a card, enforcing WIP — 422 when the column is full' },
  { method: 'DELETE', path: '/api/tasks/:taskId', does: 'remove a card (destructive, not undoable)' },
];

/* ------------------------------------------------- control plane (FastAPI) */

/** Every route below was read out of mem20controlz/mem20controlz/app.py. */
export const CONTROL_ROUTES = [
  { method: 'GET', path: '/api/health', auth: false },
  { method: 'GET', path: '/api/auth/status', auth: false },
  { method: 'POST', path: '/api/auth/login', auth: false },
  { method: 'POST', path: '/api/auth/logout', auth: true },
  { method: 'GET', path: '/api/registry', auth: true },
  { method: 'GET', path: '/api/cli/coverage', auth: true },
  { method: 'GET', path: '/api/websites/manifest', auth: true },
  { method: 'GET', path: '/api/websites/sites', auth: true },
  { method: 'GET', path: '/api/websites/dns', auth: true },
  { method: 'POST', path: '/api/websites/dns', auth: true },
  { method: 'DELETE', path: '/api/websites/dns/{record_id}', auth: true },
  { method: 'GET', path: '/api/websites/health', auth: true },
  { method: 'GET', path: '/api/websites/logs', auth: true },
  { method: 'GET', path: '/api/websites/pages', auth: true },
  { method: 'GET', path: '/api/dreams/manifest', auth: true },
  { method: 'GET', path: '/api/dreams', auth: true },
  { method: 'GET', path: '/api/dreams/idle-stats', auth: true },
  { method: 'GET', path: '/api/dreams/hollow', auth: true },
  { method: 'GET', path: '/api/dreams/runs', auth: true },
  { method: 'GET', path: '/api/dreams/runs/{job_id}', auth: true },
  { method: 'POST', path: '/api/dreams/runs', auth: true },
  { method: 'GET', path: '/api/dreams/{dream_id}', auth: true },
  { method: 'GET', path: '/api/dreams/{dream_id}/chain', auth: true },
  { method: 'POST', path: '/api/dreams/{dream_id}/verify', auth: true },
  { method: 'POST', path: '/api/dreams/{dream_id}/promote', auth: true },
  { method: 'POST', path: '/api/dreams', auth: true },
] as const;

export interface DreamSummary {
  id: string;
  title: string;
  status: string;
  epistemic: string;
  predictionErrorEvidence: unknown;
  provenance: Array<{ at: string; actor: string; action: string; cid?: string }>;
}

export interface DreamDetail extends DreamSummary {
  chain: Array<{ cid: string; at: string; origin: string; store: string; note?: string }>;
}

export const control = {
  base: getControlBase,

  async health(): Promise<{ ok: boolean; detail: string }> {
    try {
      const r = await request(getControlBase(), '/api/health', { timeoutMs: 5000 });
      return { ok: true, detail: JSON.stringify(r).slice(0, 120) };
    } catch (e) {
      return { ok: false, detail: e instanceof Error ? e.message : String(e) };
    }
  },

  async authStatus(): Promise<{ authed: boolean; detail: string }> {
    try {
      const r = await request(getControlBase(), '/api/auth/status', { timeoutMs: 5000 });
      return { authed: Boolean(r?.authenticated ?? r?.authed ?? false), detail: '' };
    } catch (e) {
      return { authed: false, detail: e instanceof Error ? e.message : String(e) };
    }
  },

  async login(password: string): Promise<boolean> {
    const r = await request(getControlBase(), '/api/auth/login', {
      method: 'POST',
      body: { password },
      timeoutMs: 8000,
    });
    return Boolean(r?.ok ?? r?.authenticated ?? false);
  },

  async logout(): Promise<void> {
    await request(getControlBase(), '/api/auth/logout', { method: 'POST' });
  },

  async dreams(): Promise<DreamSummary[]> {
    const rows = await request(getControlBase(), '/api/dreams');
    if (!Array.isArray(rows)) throw new Error('control plane returned a non-array dream list');
    return rows.map((d: any) => ({
      id: String(d.id ?? d.dream_id ?? ''),
      title: String(d.title ?? d.name ?? ''),
      status: String(d.status ?? ''),
      epistemic: String(d.epistemic_status ?? 'simulated'),
      predictionErrorEvidence: d.prediction_error_evidence ?? null,
      provenance: Array.isArray(d.provenance) ? d.provenance : [],
    }));
  },

  async dream(id: string): Promise<DreamDetail> {
    const d = await request(getControlBase(), `/api/dreams/${id}`);
    const chain = await request(getControlBase(), `/api/dreams/${id}/chain`).catch(() => []);
    return {
      id,
      title: String(d?.title ?? d?.name ?? ''),
      status: String(d?.status ?? ''),
      epistemic: String(d?.epistemic_status ?? 'simulated'),
      predictionErrorEvidence: d?.prediction_error_evidence ?? null,
      provenance: Array.isArray(d?.provenance) ? d.provenance : [],
      chain: Array.isArray(chain) ? chain : [],
    };
  },

  async promote(id: string, evidence: unknown): Promise<unknown> {
    return request(getControlBase(), `/api/dreams/${id}/promote`, {
      method: 'POST',
      body: { prediction_error_evidence: evidence },
    });
  },
};
