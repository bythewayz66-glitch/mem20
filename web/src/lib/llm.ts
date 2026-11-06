/* The ONE place in the shell that talks to a language model.
 *
 * Ported from mem20agentz/web/src/lib/llm.js, which is the pattern already
 * proven live on the deployed OREO editor. Three modes, chosen by
 * VITE_LLM_MODE:
 *
 *   pollinations (default) - a REAL LLM with no API key and no server of your
 *                            own. The browser POSTs an OpenAI-compatible chat
 *                            body straight to a public endpoint. This is what
 *                            the deployed build runs.
 *
 *   live                   - POSTs to VITE_LLM_ENDPOINT, for an endpoint you
 *                            host yourself (a proxy, a gateway, a local model).
 *
 *   mock                   - no network at all. Deterministic replies, used by
 *                            tests and by anyone who wants the UI offline.
 *                            Never silently substituted for a real call: the
 *                            mode is always rendered in the UI.
 *
 * Honesty rules carried over from the rest of mem20:
 *   - A failed call throws. It never returns a plausible-looking string.
 *   - A rate limit is named as a rate limit, not as a generic error.
 *   - The mode is rendered in the UI, so "mock" can never masquerade as real.
 *
 * Why this lives in web/ and not in a new organ: the shell is the product's
 * one front door, and a second LLM client would be a second thing to keep
 * honest. There is exactly one.
 */

export type LlmMode = 'pollinations' | 'live' | 'mock';

export const LLM_MODE: LlmMode = (() => {
  const raw = (import.meta.env && import.meta.env.VITE_LLM_MODE) || 'pollinations';
  return raw === 'live' || raw === 'mock' ? raw : 'pollinations';
})();

/** Keyless OpenAI-compatible endpoint used by `pollinations` mode. */
export const LLM_ENDPOINT =
  (import.meta.env && import.meta.env.VITE_LLM_ENDPOINT) ||
  'https://text.pollinations.ai/openai';

/** Model used by `pollinations` mode. `openai-fast` is the anonymous tier. */
export const LLM_MODEL =
  (import.meta.env && import.meta.env.VITE_LLM_MODEL) || 'openai-fast';

/** A human label for the mode, for the UI. Never says "live" for mock. */
export function modeLabel(): string {
  if (LLM_MODE === 'mock') return 'MOCK - no network';
  if (LLM_MODE === 'live') return 'LIVE - your endpoint';
  return `REAL LLM - ${LLM_MODEL.toUpperCase()} - KEYLESS`;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

/* ------------------------------------------------------------------- parse */

/**
 * Pull the reply text out of a completion payload.
 *
 * Covers the OpenAI shape, the plain-string shape, and the Anthropic block
 * shape. Throws rather than returning '' - an empty reply is a bug, not a
 * message.
 */
export function parseCompletion(payload: unknown): string {
  if (typeof payload === 'string') {
    const t = payload.trim();
    if (!t) throw new Error('The model returned an empty response.');
    return t;
  }
  if (!payload || typeof payload !== 'object') {
    throw new Error('The model returned a non-JSON response.');
  }
  const p = payload as Record<string, any>;

  const choice = p.choices?.[0]?.message?.content;
  if (typeof choice === 'string' && choice.trim()) return choice.trim();

  for (const key of ['reply', 'text', 'message', 'content', 'output']) {
    if (typeof p[key] === 'string' && p[key].trim()) return p[key].trim();
  }
  if (p.delta && typeof p.delta.content === 'string' && p.delta.content.trim()) {
    return p.delta.content.trim();
  }
  if (Array.isArray(p.content)) {
    const block = p.content.find((b: any) => b && typeof b.text === 'string');
    if (block) return String(block.text).trim();
  }

  throw new Error('Could not find reply text in the model response.');
}

/* ------------------------------------------------------------------- error */

/**
 * Turn a non-2xx body into a sentence a user can act on.
 *
 * The anonymous tier answers 402 with `{ error: { code: "FREE_LIMIT" } }` when
 * its budget is spent. That is the case worth naming precisely, because the
 * fix is "wait 30 seconds", not "the app is broken".
 */
export function describeError(status: number, body: string): string {
  let code = '';
  let message = '';
  try {
    const parsed = JSON.parse(body);
    code = parsed?.error?.code || '';
    message = parsed?.error?.message || '';
  } catch {
    /* not JSON - fall through to the status-based text */
  }

  if (code === 'FREE_LIMIT' || status === 402) {
    return 'The free LLM tier is rate-limited (about one reply every 30 seconds). Wait a moment and send again, or point this shell at your own endpoint with VITE_LLM_MODE=live.';
  }
  if (status === 429) {
    return 'The LLM endpoint is rate-limiting this browser. Wait a moment and send again.';
  }
  if (status === 401 || status === 403) {
    return `The LLM endpoint refused this request (${status}). The keyless tier may be closed to this origin.`;
  }
  return message || `The LLM endpoint replied ${status}.`;
}

/* --------------------------------------------------------------- transports */

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Deterministic reply - no network. Used by tests and mock mode. */
export function mockReply(prompt: string): string {
  const topic = (prompt || '').trim().slice(0, 80) || 'that';
  return `[mock] received: "${topic}". Set VITE_LLM_MODE=pollinations for a real answer.`;
}

export interface CompleteOptions {
  system?: string;
  signal?: AbortSignal;
  /** Override the model for this one call. */
  model?: string;
  /** Cap on generated tokens, when the endpoint honours it. */
  maxTokens?: number;
}

/**
 * One completion. Throws on failure - never returns a fabricated reply.
 *
 * `messages` is the full chat array; callers that only have a single prompt
 * should use `ask()` below.
 */
export async function complete(
  messages: ChatMessage[],
  options: CompleteOptions = {},
): Promise<string> {
  if (LLM_MODE === 'mock') {
    await sleep(120);
    const last = [...messages].reverse().find((m) => m.role === 'user');
    return mockReply(last ? last.content : '');
  }

  const endpoint = LLM_MODE === 'live' ? LLM_ENDPOINT : LLM_ENDPOINT;
  const body: Record<string, unknown> = {
    model: options.model || LLM_MODEL,
    messages,
  };
  if (options.maxTokens) body.max_tokens = options.maxTokens;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(describeError(res.status, detail));
  }
  return parseCompletion(await res.json());
}

/** Single-prompt convenience wrapper. */
export async function ask(prompt: string, options: CompleteOptions = {}): Promise<string> {
  const messages: ChatMessage[] = [];
  if (options.system) messages.push({ role: 'system', content: options.system });
  messages.push({ role: 'user', content: prompt });
  return complete(messages, options);
}

/* -------------------------------------------------------------------- ping */

export interface PingResult {
  ok: boolean;
  latencyMs: number;
  message: string;
  /** The model the endpoint actually reported, when it reports one. */
  model?: string;
}

/**
 * Reachability probe for the settings panel's "Test" button.
 *
 * Returns the endpoint's own reported model name when it gives one, so the UI
 * can show what actually answered rather than what was requested.
 */
export async function ping(): Promise<PingResult> {
  const started = Date.now();
  if (LLM_MODE === 'mock') {
    await sleep(80);
    return { ok: true, latencyMs: Date.now() - started, message: 'Mock mode - no network.' };
  }
  try {
    const res = await fetch(LLM_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: LLM_MODEL,
        messages: [{ role: 'user', content: 'Reply with the single word: ready' }],
      }),
    });
    const latencyMs = Date.now() - started;
    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      return { ok: false, latencyMs, message: describeError(res.status, detail) };
    }
    const payload = await res.json().catch(() => null);
    const model = payload && typeof payload === 'object' ? (payload as any).model : undefined;
    return {
      ok: true,
      latencyMs,
      model: typeof model === 'string' ? model : undefined,
      message: `Reachable - ${model || LLM_MODEL} (${res.status})`,
    };
  } catch (err) {
    return {
      ok: false,
      latencyMs: Date.now() - started,
      message: err instanceof Error ? err.message : 'Request failed',
    };
  }
}
