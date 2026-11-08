/* The honesty layer for every surface that needs real backend data.
 *
 * The rule this file exists to enforce: a surface that cannot reach its data
 * must SAY SO. It must never render a zero, an empty chart, or a plausible
 * number it did not measure. A dashboard showing "recall@5 = 0.00" when the
 * backend is simply down is lying to the reader about the state of the system
 * - the same failure mode door.py was written to avoid.
 *
 * So every call here returns a discriminated union rather than throwing or
 * returning a default:
 *
 *   { state: 'ok',          data }        - measured, real
 *   { state: 'unreachable', detail }      - the backend is not there
 *   { state: 'error',       detail }      - it answered, but with a failure
 *
 * Callers switch on `state`. There is no fourth case and no silent fallback.
 *
 * The routes below are transcribed from bridge/server.py, which is the real
 * HTTP surface in this repo (mem20-bridge, FastAPI, default 0.0.0.0:8000).
 * Nothing here is invented: each path and payload shape is read from that file.
 */

export type Probe<T> =
  | { state: 'ok'; data: T }
  | { state: 'unreachable'; detail: string }
  | { state: 'error'; detail: string };

const BRIDGE_KEY = 'mem20.bridge';

/** Default bridge address, matching bridge/server.py's MEM20_BRIDGE_LISTEN. */
export const DEFAULT_BRIDGE = 'http://127.0.0.1:8000';

export function getBridgeBase(): string {
  return localStorage.getItem(BRIDGE_KEY) || DEFAULT_BRIDGE;
}

export function setBridgeBase(v: string): void {
  localStorage.setItem(BRIDGE_KEY, v.replace(/\/$/, ''));
}

/* --------------------------------------------------------------- transport */

async function call<T>(
  path: string,
  init: { method?: string; body?: unknown; timeoutMs?: number } = {},
): Promise<Probe<T>> {
  const base = getBridgeBase();
  const timeoutMs = init.timeoutMs ?? 6000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const hasBody = init.body !== undefined;

  try {
    const res = await fetch(`${base}${path}`, {
      method: init.method || 'GET',
      headers: hasBody ? { 'Content-Type': 'application/json' } : undefined,
      body: hasBody ? JSON.stringify(init.body) : undefined,
      signal: controller.signal,
    });

    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const j = await res.json();
        if (j?.detail) detail = String(j.detail);
      } catch {
        /* body may be empty */
      }
      // 503 is what bridge/server.py raises when the MCP server behind it is
      // down. That is an unreachable backend, not a bug in this page.
      if (res.status === 503) return { state: 'unreachable', detail };
      return { state: 'error', detail };
    }

    const text = await res.text();
    return { state: 'ok', data: (text ? JSON.parse(text) : null) as T };
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      return { state: 'unreachable', detail: `no answer from ${base} within ${timeoutMs}ms` };
    }
    if (err instanceof TypeError) {
      // fetch rejects with TypeError on DNS failure / connection refused.
      return { state: 'unreachable', detail: (err as Error).message || 'connection refused' };
    }
    return { state: 'error', detail: err instanceof Error ? err.message : String(err) };
  } finally {
    clearTimeout(timer);
  }
}

/* ------------------------------------------------------------------ shapes */

export interface BridgeStatus {
  bridge: string;
  mcp: unknown;
  engine_available: boolean;
}

export interface MemoryRecord {
  id?: string;
  text?: string;
  content?: string;
  topic?: string;
  tags?: string[];
  origin?: string;
  store?: string;
  epistemic_status?: string;
  created_at?: string;
  [k: string]: unknown;
}

export interface MemoryList {
  count: number;
  records: MemoryRecord[];
}

/* ------------------------------------------------------------------- client */

export const bridge = {
  base: getBridgeBase,

  /** /api/status - bridge liveness, MCP health, engine availability. */
  status: () => call<BridgeStatus>('/api/status', { timeoutMs: 5000 }),

  /** /api/health - proxied MCP health. */
  health: () => call<unknown>('/api/health', { timeoutMs: 5000 }),

  /** /api/metrics - proxied MCP metrics. */
  metrics: () => call<unknown>('/api/metrics', { timeoutMs: 5000 }),

  /** /api/memory - recent grounded records. */
  memory: (limit = 100) => call<MemoryList>(`/api/memory?limit=${limit}`),

  /** /api/recall - recall by topic/tags. */
  recall: (query: string, tags: string[] | null, k = 5) =>
    call<MemoryList>('/api/recall', { method: 'POST', body: { query, tags, k } }),
};

/* ------------------------------------------------------------------ helpers */

/** True when a probe carries real data. */
export function isOk<T>(p: Probe<T>): p is { state: 'ok'; data: T } {
  return p.state === 'ok';
}

/** A one-line reason a surface is showing an empty state, for the UI. */
export function reasonOf<T>(p: Probe<T>): string {
  if (p.state === 'ok') return '';
  return p.state === 'unreachable'
    ? `Backend not reachable at ${getBridgeBase()} - ${p.detail}`
    : `Backend error - ${p.detail}`;
}

/**
 * The routes this shell knows about, transcribed from bridge/server.py.
 * The Connection view renders this list so a reader can see exactly what the
 * shell will and will not call.
 */
export const BRIDGE_ROUTES: Array<{ method: string; path: string; does: string }> = [
  { method: 'GET', path: '/api/status', does: 'bridge liveness, MCP health, engine availability' },
  { method: 'GET', path: '/api/health', does: 'proxied MCP health' },
  { method: 'GET', path: '/api/ready', does: 'proxied MCP readiness' },
  { method: 'GET', path: '/api/metrics', does: 'proxied MCP metrics' },
  { method: 'GET', path: '/api/memory?limit=N', does: 'recent grounded memory records' },
  { method: 'POST', path: '/api/recall', does: 'recall by topic/tags - body {query, tags, k}' },
];
