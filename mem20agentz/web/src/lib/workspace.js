/* OREO workspace store — pure state logic, no React, no DOM.
 *
 * Everything that decides WHAT the workspace shows lives here so it can be
 * unit-tested without a browser. The React layer only renders what these
 * functions return.
 *
 * Persistence is localStorage under one key. It is per-browser: two tabs
 * overwrite each other, and the UI says so rather than pretending otherwise.
 */

export const STORAGE_KEY = 'mem20agentz.oreo.workspace.v1';

/* --------------------------------------------------------------- defaults */

export const DEFAULT_AGENTS = [
  {
    id: 'atlas',
    name: 'Atlas',
    emoji: '🧭',
    color: '#6366f1',
    model: 'openai-fast',
    systemPrompt:
      'You are Atlas, the architect agent in a mem20 OREO workspace. You reason about system structure, memory graphs, and how components connect. Be concrete and brief.',
  },
  {
    id: 'pixel',
    name: 'Pixel',
    emoji: '🎨',
    color: '#ec4899',
    model: 'openai-fast',
    systemPrompt:
      'You are Pixel, the interface agent in a mem20 OREO workspace. You care about how humans see and use the graph. Be concrete and brief.',
  },
  {
    id: 'ledger',
    name: 'Ledger',
    emoji: '🔒',
    color: '#22c55e',
    model: 'openai-fast',
    systemPrompt:
      'You are Ledger, the trust agent in a mem20 OREO workspace. You care about provenance, append-only integrity, and what can be proven. Be concrete and brief.',
  },
];

export const DEFAULT_CHANNELS = [
  { id: 'general', name: 'general', topic: 'Everything about the OREO graph' },
  { id: 'graph', name: 'graph', topic: 'Nodes, relationships, and the memory model' },
  { id: 'trust', name: 'trust', topic: 'Provenance and auditability' },
];

/* ------------------------------------------------------------------ ids */

let seq = 0;
/** Monotonic id. Deterministic within a session; unique across reloads. */
export function nextId(prefix = 'm') {
  seq += 1;
  return `${prefix}_${Date.now().toString(36)}_${seq}`;
}

/* ------------------------------------------------------------- factories */

export function createMessage({ channelId, authorType, authorId, text, quote }) {
  return {
    id: nextId('msg'),
    channelId,
    authorType,
    authorId: authorId || null,
    text: String(text || ''),
    quote: quote || null,
    attachments: [],
    at: Date.now(),
  };
}

export function createTask({ channelId, title, assigneeId, createdBy = 'user' }) {
  return {
    id: nextId('task'),
    channelId,
    title: String(title || '').trim(),
    assigneeId: assigneeId || null,
    status: 'open',
    continuations: 0,
    createdBy,
    at: Date.now(),
  };
}

export function createTrigger({ channelId, agentId, prompt, everyMs }) {
  return {
    id: nextId('trg'),
    channelId,
    agentId,
    prompt: String(prompt || '').trim(),
    everyMs: Number(everyMs) || 60000,
    lastRunAt: null,
    enabled: true,
  };
}

export function createMemory({ text, source = 'user', channelId = null }) {
  return {
    id: nextId('mem'),
    text: String(text || '').trim(),
    source,
    channelId,
    at: Date.now(),
  };
}

/* ------------------------------------------------------------ initial state */

export function initialState() {
  return {
    agents: DEFAULT_AGENTS.map((a) => ({ ...a })),
    channels: DEFAULT_CHANNELS.map((c) => ({ ...c })),
    messages: [],
    tasks: [],
    triggers: [],
    memory: [],
    activeChannelId: 'general',
    readAt: {},
    llmMode: null,
  };
}

/* --------------------------------------------------------------- selectors */

export function messagesFor(state, channelId) {
  return state.messages.filter((m) => m.channelId === channelId);
}

export function tasksFor(state, channelId) {
  return state.tasks.filter((t) => t.channelId === channelId);
}

export function triggersFor(state, channelId) {
  return state.triggers.filter((t) => t.channelId === channelId);
}

export function agentById(state, id) {
  return state.agents.find((a) => a.id === id) || null;
}

/**
 * Unread count for a channel.
 *
 * A channel is unread from the last time the user opened it. Messages the
 * user wrote themselves never count — you do not have unread messages from
 * yourself.
 */
export function unreadCount(state, channelId) {
  const since = state.readAt[channelId] || 0;
  return state.messages.filter(
    (m) => m.channelId === channelId && m.at > since && m.authorType !== 'user',
  ).length;
}

export function totalUnread(state) {
  return state.channels.reduce((n, c) => n + unreadCount(state, c.id), 0);
}

/**
 * Cross-channel search over message text, task titles, and memory.
 * Case-insensitive substring — deliberately simple and predictable.
 */
export function search(state, query) {
  const q = String(query || '').trim().toLowerCase();
  if (!q) return { messages: [], tasks: [], memory: [] };
  const hit = (s) => String(s || '').toLowerCase().includes(q);
  return {
    messages: state.messages.filter((m) => hit(m.text)),
    tasks: state.tasks.filter((t) => hit(t.title)),
    memory: state.memory.filter((m) => hit(m.text)),
  };
}

/**
 * Triggers whose interval has elapsed.
 *
 * `lastRunAt == null` means "never run" and is due immediately. The check is
 * `== null`, NOT falsy: a trigger that last ran at epoch 0 is a real
 * timestamp, and treating it as "never" would fire it on every tick.
 */
export function dueTriggers(state, now = Date.now()) {
  return state.triggers.filter((t) => {
    if (!t.enabled) return false;
    if (t.lastRunAt == null) return true;
    return now - t.lastRunAt >= t.everyMs;
  });
}

/* ---------------------------------------------------------------- reducers */

export function addMessage(state, msg) {
  return { ...state, messages: [...state.messages, msg] };
}

export function addTask(state, task) {
  return { ...state, tasks: [...state.tasks, task] };
}

export function addTrigger(state, trigger) {
  return { ...state, triggers: [...state.triggers, trigger] };
}

export function addMemory(state, mem) {
  return { ...state, memory: [...state.memory, mem] };
}

export function markRead(state, channelId, at = Date.now()) {
  return { ...state, readAt: { ...state.readAt, [channelId]: at } };
}

export function setActiveChannel(state, channelId) {
  return markRead({ ...state, activeChannelId: channelId }, channelId);
}

export function updateAgent(state, id, patch) {
  return {
    ...state,
    agents: state.agents.map((a) => (a.id === id ? { ...a, ...patch } : a)),
  };
}

export function updateTask(state, id, patch) {
  return {
    ...state,
    tasks: state.tasks.map((t) => (t.id === id ? { ...t, ...patch } : t)),
  };
}

export function updateTrigger(state, id, patch) {
  return {
    ...state,
    triggers: state.triggers.map((t) => (t.id === id ? { ...t, ...patch } : t)),
  };
}

/** Advance a task by one continuation turn. Returns the new state. */
export function continueTask(state, id) {
  const task = state.tasks.find((t) => t.id === id);
  if (!task) return state;
  return updateTask(state, id, {
    continuations: task.continuations + 1,
    status: 'in_progress',
  });
}

/* ------------------------------------------------------------ persistence */

export function serialize(state) {
  return JSON.stringify(state);
}

/**
 * Parse persisted state, falling back to a fresh workspace on anything
 * unreadable. A corrupt blob must not brick the app.
 */
export function deserialize(raw) {
  if (!raw) return initialState();
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return initialState();
    const base = initialState();
    return {
      ...base,
      ...parsed,
      agents: Array.isArray(parsed.agents) && parsed.agents.length ? parsed.agents : base.agents,
      channels:
        Array.isArray(parsed.channels) && parsed.channels.length ? parsed.channels : base.channels,
      messages: Array.isArray(parsed.messages) ? parsed.messages : [],
      tasks: Array.isArray(parsed.tasks) ? parsed.tasks : [],
      triggers: Array.isArray(parsed.triggers) ? parsed.triggers : [],
      memory: Array.isArray(parsed.memory) ? parsed.memory : [],
      readAt: parsed.readAt && typeof parsed.readAt === 'object' ? parsed.readAt : {},
    };
  } catch {
    return initialState();
  }
}

export function load() {
  try {
    return deserialize(localStorage.getItem(STORAGE_KEY));
  } catch {
    return initialState();
  }
}

export function save(state) {
  try {
    localStorage.setItem(STORAGE_KEY, serialize(state));
  } catch {
    /* quota or private mode — the app keeps working in memory */
  }
}
