import { useEffect, useState } from 'react';
import type { Agent, AgentSkill, AgentStatus } from '../types';
import { Modal, Field } from './Modal';
import { AgentAvatar } from './Avatar';
import { CheckIcon, PlusIcon, RefreshIcon, TrashIcon } from './Icons';
import { ACCENT_PALETTE, EMOJI_PALETTE } from '../data/mock';
import { pingAgent } from '../api/agents';
import { getSettings } from '../api/settings';
import { formatRelative } from '../lib/format';

interface AgentSettingsProps {
  agent: Agent | null;
  onClose: () => void;
  onSave: (id: string, patch: Partial<Agent>) => void;
  onDelete: (id: string) => void;
  onOpenChat: (id: string) => void;
}

const STATUSES: AgentStatus[] = ['online', 'busy', 'offline'];

function validateEndpoint(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed === '') return null;
  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    return 'Enter a valid URL (e.g. http://localhost:8001/chat).';
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    return 'URL must start with http:// or https://.';
  }
  if (typeof window !== 'undefined' && window.location.protocol === 'https:' && url.protocol === 'http:') {
    return 'Mixed content: an https page cannot call an http endpoint.';
  }
  return null;
}

function skillKey(label: string): string {
  return label.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'skill';
}

export function AgentSettings({ agent, onClose, onSave, onDelete, onOpenChat }: AgentSettingsProps) {
  const [draft, setDraft] = useState<Agent | null>(agent);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string; latencyMs: number } | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [newSkillLabel, setNewSkillLabel] = useState('');
  const [newSkillLevel, setNewSkillLevel] = useState(3);

  useEffect(() => {
    setDraft(agent);
    setConfirmDelete(false);
    setNewSkillLabel('');
    setNewSkillLevel(3);
    if (agent?.lastPingAt) {
      setTestResult({
        ok: agent.lastPingOk ?? false,
        message: agent.lastPingMessage ?? '',
        latencyMs: 0,
      });
    } else {
      setTestResult(null);
    }
  }, [agent]);

  if (!draft) return null;

  const dirty = agent !== null && JSON.stringify(draft) !== JSON.stringify(agent);

  const patch = (p: Partial<Agent>) => setDraft((d) => (d ? { ...d, ...p } : d));

  const save = () => {
    onSave(draft.id, {
      name: draft.name.trim() || 'Untitled Agent',
      emoji: draft.emoji,
      accent: draft.accent,
      status: draft.status,
      endpointUrl: draft.endpointUrl.trim(),
      model: draft.model.trim(),
      systemPrompt: draft.systemPrompt,
      isLead: draft.isLead || undefined,
      skills: draft.skills ?? [],
    });
    onClose();
  };

  const runTest = async () => {
    setTesting(true);
    setTestResult(null);
    const result = await pingAgent(draft);
    setTestResult(result);
    setTesting(false);
    const pingPatch = {
      lastPingAt: Date.now(),
      lastPingOk: result.ok,
      lastPingMessage: result.message,
    };
    setDraft((d) => (d ? { ...d, ...pingPatch } : d));
    onSave(draft.id, pingPatch);
  };

  const upsertSkill = () => {
    const label = newSkillLabel.trim();
    if (!label) return;
    const key = skillKey(label);
    const level = Math.max(1, Math.min(5, Number(newSkillLevel) || 1));
    const skills = (draft.skills ?? []).slice();
    const idx = skills.findIndex((s) => s.key === key || s.label.toLowerCase() === label.toLowerCase());
    const skill: AgentSkill = { key, label, level };
    if (idx >= 0) skills[idx] = { ...skills[idx], key, label: skills[idx].label || label, level: Math.max(skills[idx].level, level) };
    else skills.push(skill);
    skills.sort((a, b) => b.level - a.level || a.label.localeCompare(b.label));
    patch({ skills });
    setNewSkillLabel('');
  };

  const removeSkill = (key: string) => {
    patch({ skills: (draft.skills ?? []).filter((s) => s.key !== key) });
  };

  const nameError = draft.name.trim() === '' ? 'Name is required.' : null;
  const modelError = draft.model.trim() === '' ? 'Model is required.' : null;
  const endpointError = validateEndpoint(draft.endpointUrl);
  const canSave = !nameError && !modelError && !endpointError;

  return (
    <Modal
      open={Boolean(agent)}
      onClose={onClose}
      title="Agent settings"
      subtitle="Configure agent identity, endpoint, system prompt, portfolio/skills, and lead/runtime role."
      width={620}
      footer={
        <>
          <div className="foot-left">
            {confirmDelete ? (
              <div className="confirm-inline">
                <span>Delete this agent? Their direct chat and any channel they’re the last member of will be removed.</span>
                <button className="btn danger sm" onClick={() => onDelete(draft.id)}>
                  Yes, delete
                </button>
                <button className="btn ghost sm" onClick={() => setConfirmDelete(false)}>
                  Cancel
                </button>
              </div>
            ) : (
              <button className="btn ghost sm danger-hover" onClick={() => setConfirmDelete(true)}>
                <TrashIcon size={14} /> Delete
              </button>
            )}
          </div>
          <div className="foot-right">
            <button className="btn ghost sm" onClick={() => { onOpenChat(draft.id); onClose(); }}>
              Open chat
            </button>
            <button className="btn primary sm" onClick={save} disabled={!dirty || !canSave}>
              <CheckIcon size={14} /> Save changes
            </button>
          </div>
        </>
      }
    >
      <div className="settings-preview">
        <AgentAvatar agent={draft} size={56} showStatus={draft.status} />
        <div>
          <strong>{draft.name || 'Untitled Agent'}{draft.isLead ? ' · Lead' : ''}</strong>
          <span>
            {draft.origin ? `${draft.origin.role} · ` : ''}
            Created {formatRelative(draft.createdAt)} ago · {draft.model || 'no model set'}
          </span>
        </div>
      </div>

      <label className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <input
          type="checkbox"
          checked={Boolean(draft.isLead)}
          onChange={(e) => patch({ isLead: e.target.checked || undefined })}
          style={{ width: 'auto' }}
        />
        <span>
          <strong>Lead agent</strong> — can be asked to add/remove/program agents and the runtime, create channels, configure agents, and orchestrate/delegate work.
        </span>
      </label>

      <div className="field">
        <span className="field-label">
          Portfolio / skills
          <em>{draft.origin ? `from ${draft.origin.templateId}` : 'agent portfolio'} · level 1-5</em>
        </span>
        <div className="skill-chips" style={{ marginBottom: 8, flexWrap: 'wrap' }}>
          {(draft.skills ?? []).map((skill) => (
            <span key={skill.key} className="skill-chip" title={`depth ${skill.level}/5`}>
              {skill.label}
              <em>L{skill.level}</em>
              <button type="button" className="icon-btn ghost" style={{ marginLeft: 4, padding: 0 }} onClick={() => removeSkill(skill.key)} aria-label={`Remove ${skill.label}`}>×</button>
            </span>
          ))}
          {(draft.skills ?? []).length === 0 && <span className="muted">No skills yet. Add learned skills/capabilities to the portfolio.</span>}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            value={newSkillLabel}
            onChange={(e) => setNewSkillLabel(e.target.value)}
            placeholder="Add skill/capability (e.g. React, Research synthesis)"
            style={{ flex: 1, minWidth: 220 }}
          />
          <select value={String(newSkillLevel)} onChange={(e) => setNewSkillLevel(Number(e.target.value))}>
            {[1,2,3,4,5].map((n) => <option key={n} value={n}>Level {n}</option>)}
          </select>
          <button type="button" className="btn ghost sm" onClick={upsertSkill} disabled={!newSkillLabel.trim()}>
            <PlusIcon size={13} /> Add/update
          </button>
        </div>
      </div>

      <Field label="Name">
        <input
          value={draft.name}
          onChange={(e) => patch({ name: e.target.value })}
          placeholder="e.g. Researcher"
          autoFocus
        />
        {nameError && <span className="field-error">{nameError}</span>}
      </Field>

      <div className="field-grid">
        <Field label="Avatar emoji">
          <div className="emoji-picker">
            {EMOJI_PALETTE.map((e) => (
              <button
                key={e}
                className={`emoji-opt${draft.emoji === e ? ' is-on' : ''}`}
                onClick={() => patch({ emoji: e })}
                aria-label={`Use ${e}`}
              >
                {e}
              </button>
            ))}
          </div>
        </Field>
      </div>

      <div className="field-grid">
        <Field label="Accent colour">
          <div className="accent-picker">
            {ACCENT_PALETTE.map((c) => (
              <button
                key={c}
                className={`accent-opt${draft.accent === c ? ' is-on' : ''}`}
                style={{ background: c }}
                onClick={() => patch({ accent: c })}
                aria-label={`Accent ${c}`}
              />
            ))}
          </div>
        </Field>
        <Field label="Status">
          <div className="seg">
            {STATUSES.map((s) => (
              <button
                key={s}
                className={draft.status === s ? 'is-on' : ''}
                onClick={() => patch({ status: s })}
              >
                {s}
              </button>
            ))}
          </div>
        </Field>
      </div>

      <Field label="Endpoint URL" hint="where your server listens (used in own-endpoints mode)">
        <input
          value={draft.endpointUrl}
          onChange={(e) => patch({ endpointUrl: e.target.value })}
          placeholder="http://localhost:8001/chat"
          spellCheck={false}
        />
        {endpointError && <span className="field-error">{endpointError}</span>}
      </Field>

      <div className="test-row">
        <button className="btn ghost sm" onClick={runTest} disabled={testing}>
          <RefreshIcon size={14} /> {testing ? 'Testing…' : 'Test connection'}
        </button>
        {testResult && (
          <span className={`test-out${testResult.ok ? ' ok' : ' bad'}`}>
            {testResult.ok ? '✓' : '✕'} {testResult.message}
            {testResult.latencyMs > 0 ? ` · ${testResult.latencyMs}ms` : ''}
          </span>
        )}
      </div>

      <Field
        label="Model"
        hint={
          getSettings().provider === 'pollinations'
            ? 'own-endpoint mode only · Pollinations uses the model in Workspace & API'
            : 'model hint for orchestrator/own endpoint'
        }
      >
        <input
          value={draft.model}
          onChange={(e) => patch({ model: e.target.value })}
          placeholder="gpt-4o-mini · qwen2.5-coder:32b · llama3.1:70b"
          spellCheck={false}
        />
        {modelError && <span className="field-error">{modelError}</span>}
      </Field>

      <Field label="System prompt" hint={`${draft.systemPrompt.length} chars`}>
        <textarea
          value={draft.systemPrompt}
          onChange={(e) => patch({ systemPrompt: e.target.value })}
          rows={6}
          placeholder="You are a helpful agent that…"
        />
      </Field>
    </Modal>
  );
}
