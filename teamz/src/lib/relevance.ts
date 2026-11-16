import type { Agent, Conversation } from '../types';

function norm(s: string): string {
  return (s || '')
    .toLowerCase()
    .replace(/[^a-z0-9\s+#./-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function tokens(s: string): string[] {
  const n = norm(s);
  if (!n) return [];
  return n.split(' ').filter((t) => t.length >= 2);
}

const INTENT_KEYWORDS: Array<{ test: RegExp; keys: string[]; weight: number }> = [
  { test: /\b(code|bug|fix|implement|api|typescript|javascript|react|frontend|backend|server|database|sql|test|build|deploy|refactor|function|class|error|stack)\b/i, keys: ['engineer', 'developer', 'frontend', 'backend', 'software', 'typescript', 'react', 'api', 'coding', 'debug'], weight: 3 },
  { test: /\b(design|ui|ux|layout|color|spacing|typography|visual|mockup|wireframe|accessible|contrast|figma)\b/i, keys: ['design', 'designer', 'ux', 'ui', 'visual', 'accessibility'], weight: 3 },
  { test: /\b(research|source|cite|evidence|compare|investigate|find|analy[sz]e|study|paper)\b/i, keys: ['research', 'researcher', 'analyst', 'scout', 'sourcing', 'synthesis'], weight: 3 },
  { test: /\b(write|edit|copy|draft|rewrite|summari[sz]e|document|docs|tone|grammar|blog|article)\b/i, keys: ['writer', 'editor', 'copy', 'content', 'sage', 'documentation'], weight: 3 },
  { test: /\b(plan|roadmap|prioriti[sz]e|strategy|organize|coordinate|delegate|assign|manage|schedule|task|project)\b/i, keys: ['lead', 'manager', 'pm', 'planner', 'orchestrat', 'coordinator', 'strategy'], weight: 3 },
  { test: /\b(create|make|add|remove|delete|update|program|configure|channel|agent|team|runtime|workflow)\b/i, keys: ['lead', 'orchestrat', 'manager', 'admin', 'runtime', 'ops'], weight: 4 },
  { test: /\b(data|chart|metric|dashboard|analytics|sql|report|numbers|trend)\b/i, keys: ['data', 'analyst', 'analytics', 'metrics'], weight: 3 },
  { test: /\b(security|auth|permission|secret|vulnerability|threat)\b/i, keys: ['security', 'secure', 'auth'], weight: 3 },
  { test: /\b(test|qa|quality|regression|verify)\b/i, keys: ['test', 'qa', 'quality'], weight: 2 },
];

function agentHaystack(agent: Agent): string {
  const parts = [
    agent.name,
    agent.model,
    agent.systemPrompt,
    agent.origin?.role ?? '',
    ...(agent.skills ?? []).map((s) => `${s.key} ${s.label}`),
  ];
  return norm(parts.join(' '));
}

export function scoreAgentRelevance(message: string, agent: Agent, conversation?: Conversation | null): number {
  const msg = norm(message);
  if (!msg) return 0;
  const msgTokens = new Set(tokens(message));
  const hay = agentHaystack(agent);
  let score = 0;

  // Token overlap
  for (const t of msgTokens) {
    if (t.length < 3) continue;
    if (hay.includes(t)) score += 1.2;
    if (norm(agent.name).includes(t)) score += 2.5;
    if (norm(agent.origin?.role ?? '').includes(t)) score += 2.2;
  }

  // Intent keyword boosts
  for (const intent of INTENT_KEYWORDS) {
    if (!intent.test.test(message)) continue;
    for (const k of intent.keys) {
      if (hay.includes(k)) score += intent.weight;
    }
  }

  // Lead/orchestrator affinity for control requests
  if (/\b(create|make|add|remove|delete|program|configure|orchestrate|delegate|channel|agent|runtime)\b/i.test(message)) {
    if (/\b(lead|orchestr|manager|coordinator|chief|captain)\b/i.test(hay) || /lead|orchestr/i.test(norm(agent.name))) {
      score += 5;
    }
  }

  // Slight boost for online/available agents, small penalty for offline
  if (agent.status === 'online') score += 0.2;
  if (agent.status === 'busy') score += 0.1;
  if (agent.status === 'offline') score -= 0.1;

  // Topic/context hint
  if (conversation?.topic) {
    const topic = norm(conversation.topic);
    for (const t of tokens(topic)) {
      if (t.length >= 3 && hay.includes(t)) score += 0.6;
    }
  }

  return score;
}

export interface RelevanceOptions {
  minResponders?: number;
  maxResponders?: number;
  alwaysIncludeLead?: boolean;
}

export function selectRelevantAgents(
  message: string,
  members: Agent[],
  conversation?: Conversation | null,
  options: RelevanceOptions = {},
): Agent[] {
  if (members.length === 0) return [];
  if (members.length === 1) return [members[0]];

  const minResponders = Math.max(1, options.minResponders ?? 1);
  const maxResponders = Math.max(minResponders, Math.min(options.maxResponders ?? 3, members.length));

  const scored = members
    .map((agent) => ({ agent, score: scoreAgentRelevance(message, agent, conversation) }))
    .sort((a, b) => b.score - a.score || a.agent.name.localeCompare(b.agent.name));

  const bestScore = scored[0]?.score ?? 0;
  // If everything scores ~0, fall back to a sensible default: prefer lead/manager-like agents else first member(s)
  const allLow = bestScore < 1.2;
  let selected: Agent[] = [];

  if (allLow) {
    const leadish = scored.filter(({ agent }) => /lead|orchestr|manager|coordinator|chief|captain/i.test(`${agent.name} ${agent.origin?.role ?? ''} ${agent.systemPrompt ?? ''}`));
    if (leadish.length > 0) {
      selected = leadish.slice(0, Math.min(2, maxResponders)).map((s) => s.agent);
    } else {
      selected = scored.slice(0, minResponders).map((s) => s.agent);
    }
  } else {
    // Take agents with meaningful score; keep within maxResponders
    const threshold = Math.max(1.5, bestScore * 0.45);
    selected = scored.filter((s) => s.score >= threshold).slice(0, maxResponders).map((s) => s.agent);
    if (selected.length < minResponders) {
      for (const s of scored) {
        if (!selected.find((a) => a.id === s.agent.id)) selected.push(s.agent);
        if (selected.length >= minResponders) break;
      }
    }
  }

  // Ensure at least one
  if (selected.length === 0) selected = [scored[0].agent];
  return selected;
}
