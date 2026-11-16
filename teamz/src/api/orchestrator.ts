import type { Agent, Message } from '../types';
import { getSettings, saveSettings, type LlmSettings, type RoutingMeta } from './settings';
import { windowHistory } from './agents';

export interface OrchestratorContext {
  conversationKind?: 'direct' | 'channel';
  conversationName?: string;
  topic?: string;
  otherAgents?: { id: string; name: string }[];
  directed?: boolean;
  conversationId?: string;
  workspace?: {
    agents?: any[];
    conversations?: any[];
  };
}

export interface OrchestratorChatResult {
  text: string;
  routing?: RoutingMeta | null;
  usage?: { prompt_tokens?: number | null; completion_tokens?: number | null; total_tokens?: number | null } | null;
  provider?: string | null;
  model?: string | null;
}

function baseUrl(settings: Pick<LlmSettings, 'orchestratorUrl'>): string {
  return (settings.orchestratorUrl || 'http://localhost:8787').replace(/\/+$/, '');
}

function headers(settings: Pick<LlmSettings, 'orchestratorToken'>): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (settings.orchestratorToken?.trim()) h.Authorization = `Bearer ${settings.orchestratorToken.trim()}`;
  return h;
}

export function buildOrchestratorMessages(
  agent: Agent,
  history: Message[],
  agentsById: Map<string, Agent>,
  ctx: OrchestratorContext,
): Array<{ role: 'system' | 'user' | 'assistant'; content: string }> {
  const isChannel = ctx.conversationKind === 'channel';
  const systemParts: string[] = [];
  systemParts.push(agent.systemPrompt?.trim() || `You are ${agent.name}, a helpful AI agent.`);
  const facts: string[] = [`Your name is ${agent.name}.`];
  if (agent.origin?.role) facts.push(`Your role: ${agent.origin.role}.`);
  if (agent.skills?.length) {
    facts.push(`Skills: ${agent.skills.slice().sort((a, b) => b.level - a.level).slice(0, 8).map((s) => `${s.label} (L${s.level})`).join(', ')}.`);
  }
  if (isChannel) {
    facts.push(
      `You are in a group chat channel called "${ctx.conversationName ?? 'channel'}"` +
        (ctx.topic ? ` (topic: ${ctx.topic})` : '') +
        '.',
    );
    if (ctx.otherAgents?.length) facts.push(`Other agents present: ${ctx.otherAgents.map((a) => a.name).join(', ')}.`);
    facts.push('Messages from other participants are prefixed with their name in square brackets. Reply only as yourself.');
    if (ctx.directed) facts.push('The user addressed you directly; answer their latest message.');
  } else {
    facts.push('You are in a private one-to-one chat with the user.');
  }
  facts.push('Use conversation context and memory-aware reasoning when relevant. Keep replies clear and useful.');
  systemParts.push(facts.join('\n'));

  const out: Array<{ role: 'system' | 'user' | 'assistant'; content: string }> = [
    { role: 'system', content: systemParts.join('\n\n') },
  ];
  const usable = windowHistory(history).filter((m) => m.status === 'sent' && m.text.trim() && !m.unsent && !m.deleted);
  for (const m of usable) {
    if (m.authorType === 'agent' && m.authorId === agent.id) {
      out.push({ role: 'assistant', content: m.text });
      continue;
    }
    const speaker = m.authorType === 'user' ? 'User' : agentsById.get(m.authorId ?? '')?.name ?? 'Another agent';
    out.push({ role: 'user', content: isChannel || m.authorType === 'agent' ? `[${speaker}]: ${m.text}` : m.text });
  }
  return out;
}

function recordRouting(meta: RoutingMeta | null | undefined, usage?: OrchestratorChatResult['usage'], provider?: string | null, model?: string | null) {
  const current = getSettings();
  saveSettings({
    ...current,
    lastRouting: meta ?? null,
    lastUsage: usage ?? meta?.attempts?.find((a) => a.status === 'success')?.usage ?? null,
    lastProvider: provider ?? meta?.selected_provider ?? null,
    lastModel: model ?? meta?.selected_model ?? null,
    lastUpdatedAt: Date.now(),
  });
}

async function readError(res: Response): Promise<string> {
  try {
    const text = await res.text();
    try {
      const j = JSON.parse(text);
      return j?.detail || j?.error?.message || j?.error || j?.message || text || `${res.status}`;
    } catch {
      return text || `${res.status}`;
    }
  } catch {
    return `${res.status}`;
  }
}

export async function callOrchestratorChat(
  agent: Agent,
  history: Message[],
  agentsById: Map<string, Agent>,
  ctx: OrchestratorContext,
  opts: { signal?: AbortSignal; onDelta?: (fullText: string) => void } = {},
): Promise<OrchestratorChatResult> {
  const settings = getSettings();
  const url = `${baseUrl(settings)}/v1/chat/completions`;
  const body = {
    model: agent.model || settings.model || undefined,
    stream: settings.stream,
    messages: buildOrchestratorMessages(agent, history, agentsById, ctx),
    agent: {
      id: agent.id,
      name: agent.name,
      model: agent.model,
      systemPrompt: agent.systemPrompt,
      skills: agent.skills,
      origin: agent.origin,
      isLead: (agent as any).isLead || false,
    },
    conversation: {
      id: ctx.conversationId,
      name: ctx.conversationName,
      kind: ctx.conversationKind,
      topic: ctx.topic,
      directed: ctx.directed,
      otherAgents: ctx.otherAgents ?? [],
    },
    metadata: ctx.workspace ? { workspace: ctx.workspace } : undefined,
  };

  const res = await fetch(url, {
    method: 'POST',
    headers: headers(settings),
    body: JSON.stringify(body),
    signal: opts.signal,
  });
  if (!res.ok) {
    throw new Error(await readError(res));
  }

  const ct = res.headers.get('content-type') ?? '';
  if (settings.stream && ct.includes('text/event-stream') && res.body) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let full = '';
    let routing: RoutingMeta | null = null;
    let usage: OrchestratorChatResult['usage'] = null;
    let provider: string | null = null;
    let model: string | null = null;
    let errorMsg: string | null = null;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const rawEvent = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const lines = rawEvent.split(/\r?\n/);
        let eventName = 'message';
        const dataLines: string[] = [];
        for (const line of lines) {
          if (line.startsWith('event:')) eventName = line.slice(6).trim();
          else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
        }
        const dataStr = dataLines.join('\n');
        if (!dataStr) continue;
        if (dataStr === '[DONE]') {
          continue;
        }
        let payload: any = null;
        try { payload = JSON.parse(dataStr); } catch { payload = null; }
        if (!payload) continue;

        if (eventName === 'meta' || payload.type === 'meta') {
          if (payload.attempts || payload.selected_provider || payload.routing) {
            routing = (payload.routing ?? payload) as RoutingMeta;
          }
        } else if (eventName === 'error' || payload.type === 'error') {
          errorMsg = payload.error || 'Orchestrator stream error';
        } else if (eventName === 'done' || payload.type === 'done') {
          if (typeof payload.text === 'string') full = payload.text || full;
          routing = (payload.routing ?? routing) as RoutingMeta | null;
          usage = payload.usage ?? usage;
          provider = payload.provider ?? routing?.selected_provider ?? provider;
          model = payload.model ?? routing?.selected_model ?? model;
        } else {
          // delta chunk (OpenAI-style or custom)
          const delta = payload?.choices?.[0]?.delta?.content ?? payload?.delta ?? '';
          if (typeof delta === 'string' && delta) {
            full += delta;
            opts.onDelta?.(full);
          }
          provider = payload?.provider ?? provider;
          model = payload?.model ?? model;
        }
      }
    }
    if (errorMsg) throw new Error(errorMsg);
    if (!full.trim()) throw new Error('Orchestrator returned an empty reply.');
    recordRouting(routing, usage, provider, model);
    return { text: full, routing, usage, provider, model };
  }

  const payload = ct.includes('application/json') ? await res.json() : await res.text();
  const text =
    typeof payload === 'string'
      ? payload
      : payload?.choices?.[0]?.message?.content ?? payload?.text ?? payload?.reply ?? '';
  if (typeof text !== 'string' || !text.trim()) throw new Error('Orchestrator returned an empty reply.');
  const routing = (payload?.routing ?? null) as RoutingMeta | null;
  const usage = payload?.usage ?? null;
  const provider = payload?.routing?.selected_provider ?? null;
  const model = payload?.model ?? payload?.routing?.selected_model ?? null;
  recordRouting(routing, usage, provider, model);
  return { text, routing, usage, provider, model };
}

export async function pingOrchestrator(): Promise<{ ok: boolean; latencyMs: number; message: string; status?: any }> {
  const settings = getSettings();
  const started = performance.now();
  try {
    const res = await fetch(`${baseUrl(settings)}/health`, { headers: headers(settings) });
    const latencyMs = Math.round(performance.now() - started);
    const status = await res.json().catch(() => null);
    if (!res.ok) return { ok: false, latencyMs, message: `Orchestrator ${res.status}`, status };
    return { ok: true, latencyMs, message: `Orchestrator healthy · ${status?.providers?.length ?? 0} providers`, status };
  } catch (err) {
    return { ok: false, latencyMs: Math.round(performance.now() - started), message: err instanceof Error ? err.message : 'Request failed' };
  }
}

export async function optimizePromptWithOrchestrator(input: {
  draft: string;
  conversation?: any;
  history?: Array<{ role?: string; authorType?: string; authorName?: string; name?: string; text?: string; content?: string }>;
  agents?: any[];
  goal?: string;
  useMemory?: boolean;
}): Promise<{ prompt: string; original: string; memories_used?: any[]; routing?: RoutingMeta | null }> {
  const settings = getSettings();
  const res = await fetch(`${baseUrl(settings)}/v1/optimize-prompt`, {
    method: 'POST',
    headers: headers(settings),
    body: JSON.stringify({
      draft: input.draft,
      conversation: input.conversation,
      history: input.history ?? [],
      agents: input.agents ?? [],
      goal: input.goal,
      use_memory: input.useMemory ?? true,
    }),
  });
  if (!res.ok) throw new Error(await readError(res));
  const data = await res.json();
  if (data?.routing) recordRouting(data.routing, null, data.routing.selected_provider, data.routing.selected_model);
  return data;
}
