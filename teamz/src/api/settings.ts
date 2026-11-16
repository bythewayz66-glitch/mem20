/**
 * Browser-local LLM settings. Stored in `localStorage` under its own key so a
 * workspace reset never wipes the user's API key, and nothing here is ever
 * bundled into the build or committed.
 */

export type Provider = 'pollinations' | 'custom' | 'mock' | 'orchestrator';

export interface RoutingAttempt {
  provider: string;
  model?: string | null;
  status: string;
  latency_ms?: number | null;
  reason?: string | null;
  error?: string | null;
  usage?: { prompt_tokens?: number | null; completion_tokens?: number | null; total_tokens?: number | null } | null;
  keyless?: boolean | null;
}

export interface RoutingMeta {
  selected_provider?: string | null;
  selected_model?: string | null;
  attempts?: RoutingAttempt[];
  fallback_used?: boolean;
  requested_model?: string | null;
}

export interface LlmSettings {
  provider: Provider;
  /** Empty → the tier's default model. */
  model: string;
  /** Optional Pollinations API key (`sk_…`). Empty → anonymous tier. */
  apiKey: string;
  /** Optional referrer / app name sent to Pollinations. */
  referrer: string;
  /** Stream tokens as they arrive. */
  stream: boolean;
  /** Base URL for the teamz FastAPI orchestrator (provider=orchestrator). */
  orchestratorUrl: string;
  /** Optional bearer token for the orchestrator, if configured. */
  orchestratorToken: string;
  /** Last observed routing/usage metadata (for live provider/usage panel). */
  lastRouting?: RoutingMeta | null;
  lastUsage?: { prompt_tokens?: number | null; completion_tokens?: number | null; total_tokens?: number | null } | null;
  lastProvider?: string | null;
  lastModel?: string | null;
  lastUpdatedAt?: number | null;
}

export const SETTINGS_KEY = 'teamz:llm-settings:v1';

const envMode = (import.meta.env?.VITE_API_MODE as string | undefined) ?? '';
const envOrchestrator = (import.meta.env?.VITE_ORCHESTRATOR_URL as string | undefined) ?? '';

/** `VITE_API_MODE=live` keeps the old custom-endpoint behaviour as the default. */
export const DEFAULT_PROVIDER: Provider =
  envMode === 'live' ? 'custom' : envMode === 'mock' ? 'mock' : envMode === 'orchestrator' ? 'orchestrator' : 'pollinations';

export const DEFAULT_SETTINGS: LlmSettings = {
  provider: DEFAULT_PROVIDER,
  model: '',
  apiKey: '',
  referrer: 'teamz',
  stream: true,
  orchestratorUrl: envOrchestrator || 'http://localhost:8787',
  orchestratorToken: '',
  lastRouting: null,
  lastUsage: null,
  lastProvider: null,
  lastModel: null,
  lastUpdatedAt: null,
};

export function normaliseSettings(raw: unknown): LlmSettings {
  const r = (raw && typeof raw === 'object' ? raw : {}) as Partial<LlmSettings> & Record<string, unknown>;
  const provider: Provider =
    r.provider === 'custom' || r.provider === 'mock' || r.provider === 'pollinations' || r.provider === 'orchestrator'
      ? r.provider
      : DEFAULT_SETTINGS.provider;
  return {
    provider,
    model: typeof r.model === 'string' ? r.model : DEFAULT_SETTINGS.model,
    apiKey: typeof r.apiKey === 'string' ? r.apiKey : '',
    referrer: typeof r.referrer === 'string' ? r.referrer : DEFAULT_SETTINGS.referrer,
    stream: typeof r.stream === 'boolean' ? r.stream : DEFAULT_SETTINGS.stream,
    orchestratorUrl:
      typeof r.orchestratorUrl === 'string' && r.orchestratorUrl.trim()
        ? r.orchestratorUrl
        : DEFAULT_SETTINGS.orchestratorUrl,
    orchestratorToken: typeof r.orchestratorToken === 'string' ? r.orchestratorToken : '',
    lastRouting: (r.lastRouting && typeof r.lastRouting === 'object' ? (r.lastRouting as RoutingMeta) : null) ?? null,
    lastUsage: (r.lastUsage && typeof r.lastUsage === 'object' ? (r.lastUsage as LlmSettings['lastUsage']) : null) ?? null,
    lastProvider: typeof r.lastProvider === 'string' ? r.lastProvider : null,
    lastModel: typeof r.lastModel === 'string' ? r.lastModel : null,
    lastUpdatedAt: typeof r.lastUpdatedAt === 'number' ? r.lastUpdatedAt : null,
  };
}

export function loadSettings(): LlmSettings {
  try {
    const raw = globalThis.localStorage?.getItem(SETTINGS_KEY);
    return normaliseSettings(raw ? JSON.parse(raw) : {});
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

type Listener = (s: LlmSettings) => void;
const listeners = new Set<Listener>();
let current: LlmSettings | null = null;

export function getSettings(): LlmSettings {
  if (!current) current = loadSettings();
  return current;
}

export function saveSettings(next: LlmSettings): void {
  current = normaliseSettings(next);
  try {
    globalThis.localStorage?.setItem(SETTINGS_KEY, JSON.stringify(current));
  } catch {
    /* storage disabled — settings still apply for this session */
  }
  listeners.forEach((l) => l(current!));
}

export function subscribeSettings(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
