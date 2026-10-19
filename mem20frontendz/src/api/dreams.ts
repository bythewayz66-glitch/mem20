/**
 * Dreams transport — the mem20controlz FastAPI surface.
 *
 * ── Ground truth ────────────────────────────────────────────────────────────
 * Routes read from `mem20controlz/mem20controlz/app.py`:
 *
 *   GET  /api/health
 *   GET  /api/auth/status          → posture + whether *this* caller is admitted
 *   POST /api/auth/login           → sets an httpOnly session cookie
 *   GET  /api/dreams/manifest
 *   GET  /api/dreams?kind&include_hollow&only_unpromoted&limit
 *   GET  /api/dreams/idle-stats
 *   GET  /api/dreams/hollow
 *   GET  /api/dreams/runs
 *   GET  /api/dreams/runs/{job_id}
 *   POST /api/dreams/runs          → {dream_id, iterations}
 *   GET  /api/dreams/{dream_id}
 *   GET  /api/dreams/{dream_id}/chain
 *   POST /api/dreams/{dream_id}/verify
 *   POST /api/dreams/{dream_id}/promote   → {force}
 *   POST /api/dreams               → {seed, foundation, kind}
 *
 * ── Two rules taken from the server itself ───────────────────────────────────
 * 1. A refusal is a **409 with the engine's own words**, not a generic error
 *    (`app.py:_dream_error`). Flattening it would hide *why* — hollow lineage vs
 *    broken braid — so `ControlError` carries `status` and the verbatim detail.
 * 2. Promotion that is declined comes back **200 with `promoted: false`**. That
 *    is not a failure of the request; it is the gate working. The UI must render
 *    the reason, not an error toast.
 *
 * ── Honesty about an empty estate ────────────────────────────────────────────
 * `/opt/mem20/store/dreams` did not exist on sidney at capture time, so there
 * are zero lineages and zero promotions. That is a real, reportable state — the
 * UI shows an empty store plus the exact path it looked in, never seeded demo
 * dreams. Read `loadDreams()` and see `empty` on the envelope.
 */

import { CONTROL_BASE, SOURCE_MODE } from './config';
import type {
  DreamChain,
  DreamDetail,
  DreamHollowReport,
  DreamIdleStats,
  DreamListResponse,
  DreamManifest,
  DreamRunsResponse,
  DreamVerify,
  Loaded,
} from './types';

/* ------------------------------------------------------------------ errors */

export class ControlError extends Error {
  readonly status: number;
  readonly kind: 'unauthorized' | 'refused' | 'unreachable' | 'server';
  constructor(kind: ControlError['kind'], status: number, message: string) {
    super(message);
    this.name = 'ControlError';
    this.kind = kind;
    this.status = status;
  }
}

/* --------------------------------------------------------------- transport */

interface RequestOptions {
  method?: 'GET' | 'POST';
  payload?: unknown;
  timeoutMs?: number;
}

async function controlFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', payload, timeoutMs = 12000 } = opts;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${CONTROL_BASE}${path}`, {
      method,
      // Session cookie is httpOnly and scoped to this origin; credentials are
      // required for it to travel through the proxy.
      credentials: 'include',
      signal: controller.signal,
      ...(payload !== undefined
        ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }
        : {}),
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
      parsed && typeof parsed === 'object' && 'detail' in parsed
        ? String((parsed as { detail: unknown }).detail)
        : '';

    if (res.status === 401) {
      throw new ControlError(
        'unauthorized',
        401,
        detail || 'The control plane requires a session.',
      );
    }
    // 409 is the engine declining with its own wording — keep it verbatim.
    if (res.status === 409) {
      throw new ControlError('refused', 409, detail || 'The estate declined this request.');
    }
    if (res.status >= 500) {
      throw new ControlError(
        'server',
        res.status,
        detail || `Control plane error ${res.status}.`,
      );
    }
    throw new ControlError('server', res.status, detail || `HTTP ${res.status} ${path}`);
  } catch (err) {
    if (err instanceof ControlError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ControlError('unreachable', 0, `No answer within ${timeoutMs}ms.`);
    }
    throw new ControlError(
      'unreachable',
      0,
      err instanceof Error ? err.message : 'The control plane is unreachable.',
    );
  } finally {
    window.clearTimeout(timer);
  }
}

/* --------------------------------------------------------------- read side */

export interface DreamsEnvelope {
  list: Loaded<DreamListResponse | null>;
  /** True when the store genuinely holds nothing — distinct from "unreachable". */
  empty: boolean;
}

export async function loadDreams(
  params: {
    kind?: string;
    includeHollow?: boolean;
    onlyUnpromoted?: boolean;
  } = {},
): Promise<DreamsEnvelope> {
  const q = new URLSearchParams();
  if (params.kind) q.set('kind', params.kind);
  q.set('include_hollow', String(params.includeHollow ?? true));
  q.set('only_unpromoted', String(params.onlyUnpromoted ?? false));

  const started = performance.now();
  try {
    const data = await controlFetch<DreamListResponse>(`/api/dreams?${q}`);
    return {
      list: {
        data,
        source: 'live',
        at: new Date().toISOString(),
        latencyMs: Math.round(performance.now() - started),
      },
      empty: data.total === 0,
    };
  } catch (err) {
    if (SOURCE_MODE === 'live') {
      return {
        list: {
          data: null,
          source: 'live',
          at: new Date().toISOString(),
          note: err instanceof Error ? err.message : 'Failed.',
        },
        empty: false,
      };
    }
    return {
      list: {
        data: null,
        source: 'snapshot',
        at: new Date().toISOString(),
        note:
          err instanceof ControlError && err.kind === 'unreachable'
            ? `Control plane unreachable at ${CONTROL_BASE}. The dream store at /opt/mem20/store/dreams held no lineages when captured, so there is nothing to display rather than something to fake.`
            : err instanceof Error
              ? err.message
              : 'Live read failed.',
      },
      empty: true,
    };
  }
}

export function loadDream(dreamId: string): Promise<DreamDetail> {
  return controlFetch<DreamDetail>(`/api/dreams/${encodeURIComponent(dreamId)}`);
}

export function loadChain(dreamId: string): Promise<DreamChain> {
  return controlFetch<DreamChain>(`/api/dreams/${encodeURIComponent(dreamId)}/chain`);
}

export function loadManifest(): Promise<DreamManifest> {
  return controlFetch<DreamManifest>('/api/dreams/manifest');
}

export function loadRuns(): Promise<DreamRunsResponse> {
  return controlFetch<DreamRunsResponse>('/api/dreams/runs');
}

export function loadHollow(): Promise<DreamHollowReport> {
  return controlFetch<DreamHollowReport>('/api/dreams/hollow');
}

export function loadIdleStats(): Promise<DreamIdleStats> {
  return controlFetch<DreamIdleStats>('/api/dreams/idle-stats');
}

export interface HealthReport {
  ok: boolean;
  status: number;
  body: unknown;
  detail: string;
  latencyMs: number;
}

export async function probeControl(): Promise<HealthReport> {
  const started = performance.now();
  try {
    const body = await controlFetch<unknown>('/api/health', { timeoutMs: 4000 });
    return {
      ok: true,
      status: 200,
      body,
      detail: 'Control plane answered /api/health.',
      latencyMs: Math.round(performance.now() - started),
    };
  } catch (err) {
    return {
      ok: false,
      status: err instanceof ControlError ? err.status : 0,
      body: null,
      detail: err instanceof Error ? err.message : 'Unreachable.',
      latencyMs: Math.round(performance.now() - started),
    };
  }
}

export interface AuthStatus {
  authenticated: boolean;
  admitted_by?: string | null;
  identity?: string | null;
  [key: string]: unknown;
}

export function loadAuthStatus(): Promise<AuthStatus> {
  return controlFetch<AuthStatus>('/api/auth/status', { timeoutMs: 4000 });
}

export function login(password: string): Promise<{ ok: boolean; admitted_by?: string }> {
  return controlFetch<{ ok: boolean; admitted_by?: string }>('/api/auth/login', {
    method: 'POST',
    payload: { password },
  });
}

/* -------------------------------------------------------------- write side */

/**
 * Promote a dream.
 *
 * Returns the engine's own verdict. `promoted: false` with a `reason` is a
 * legitimate outcome (hollow lineage, broken chain) — callers must render it as
 * information, not as an error.
 */
export function promoteDream(
  dreamId: string,
  force = false,
): Promise<{ promoted: boolean; reason?: string; path?: string; files?: string[] }> {
  return controlFetch(`/api/dreams/${encodeURIComponent(dreamId)}/promote`, {
    method: 'POST',
    payload: { force },
  });
}

/** Re-prove every braid node. The only call that can report `verified: true`. */
export function verifyDream(dreamId: string): Promise<DreamVerify> {
  return controlFetch<DreamVerify>(`/api/dreams/${encodeURIComponent(dreamId)}/verify`, {
    method: 'POST',
  });
}

export function createDream(input: {
  seed: string;
  foundation?: string;
  kind?: string;
}): Promise<{ dream_id: string; kind: string; state_path: string; note: string }> {
  return controlFetch('/api/dreams', {
    method: 'POST',
    payload: {
      seed: input.seed,
      foundation: input.foundation ?? '',
      kind: input.kind ?? 'active',
    },
  });
}

export function startRun(dreamId: string, iterations = 1): Promise<{ job_id: string }> {
  return controlFetch('/api/dreams/runs', {
    method: 'POST',
    payload: { dream_id: dreamId, iterations },
  });
}

export function runStatus(jobId: string) {
  return controlFetch<{ status: string; note: string; log: string[]; log_lines: number }>(
    `/api/dreams/runs/${encodeURIComponent(jobId)}`,
  );
}
