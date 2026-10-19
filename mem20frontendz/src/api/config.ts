/**
 * mem20frontendz — transport configuration.
 *
 * Three real backends, three endpoints. Nothing here invents a route: every
 * path below is one that the estate actually serves (see `api/kanban.ts`,
 * `api/dreams.ts`, `api/mcp.ts` for the exact shape of each call).
 *
 * Browser clients cannot talk to these directly in every case, so all three go
 * through the dev/preview proxy defined in `vite.config.ts` under `/api/*`.
 * That is deliberate and load-bearing:
 *
 *   • :8221 — the kanban door. Nothing listens there yet (no listener, no unit
 *     on sidney), so requests fail fast and the UI says so instead of showing
 *     an empty board. Wire this to a real host once the door exists.
 *   • controlz — the only surface with a working Dreams API today.
 *   • :8082 — the MCP HTTP/SSE transport. It answers POST / with JSON-RPC, but
 *     it sends no CORS preflight headers, so a browser cannot call it
 *     cross-origin. The proxy is what makes the tool browser real.
 *
 * Override any target at build time with VITE_* env vars; there is no secret
 * in this file and none may be added — controlz authenticates with an httpOnly
 * session cookie, never with a key embedded in client code.
 */

export const BASE = import.meta.env.BASE_URL;

/** Proxy prefixes. These are stable; the upstream targets behind them are not. */
export const DOOR_BASE = '/api/door';
export const CONTROL_BASE = '/api/control';
export const MCP_BASE = '/api/mcp';

export type SourceMode = 'live' | 'snapshot';

/**
 * `VITE_SOURCE_MODE` decides whether a surface may fall back to the captured
 * snapshot when its live backend is unreachable.
 *
 *   'snapshot' (default) — try live, fall back to the checked-in capture, and
 *                          label the surface as a capture with its timestamp.
 *   'live'               — never fall back. A dead backend renders an error.
 *
 * Either way the UI states which one it is showing. A capture that reads as
 * live data is the one failure mode this app must not have.
 */
export const SOURCE_MODE: SourceMode =
  (import.meta.env.VITE_SOURCE_MODE as SourceMode | undefined) ?? 'snapshot';

/** Provenance stamped into every checked-in capture. */
export const SNAPSHOT_META = {
  capturedAt: '2026-10-19T06:32:00-06:00',
  capturedFrom: 'sidney (216.198.115.91)',
  kanban: {
    store: '/opt/mem20/mem20/kanban/kanban_3.db',
    note: 'read-only dump of the live SQLite store',
  },
  tools: {
    store: 'mem20-mcp JSON-RPC tools/list over :8082',
    note: 'live handshake, session id issued by the server',
  },
  roadmaps: {
    store: '/opt/mem20/mem20/roadmaps/*.json',
    note: 'Sarge input corpus',
  },
  dreams: {
    store: '/opt/mem20/store/dreams',
    note: 'store did not exist on the host at capture time — zero lineages',
  },
} as const;

/** The identity of each backend, surfaced in the Connection panel. */
export interface Endpoint {
  id: 'door' | 'control' | 'mcp';
  label: string;
  path: string;
  envVar: string;
  defaultTarget: string;
  /** What this backend does and does not expose — stated, not implied. */
  contract: string;
}

export const ENDPOINTS: Endpoint[] = [
  {
    id: 'door',
    label: 'Kanban door',
    path: DOOR_BASE,
    envVar: 'MEM20_DOOR_URL',
    defaultTarget: 'http://127.0.0.1:8221',
    contract:
      'REST: /api/boards, /api/boards/{id}, /api/boards/{id}/done-column, ' +
      '/api/tasks, /api/tasks/{id}, /api/tasks/{id}/move, /api/tasks/{id}/metadata. ' +
      'No kanban MCP tools exist — REST is the only surface.',
  },
  {
    id: 'control',
    label: 'Control plane',
    path: CONTROL_BASE,
    envVar: 'MEM20_CONTROL_URL',
    defaultTarget: 'http://127.0.0.1:8200',
    contract:
      'FastAPI: /api/health, /api/auth/*, /api/dreams + /{id}, /{id}/chain, ' +
      '/{id}/verify, /{id}/promote, /runs, /idle-stats, /hollow, plus /api/registry.',
  },
  {
    id: 'mcp',
    label: 'mem20 MCP',
    path: MCP_BASE,
    envVar: 'MEM20_MCP_URL',
    defaultTarget: 'http://127.0.0.1:8082',
    contract:
      'JSON-RPC 2.0 over HTTP: initialize → notifications/initialized → tools/list. ' +
      'Issues an Mcp-Session-Id header; no CORS preflight, hence the proxy.',
  },
];
