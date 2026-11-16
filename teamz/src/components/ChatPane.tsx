import { useEffect, useMemo, useRef, useState } from 'react';
import type { Agent, Conversation, Message, MessageFilter } from '../types';
import { AgentAvatar, StatusDot } from './Avatar';
import { RichText } from './RichText';
import { MentionAutocomplete } from './MentionAutocomplete';
import {
  ChatIcon,
  CloseIcon,
  HashIcon,
  PlusIcon,
  SendIcon,
  SettingsIcon,
  TrashIcon,
  UsersIcon,
  TargetIcon,
  PlayIcon,
  PauseIcon,
} from './Icons';
import { formatDayLabel, formatTime, isNewDay } from '../lib/format';
import { activeQuery, applyMention, parseMentions, rankMentions } from '../lib/mentions';
import { selectRelevantAgents } from '../lib/relevance';
import { optimizePromptWithOrchestrator } from '../api/orchestrator';
import { getSettings } from '../api/settings';

interface ChatPaneProps {
  conversation: Conversation | null;
  messages: Message[];
  agentsById: Map<string, Agent>;
  allAgents: Agent[];
  typingAgentIds: string[];
  canReply: boolean;
  filter: MessageFilter;
  onSetFilter: (filter: MessageFilter) => void;
  onSend: (text: string, opts?: { replyToId?: string }) => void;
  onOpenAgentSettings: (agentId: string) => void;
  onManageMembers: () => void;
  onDeleteConversation: () => void;
  onOpenDirectChat: (agentId: string) => void;
  onInviteAgent: (agentId: string) => void;
  apiMode: string;
  modeLabel?: string;
  onOpenSettings?: () => void;
  onUnsendMessage: (conversationId: string, messageId: string) => void;
  onDeleteMessage: (conversationId: string, messageId: string) => void;
  onToggleAttention: (conversationId: string, messageId: string) => void;
  // Goal / worker
  conversationGoal?: { text: string; active: boolean; progress?: number } | null;
  onSetGoal?: (conversationId: string, text: string, active?: boolean) => void;
  onWorkerControl?: (action: 'start' | 'stop' | 'tick') => void;
  workerStatus?: { running: boolean; activeGoals: string[] } | null;
}

type MsgActionMenu = {
  messageId: string;
  x: number;
  y: number;
} | null;

function WandIcon({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M15 4V2M15 16v-2M8 9h2M20 9h2M17.8 11.8L19 13M17.8 6.2L19 5M3 21l9-9M12.2 6.2L11 5" />
    </svg>
  );
}

function ReplyIcon({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9 17l-5-5 5-5" />
      <path d="M20 18v-2a4 4 0 00-4-4H4" />
    </svg>
  );
}

function FlagIcon({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 21V5a1 1 0 011-1h9.5a1 1 0 01.8.4l.7.93a1 1 0 00.8.4H20v9h-2.7a1 1 0 01-.8-.4l-.7-.93a1 1 0 00-.8-.4H6" />
    </svg>
  );
}

function UndoIcon({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9 14L4 9l5-5" />
      <path d="M20 20v-7a4 4 0 00-4-4H4" />
    </svg>
  );
}

function pickRelevantPreview(conversation: Conversation | null, members: Agent[], draft: string): Agent[] {
  if (!conversation || conversation.kind !== 'channel') return [];
  const trimmed = draft.trim();
  if (!trimmed) return [];
  const mentioned = parseMentions(trimmed, members);
  if (mentioned.length > 0) return mentioned;
  return selectRelevantAgents(trimmed, members, conversation, { minResponders: 1, maxResponders: Math.min(3, members.length) });
}

export function ChatPane({
  conversation,
  messages,
  agentsById,
  allAgents,
  typingAgentIds,
  canReply,
  filter,
  onSetFilter,
  onSend,
  onOpenAgentSettings,
  onManageMembers,
  onDeleteConversation,
  onOpenDirectChat,
  onInviteAgent,
  apiMode,
  modeLabel,
  onOpenSettings,
  onUnsendMessage,
  onDeleteMessage,
  onToggleAttention,
  conversationGoal,
  onSetGoal,
  onWorkerControl,
}: ChatPaneProps) {
  const [draft, setDraft] = useState('');
  const [showMembers, setShowMembers] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [mentionIndex, setMentionIndex] = useState(0);
  const [replyToId, setReplyToId] = useState<string | null>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [actionMenu, setActionMenu] = useState<MsgActionMenu>(null);
  const longPressTimer = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [mentionToken, setMentionToken] = useState<{
    query: string;
    start: number;
    end: number;
  } | null>(null);

  const members = useMemo(
    () =>
      (conversation?.agentIds ?? [])
        .map((id) => agentsById.get(id))
        .filter((a): a is Agent => Boolean(a)),
    [conversation, agentsById],
  );

  const messagesById = useMemo(() => new Map(messages.map((m) => [m.id, m])), [messages]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages.length, conversation?.id, typingAgentIds.length]);

  useEffect(() => {
    setDraft('');
    setShowMembers(false);
    setShowInvite(false);
    setMentionToken(null);
    setReplyToId(null);
    setActionMenu(null);
  }, [conversation?.id]);

  useEffect(() => {
    if (!actionMenu) return;
    const close = () => setActionMenu(null);
    window.addEventListener('click', close);
    window.addEventListener('scroll', close, true);
    window.addEventListener('resize', close);
    return () => {
      window.removeEventListener('click', close);
      window.removeEventListener('scroll', close, true);
      window.removeEventListener('resize', close);
    };
  }, [actionMenu]);

  const mentions = useMemo(
    () => (mentionToken ? rankMentions(mentionToken.query, members) : []),
    [mentionToken, members],
  );

  useEffect(() => {
    if (mentionIndex >= mentions.length) setMentionIndex(0);
  }, [mentions.length, mentionIndex]);

  const syncMention = (value: string, caret: number) => {
    const token = activeQuery(value, caret);
    setMentionToken(token);
    if (!token) setMentionIndex(0);
  };

  const commitMention = (agent: Agent) => {
    const el = textareaRef.current;
    const token = mentionToken ?? (el ? activeQuery(draft, el.selectionStart ?? draft.length) : null);
    if (!token) return;
    const { text, caret } = applyMention(draft, token, agent.name);
    setDraft(text);
    setMentionToken(null);
    setMentionIndex(0);
    requestAnimationFrame(() => {
      if (!el) return;
      el.focus();
      el.setSelectionRange(caret, caret);
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    });
  };

  const handleMentionKeys = (e: React.KeyboardEvent<HTMLTextAreaElement>): boolean => {
    if (!mentionToken || mentions.length === 0) {
      if (e.key === 'Escape' && mentionToken) {
        setMentionToken(null);
        return true;
      }
      return false;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setMentionIndex((i) => (i + 1) % mentions.length);
      return true;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setMentionIndex((i) => (i - 1 + mentions.length) % mentions.length);
      return true;
    }
    if (e.key === 'Enter' || e.key === 'Tab') {
      e.preventDefault();
      commitMention(mentions[mentionIndex] ?? mentions[0]);
      return true;
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      setMentionToken(null);
      return true;
    }
    return false;
  };

  const autoGrow = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  const submit = () => {
    const text = draft.trim();
    if (!text || !canReply) return;
    onSend(text, replyToId ? { replyToId } : undefined);
    setDraft('');
    setMentionToken(null);
    setReplyToId(null);
    requestAnimationFrame(() => {
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    });
  };

  const doOptimizePrompt = async () => {
    const text = draft.trim();
    if (!text || !conversation) return;
    setOptimizing(true);
    try {
      const history = messages
        .filter((m) => m.status === 'sent' && !m.deleted && !m.unsent && m.text.trim())
        .slice(-20)
        .map((m) => ({
          role: m.authorType === 'user' ? 'user' : 'assistant',
          authorType: m.authorType,
          authorName: m.authorType === 'user' ? 'User' : agentsById.get(m.authorId ?? '')?.name ?? 'Agent',
          text: m.text,
        }));
      const agents = members.map((a) => ({ id: a.id, name: a.name, isLead: a.isLead, origin: a.origin, skills: a.skills, model: a.model }));
      const settings = getSettings();
      if (settings.provider === 'orchestrator') {
        const res = await optimizePromptWithOrchestrator({
          draft: text,
          conversation: { id: conversation.id, name: conversation.name, kind: conversation.kind, topic: conversation.topic },
          history,
          agents,
          useMemory: true,
        });
        if (res?.prompt?.trim()) setDraft(res.prompt.trim());
      } else {
        // Local heuristic improvement when not using orchestrator (still memory/context-aware in content)
        const convLabel = conversation.kind === 'channel' ? `#${conversation.name}` : conversation.name;
        const agentHints = agents.map((a) => a.name).join(', ');
        const improved = `Context: ${convLabel}${conversation.topic ? ` (topic: ${conversation.topic})` : ''}.\nParticipants: ${agentHints || 'current agent'}.\n\nRequest:\n${text}\n\nPlease respond clearly and specifically, using the conversation context above. If you complete a job that benefits from a visual summary, include an HTML presentation in a \`\`\`presentation\`\`\` fenced block.`;
        setDraft(improved);
      }
    } catch (e) {
      console.warn('[teamz] prompt optimization failed', e);
    } finally {
      setOptimizing(false);
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          autoGrow();
        }
      });
    }
  };

  const addressed = useMemo(() => {
    if (!conversation || conversation.kind !== 'channel') return [];
    const trimmed = draft.trim();
    if (!trimmed) return [];
    const mentioned = parseMentions(trimmed, members);
    if (mentioned.length > 0) return mentioned;
    // Preview relevance-based responders for unmentioned messages
    return pickRelevantPreview(conversation, members, trimmed);
  }, [draft, conversation, members]);

  const draftIsDirected = useMemo(() => {
    if (!conversation || conversation.kind !== 'channel') return false;
    return parseMentions(draft, members).length > 0;
  }, [draft, conversation, members]);

  const visibleMessages = useMemo(() => {
    const base = messages.filter((m) => !m.deleted);
    if (!conversation || conversation.kind !== 'channel') return base;
    if (filter.mode === 'all') return base;
    if (filter.mode === 'directed') {
      return base.filter((m) => m.directed || (m.mentions?.length ?? 0) > 0);
    }
    const target = filter.agentId;
    if (!target) return base;
    return base.filter(
      (m) => m.mentions?.includes(target) || (m.authorType === 'agent' && m.authorId === target),
    );
  }, [messages, filter, conversation]);

  const invitable = useMemo(() => {
    if (!conversation) return [];
    const inRoom = new Set(conversation.agentIds);
    return allAgents.filter((a) => !inRoom.has(a.id));
  }, [allAgents, conversation]);

  const lastAgentReply = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.authorType === 'agent' && m.status === 'sent' && m.text.trim() && !m.deleted && !m.unsent) {
        const a = m.authorId ? agentsById.get(m.authorId) : undefined;
        return { name: a?.name ?? 'Agent', text: m.text };
      }
    }
    return null;
  }, [messages, agentsById]);

  const replyTarget = replyToId ? messagesById.get(replyToId) : undefined;
  const replyTargetAuthor = replyTarget
    ? (replyTarget.authorType === 'user' ? 'You' : (replyTarget.authorId ? agentsById.get(replyTarget.authorId)?.name : undefined) ?? 'Agent')
    : null;

  const openActionMenu = (messageId: string, x: number, y: number) => {
    const vw = typeof window !== 'undefined' ? window.innerWidth : 1000;
    const vh = typeof window !== 'undefined' ? window.innerHeight : 800;
    setActionMenu({ messageId, x: Math.min(x, vw - 220), y: Math.min(y, vh - 260) });
  };

  const onMsgContextMenu = (e: React.MouseEvent, messageId: string) => {
    e.preventDefault();
    openActionMenu(messageId, e.clientX, e.clientY);
  };

  const onTouchStartMsg = (e: React.TouchEvent, messageId: string) => {
    if (e.touches.length !== 1) return;
    const t = e.touches[0];
    if (longPressTimer.current) window.clearTimeout(longPressTimer.current);
    longPressTimer.current = window.setTimeout(() => {
      openActionMenu(messageId, t.clientX, t.clientY);
    }, 450);
  };
  const clearLongPress = () => {
    if (longPressTimer.current) window.clearTimeout(longPressTimer.current);
    longPressTimer.current = null;
  };

  if (!conversation) {
    return (
      <main className="chat-pane empty-pane">
        <div className="empty-card">
          <div className="empty-glyph">🛰️</div>
          <h2>No conversation selected</h2>
          <p>Pick an agent on the left, or start a channel to put several of them in one room.</p>
        </div>
      </main>
    );
  }

  const isChannel = conversation.kind === 'channel';
  const soloAgent = !isChannel ? members[0] : undefined;
  const actionMsg = actionMenu ? messagesById.get(actionMenu.messageId) : undefined;

  return (
    <main className="chat-pane">
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {typingAgentIds.length > 0
          ? `${typingAgentIds
              .map((id) => agentsById.get(id)?.name)
              .filter(Boolean)
              .join(', ')} is typing`
          : lastAgentReply
            ? `${lastAgentReply.name} replied: ${lastAgentReply.text.slice(0, 160)}`
            : ''}
      </div>
      <header className="chat-head">
        <div className="chat-head-id">
          <div className={`chat-head-badge${isChannel ? ' is-channel' : ''}`}>
            {isChannel ? <HashIcon size={17} /> : soloAgent ? <AgentAvatar agent={soloAgent} size={34} showStatus={soloAgent.status} /> : '?'}
          </div>
          <div className="chat-head-text">
            <h1>{conversation.name}{soloAgent?.isLead ? ' · Lead' : ''}</h1>
            <p>
              {isChannel ? (
                <>
                  <UsersIcon size={12} />
                  {members.length} agent{members.length === 1 ? '' : 's'}
                  {conversation.topic ? <span className="dot-sep">·</span> : null}
                  {conversation.topic && <span className="topic">{conversation.topic}</span>}
                </>
              ) : soloAgent ? (
                <>
                  <StatusDot status={soloAgent.status} size={6} />
                  {soloAgent.status}
                  <span className="dot-sep">·</span>
                  <span className="mono">{soloAgent.model}</span>
                  {soloAgent.isLead && <><span className="dot-sep">·</span><span>Lead agent (can orchestrate runtime)</span></>}
                </>
              ) : (
                'No agent attached'
              )}
            </p>
          </div>
        </div>

        <div className="chat-head-actions">
          <button
            className={`member-stack-btn${showMembers ? ' is-open' : ''}`}
            onClick={() => setShowMembers((v) => !v)}
            title="Channel members"
          >
            <span className="member-faces">
              {members.slice(0, 4).map((a) => (
                <AgentAvatar key={a.id} agent={a} size={20} />
              ))}
            </span>
            <span className="member-count">{members.length}</span>
          </button>

          {isChannel && (
            <button className="icon-btn ghost" onClick={onManageMembers} title="Manage members">
              <UsersIcon size={16} />
            </button>
          )}

          {isChannel && (
            <button
              className={`icon-btn ghost${showInvite ? ' is-open' : ''}`}
              onClick={() => setShowInvite((v) => !v)}
              title="Invite an existing agent"
              aria-label="Invite an existing agent"
            >
              <PlusIcon size={16} />
            </button>
          )}

          {soloAgent && (
            <button
              className="icon-btn ghost"
              onClick={() => onOpenAgentSettings(soloAgent.id)}
              title="Agent settings"
            >
              <SettingsIcon size={16} />
            </button>
          )}

          <button
            className="icon-btn ghost danger-hover"
            onClick={onDeleteConversation}
            title={isChannel ? 'Delete channel' : 'Delete chat'}
          >
            <TrashIcon size={15} />
          </button>
        </div>
      </header>

      {showMembers && (
        <div className="members-pop">
          <div className="members-pop-head">
            <strong>In this {isChannel ? 'channel' : 'chat'}</strong>
            <button className="icon-btn ghost" onClick={() => setShowMembers(false)} aria-label="Close">
              <CloseIcon size={14} />
            </button>
          </div>
          <ul>
            {members.map((a) => (
              <li key={a.id}>
                <AgentAvatar agent={a} size={28} showStatus={a.status} />
                <span className="mp-text">
                  <span className="mp-name">{a.name}{a.isLead ? ' (Lead)' : ''}</span>
                  <span className="mp-model">{a.origin?.role ?? a.model}</span>
                </span>
                <button
                  className="icon-btn ghost"
                  onClick={() => onOpenDirectChat(a.id)}
                  title={`Message ${a.name} directly`}
                  aria-label={`Message ${a.name} directly`}
                >
                  <ChatIcon size={13} />
                </button>
                <button
                  className="icon-btn ghost"
                  onClick={() => onOpenAgentSettings(a.id)}
                  title={`${a.name} settings`}
                >
                  <SettingsIcon size={13} />
                </button>
              </li>
            ))}
            {members.length === 0 && <li className="rail-empty">Nobody here yet.</li>}
          </ul>
          {isChannel && (
            <button className="ghost-wide" onClick={onManageMembers}>
              <UsersIcon size={14} /> Manage members
            </button>
          )}
        </div>
      )}

      {showInvite && isChannel && (
        <div className="invite-pop">
          <div className="members-pop-head">
            <strong>Invite an existing agent</strong>
            <button className="icon-btn ghost" onClick={() => setShowInvite(false)} aria-label="Close">
              <CloseIcon size={14} />
            </button>
          </div>
          <p className="invite-note">
            Adds an agent you already have to <strong>#{conversation.name}</strong>. Nothing new is created — to make a new one, use <em>Add an agent</em>.
          </p>
          <ul>
            {invitable.map((a) => (
              <li key={a.id}>
                <AgentAvatar agent={a} size={28} showStatus={a.status} />
                <span className="mp-text">
                  <span className="mp-name">{a.name}{a.isLead ? ' (Lead)' : ''}</span>
                  <span className="mp-model">{a.origin?.role ?? a.model}</span>
                </span>
                <button
                  className="btn primary sm"
                  onClick={() => {
                    onInviteAgent(a.id);
                    setShowInvite(false);
                  }}
                >
                  <PlusIcon size={12} /> Invite
                </button>
              </li>
            ))}
            {invitable.length === 0 && (
              <li className="rail-empty">Every agent in the workspace is already here.</li>
            )}
          </ul>
        </div>
      )}

      {isChannel && conversationGoal && conversationGoal.text && (
        <div className="goal-bar">
          <div className="goal-main">
            <TargetIcon size={14} />
            <div className="goal-text">
              <strong>Goal:</strong> <span>{conversationGoal.text}</span>
            </div>
            <div className="goal-progress">
              <div className="goal-progress-bar" style={{ width: `${Math.min(100, Math.max(0, conversationGoal.progress ?? 0))}%` }} />
            </div>
          </div>
          <div className="goal-actions">
            <label className="goal-active-toggle" title={conversationGoal.active ? 'Worker active' : 'Worker paused'}>
              <input
                type="checkbox"
                checked={conversationGoal.active}
                onChange={(e) => onSetGoal?.(conversation.id, conversationGoal.text, e.target.checked)}
              />
              <span>{conversationGoal.active ? 'Running' : 'Paused'}</span>
            </label>
            {onWorkerControl && (
              <button
                className="btn ghost sm"
                onClick={() => onWorkerControl(conversationGoal.active ? 'stop' : 'start')}
                title={conversationGoal.active ? 'Stop worker' : 'Start worker'}
              >
                {conversationGoal.active ? <PauseIcon size={12} /> : <PlayIcon size={12} />}
              </button>
            )}
            {onSetGoal && (
              <button
                className="btn ghost sm"
                onClick={() => {
                  // Open channel dialog in goal mode
                  // This will be handled by parent
                }}
                title="Edit goal"
              >
                <TargetIcon size={12} />
              </button>
            )}
          </div>
        </div>
      )}

      {isChannel && (
        <div className="filter-bar">
          <span className="filter-label">Show</span>
          <button
            className={`filter-chip${filter.mode === 'all' ? ' is-on' : ''}`}
            onClick={() => onSetFilter({ mode: 'all' })}
            aria-pressed={filter.mode === 'all'}
          >
            Everything
          </button>
          <button
            className={`filter-chip${filter.mode === 'directed' ? ' is-on' : ''}`}
            onClick={() => onSetFilter({ mode: 'directed' })}
            aria-pressed={filter.mode === 'directed'}
            title="Only messages addressed to an agent with @"
          >
            Directed only
          </button>
          {members.map((a) => (
            <button
              key={a.id}
              className={`filter-chip is-agent${
                filter.mode === 'agent' && filter.agentId === a.id ? ' is-on' : ''
              }`}
              style={{ borderColor: `${a.accent}59`, color: a.accent }}
              onClick={() => onSetFilter({ mode: 'agent', agentId: a.id })}
              aria-pressed={filter.mode === 'agent' && filter.agentId === a.id}
              title={`Only the thread addressed to ${a.name}`}
            >
              {a.emoji} {a.name}
            </button>
          ))}
          {filter.mode !== 'all' && (
            <span className="filter-count">
              {visibleMessages.length} of {messages.filter(m=>!m.deleted).length}
            </span>
          )}
        </div>
      )}

      <div className="message-scroll" ref={scrollRef}>
        <div className="message-list">
          <div className="thread-intro">
            <div className="thread-intro-glyph">{isChannel ? <HashIcon size={22} /> : '💬'}</div>
            <h2>{isChannel ? `#${conversation.name}` : conversation.name}</h2>
            <p>
              {isChannel
                ? 'Messages route to the most relevant agents for the task (use @mentions to direct explicitly). The lead agent can orchestrate, create/program agents and channels, and delegate work.'
                : soloAgent?.isLead
                  ? 'This is a direct chat with the lead agent. Ask to add/remove/program agents or the runtime, create channels, configure agents, or orchestrate and delegate work.'
                  : 'This chat is wired to a single agent.'}
            </p>
          </div>

          {messages.filter(m=>!m.deleted).length === 0 && (
            <div className="empty-thread">
              <p>No messages yet — say hello to start the thread.</p>
              <div className="suggestion-row">
                {['What are you working on right now?', 'Summarise our last decision', 'Draft a plan for today'].map(
                  (s) => (
                    <button key={s} className="suggestion" onClick={() => onSend(s)}>
                      {s}
                    </button>
                  ),
                )}
              </div>
            </div>
          )}

          {visibleMessages.length === 0 && messages.filter(m=>!m.deleted).length > 0 && (
            <div className="empty-thread">
              <p>
                No messages match this filter. Switch back to <strong>Everything</strong> to see the whole channel.
              </p>
            </div>
          )}

          {visibleMessages.map((m, i) => {
            const prev = visibleMessages[i - 1];
            const agent = m.authorId ? agentsById.get(m.authorId) : undefined;
            const showDay = isNewDay(prev?.createdAt, m.createdAt);
            const groupedWithPrev =
              prev &&
              prev.authorType === m.authorType &&
              prev.authorId === m.authorId &&
              m.createdAt - prev.createdAt < 3 * 60_000 &&
              !showDay;
            const repliedTo = m.replyToId ? messagesById.get(m.replyToId) : undefined;

            return (
              <div key={m.id}>
                {showDay && (
                  <div className="day-divider">
                    <span>{formatDayLabel(m.createdAt)}</span>
                  </div>
                )}
                <MessageRow
                  message={m}
                  agent={agent}
                  repliedTo={repliedTo}
                  repliedToAuthor={repliedTo ? (repliedTo.authorType === 'user' ? 'You' : (repliedTo.authorId ? agentsById.get(repliedTo.authorId)?.name : undefined) ?? 'Agent') : undefined}
                  mentioned={
                    m.mentions
                      ? m.mentions
                          .map((id) => agentsById.get(id))
                          .filter((a): a is Agent => Boolean(a))
                      : []
                  }
                  isChannel={isChannel}
                  grouped={Boolean(groupedWithPrev)}
                  onOpenAgentSettings={onOpenAgentSettings}
                  onOpenDirectChat={onOpenDirectChat}
                  onContextMenu={(e) => onMsgContextMenu(e, m.id)}
                  onTouchStart={(e) => onTouchStartMsg(e, m.id)}
                  onTouchEnd={clearLongPress}
                  onTouchMove={clearLongPress}
                />
              </div>
            );
          })}

          {typingAgentIds.length > 0 && (
            <div className="typing-row" aria-live="polite" aria-atomic="false">
              {typingAgentIds.map((id) => {
                const a = agentsById.get(id);
                if (!a) return null;
                return (
                  <div className="typing-inline" key={id}>
                    <AgentAvatar agent={a} size={22} />
                    <span className="dots" aria-label={`${a.name} is typing`}>
                      <i /> <i /> <i />
                    </span>
                    <span className="typing-label">{a.name} is thinking…</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {actionMenu && actionMsg && (
        <div
          className="msg-action-menu"
          style={{ position: 'fixed', top: actionMenu.y, left: actionMenu.x, zIndex: 50 }}
          onClick={(e) => e.stopPropagation()}
          role="menu"
        >
          <button className="msg-action-item" onClick={() => { setReplyToId(actionMsg.id); setActionMenu(null); textareaRef.current?.focus(); }}>
            <ReplyIcon /> Reply / bring attention
          </button>
          <button className="msg-action-item" onClick={() => { onToggleAttention(conversation.id, actionMsg.id); if (!actionMsg.attention) setReplyToId(actionMsg.id); setActionMenu(null); }}>
            <FlagIcon /> {actionMsg.attention ? 'Remove attention' : 'Bring attention'}
          </button>
          {actionMsg.authorType === 'user' && actionMsg.status === 'sent' && !actionMsg.unsent && (
            <button className="msg-action-item" onClick={() => { onUnsendMessage(conversation.id, actionMsg.id); setActionMenu(null); }}>
              <UndoIcon /> Unsend
            </button>
          )}
          <button className="msg-action-item danger" onClick={() => { onDeleteMessage(conversation.id, actionMsg.id); if (replyToId === actionMsg.id) setReplyToId(null); setActionMenu(null); }}>
            <TrashIcon size={14} /> Delete message
          </button>
        </div>
      )}

      <div className="composer-wrap">
        {mentionToken && mentions.length > 0 && (
          <MentionAutocomplete
            agents={mentions}
            activeIndex={mentionIndex}
            onHover={setMentionIndex}
            onPick={commitMention}
            top={0}
            left={12}
          />
        )}

        {replyToId && replyTarget && (
          <div className="reply-banner">
            <span className="reply-banner-label"><ReplyIcon size={13} /> Replying to <strong>{replyTargetAuthor}</strong></span>
            <span className="reply-banner-text">{(replyTarget.text || '(message)').slice(0, 120)}</span>
            <button className="icon-btn ghost" onClick={() => setReplyToId(null)} aria-label="Cancel reply"><CloseIcon size={12} /></button>
          </div>
        )}

        {addressed.length > 0 && (
          <div className="addressed-row">
            <span className="addressed-label">{draftIsDirected ? 'Directed to' : 'Likely responders'}</span>
            {addressed.map((a) => (
              <button
                key={a.id}
                className="addressed-chip"
                style={{ borderColor: `${a.accent}59`, color: a.accent }}
                onClick={() => onOpenDirectChat(a.id)}
                title={`Open the DM with ${a.name}`}
              >
                {a.emoji} {a.name}{a.isLead ? ' · Lead' : ''}
              </button>
            ))}
            <span className="addressed-hint">{draftIsDirected ? 'only these answer' : 'relevance-based (use @ to direct)'}</span>
          </div>
        )}

        <div className={`composer${canReply ? '' : ' is-disabled'}`}>
          <button
            type="button"
            className="icon-btn ghost"
            onClick={doOptimizePrompt}
            disabled={!draft.trim() || !canReply || optimizing}
            title="Improve prompt using conversation and memory context"
            aria-label="Improve prompt"
          >
            <WandIcon size={16} />
          </button>
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={(e) => {
              setDraft(e.target.value);
              syncMention(e.target.value, e.target.selectionStart ?? e.target.value.length);
              autoGrow();
            }}
            onKeyDown={(e) => {
              if (handleMentionKeys(e)) return;
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            onClick={(e) =>
              syncMention(draft, (e.target as HTMLTextAreaElement).selectionStart ?? 0)
            }
            onBlur={() => {
              setTimeout(() => setMentionToken(null), 120);
            }}
            placeholder={
              canReply
                ? isChannel
                  ? `Message ${conversation.name}… @ to direct, long-press messages for actions`
                  : `Message ${conversation.name}…`
                : 'Add an agent to start talking'
            }
            rows={1}
            disabled={!canReply}
            aria-label="Message composer"
          />
          <button className="send-btn" onClick={submit} disabled={!draft.trim() || !canReply} aria-label="Send">
            <SendIcon size={17} />
          </button>
        </div>
        <div className="composer-foot">
          <span>
            <kbd>Enter</kbd> send · <kbd>Shift</kbd>+<kbd>Enter</kbd> newline · <kbd>@</kbd> direct · ✨ improve prompt · long-press/right-click message for actions
          </span>
          <button
            type="button"
            className={`mode-pill${apiMode === 'live' ? ' is-live' : ''}`}
            onClick={onOpenSettings}
            title="AI provider settings"
            style={{ cursor: onOpenSettings ? 'pointer' : undefined }}
          >
            {optimizing ? 'optimizing…' : (modeLabel ?? (apiMode === 'live' ? 'live endpoints' : 'mock mode'))}
          </button>
        </div>
      </div>
    </main>
  );
}

function MessageRow({
  message,
  agent,
  repliedTo,
  repliedToAuthor,
  mentioned,
  isChannel,
  grouped,
  onOpenAgentSettings,
  onOpenDirectChat,
  onContextMenu,
  onTouchStart,
  onTouchEnd,
  onTouchMove,
}: {
  message: Message;
  agent?: Agent;
  repliedTo?: Message;
  repliedToAuthor?: string;
  mentioned: Agent[];
  isChannel: boolean;
  grouped: boolean;
  onOpenAgentSettings: (agentId: string) => void;
  onOpenDirectChat: (agentId: string) => void;
  onContextMenu: (e: React.MouseEvent) => void;
  onTouchStart: (e: React.TouchEvent) => void;
  onTouchEnd: () => void;
  onTouchMove: () => void;
}) {
  const isUser = message.authorType === 'user';
  const isPending = message.status === 'pending';
  const isError = message.status === 'error';
  const accent = agent?.accent ?? '#7c9cff';
  const displayText = message.unsent ? '_Message unsent_' : message.text;

  return (
    <div
      className={`msg-row ${isUser ? 'is-user' : 'is-agent'}${grouped ? ' is-grouped' : ''}${message.attention ? ' is-attention' : ''}${message.unsent ? ' is-unsent' : ''}`}
      onContextMenu={onContextMenu}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      onTouchMove={onTouchMove}
      onTouchCancel={onTouchEnd}
    >
      <div className="msg-gutter">
        {!isUser && agent && !grouped ? (
          <AgentAvatar agent={agent} size={30} />
        ) : !isUser && agent ? (
          <span className="gutter-time">{formatTime(message.createdAt)}</span>
        ) : null}
      </div>

      <div className="msg-body">
        {!grouped && (
          <div className="msg-head">
            <span
              className="msg-author"
              style={{ color: isUser ? undefined : accent }}
              onClick={() => !isUser && agent && onOpenAgentSettings(agent.id)}
              role={!isUser && agent ? 'button' : undefined}
            >
              {isUser ? 'You' : agent?.name ?? 'Agent'}
            </span>
            {!isUser && isChannel && agent && (
              <span className="msg-badge" style={{ color: accent, borderColor: `${accent}40` }}>
                agent{agent.isLead ? ' · lead' : ''}
              </span>
            )}
            {isUser && mentioned.length > 0 && (
              <span className="msg-badge is-directed">directed</span>
            )}
            {message.attention && <span className="msg-badge is-attention">attention</span>}
            {message.unsent && <span className="msg-badge">unsent</span>}
            <span className="msg-time">{formatTime(message.createdAt)}</span>
          </div>
        )}

        {repliedTo && (
          <div className="msg-reply-ref" title={repliedTo.text}>
            <ReplyIcon size={12} /> <strong>{repliedToAuthor}</strong>: {(repliedTo.unsent ? 'Message unsent' : repliedTo.text || '…').slice(0, 100)}
          </div>
        )}

        {isUser && mentioned.length > 0 && (
          <div className="msg-mentions">
            {mentioned.map((a) => (
              <button
                key={a.id}
                className="msg-mention-chip"
                style={{ borderColor: `${a.accent}4d`, color: a.accent }}
                onClick={() => onOpenDirectChat(a.id)}
                title={`Open the DM with ${a.name}`}
              >
                @{a.name}
              </button>
            ))}
          </div>
        )}

        <div
          className={`bubble${isUser ? ' bubble-user' : ' bubble-agent'}${isPending ? ' is-pending' : ''}${isError ? ' is-error' : ''}${message.attention ? ' is-attention' : ''}`}
          style={
            !isUser && agent
              ? { borderColor: `${accent}33`, background: `linear-gradient(180deg, ${accent}0f, #151a23 60%)` }
              : undefined
          }
        >
          {isPending && !message.text ? (
            <span className="bubble-typing">
              <i /> <i /> <i />
            </span>
          ) : (
            <RichText text={displayText} />
          )}
        </div>
      </div>
    </div>
  );
}
