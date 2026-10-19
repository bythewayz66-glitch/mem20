/**
 * Connection / status surface.
 *
 * The one screen that answers "what am I actually talking to right now". Every
 * probe here is a real request to a real endpoint, and a failure is reported as
 * a failure with its own message — there is no green light that is not backed by
 * a 200.
 */

import { useState } from 'react';
import {
  CONTROL_BASE,
  DOOR_BASE,
  ENDPOINTS,
  MCP_BASE,
  SNAPSHOT_META,
  SOURCE_MODE,
} from '../api/config';
import { probeDoor } from '../api/kanban';
import { probeControl } from '../api/dreams';
import { probeMcp } from '../api/mcp';
import { Chip, Notice, Stat } from '../components/ui';

interface ProbeResult {
  ok: boolean;
  detail: string;
  latencyMs: number;
  count?: number;
}

export default function StatusView() {
  const [results, setResults] = useState<Record<string, ProbeResult | null>>({
    door: null,
    control: null,
    mcp: null,
  });
  const [running, setRunning] = useState(false);

  const runAll = async () => {
    setRunning(true);
    const [door, control, mcp] = await Promise.all([probeDoor(), probeControl(), probeMcp()]);
    setResults({
      door,
      control: {
        ok: control.ok,
        detail: control.detail,
        latencyMs: control.latencyMs,
      },
      mcp,
    });
    setRunning(false);
  };

  const probed = Object.values(results).filter(Boolean) as ProbeResult[];

  return (
    <>
      <div className="spread" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div className="flex" style={{ flexWrap: 'wrap' }}>
          <Chip tone={SOURCE_MODE === 'live' ? 'green' : 'amber'}>
            source mode: {SOURCE_MODE}
          </Chip>
          {probed.length ? (
            <Chip tone={probed.every((p) => p.ok) ? 'green' : 'red'}>
              {probed.filter((p) => p.ok).length}/{probed.length} reachable
            </Chip>
          ) : null}
        </div>
        <button
          type="button"
          className="btn btn-sm btn-primary"
          onClick={runAll}
          disabled={running}
        >
          {running ? 'Probing all three\u2026' : 'Probe all'}
        </button>
      </div>

      <Notice>
        <strong>source mode is {SOURCE_MODE}.</strong>{' '}
        {SOURCE_MODE === 'snapshot'
          ? 'Each surface tries its live backend first, then falls back to the checked-in capture and says so. Set VITE_SOURCE_MODE=live to forbid the fallback.'
          : 'A dead backend renders an error instead of a capture. Nothing here will show stale data as live.'}
      </Notice>

      <div className="stack" style={{ marginTop: 14 }}>
        {ENDPOINTS.map((endpoint) => {
          const result = results[endpoint.id];
          const proxy =
            endpoint.id === 'door'
              ? DOOR_BASE
              : endpoint.id === 'control'
                ? CONTROL_BASE
                : MCP_BASE;
          return (
            <section key={endpoint.id} className="card">
              <header className="card-header">
                <h2>{endpoint.label}</h2>
                <Chip tone={result ? (result.ok ? 'green' : 'red') : undefined}>
                  {result ? (result.ok ? 'reachable' : 'unreachable') : 'not probed'}
                </Chip>
                {result ? <Chip>{result.latencyMs}ms</Chip> : null}
                <span className="spacer" />
                <button
                  type="button"
                  className="btn btn-sm"
                  disabled={running}
                  onClick={async () => {
                    const next =
                      endpoint.id === 'door'
                        ? await probeDoor()
                        : endpoint.id === 'control'
                          ? await probeControl()
                          : await probeMcp();
                    setResults((prev) => ({ ...prev, [endpoint.id]: next }));
                  }}
                >
                  Probe
                </button>
              </header>
              <div className="card-pad" style={{ display: 'grid', gap: 9 }}>
                <div className="grid-2" style={{ gap: 8 }}>
                  <div>
                    <div className="stat-label">Proxy path</div>
                    <div className="mono" style={{ fontSize: 12 }}>
                      {proxy}
                    </div>
                  </div>
                  <div>
                    <div className="stat-label">Upstream</div>
                    <div className="mono" style={{ fontSize: 12 }}>
                      {endpoint.defaultTarget}
                    </div>
                  </div>
                  <div>
                    <div className="stat-label">Override</div>
                    <div className="mono" style={{ fontSize: 12 }}>
                      {endpoint.envVar}
                    </div>
                  </div>
                </div>

                <div>
                  <div className="stat-label" style={{ marginBottom: 3 }}>
                    Contract
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: 11.5,
                      lineHeight: 1.65,
                      color: 'var(--text-dim)',
                    }}
                  >
                    {endpoint.contract}
                  </p>
                </div>

                {result ? (
                  <div className="notice" data-tone={result.ok ? 'ok' : 'error'}>
                    <div style={{ fontSize: 12 }}>
                      {result.detail}
                      {result.count !== undefined ? ` (${result.count} tools)` : ''}
                    </div>
                  </div>
                ) : null}
              </div>
            </section>
          );
        })}
      </div>

      <div className="card card-pad" style={{ marginTop: 14 }}>
        <div className="stat-label" style={{ marginBottom: 8 }}>
          Capture provenance
        </div>
        <div className="stat-row">
          <Stat
            label="Captured"
            value={
              <span style={{ fontSize: 13 }}>{SNAPSHOT_META.capturedAt.slice(0, 10)}</span>
            }
            hint={SNAPSHOT_META.capturedAt}
          />
          <Stat
            label="From"
            value={<span style={{ fontSize: 13 }}>{SNAPSHOT_META.capturedFrom}</span>}
          />
        </div>
        <table className="table" style={{ marginTop: 10 }}>
          <thead>
            <tr>
              <th>Dataset</th>
              <th>Source</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(SNAPSHOT_META)
              .filter(([, v]) => typeof v === 'object')
              .map(([key, value]) => {
                const v = value as { store: string; note: string };
                return (
                  <tr key={key}>
                    <td className="mono">{key}</td>
                    <td className="mono" style={{ fontSize: 11 }}>
                      {v.store}
                    </td>
                    <td className="dim" style={{ fontSize: 11.5 }}>
                      {v.note}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </>
  );
}
