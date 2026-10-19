/**
 * Agent builder.
 *
 * An agent in mem20 is a configuration, not a service: identity, endpoint,
 * model, system prompt, and the tool namespaces it is allowed to touch. This
 * surface edits that configuration and persists it to the workspace store that
 * the teamz chat already uses, so an agent created here is immediately
 * addressable in Team — same store, same @mention routing, no second registry.
 *
 * The tool-namespace picker is fed from the real `tools/list` registry, so the
 * scopes you can grant are exactly the namespaces that exist.
 */

import { useMemo, useState } from 'react';
import { groupByDomain, domainLabel, loadTools } from '../api/mcp';
import { useAsync } from '../lib/useAsync';
import { useWorkspace } from '../teamz/store/useWorkspace';
import type { Agent } from '../teamz/types';
import {
  Chip,
  EmptyState,
  IconPlus,
  IconTrash,
  IconUsers,
  LoadingState,
  Modal,
  Notice,
  Stat,
  plural,
} from '../components/ui';

const ACCENTS = ['#7c9cff', '#3ddc97', '#f5b544', '#f87171', '#b28cff', '#4fd1c5', '#f472b6', '#60a5fa'];
const MODELS = ['gpt-4o', 'gpt-4o-mini', 'claude-sonnet-4', 'llama3.1:70b', 'qwen2.5:32b', 'local'];

export default function AgentsView() {
  const ws = useWorkspace();
  const tools = useAsync(loadTools, []);
  const [editing, setEditing] = useState<Agent | null>(null);
  const [creating, setCreating] = useState(false);

  const domains = useMemo(() => (tools.data ? groupByDomain(tools.data.data) : []), [tools.data]);

  /** Namespace scopes are stored as tags on the prompt's front matter line. */
  const scopeOf = (agent: Agent): string[] => {
    const match = /^scopes:\s*(.+)$/im.exec(agent.systemPrompt);
    return match
      ? match[1]
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
      : [];
  };

  return (
    <>
      <div className="spread" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div className="flex" style={{ flexWrap: 'wrap' }}>
          <Chip tone="accent">{plural(ws.state.agents.length, 'agent')}</Chip>
          <Chip>{plural(ws.state.conversations.length, 'conversation')}</Chip>
          {tools.data ? <Chip tone="dream">{tools.data.data.length} tools available</Chip> : null}
        </div>
        <button type="button" className="btn btn-sm btn-primary" onClick={() => setCreating(true)}>
          <IconPlus size={13} /> New agent
        </button>
      </div>

      <Notice>
        An agent here is a configuration the workspace owns: name, endpoint, model, prompt and tool
        scopes. Creating one also opens its 1:1 thread and invites it into the room you are looking at
        — the same store the Team surface reads, so the two cannot drift.
      </Notice>

      <div className="stat-row" style={{ marginBottom: 16, marginTop: 12 }}>
        <Stat label="Agents" value={ws.state.agents.length} hint="in this workspace" />
        <Stat
          label="Online"
          value={ws.state.agents.filter((a) => a.status === 'online').length}
          hint="status field"
        />
        <Stat
          label="From templates"
          value={ws.state.agents.filter((a) => a.origin).length}
          hint="with role provenance"
        />
        <Stat
          label="Scoped"
          value={ws.state.agents.filter((a) => scopeOf(a).length > 0).length}
          hint="with tool namespaces"
        />
      </div>

      {ws.state.agents.length === 0 ? (
        <EmptyState
          title="No agents yet"
          icon={<IconUsers size={20} />}
          action={
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => setCreating(true)}
            >
              <IconPlus size={13} /> Create the first one
            </button>
          }
        >
          The workspace ships empty — there is no seeded roster, because an agent you did not create
          is not yours.
        </EmptyState>
      ) : (
        <div className="grid-2">
          {ws.state.agents.map((agent) => {
            const scopes = scopeOf(agent);
            return (
              <article key={agent.id} className="card card-pad" style={{ display: 'grid', gap: 9 }}>
                <div className="spread" style={{ gap: 8 }}>
                  <div className="flex" style={{ minWidth: 0 }}>
                    <span
                      aria-hidden="true"
                      style={{
                        width: 32,
                        height: 32,
                        borderRadius: 10,
                        display: 'grid',
                        placeItems: 'center',
                        background: `color-mix(in srgb, ${agent.accent} 18%, var(--bg-panel-2))`,
                        border: `1px solid ${agent.accent}`,
                        fontSize: 16,
                        flex: '0 0 32px',
                      }}
                    >
                      {agent.emoji}
                    </span>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 600 }} className="truncate">
                        {agent.name}
                      </div>
                      <div className="mono muted" style={{ fontSize: 10.5 }}>
                        {agent.model}
                      </div>
                    </div>
                  </div>
                  <Chip
                    tone={
                      agent.status === 'online' ? 'green' : agent.status === 'busy' ? 'amber' : 'red'
                    }
                  >
                    {agent.status}
                  </Chip>
                </div>

                {agent.origin ? (
                  <div className="flex" style={{ gap: 4, flexWrap: 'wrap' }}>
                    <Chip tone="accent" title="Template provenance">
                      {agent.origin.role}
                    </Chip>
                    <Chip>{agent.origin.templateId}</Chip>
                  </div>
                ) : null}

                <div
                  className="mono muted truncate"
                  style={{ fontSize: 10.5 }}
                  title={agent.endpointUrl}
                >
                  {agent.endpointUrl || 'no endpoint set'}
                </div>

                {scopes.length ? (
                  <div className="flex" style={{ gap: 4, flexWrap: 'wrap' }}>
                    {scopes.slice(0, 6).map((s) => (
                      <Chip key={s} tone="dream">
                        {s}
                      </Chip>
                    ))}
                    {scopes.length > 6 ? <Chip>+{scopes.length - 6}</Chip> : null}
                  </div>
                ) : null}

                <div className="flex" style={{ gap: 6, marginTop: 2 }}>
                  <button type="button" className="btn btn-sm" onClick={() => setEditing(agent)}>
                    Configure
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-ghost"
                    onClick={() => ws.openDirectChat(agent.id)}
                  >
                    Open chat
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-ghost btn-danger"
                    style={{ marginLeft: 'auto' }}
                    aria-label={`Delete ${agent.name}`}
                    onClick={() => {
                      if (window.confirm(`Delete ${agent.name}? Its conversations go with it.`)) {
                        ws.deleteAgent(agent.id);
                      }
                    }}
                  >
                    <IconTrash size={12} />
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <AgentForm
        open={creating || Boolean(editing)}
        agent={editing}
        domains={domains.map((d) => d.id)}
        onClose={() => {
          setCreating(false);
          setEditing(null);
        }}
        onSave={(values) => {
          if (editing) {
            ws.updateAgent(editing.id, values as Partial<Agent>);
          } else {
            ws.createAgent({
              name: values.name!,
              emoji: values.emoji!,
              accent: values.accent!,
              endpointUrl: values.endpointUrl!,
              model: values.model!,
              systemPrompt: values.systemPrompt!,
              skills: [],
            });
          }
          setCreating(false);
          setEditing(null);
        }}
      />

      {tools.loading ? <LoadingState rows={1} label="Reading namespaces" /> : null}
    </>
  );
}

/* ------------------------------------------------------------------ form */

interface AgentValues {
  name: string;
  emoji: string;
  accent: string;
  endpointUrl: string;
  model: string;
  systemPrompt: string;
  scopes: string[];
}

function AgentForm({
  open,
  agent,
  domains,
  onClose,
  onSave,
}: {
  open: boolean;
  agent: Agent | null;
  domains: string[];
  onClose: () => void;
  onSave: (values: Partial<AgentValues> & Record<string, unknown>) => void;
}) {
  const initial = useMemo<AgentValues>(() => {
    if (!agent) {
      return {
        name: '',
        emoji: '\u{1F916}',
        accent: ACCENTS[0],
        endpointUrl: 'http://localhost:8001/chat',
        model: MODELS[0],
        systemPrompt: '',
        scopes: [],
      };
    }
    const match = /^scopes:\s*(.+)$/im.exec(agent.systemPrompt);
    return {
      name: agent.name,
      emoji: agent.emoji,
      accent: agent.accent,
      endpointUrl: agent.endpointUrl,
      model: agent.model,
      systemPrompt: agent.systemPrompt.replace(/^scopes:.*$\n?/im, ''),
      scopes: match
        ? match[1]
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean)
        : [],
    };
  }, [agent]);

  const [values, setValues] = useState<AgentValues>(initial);
  const [error, setError] = useState<string | null>(null);

  // Re-seed the form when the target agent changes.
  const key = agent?.id ?? 'new';
  const [formKey, setFormKey] = useState(key);
  if (formKey !== key) {
    setFormKey(key);
    setValues(initial);
    setError(null);
  }

  const set = <K extends keyof AgentValues>(k: K, v: AgentValues[K]) =>
    setValues((prev) => ({ ...prev, [k]: v }));

  const submit = () => {
    if (!values.name.trim()) {
      setError('An agent needs a name — it is what @mentions resolve against.');
      return;
    }
    if (!values.endpointUrl.trim()) {
      setError('An agent needs an endpoint, or it can never answer.');
      return;
    }
    const prompt = [
      values.scopes.length ? `scopes: ${values.scopes.join(', ')}` : '',
      values.systemPrompt,
    ]
      .filter(Boolean)
      .join('\n');

    onSave({
      name: values.name.trim(),
      emoji: values.emoji,
      accent: values.accent,
      endpointUrl: values.endpointUrl.trim(),
      model: values.model,
      systemPrompt: prompt,
    });
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={agent ? `Configure ${agent.name}` : 'New agent'}
      subtitle={
        agent
          ? 'Changes apply immediately in Team — same store, no publish step.'
          : 'Creating an agent also opens its 1:1 thread and invites it into the current room.'
      }
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="btn btn-primary" onClick={submit}>
            {agent ? 'Save changes' : 'Create agent'}
          </button>
        </>
      }
    >
      {error ? (
        <div style={{ marginBottom: 12 }}>
          <Notice tone="error">{error}</Notice>
        </div>
      ) : null}

      <div className="field">
        <label htmlFor="ag-name">Name</label>
        <input
          id="ag-name"
          className="input"
          value={values.name}
          onChange={(e) => set('name', e.target.value)}
          placeholder="e.g. Atlas"
        />
        <span className="field-hint">@mentions resolve on this name and its kebab handle.</span>
      </div>

      <div className="field">
        <label htmlFor="ag-emoji">Avatar</label>
        <div className="flex" style={{ gap: 6, flexWrap: 'wrap' }}>
          <input
            id="ag-emoji"
            className="input"
            style={{ width: 76 }}
            value={values.emoji}
            onChange={(e) => set('emoji', e.target.value.slice(0, 2))}
            aria-label="Emoji"
          />
          <div className="flex" style={{ gap: 4, flexWrap: 'wrap' }}>
            {['\u{1F916}', '\u{1F6F0}\uFE0F', '\u{1F4D0}', '\u{1F3A8}', '\u{1F9E0}', '\u{1F6E0}\uFE0F', '\u{1F52D}', '\u{1F5C2}\uFE0F'].map(
              (e) => (
                <button
                  key={e}
                  type="button"
                  className="btn btn-sm"
                  onClick={() => set('emoji', e)}
                  aria-label={`Use ${e}`}
                >
                  {e}
                </button>
              ),
            )}
          </div>
        </div>
      </div>

      <div className="field">
        <label>Accent</label>
        <div className="flex" style={{ gap: 6, flexWrap: 'wrap' }}>
          {ACCENTS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => set('accent', c)}
              aria-label={`Accent ${c}`}
              aria-pressed={values.accent === c}
              style={{
                width: 24,
                height: 24,
                borderRadius: 7,
                background: c,
                border: values.accent === c ? '2px solid var(--text)' : '1px solid var(--line)',
              }}
            />
          ))}
        </div>
      </div>

      <div className="field">
        <label htmlFor="ag-endpoint">Endpoint</label>
        <input
          id="ag-endpoint"
          className="input mono"
          value={values.endpointUrl}
          onChange={(e) => set('endpointUrl', e.target.value)}
          placeholder="http://localhost:8001/chat"
        />
        <span className="field-hint">
          The chat transport POSTs a JSON body here. Nothing is proxied through me — the browser calls
          it directly, so it must allow your origin.
        </span>
      </div>

      <div className="field">
        <label htmlFor="ag-model">Model</label>
        <input
          id="ag-model"
          className="input mono"
          list="ag-models"
          value={values.model}
          onChange={(e) => set('model', e.target.value)}
        />
        <datalist id="ag-models">
          {MODELS.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
      </div>

      <div className="field">
        <label>Tool namespaces</label>
        <div
          style={{
            display: 'flex',
            gap: 5,
            flexWrap: 'wrap',
            maxHeight: 132,
            overflowY: 'auto',
            padding: 8,
            border: '1px solid var(--line)',
            borderRadius: 'var(--r-md)',
            background: 'var(--bg-panel-2)',
          }}
        >
          {domains.length === 0 ? (
            <span className="muted" style={{ fontSize: 11.5 }}>
              Reading the registry…
            </span>
          ) : (
            domains.map((d) => {
              const on = values.scopes.includes(d.id);
              return (
                <button
                  key={d.id}
                  type="button"
                  className={`chip${on ? ' chip-accent' : ''}`}
                  aria-pressed={on}
                  onClick={() =>
                    set(
                      'scopes',
                      on ? values.scopes.filter((s) => s !== d.id) : [...values.scopes, d.id],
                    )
                  }
                  title={domainLabel(d.id)}
                >
                  {d.id}
                </button>
              );
            })
          )}
        </div>
        <span className="field-hint">
          Stored as <span className="mono">scopes:</span> in the prompt. These are the real
          namespaces from the live tool registry — nothing invented.
        </span>
      </div>

      <div className="field" style={{ marginBottom: 0 }}>
        <label htmlFor="ag-prompt">System prompt</label>
        <textarea
          id="ag-prompt"
          className="textarea"
          rows={7}
          value={values.systemPrompt}
          onChange={(e) => set('systemPrompt', e.target.value)}
          placeholder="Operating instructions for this agent."
        />
      </div>
    </Modal>
  );
}
