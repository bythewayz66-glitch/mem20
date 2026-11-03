/* OREO editor LLM transport — the ONE place that talks to a model.
 *
 * Three modes, chosen by VITE_LLM_MODE:
 *
 *   pollinations (default) — a REAL LLM with no API key and no server of your
 *                            own. The browser POSTs an OpenAI-compatible chat
 *                            body straight to a public endpoint. This is what
 *                            the deployed build runs.
 *
 *   live                   — POSTs to `agent.endpointUrl`, for agents you host
 *                            yourself.
 *
 *   mock                   — no network at all. Deterministic persona replies,
 *                            used by tests and by anyone who wants the UI
 *                            offline. Never silently substituted for a real
 *                            call: the mode is always shown in the UI.
 *
 * Honesty rules carried over from the rest of mem20:
 *   • A failed call throws. It never returns a plausible-looking string.
 *   • A rate limit is named as a rate limit, not as a generic error.
 *   • The mode is rendered in the UI, so "mock" can never masquerade as real.
 */

export const LLM_MODE =
  (import.meta.env && import.meta.env.VITE_LLM_MODE) || 'pollinations';

/** Keyless OpenAI-compatible endpoint used by `pollinations` mode. */
export const LLM_ENDPOINT =
  (import.meta.env && import.meta.env.VITE_LLM_ENDPOINT) ||
  'https://text.pollinations.ai/openai';

/** Model used by `pollinations` mode. `openai-fast` is the anonymous tier. */
export const LLM_MODEL =
  (import.meta.env && import.meta.env.VITE_LLM_MODEL) || 'openai-fast';

/* ------------------------------------------------------------------ prompt */

/**
 * Build the OpenAI chat array for one agent turn.
 *
 * Two things matter here and both are easy to get wrong:
 *
 *  1. Another agent's turn is CONTEXT, not this agent's own words. It is
 *     labelled `[Name] …` so the model does not read the room as its own
 *     monologue and start answering itself.
 *  2. The room roster goes in the system preamble, so an agent knows who else
 *     is present and can hand off by name instead of guessing.
 */
export function buildMessages(agent, history, agentsById, options = {}) {
  const turns = [];

  const preamble = [];
  if (agent.systemPrompt && agent.systemPrompt.trim()) {
    preamble.push(agent.systemPrompt.trim());
  }
  if (options.roomMembers && options.roomMembers.length > 0) {
    preamble.push(
      `You are in a shared channel with: ${options.roomMembers.join(', ')}. ` +
        `Messages from other agents are prefixed with their name in brackets. ` +
        `Answer as ${agent.name} only — never write another agent's turn.`,
    );
  }
  if (options.directed) {
    preamble.push('The user addressed you directly with an @mention. Answer this one.');
  }
  if (preamble.length > 0) {
    turns.push({ role: 'system', content: preamble.join('\n\n') });
  }

  for (const m of history) {
    if (m.authorType === 'user') {
      turns.push({ role: 'user', content: m.text });
    } else {
      const name = m.authorId ? (agentsById.get(m.authorId) || {}).name : undefined;
      turns.push({
        role: 'assistant',
        content: name ? `[${name}] ${m.text}` : m.text,
      });
    }
  }

  return turns;
}

/* ------------------------------------------------------------------- parse */

/**
 * Pull the reply text out of a completion payload.
 *
 * Covers the OpenAI shape, the plain-string shape, and the Anthropic block
 * shape. Throws rather than returning '' — an empty reply is a bug, not a
 * message.
 */
export function parseCompletion(payload) {
  if (typeof payload === 'string') {
    const t = payload.trim();
    if (!t) throw new Error('The model returned an empty response.');
    return t;
  }
  if (!payload || typeof payload !== 'object') {
    throw new Error('The model returned a non-JSON response.');
  }
  const p = payload;

  const choice = p.choices && p.choices[0] && p.choices[0].message && p.choices[0].message.content;
  if (typeof choice === 'string' && choice.trim()) return choice.trim();

  for (const key of ['reply', 'text', 'message', 'content', 'output']) {
    if (typeof p[key] === 'string' && p[key].trim()) return p[key].trim();
  }
  if (p.delta && typeof p.delta.content === 'string' && p.delta.content.trim()) {
    return p.delta.content.trim();
  }
  if (Array.isArray(p.content)) {
    const block = p.content.find((b) => b && typeof b.text === 'string');
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
export function describeError(status, body) {
  let code = '';
  let message = '';
  try {
    const parsed = JSON.parse(body);
    code = (parsed.error && parsed.error.code) || '';
    message = (parsed.error && parsed.error.message) || '';
  } catch {
    /* not JSON — fall through to the status-based text */
  }

  if (code === 'FREE_LIMIT' || status === 402) {
    return 'The free LLM tier is rate-limited (about one reply every 30 seconds). Wait a moment and send again, or point this agent at your own endpoint.';
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

async function callPollinations(agent, history, agentsById, options) {
  const res = await fetch(LLM_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: agent.model || LLM_MODEL,
      messages: buildMessages(agent, history, agentsById, options),
    }),
    signal: options.signal,
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(describeError(res.status, detail));
  }
  return parseCompletion(await res.json());
}

async function callLive(agent, history, agentsById, options) {
  const endpoint = agent.endpointUrl && agent.endpointUrl.trim();
  if (!endpoint) {
    throw new Error(`${agent.name} has no endpoint URL. Add one in its settings.`);
  }

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent: {
        id: agent.id,
        name: agent.name,
        model: agent.model,
        systemPrompt: agent.systemPrompt,
      },
      messages: buildMessages(agent, history, agentsById, options),
      directed: options.directed || false,
    }),
    signal: options.signal,
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(
      `${agent.name} replied ${res.status} ${res.statusText}${detail ? ` — ${detail.slice(0, 240)}` : ''}`,
    );
  }

  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return parseCompletion(await res.json());
  const text = (await res.text()).trim();
  if (!text) throw new Error(`${agent.name} returned an empty body.`);
  return text;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Deterministic persona reply — no network. Used by tests and mock mode. */
export function mockReply(agent, lastUserText) {
  const topic = (lastUserText || '').trim().slice(0, 80) || 'that';
  return `[mock] ${agent.name} received: "${topic}". Set VITE_LLM_MODE=pollinations for a real answer.`;
}

async function callMock(agent, history) {
  await sleep(120);
  const lastUser = [...history].reverse().find((m) => m.authorType === 'user');
  return mockReply(agent, lastUser ? lastUser.text : '');
}

/* -------------------------------------------------------------- public API */

/** One agent turn. Throws on failure — never returns a fabricated reply. */
export async function complete(agent, history, agentsById, options = {}) {
  if (LLM_MODE === 'live') return callLive(agent, history, agentsById, options);
  if (LLM_MODE === 'mock') return callMock(agent, history);
  return callPollinations(agent, history, agentsById, options);
}

/** Reachability probe for the settings panel's "Test" button. */
export async function ping() {
  const started = Date.now();
  if (LLM_MODE === 'mock') {
    await sleep(80);
    return { ok: true, latencyMs: Date.now() - started, message: 'Mock mode — no network.' };
  }
  if (LLM_MODE === 'live') {
    return {
      ok: false,
      latencyMs: 0,
      message: 'Live mode probes each agent endpoint, not a shared one.',
    };
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
    if (res.ok) {
      return { ok: true, latencyMs, message: `Reachable — ${LLM_MODEL} (${res.status})` };
    }
    const detail = await res.text().catch(() => '');
    return { ok: false, latencyMs, message: describeError(res.status, detail) };
  } catch (err) {
    return {
      ok: false,
      latencyMs: Date.now() - started,
      message: err instanceof Error ? err.message : 'Request failed',
    };
  }
}
