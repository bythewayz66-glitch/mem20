import { useEffect, useState } from 'react';
import type { Agent } from '../types';
import { Modal, Field } from './Modal';
import { AgentAvatar } from './Avatar';
import { CheckIcon, HashIcon, UsersIcon, SparkIcon } from './Icons';

interface ChannelDialogProps {
  open: boolean;
  onClose: () => void;
  agents: Agent[];
  /** When editing an existing channel, pass it in. */
  editing?: { id: string; name: string; topic?: string; agentIds: string[] } | null;
  onCreate?: (name: string, agentIds: string[], topic?: string) => void;
  onUpdateMembers?: (id: string, agentIds: string[]) => void;
  onRename?: (id: string, name: string) => void;
  mode?: 'create' | 'members' | 'goal';
  /** Current goal text for the channel (when editing). */
  currentGoal?: string;
  onSetGoal?: (conversationId: string, text: string, active?: boolean) => void;
}

export function ChannelDialog({
  open,
  onClose,
  agents,
  editing,
  onCreate,
  onUpdateMembers,
  onRename,
  mode = 'create',
  currentGoal = '',
  onSetGoal,
}: ChannelDialogProps) {
  const [name, setName] = useState('');
  const [topic, setTopic] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [goalText, setGoalText] = useState(currentGoal);
  const [goalActive, setGoalActive] = useState(true);
  const isMembersMode = mode === 'members';
  const isGoalMode = mode === 'goal';

  useEffect(() => {
    if (!open) return;
    setName(editing?.name ?? '');
    setTopic(editing?.topic ?? '');
    setSelected(editing?.agentIds ?? agents.slice(0, 2).map((a) => a.id));
    if (isGoalMode && currentGoal !== undefined) {
      setGoalText(currentGoal);
      setGoalActive(true);
    }
  }, [open, editing, agents, isGoalMode, currentGoal]);

  const toggle = (id: string) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const submit = () => {
    if (isGoalMode && editing) {
      onSetGoal?.(editing.id, goalText.trim(), goalActive);
    } else if (isMembersMode && editing) {
      onUpdateMembers?.(editing.id, selected);
      if (name.trim() && name.trim() !== editing.name) onRename?.(editing.id, name.trim());
    } else {
      onCreate?.(name.trim() || 'New Channel', selected, topic.trim() || undefined);
    }
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={
        isMembersMode
          ? `Members of #${editing?.name ?? ''}`
          : isGoalMode
          ? `Goal for #${editing?.name ?? ''}`
          : 'New channel'
      }
      subtitle={
        isMembersMode
          ? 'Add or remove agents. Every message you send goes to all of them.'
          : isGoalMode
          ? 'Set a room goal. The assigned team will work toward it autonomously — running commands, writing files, and using tools until the goal is complete.'
          : 'A channel is a room with several agents in it. Your message fans out to all members.'
      }
      width={isGoalMode ? 640 : 540}
      footer={
        <>
          <div className="foot-left">
            {isGoalMode ? (
              <span className="picker-count">
                {goalText.trim() ? 'Goal set' : 'No goal'}
              </span>
            ) : (
              <span className="picker-count">{selected.length} selected</span>
            )}
          </div>
          <div className="foot-right">
            <button className="btn ghost sm" onClick={onClose}>Cancel</button>
            <button className="btn primary sm" onClick={submit} disabled={isGoalMode ? false : selected.length === 0}>
              <CheckIcon size={14} />
              {isGoalMode ? 'Save goal' : isMembersMode ? 'Save members' : 'Create channel'}
            </button>
          </div>
        </>
      }
    >
      {!isGoalMode && (
        <>
          <div className="field-grid">
            <Field label="Channel name">
              <div className="input-with-icon">
                <HashIcon size={14} />
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="design-review"
                  autoFocus={!isMembersMode}
                  onKeyDown={(e) => e.key === 'Enter' && submit()}
                />
              </div>
            </Field>
          </div>

          <Field label="Topic" hint="optional">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="What this room is for"
            />
          </Field>
        </>
      )}

      {!isGoalMode && (
        <div className="field">
          <span className="field-label">
            Member agents
            <em>
              <UsersIcon size={12} /> pick at least one
            </em>
          </span>
          <ul className="member-picker">
            {agents.map((a) => {
              const on = selected.includes(a.id);
              return (
                <li key={a.id}>
                  <button className={`member-opt${on ? ' is-on' : ''}`} onClick={() => toggle(a.id)}>
                    <AgentAvatar agent={a} size={30} showStatus={a.status} />
                    <span className="mo-text">
                      <span className="mo-name">{a.name}</span>
                      <span className="mo-model">{a.model}</span>
                    </span>
                    <span className={`checkbox${on ? ' is-on' : ''}`}>{on && <CheckIcon size={12} />}</span>
                  </button>
                </li>
              );
            })}
            {agents.length === 0 && <li className="rail-empty">Create an agent first.</li>}
          </ul>
        </div>
      )}

      {isGoalMode && editing && (
        <div className="goal-editor">
          <Field label="Goal" hint="What should the team accomplish? Be specific and actionable.">
            <textarea
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              placeholder="e.g. Build a React todo app with TypeScript, Vite, and tests. Use ESLint and Prettier."
              rows={4}
              spellCheck={true}
            />
          </Field>
          <label className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={goalActive}
              onChange={(e) => setGoalActive(e.target.checked)}
              style={{ width: 'auto' }}
            />
            <span>
              <strong>Active</strong> — when on, the worker will take autonomous steps toward this goal.
            </span>
          </label>
          <div className="goal-hint">
            <SparkIcon size={14} />
            <span>
              The worker picks the best agent for each step, runs real terminal commands, writes files,
              and uses GitHub/gh tools. You can watch progress in the room — it posts step updates.
            </span>
          </div>
        </div>
      )}
    </Modal>
  );
}
