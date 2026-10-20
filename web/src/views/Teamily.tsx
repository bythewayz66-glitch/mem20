/* Teamily / Gamut Lime — members, roles, groups, activity.
 *
 * No member/role read route exists in mem20controlz today (app.py exposes
 * dreams, websites, registry, cli/coverage and auth only). The role model below
 * is the one the estate actually enforces in mem20botz/identity.py, so the
 * shapes are real even though the roster is not yet live.
 */
import React, { useState } from 'react';
import { Notice, Panel, Pill } from '../components/ui';

const ROLES = [
  { role: 'operator', who: 'jayson', may: 'everything, privileged commands included — by direct message only', tone: 'violet' as const },
  { role: 'crew', who: 'registered agents', may: 'take and report work; read everything', tone: 'cyan' as const },
  { role: 'guest', who: 'anyone else', may: 'read-only self-description', tone: '' as const },
];

const RULES = [
  ['a guest cannot take work', 'a stranger should not be able to claim the operator’s board.'],
  ['a privileged command is refused in the channel', 'even from the operator — the transcript is readable by everyone in it, so an instruction sent there could be replayed by a guest.'],
  ['a nick is a claim, not proof', 'an IRC nick is not authentication, so authority is scoped to match what the nick can prove.'],
];

export default function Teamily() {
  const [tab, setTab] = useState<'members' | 'roles' | 'groups' | 'activity'>('members');

  return (
    <div className="page">
      <p className="lede">
        Teamily is the agent workspace — a chat front end over agents on your own server. This shell is built on that base, so
        the surface keeps its four concerns: members, roles, groups and activity.
      </p>

      <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
        {(['members', 'roles', 'groups', 'activity'] as const).map((t) => (
          <button key={t} className={`btn sm ${tab === t ? 'primary' : ''}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'members' && (
        <Panel title="Members" right={<Pill mono>roster pending</Pill>}>
          <Notice tone="warn" title="No member read route yet">
            The guild roster lives in the agent runtime, not in the control plane this shell talks to. Listing invented members
            would be the exact failure the kanban merge was done to kill, so the table stays empty until a real route exists.
          </Notice>
          <div className="empty" style={{ paddingTop: 24 }}>
            waiting on a <span className="mono">&nbsp;GET /api/teamily/members&nbsp;</span> route on mem20controlz
          </div>
        </Panel>
      )}

      {tab === 'roles' && (
        <Panel title="Roles — the authority model actually enforced">
          <table className="tbl">
            <thead>
              <tr>
                <th>role</th>
                <th>who</th>
                <th>may</th>
              </tr>
            </thead>
            <tbody>
              {ROLES.map((r) => (
                <tr key={r.role}>
                  <td>
                    <Pill tone={r.tone} mono>
                      {r.role}
                    </Pill>
                  </td>
                  <td>{r.who}</td>
                  <td>{r.may}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <hr className="sep" />
          <div style={{ display: 'grid', gap: 11 }}>
            {RULES.map(([t, d]) => (
              <div key={t}>
                <div style={{ color: 'var(--ink-0)', fontWeight: 600, fontSize: 12.5 }}>{t}</div>
                <div style={{ color: 'var(--ink-2)', fontSize: 12.5 }}>{d}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 14, fontSize: 11.5, color: 'var(--ink-3)' }}>
            source: <span className="mono">mem20botz/identity.py</span>
          </div>
        </Panel>
      )}

      {tab === 'groups' && (
        <Panel title="Groups &amp; channels" right={<Pill mono>#mem20</Pill>}>
          <div className="lede" style={{ marginBottom: 12 }}>
            One channel, four bots, each a <em>view</em> rather than a writer: <span className="mono">kanban</span>,{' '}
            <span className="mono">agentz</span>, <span className="mono">crewbot</span>, <span className="mono">relay</span>.
          </div>
          <table className="tbl">
            <thead>
              <tr>
                <th>nick</th>
                <th>what it is for</th>
                <th>what it reads</th>
              </tr>
            </thead>
            <tbody>
              <tr><td className="mono">kanban</td><td>advertises open work, records claims and completions</td><td className="mono">mem20-kanban :8221</td></tr>
              <tr><td className="mono">agentz</td><td>chat access to the agent platform</td><td className="mono">mem20agentz cli</td></tr>
              <tr><td className="mono">crewbot</td><td>chat access to the crew runtime</td><td className="mono">python -m mem20crewz</td></tr>
              <tr><td className="mono">relay</td><td>scribes the channel into memory, masks secret-shaped text</td><td className="mono">mem20 memory</td></tr>
            </tbody>
          </table>
          <div style={{ marginTop: 12 }}>
            <Notice tone="warn" title="Channel state is not streamed into this shell">
              A browser cannot speak IRC on <span className="mono">127.0.0.1:6667</span>; it needs a websocket bridge. The table
              above is the real bot map from <span className="mono">mem20botz/README.md</span>; live presence is pending that bridge.
            </Notice>
          </div>
        </Panel>
      )}

      {tab === 'activity' && (
        <Panel title="Activity">
          <Notice tone="warn" title="No activity feed to read">
            Activity would come from the same channel bridge as presence. Until then this surface shows nothing rather than a
            plausible-looking stream.
          </Notice>
        </Panel>
      )}
    </div>
  );
}
