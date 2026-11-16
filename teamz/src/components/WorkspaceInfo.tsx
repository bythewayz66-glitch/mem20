import { useEffect, useState } from 'react';
import { Modal, Field } from './Modal';
import { RefreshIcon } from './Icons';
import { useLlmSettings } from '../store/useLlmSettings';
import type { LlmSettings, Provider } from '../api/settings';
import {
  DEFAULT_ANON_MODEL,
  DEFAULT_KEYED_MODEL,
  callPollinations,
  hasKey,
  listPollinationsModels,
  resolveModel,
  buildPollinationsRequest,
  type ModelOption,
} from '../api/pollinations';

const PROVIDERS: { id: Provider; label: string }[] = [
  { id: 'orchestrator', label: 'Teamz orchestrator' },
  { id: 'pollinations', label: 'Pollinations' },
  { id: 'custom', label: 'Own endpoints' },
  { id: 'mock', label: 'Mock' },
];

function formatUsage(u?: { prompt_tokens?: number | null; completion_tokens?: number | null; total_tokens?: number | null } | null) {
  if (!u) return '—';
  const p = u.prompt_tokens ?? '—';
  const c = u.completion_tokens ?? '—';
  const t = u.total_tokens ?? '—';
  return `${t} total (prompt ${p}, completion ${c})`;
}

function ProviderSettings() {
  const [saved, save] = useLlmSettings();
  const [draft, setDraft] = useState<LlmSettings>(saved);
  const [showKey, setShowKey] = useState(false);
  const [showOrchToken, setShowOrchToken] = useState(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [test, setTest] = useState<{ ok: boolean; text: string } | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => setDraft(saved), [saved]);

  const keyed = hasKey(draft);
  useEffect(() => {
    if (draft.provider !== 'pollinations') return;
    let live = true;
    listPollinationsModels(draft).then((m) => live && setModels(m));
    return () => {
      live = false;
    };
  }, [draft.provider, keyed]);

  const dirty = JSON.stringify(draft) !== JSON.stringify(saved);
  const patch = (p: Partial<LlmSettings>) => {
    setDraft((d) => ({ ...d, ...p }));
    setTest(null);
  };

  const runTest = async () => {
    setTesting(true);
    setTest(null);
    const started = performance.now();
    try {
      if (draft.provider === 'orchestrator') {
        // Save draft temporarily? ping uses getSettings(); so do a lightweight direct check
        const base = (draft.orchestratorUrl || 'http://localhost:8787').replace(/\/+$/, '');
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (draft.orchestratorToken?.trim()) headers.Authorization = `Bearer ${draft.orchestratorToken.trim()}`;
        const hres = await fetch(`${base}/health`, { headers });
        if (!hres.ok) throw new Error(`Orchestrator health ${hres.status}`);
        const h = await hres.json().catch(() => ({}));
        // quick optimize prompt call as functional test through orchestrator
        const ores = await fetch(`${base}/v1/optimize-prompt`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ draft: 'say hello clearly', use_memory: false, history: [], agents: [] }),
        });
        if (!ores.ok) {
          const t = await ores.text();
          throw new Error(`Optimize test failed: ${ores.status} ${t.slice(0, 180)}`);
        }
        const o = await ores.json();
        setTest({
          ok: true,
          text: `Healthy (${h?.providers?.length ?? 0} providers). Optimize test via ${o?.routing?.selected_provider ?? 'provider'} · ${o?.routing?.selected_model ?? 'model'} · ${Math.round(performance.now() - started)}ms`,
        });
      } else if (draft.provider === 'pollinations') {
        const req = buildPollinationsRequest(
          { id: 'test', name: 'Test', emoji: '', accent: '', status: 'online', endpointUrl: '', model: '', systemPrompt: 'You are a connection test.', skills: [], createdAt: 0 },
          [{ id: 't', conversationId: 't', authorType: 'user', text: 'Reply with the single word: pong', createdAt: Date.now(), status: 'sent' }],
          new Map(),
          { conversationKind: 'direct', conversationName: 'test' },
          { ...draft, stream: false },
        );
        const reply = await callPollinations(req);
        setTest({ ok: true, text: `${resolveModel(draft)} replied “${reply.trim().slice(0, 60)}” · ${Math.round(performance.now() - started)}ms` });
      } else if (draft.provider === 'custom') {
        setTest({ ok: true, text: 'Custom mode uses each agent’s own endpoint. Use the Test button in an agent’s settings.' });
      } else {
        setTest({ ok: true, text: 'Mock mode is local and always available.' });
      }
    } catch (err) {
      setTest({ ok: false, text: err instanceof Error ? err.message : 'Request failed' });
    } finally {
      setTesting(false);
    }
  };

  const defaultModel = keyed ? DEFAULT_KEYED_MODEL : DEFAULT_ANON_MODEL;
  const routing = saved.lastRouting;
  const attempts = routing?.attempts ?? [];

  return (
    <div className="info-block">
      <h3>AI provider</h3>
      <div className="seg" style={{ marginBottom: 12, flexWrap: 'wrap' }}>
        {PROVIDERS.map((p) => (
          <button
            key={p.id}
            className={draft.provider === p.id ? 'is-on' : ''}
            onClick={() => patch({ provider: p.id })}
          >
            {p.label}
          </button>
        ))}
      </div>

      {draft.provider === 'orchestrator' && (
        <>
          <p className="muted">
            Use the local/teamz FastAPI orchestrator for keyless-first LLM routing across providers with an observable fallback chain,
            persistent channel memory via mem20, prompt optimization, connectors, and runtime orchestration APIs.
          </p>
          <Field label="Orchestrator URL" hint="base URL of the FastAPI server">
            <input
              value={draft.orchestratorUrl}
              onChange={(e) => patch({ orchestratorUrl: e.target.value })}
              placeholder="http://localhost:8787"
              spellCheck={false}
            />
          </Field>
          <Field label="Orchestrator token" hint="optional bearer token (if configured)">
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type={showOrchToken ? 'text' : 'password'}
                value={draft.orchestratorToken}
                onChange={(e) => patch({ orchestratorToken: e.target.value })}
                placeholder="(optional)"
                spellCheck={false}
                autoComplete="off"
                style={{ flex: 1 }}
              />
              <button className="btn ghost sm" onClick={() => setShowOrchToken((v) => !v)}>
                {showOrchToken ? 'Hide' : 'Show'}
              </button>
            </div>
          </Field>
          <Field label="Preferred model hint" hint="optional; agents may override; router treats as preference with fallback">
            <input
              value={draft.model}
              onChange={(e) => patch({ model: e.target.value })}
              placeholder="(auto / provider-selected)"
              spellCheck={false}
            />
          </Field>
          <label className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={draft.stream}
              onChange={(e) => patch({ stream: e.target.checked })}
              style={{ width: 'auto' }}
            />
            <span>Stream replies token by token</span>
          </label>
        </>
      )}

      {draft.provider === 'pollinations' && (
        <>
          <p className="muted">
            Real replies from <a href="https://pollinations.ai" target="_blank" rel="noreferrer">Pollinations.ai</a>.
            Without a key you use the free anonymous tier (<code>{DEFAULT_ANON_MODEL}</code>, rate-limited per IP).
            Add a key from <a href="https://enter.pollinations.ai/keys" target="_blank" rel="noreferrer">enter.pollinations.ai</a> for more models.
          </p>
          <Field label="API key" hint="optional · stored only in this browser">
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type={showKey ? 'text' : 'password'}
                value={draft.apiKey}
                onChange={(e) => patch({ apiKey: e.target.value })}
                placeholder="sk_… (leave empty for the anonymous tier)"
                spellCheck={false}
                autoComplete="off"
                style={{ flex: 1 }}
              />
              <button className="btn ghost sm" onClick={() => setShowKey((v) => !v)}>
                {showKey ? 'Hide' : 'Show'}
              </button>
            </div>
          </Field>
          <Field label="Model" hint={`empty = ${defaultModel}`}>
            <input
              value={draft.model}
              onChange={(e) => patch({ model: e.target.value })}
              placeholder={defaultModel}
              list="pollinations-models"
              spellCheck={false}
            />
            <datalist id="pollinations-models">
              {models.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </datalist>
          </Field>
          {!keyed && (
            <Field label="Referrer" hint="optional app name sent to Pollinations">
              <input
                value={draft.referrer}
                onChange={(e) => patch({ referrer: e.target.value })}
                placeholder="teamz"
                spellCheck={false}
              />
            </Field>
          )}
          <label className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={draft.stream}
              onChange={(e) => patch({ stream: e.target.checked })}
              style={{ width: 'auto' }}
            />
            <span>Stream replies token by token</span>
          </label>
        </>
      )}

      {draft.provider === 'custom' && (
        <p className="muted">Each agent calls the endpoint URL set in its own settings (request contract below).</p>
      )}
      {draft.provider === 'mock' && (
        <p className="muted">No network. Replies are canned persona text and are labelled as mock in the chat.</p>
      )}

      <div className="test-row">
        <button className="btn ghost sm" onClick={runTest} disabled={testing}>
          <RefreshIcon size={14} /> {testing ? 'Testing…' : `Test ${PROVIDERS.find(p=>p.id===draft.provider)?.label ?? 'provider'}`}
        </button>
        {test && <span className={`test-out${test.ok ? ' ok' : ' bad'}`}>{test.ok ? '✓' : '✕'} {test.text}</span>}
      </div>

      <div className="test-row" style={{ justifyContent: 'flex-end' }}>
        <button className="btn primary sm" onClick={() => save(draft)} disabled={!dirty}>
          Save provider settings
        </button>
      </div>

      <div className="info-block" style={{ marginTop: 12 }}>
        <h3>Live provider & usage</h3>
        <p className="muted" style={{ marginBottom: 8 }}>
          Last observed routing/usage from the active provider (persisted locally).
        </p>
        <div className="info-list" style={{ display: 'grid', gap: 6 }}>
          <div><strong>Provider:</strong> <code>{saved.lastProvider ?? '—'}</code></div>
          <div><strong>Model:</strong> <code>{saved.lastModel ?? '—'}</code></div>
          <div><strong>Usage:</strong> <code>{formatUsage(saved.lastUsage)}</code></div>
          <div><strong>Fallback used:</strong> <code>{routing?.fallback_used ? 'yes' : 'no'}</code></div>
          <div><strong>Updated:</strong> <code>{saved.lastUpdatedAt ? new Date(saved.lastUpdatedAt).toLocaleString() : '—'}</code></div>
        </div>
        {attempts.length > 0 && (
          <div style={{ marginTop: 10 }}>
            <div className="field-label" style={{ marginBottom: 6 }}>Fallback chain / attempts</div>
            <div style={{ display: 'grid', gap: 6 }}>
              {attempts.map((a, i) => (
                <div key={`${a.provider}-${a.model}-${i}`} style={{ padding: '8px 10px', border: '1px solid var(--border, #2a3242)', borderRadius: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                    <strong>{a.provider}{a.model ? ` · ${a.model}` : ''}</strong>
                    <span style={{ opacity: 0.9 }}>{a.status}{typeof a.latency_ms === 'number' ? ` · ${a.latency_ms}ms` : ''}</span>
                  </div>
                  {(a.reason || a.error) && (
                    <div className="muted" style={{ marginTop: 4 }}>{a.reason ? `Reason: ${a.reason}` : ''}{a.reason && a.error ? ' · ' : ''}{a.error ? `Error: ${a.error}` : ''}</div>
                  )}
                  {a.usage && <div className="muted" style={{ marginTop: 4 }}>Usage: {formatUsage(a.usage)}</div>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface WorkspaceInfoProps {
  open: boolean;
  onClose: () => void;
  onReset: () => void;
  agentCount: number;
  conversationCount: number;
}

export function WorkspaceInfo({ open, onClose, onReset, agentCount, conversationCount }: WorkspaceInfoProps) {
  const [confirmReset, setConfirmReset] = useState(false);
  const [llm] = useLlmSettings();

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Workspace & API"
      subtitle="Provider, orchestrator, memory/connectors, and runtime integration settings."
      width={720}
      footer={
        <>
          <div className="foot-left">
            {confirmReset ? (
              <div className="confirm-inline">
                <span>Reset all local data?</span>
                <button
                  className="btn danger sm"
                  onClick={() => {
                    onReset();
                    setConfirmReset(false);
                    onClose();
                  }}
                >
                  Yes, reset
                </button>
                <button className="btn ghost sm" onClick={() => setConfirmReset(false)}>Cancel</button>
              </div>
            ) : (
              <button className="btn ghost sm danger-hover" onClick={() => setConfirmReset(true)}>
                <RefreshIcon size={14} /> Reset to demo data
              </button>
            )}
          </div>
          <div className="foot-right">
            <button className="btn primary sm" onClick={onClose}>Done</button>
          </div>
        </>
      }
    >
      <div className="info-stats">
        <div>
          <strong>{agentCount}</strong>
          <span>agents</span>
        </div>
        <div>
          <strong>{conversationCount}</strong>
          <span>conversations</span>
        </div>
        <div>
          <strong className={llm.provider === 'mock' ? '' : 'live'}>{llm.provider}</strong>
          <span>provider</span>
        </div>
      </div>

      <ProviderSettings />

      <div className="info-block">
        <h3>Teamz orchestrator (server/)</h3>
        <p className="muted">
          Run the FastAPI orchestrator for keyless-first routing, observable fallback, mem20-backed persistent channel memory,
          prompt optimization, opportunity scanning, runtime planning for the lead agent, and connectors (GitHub, gh, Google).
        </p>
        <pre className="code-block">{`cd server
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=.. uvicorn server.app.main:app --host 0.0.0.0 --port 8787`}</pre>
        <p className="muted">
          Configure via env vars (e.g. <code>MEM20_ENABLED</code>, <code>MEM20_MCP_COMMAND/ARGS</code>, provider keys/base URLs,
          <code>GITHUB_TOKEN</code>/<code>GH_TOKEN</code>, <code>GOOGLE_ACCESS_TOKEN</code> or <code>GOOGLE_APPLICATION_CREDENTIALS</code>).
        </p>
      </div>

      <div className="info-block">
        <h3>Own endpoints contract</h3>
        <p>Pick <strong>Own endpoints</strong> above, then set each agent’s endpoint in its settings panel.</p>
        <pre className="code-block">
{`POST {agent.endpointUrl}
Content-Type: application/json

{
  "agent":   { "id", "name", "model", "systemPrompt" },
  "messages":[{ "role": "user" | "assistant",
                "content": "...", "authorName": "Scout" }],
  "channel": { "id", "name", "members": [{ "id", "name" }] }
}`}
        </pre>
        <p className="muted">
          Response can be <code>{'{ "reply": "..." }'}</code>, <code>{'{ "text": "..." }'}</code>, or OpenAI/Anthropic-compatible shapes.
        </p>
      </div>

      <div className="info-block">
        <h3>Where to change things</h3>
        <ul className="info-list">
          <li><code>src/api/agents.ts</code> — provider switch, routing, own-endpoint transport.</li>
          <li><code>src/api/orchestrator.ts</code> — teamz orchestrator transport, streaming/meta/usage, prompt optimization.</li>
          <li><code>src/api/pollinations.ts</code> — Pollinations request builder and streaming parser.</li>
          <li><code>src/store/useWorkspace.ts</code> — state, persistence, relevance routing, message/runtime actions.</li>
          <li><code>server/app/</code> — FastAPI orchestrator, providers/fallback, mem20, connectors, runtime planning.</li>
          <li><code>src/styles.css</code> — design tokens and UI styles.</li>
        </ul>
      </div>
    </Modal>
  );
}
