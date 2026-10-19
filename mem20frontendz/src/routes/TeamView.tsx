/**
 * Team surface — the teamz workspace, hosted inside the mem20 shell.
 *
 * This is the original teamz application (AgentSettings, ChatPane, Sidebar,
 * NewAgentDialog, ChannelDialog, @mention routing) mounted unchanged. It is
 * imported rather than copied so the teamz code stays a single, upgradable
 * subtree under `src/teamz/`, and its own LICENSE ships alongside it.
 *
 * What the shell adds is framing: a real route in the nav, and the note that the
 * chat transport is in mock mode unless `VITE_API_MODE=live` — stated, because a
 * mock reply that reads as a real agent response would be a lie.
 */

import TeamzApp from '../teamz/App';
import { API_MODE } from '../teamz/api/agents';
import { Chip } from '../components/ui';

export default function TeamView() {
  return (
    <div
      style={{
        // Team owns the whole viewport: it is a full-height chat app, not a card.
        margin: '-20px -22px -56px',
        height: 'calc(100dvh - 62px)',
        overflow: 'hidden',
      }}
    >
      <div style={{ height: '100%' }}>
        <TeamzApp />
      </div>
    </div>
  );
}

/** Shown in the shell topbar so the transport mode is never a surprise. */
export function TeamModeChip() {
  return (
    <Chip
      tone={API_MODE === 'live' ? 'green' : 'amber'}
      title={
        API_MODE === 'live'
          ? 'Replies come from each agent\u2019s own endpoint.'
          : 'Replies are generated locally. Set VITE_API_MODE=live to reach real endpoints.'
      }
    >
      chat: {API_MODE}
    </Chip>
  );
}
