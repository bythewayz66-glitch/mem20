import { useState } from 'react';
import type { Agent, Conversation } from '../types';
import { AgentAvatar, AvatarStack, StatusDot } from './Avatar';
import { ChatIcon, HashIcon, PlusIcon, SearchIcon, SettingsIcon, SparkIcon, TargetIcon } from './Icons';
import { formatRelative } from '../lib/format';

interface SidebarProps {
  agents: Agent[];
  conversations: Conversation[];
  agentsById: Map<string, Agent>;
  activeConversationId: string | null;
  lastMessageAt: Record<string, number>;
  typing: Record<string, string[]>;
  onSelectConversation: (id: string) => void;
  onNewAgent: () => void;
  onNewChannel: () => void;
  onOpenAgentSettings: (agentId: string) => void;
  onOpenAgentChat: (agentId: string) => void;
  onOpenWorkspaceInfo: () => void;
  /** Worker status from the orchestrator */
  workerStatus?: { running: boolean; activeGoals: string[] } | null;
  /** Callback to open the goal dialog for the active channel */
  onOpenGoal?: () => void;
  /** Whether the active conversation is a channel with a goal */
  activeGoal?: { text: string; active: boolean } | null;
}

export function Sidebar({
  agents,
  conversations,
  agentsById,
  activeConversationId,
  lastMessageAt,
  typing,
  onSelectConversation,
  onNewAgent,
  onNewChannel,
  onOpenAgentSettings,
  onOpenAgentChat,
  onOpenWorkspaceInfo,
  onOpenGoal,
  activeGoal,
}: SidebarProps) {
  const [query, setQuery] = useState('');

  const q = query.trim().toLowerCase();
  const visibleAgents = q
    ? agents.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.model.toLowerCase().includes(q) ||
          (a.origin?.role.toLowerCase().includes(q) ?? false) ||
          a.skills.some((s) => s.label.toLowerCase().includes(q)) ||
          (a.isLead && 'lead'.includes(q)),
      )
    : agents;

  const channels = conversations.filter((c) => c.kind === 'channel');
  const directs = conversations.filter((c) => c.kind === 'direct');
  const onlineCount = agents.filter((a) => a.status !== 'offline').length;

  const isAgentActive = (agentId: string) => {
    const direct = directs.find((c) => c.agentIds[0] === agentId);
    return Boolean(direct && direct.id === activeConversationId);
  };

  return (
    <aside className="sidebar">
      <header className="sidebar-brand">
        <div className="brand-mark" aria-hidden="true">
          <SparkIcon size={17} />
        </div>
        <div className="brand-copy">
          <strong>teamz</strong>
          <span>{agents.length} agents · {onlineCount} live</span>
        </div>
        <button className="icon-btn ghost" onClick={onOpenWorkspaceInfo} title="Workspace & API settings">
          <SettingsIcon size={16} />
        </button>
      </header>

      <div className="sidebar-search">
        <SearchIcon size={14} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search agents, roles, skills…"
          aria-label="Search agents"
        />
      </div>

      <div className="sidebar-scroll">
        <section className="rail-section">
          <div className="rail-heading">
            <span>Agents</span>
            <button className="mini-btn" onClick={onNewAgent} title="Create a new agent">
              <PlusIcon size={13} />
              New Agent
            </button>
          </div>

          <ul className="agent-list">
            {visibleAgents.map((agent) => {
              const isActive = isAgentActive(agent.id);
              const isTyping = Object.values(typing).some((ids) => ids.includes(agent.id));
              const direct = directs.find((c) => c.agentIds[0] === agent.id);
              const last = direct ? lastMessageAt[direct.id] : undefined;

              return (
                <li key={agent.id}>
                  <div className={`agent-row${isActive ? ' is-active' : ''}`}>
                    <button
                      className="agent-row-main"
                      onClick={() => onOpenAgentChat(agent.id)}
                      title={`Open chat with ${agent.name}${agent.isLead ? ' (Lead agent)' : ''}`}
                    >
                      <AgentAvatar agent={agent} size={34} showStatus={agent.status} />
                      <span className="agent-row-text">
                        <span className="agent-name">
                          {agent.name}
                          {agent.isLead && <span className="typing-chip" title="Lead agent">lead</span>}
                          {isTyping && <span className="typing-chip">typing…</span>}
                        </span>
                        <span className="agent-meta">
                          <StatusDot status={agent.status} size={6} />
                          {agent.status === 'online' ? 'Online' : agent.status === 'busy' ? 'Busy' : 'Offline'}
                          <span className="dot-sep">·</span>
                          <span className="agent-model">
                            {agent.origin?.role ?? agent.model}
                          </span>
                          {last ? <><span className="dot-sep">·</span><span>{formatRelative(last)}</span></> : null}
                        </span>
                        {agent.skills.length > 0 && (
                          <span className="agent-skills">
                            {agent.skills.slice(0, 3).map((s) => (
                              <span key={s.key} className="agent-skill" title={`${s.label} (level ${s.level})`}>
                                {s.label}
                              </span>
                            ))}
                            {agent.skills.length > 3 && (
                              <span className="agent-skill is-more">
                                +{agent.skills.length - 3}
                              </span>
                            )}
                          </span>
                        )}
                      </span>
                    </button>
                    <button
                      className="agent-row-action"
                      onClick={() => onOpenAgentChat(agent.id)}
                      title={`Message ${agent.name}`}
                      aria-label={`Message ${agent.name}`}
                    >
                      <ChatIcon size={14} />
                    </button>
                    <button
                      className="agent-row-action"
                      onClick={() => onOpenAgentSettings(agent.id)}
                      title={`${agent.name} settings`}
                      aria-label={`${agent.name} settings`}
                    >
                      <SettingsIcon size={14} />
                    </button>
                  </div>
                </li>
              );
            })}
            {visibleAgents.length === 0 && (
              <li className="rail-empty">No agents match “{query}”.</li>
            )}
          </ul>
        </section>

        <section className="rail-section">
          <div className="rail-heading">
            <span>Channels</span>
            <button className="mini-btn" onClick={onNewChannel} title="Create a multi-agent channel">
              <PlusIcon size={13} />
              New
            </button>
          </div>

          <ul className="conv-list">
            {channels.map((conv) => {
              const members = conv.agentIds
                .map((id) => agentsById.get(id))
                .filter((a): a is Agent => Boolean(a));
              const isActive = conv.id === activeConversationId;
              const isTyping = (typing[conv.id] ?? []).length > 0;
              const last = lastMessageAt[conv.id];

              return (
                <li key={conv.id}>
                  <button
                    className={`conv-row${isActive ? ' is-active' : ''}`}
                    onClick={() => onSelectConversation(conv.id)}
                  >
                    <span className="conv-icon">
                      <HashIcon size={14} />
                    </span>
                    <span className="conv-text">
                      <span className="conv-name">{conv.name}</span>
                      <span className="conv-meta">
                        {isTyping ? (
                          <em className="typing-text">responding…</em>
                        ) : (
                          <>
                            <AvatarStack agents={members} size={16} max={3} />
                            <span>{members.length} agents</span>
                          </>
                        )}
                      </span>
                    </span>
                    {last && <span className="conv-time">{formatRelative(last)}</span>}
                  </button>
                </li>
              );
            })}
            {channels.length === 0 && <li className="rail-empty">No channels yet. Create one to collaborate with multiple agents.</li>}
          </ul>
        </section>
      </div>

      <footer className="sidebar-foot">
        {activeGoal && (
          <div className="worker-status" style={{ padding: '8px 12px', marginBottom: 8 }}>
            <div className={`worker-pill${activeGoal.active ? ' running' : ''}`}>
              <span className="dot" />
              <TargetIcon size={11} />
              <span>{activeGoal.active ? 'Worker running' : 'Worker paused'}</span>
            </div>
          </div>
        )}
        <button className="foot-btn" onClick={onNewAgent}>
          <span className="foot-avatar">
            <PlusIcon size={14} />
          </span>
          <span>
            <strong>Add an agent</strong>
            <small>Create or program an agent</small>
          </span>
        </button>
        {onOpenGoal && activeConversationId && (
          <button className="foot-btn" onClick={onOpenGoal} style={{ marginTop: 8 }}>
            <span className="foot-avatar">
              <TargetIcon size={14} />
            </span>
            <span>
              <strong>Room goal</strong>
              <small>Set or edit the autonomous goal</small>
            </span>
          </button>
        )}
      </footer>
    </aside>
  );
}
