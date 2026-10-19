/**
 * Tool-surface browser.
 *
 * Built from the live `tools/list` response (see `api/mcp.ts`), so every row is
 * a tool the server actually registered — 257 of them, 36 namespace prefixes.
 * Two things this surface is careful about:
 *
 *  • **It never claims an MCP connection it does not have.** The header says
 *    whether this is a fresh handshake or the checked-in capture, and the
 *    capture is labelled with when and where it was taken.
 *  • **It shows the schema, not a paraphrase.** Parameter names and required-ness
 *    come straight from `inputSchema`, because that is what an agent has to
 *    satisfy to call the tool.
 *
 * The proxy matters here: the MCP transport sends no CORS preflight headers, so
 * a browser can only reach it through `/api/mcp`.
 */

import { useMemo, useState } from 'react';
import { domainLabel, filterTools, groupByDomain, loadTools, probeMcp, toolStats } from '../api/mcp';
import type { ToolEntry } from '../api/types';
import { useAsync } from '../lib/useAsync';
import {
  CaptureNotice,
  Chip,
  EmptyState,
  ErrorState,
  IconBook,
  IconCube,
  IconInfo,
  IconRefresh,
  IconSearch,
  IconX,
  LoadingState,
  Notice,
  Provenance,
  Stat,
  plural,
} from '../components/ui';

export default function ToolsView() {
  const tools = useAsync(loadTools, []);
  const [query, setQuery] = useState('');
  const [domain, setDomain] = useState('');
  const [requiresArgs, setRequiresArgs] = useState(false);
  const [openTool, setOpenTool] = useState<string | null>(null);
  const [probe, setProbe] = useState<{
    ok: boolean;
    detail: string;
    latencyMs: number;
    count?: number;
  } | null>(null);
  const [probing, setProbing] = useState(false);

  const all: ToolEntry[] = tools.data?.data ?? [];
  const stats = useMemo(() => toolStats(all), [all]);
  const domains = useMemo(() => groupByDomain(all), [all]);

  const filtered = useMemo(
    () => filterTools(all, { query, domain, requiresArgs }),
    [all, query, domain, requiresArgs],
  );

  const grouped = useMemo(
    () => (domain || query ? null : groupByDomain(filtered)),
    [filtered, domain, query],
  );

  if (tools.loading) return <LoadingState rows={5} label="Reading the tool surface" />;
  if (tools.error) return <ErrorState error={tools.error} onRetry={tools.reload} />;

  const loaded = tools.data!;

  return (
    <>
      <div className="spread" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div className="flex" style={{ flexWrap: 'wrap' }}>
          <Provenance loaded={loaded} what="Tool surface" />
          <Chip tone="accent">{plural(stats.total, 'tool')}</Chip>
          <Chip>{plural(stats.domains, 'namespace')}</Chip>
          <Chip tone="dream">{stats.memoryTools} memory_*</Chip>
        </div>
        <div className="flex">
          <button type="button" className="btn btn-sm" onClick={tools.reload}>
            <IconRefresh size={13} /> Re-read
          </button>
          <button
            type="button"
            className="btn btn-sm"
            disabled={probing}
            onClick={async () => {
              setProbing(true);
              setProbe(await probeMcp());
              setProbing(false);
            }}
          >
            {probing ? 'Handshaking…' : 'Test handshake'}
          </button>
        </div>
      </div>

      <CaptureNotice loaded={loaded} />

      {probe ? (
        <div style={{ marginBottom: 12 }}>
          <Notice tone={probe.ok ? 'ok' : 'error'}>
            {probe.ok
              ? `Handshake OK in ${probe.latencyMs}ms — ${probe.count} tools listed over the live transport.`
              : `Handshake failed: ${probe.detail}. The tool list above is the capture, not a live read.`}
          </Notice>
        </div>
      ) : null}

      <div className="stat-row" style={{ marginBottom: 14 }}>
        <Stat label="Tools" value={stats.total} hint="registered on the server" />
        <Stat label="Namespaces" value={stats.domains} hint="by name prefix" />
        <Stat label="With params" value={stats.withParams} hint="declared input schema" />
        <Stat label="Parameters" value={stats.params} hint="across all tools" />
      </div>

      <div className="flex" style={{ marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div className="search" style={{ maxWidth: 420 }}>
          <IconSearch className="search-icon" />
          <input
            className="input"
            placeholder="Search names, descriptions, parameters…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search tools"
          />
        </div>
        <select
          className="select"
          style={{ width: 'auto', minWidth: 180 }}
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          aria-label="Filter by namespace"
        >
          <option value="">All namespaces</option>
          {domains.map((d) => (
            <option key={d.id} value={d.id}>
              {domainLabel(d.id)} ({d.count})
            </option>
          ))}
        </select>
        <label className="flex" style={{ fontSize: 12.5, color: 'var(--text-dim)', gap: 6 }}>
          <input
            type="checkbox"
            checked={requiresArgs}
            onChange={(e) => setRequiresArgs(e.target.checked)}
          />
          Requires arguments
        </label>
        {query || domain || requiresArgs ? (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setQuery('');
              setDomain('');
              setRequiresArgs(false);
            }}
          >
            <IconX size={12} /> Clear
          </button>
        ) : null}
        <span className="muted" style={{ fontSize: 11.5, marginLeft: 'auto' }}>
          {plural(filtered.length, 'result')}
        </span>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No tool matches" icon={<IconSearch size={20} />}>
          Searched {stats.total} registered tools. Try a namespace like <code>memory</code> or{' '}
          <code>braid</code>.
        </EmptyState>
      ) : grouped ? (
        <div style={{ display: 'grid', gap: 12 }}>
          {grouped.map((d) => (
            <section key={d.id} className="card">
              <header className="card-header">
                <IconCube size={15} />
                <h2>{domainLabel(d.id)}</h2>
                <Chip>{d.count}</Chip>
                <span className="spacer" />
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => setDomain(d.id)}
                  title="Filter to this namespace"
                >
                  Only this
                </button>
              </header>
              <div style={{ padding: '4px 0' }}>
                {d.tools.map((t) => (
                  <ToolRow
                    key={t.name}
                    tool={t}
                    open={openTool === t.name}
                    onToggle={() => setOpenTool(openTool === t.name ? null : t.name)}
                    isStart={t.name === d.startHere}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="card">
          {filtered.map((t) => (
            <ToolRow
              key={t.name}
              tool={t}
              open={openTool === t.name}
              onToggle={() => setOpenTool(openTool === t.name ? null : t.name)}
            />
          ))}
        </div>
      )}

      <div className="notice" style={{ marginTop: 16 }}>
        <IconInfo className="notice-icon" size={16} />
        <div>
          Kanban, dreams and agents are <strong>not</strong> MCP tools — they are REST surfaces. No{' '}
          <span className="mono">kanban_*</span>, <span className="mono">board_*</span>,{' '}
          <span className="mono">dream_*</span> or <span className="mono">agent_*</span> tool exists
          in this registry, which is why those living areas call REST directly.
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------- tool row */

function ToolRow({
  tool,
  open,
  onToggle,
  isStart,
}: {
  tool: ToolEntry;
  open: boolean;
  onToggle: () => void;
  isStart?: boolean;
}) {
  const props = (tool.inputSchema.properties ?? {}) as Record<
    string,
    { type?: string; description?: string }
  >;
  const propNames = Object.keys(props);

  return (
    <div style={{ borderBottom: '1px solid var(--line-soft)' }}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 10,
          width: '100%',
          padding: '10px 16px',
          textAlign: 'left',
        }}
      >
        <span
          className="mono"
          style={{ fontSize: 12.5, fontWeight: 600, minWidth: 0, wordBreak: 'break-all' }}
        >
          {tool.name}
        </span>
        {isStart ? (
          <Chip tone="accent" title="Start here">
            start here
          </Chip>
        ) : null}
        {propNames.length > 0 ? <Chip>{propNames.length} params</Chip> : <Chip>no params</Chip>}
        <span
          className="muted truncate"
          style={{ fontSize: 12, flex: 1, minWidth: 0, textAlign: 'right', maxWidth: 460 }}
        >
          {tool.description}
        </span>
      </button>

      {open ? (
        <div style={{ padding: '0 16px 14px 16px' }}>
          {tool.title ? (
            <div className="stat-label" style={{ marginBottom: 4 }}>
              {tool.title}
            </div>
          ) : null}
          <p style={{ margin: '0 0 10px', fontSize: 12.5, color: 'var(--text-dim)', lineHeight: 1.65 }}>
            {tool.description}
          </p>

          {propNames.length === 0 ? (
            <div className="notice" style={{ fontSize: 11.5 }}>
              No input schema — this tool takes no arguments.
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Type</th>
                  <th>Required</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {propNames.map((p) => (
                  <tr key={p}>
                    <td className="mono">{p}</td>
                    <td className="mono">{props[p]?.type ?? 'any'}</td>
                    <td>
                      {tool.required.includes(p) ? (
                        <Chip tone="amber">yes</Chip>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>
                      {props[p]?.description ?? ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <details style={{ marginTop: 10 }}>
            <summary style={{ cursor: 'pointer', fontSize: 11.5, color: 'var(--text-mute)' }}>
              Raw input schema
            </summary>
            <pre
              style={{
                margin: '8px 0 0',
                padding: 10,
                background: 'var(--bg-panel-2)',
                border: '1px solid var(--line)',
                borderRadius: 'var(--r-sm)',
                fontSize: 11,
                overflow: 'auto',
                maxHeight: 260,
              }}
            >
              {JSON.stringify(tool.inputSchema, null, 2)}
            </pre>
          </details>
        </div>
      ) : null}
    </div>
  );
}

/* Kept so the docs route can deep-link a namespace without importing the view. */
export function ToolNamespaceHint({ domain }: { domain: string }) {
  return (
    <span className="flex" style={{ gap: 5 }}>
      <IconBook size={13} />
      <span className="mono">{domain}</span>
    </span>
  );
}
