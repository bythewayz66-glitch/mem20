/**
 * MCP tool-surface transport.
 *
 * ── Ground truth ────────────────────────────────────────────────────────────
 * mem20-mcp speaks JSON-RPC 2.0 over HTTP. A real handshake, captured on
 * sidney against :8082, is:
 *
 *   POST /  {jsonrpc, id:1, method:"initialize",
 *            params:{protocolVersion:"2024-11-05", capabilities:{},
 *                    clientInfo:{name,version}}}
 *        → response headers carry `Mcp-Session-Id: <uuid>`
 *   POST /  {jsonrpc, method:"notifications/initialized"}   (same session id)
 *   POST /  {jsonrpc, id:2, method:"tools/list", params:{}} (same session id)
 *        → text/event-stream, one `data: {...}` frame per message
 *
 * Two facts drive the design here:
 *
 * 1. **There is no REST endpoint that lists the tools.** The only authority is
 *    `tools/list` over that handshake. So the bundled `data/tools.json` is the
 *    capture of that exact call (257 tools, taken live), not a hand-written
 *    catalogue — and `loadTools()` prefers a fresh handshake when one is
 *    reachable, falling back to the capture with the provenance shown.
 *
 * 2. **The server sends no CORS preflight headers.** A browser cannot call it
 *    cross-origin; every request must travel through the proxy at `/api/mcp`.
 *    That is a deployment fact, not a bug to work around in client code.
 *
 * The live path also must cope with a session id that expires: if `tools/list`
 * answers "Missing session ID", the client re-initialises once and retries.
 */

import { MCP_BASE, SNAPSHOT_META } from './config';
import capturedTools from '../data/tools.json';
import type { Loaded, McpTool, ToolDomain, ToolEntry } from './types';

const capture = capturedTools as unknown as McpTool[];

/* ------------------------------------------------------------------ derive */

/** Namespace prefix of a tool name: `memory_store` → `memory`. */
export function domainOf(name: string): string {
  const idx = name.indexOf('_');
  return idx === -1 ? name : name.slice(0, idx);
}

/** A short human label for a namespace, used in the domain index. */
const DOMAIN_LABELS: Record<string, string> = {
  memory: 'Memory',
  fs: 'Filesystem',
  vcs: 'Version control',
  cloud: 'Cloud',
  db: 'Database',
  prod: 'Productivity',
  world: 'World model',
  comm: 'Communication',
  dev: 'Development',
  mkt: 'Marketing',
  braid: 'Braid ledger',
  imagination: 'Imagination',
  cloudstorage: 'Cloud storage',
  design: 'Design',
  fin: 'Finance',
  scrape: 'Scraping',
  blender: 'Blender / 3D',
  search: 'Search',
  cog: 'Cognition',
  affective: 'Affective state',
  procedural: 'Procedural memory',
  unity: 'Unity / 3D',
  a2a: 'Agent-to-agent',
  irc: 'IRC',
  roadmap: 'Roadmap',
  self: 'Self-model',
  tot: 'Tree of thought',
  theory: 'Theory of mind',
  corrigibility: 'Corrigibility',
  job: 'Jobs',
  reflexion: 'Reflexion',
  least: 'Least-to-most',
  react: 'ReAct',
  beam: 'Beam search',
  cognitive: 'Cognitive',
  get: 'Miscellaneous',
};

export function domainLabel(id: string): string {
  return DOMAIN_LABELS[id] ?? id.charAt(0).toUpperCase() + id.slice(1);
}

/**
 * Which tool to read first in a namespace.
 *
 * Chosen by convention, not by guessing semantics: a `*_status` tool is the
 * cheapest entry point for an ops namespace, and the plainest `<domain>_...`
 * name otherwise. Falls back to the shortest name so the pick is deterministic.
 */
function pickStartHere(tools: ToolEntry[]): string {
  const preferred = ['status', 'health', 'list', 'get', 'query', 'search'];
  for (const suffix of preferred) {
    const hit = tools.find((t) => t.name.endsWith(`_${suffix}`));
    if (hit) return hit.name;
  }
  return [...tools].sort((a, b) => a.name.length - b.name.length)[0]?.name ?? '';
}

/** Enrich the raw `tools/list` entries with the fields the browser groups on. */
export function toEntries(tools: McpTool[]): ToolEntry[] {
  return tools.map((t) => {
    const props = t.inputSchema?.properties ?? {};
    return {
      ...t,
      domain: domainOf(t.name),
      paramCount: Object.keys(props).length,
      required: Array.isArray(t.inputSchema?.required) ? t.inputSchema.required : [],
    };
  });
}

export function groupByDomain(tools: ToolEntry[]): ToolDomain[] {
  const buckets = new Map<string, ToolEntry[]>();
  for (const tool of tools) {
    const list = buckets.get(tool.domain) ?? [];
    list.push(tool);
    buckets.set(tool.domain, list);
  }
  return [...buckets.entries()]
    .map(([id, list]) => ({
      id,
      count: list.length,
      startHere: pickStartHere(list),
      tools: [...list].sort((a, b) => a.name.localeCompare(b.name)),
    }))
    .sort((a, b) => b.count - a.count || a.id.localeCompare(b.id));
}

/* --------------------------------------------------------------- live call */

let sessionId: string | null = null;

interface RpcResponse {
  jsonrpc: '2.0';
  id: number | null;
  result?: unknown;
  error?: { code: number; message: string };
}

/** Parse either a plain JSON body or an SSE frame carrying one message. */
function readRpcPayload(text: string, contentType: string): RpcResponse | null {
  const trimmed = text.trim();
  if (!trimmed) return null;
  if (contentType.includes('text/event-stream')) {
    // One `data:` line per message; take the first JSON frame.
    for (const line of trimmed.split('\n')) {
      const l = line.trim();
      if (!l.startsWith('data:')) continue;
      try {
        return JSON.parse(l.slice(5).trim()) as RpcResponse;
      } catch {
        /* keep scanning */
      }
    }
    return null;
  }
  try {
    return JSON.parse(trimmed) as RpcResponse;
  } catch {
    return null;
  }
}

async function rpc(
  body: Record<string, unknown>,
  session: string | null,
  timeoutMs = 10000,
): Promise<{ payload: RpcResponse | null; session: string | null }> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${MCP_BASE}/`, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        ...(session ? { 'Mcp-Session-Id': session } : {}),
      },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    const nextSession = res.headers.get('mcp-session-id') ?? session;
    return {
      payload: readRpcPayload(text, res.headers.get('content-type') ?? ''),
      session: nextSession,
    };
  } finally {
    window.clearTimeout(timer);
  }
}

/** Full handshake → `tools/list`. Raises on any transport or protocol problem. */
export async function fetchLiveTools(): Promise<McpTool[]> {
  if (!sessionId) {
    const init = await rpc(
      {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          clientInfo: { name: 'mem20frontendz', version: '1.0.0' },
        },
      },
      null,
    );
    if (init.payload?.error) {
      throw new Error(`initialize failed: ${init.payload.error.message}`);
    }
    if (!init.session) throw new Error('The server issued no Mcp-Session-Id.');
    sessionId = init.session;

    await rpc({ jsonrpc: '2.0', method: 'notifications/initialized' }, sessionId, 6000);
  }

  const listed = await rpc(
    { jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} },
    sessionId,
  );
  if (listed.payload?.error) {
    // A stale session answers "Missing session ID" — re-init once, then give up.
    if (/session/i.test(listed.payload.error.message)) {
      sessionId = null;
      return fetchLiveTools();
    }
    throw new Error(`tools/list failed: ${listed.payload.error.message}`);
  }

  const result = listed.payload?.result as { tools?: McpTool[] } | undefined;
  if (!result?.tools) throw new Error('tools/list returned no tools array.');
  return result.tools;
}

export interface ToolProbe {
  ok: boolean;
  detail: string;
  latencyMs: number;
  count?: number;
}

export async function probeMcp(): Promise<ToolProbe> {
  const started = performance.now();
  try {
    const tools = await fetchLiveTools();
    return {
      ok: true,
      detail: `Handshake succeeded — ${tools.length} tools listed.`,
      latencyMs: Math.round(performance.now() - started),
      count: tools.length,
    };
  } catch (err) {
    return {
      ok: false,
      detail: err instanceof Error ? err.message : 'Unreachable.',
      latencyMs: Math.round(performance.now() - started),
    };
  }
}

/* --------------------------------------------------------------- read side */

export async function loadTools(): Promise<Loaded<ToolEntry[]>> {
  const started = performance.now();
  try {
    const live = await fetchLiveTools();
    if (!live.length) throw new Error('The server reported an empty tool list.');
    return {
      data: toEntries(live),
      source: 'live',
      at: new Date().toISOString(),
      latencyMs: Math.round(performance.now() - started),
    };
  } catch (err) {
    return {
      data: toEntries(capture),
      source: 'snapshot',
      at: SNAPSHOT_META.capturedAt,
      note:
        `Live handshake failed (${err instanceof Error ? err.message : 'unknown'}). ` +
        `Showing the tools/list capture taken ${SNAPSHOT_META.capturedAt.slice(0, 10)} from ${SNAPSHOT_META.capturedFrom}.`,
    };
  }
}

/* ------------------------------------------------------------- filtering */

export interface ToolFilter {
  query?: string;
  domain?: string;
  /** Only tools that require at least one argument. */
  requiresArgs?: boolean;
}

export function filterTools(tools: ToolEntry[], filter: ToolFilter): ToolEntry[] {
  const q = (filter.query ?? '').trim().toLowerCase();
  return tools.filter((t) => {
    if (filter.domain && t.domain !== filter.domain) return false;
    if (filter.requiresArgs && t.required.length === 0) return false;
    if (!q) return true;
    return (
      t.name.toLowerCase().includes(q) ||
      (t.title ?? '').toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.required.some((p) => p.toLowerCase().includes(q))
    );
  });
}

/** Totals for the header strip — computed once, from the real list. */
export function toolStats(tools: ToolEntry[]) {
  const domains = new Set(tools.map((t) => t.domain));
  return {
    total: tools.length,
    domains: domains.size,
    memoryTools: tools.filter((t) => t.domain === 'memory').length,
    withParams: tools.filter((t) => t.paramCount > 0).length,
    params: tools.reduce((n, t) => n + t.paramCount, 0),
  };
}
