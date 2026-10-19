/**
 * Dreams surface.
 *
 * Wired to the mem20controlz routes in `api/dreams.ts`. The rules the server
 * enforces are visible in the UI rather than hidden behind a spinner:
 *
 *   • A **hollow** lineage recorded provider errors, not work. It is listed and
 *     flagged (the server lists it by default on purpose), but promotion is
 *     refused and the button says why before you press it.
 *   • **Promotion is a gate, not a button.** The engine refuses on a hollow
 *     lineage and on a braid chain that does not verify, and a refusal comes
 *     back 200 with `promoted: false`. That reason is rendered verbatim.
 *   • **`promoted` is directory-derived.** It is read from the promotions store
 *     on disk, not from the ledger, so a pack written elsewhere will not appear.
 *     The panel states that limitation instead of implying ledger provenance.
 *   • **Verification is a POST.** Proving every braid node is real work, so it is
 *     an explicit action and the only thing that can report `verified: true`.
 *
 * The store on sidney held zero lineages at capture. This surface therefore
 * renders an empty store with the exact path it looked in — it does not seed
 * demo dreams, because a fabricated dream would be the worst possible thing to
 * show in a product whose whole premise is grounded vs simulated.
 */

import { useState } from 'react';
import {
  ControlError,
  createDream,
  loadChain,
  loadDream,
  loadDreams,
  loadHollow,
  loadIdleStats,
  loadManifest,
  loadRuns,
  probeControl,
  promoteDream,
  startRun,
  verifyDream,
} from '../api/dreams';
import type { DreamDetail, DreamRow } from '../api/types';
import { useAsync } from '../lib/useAsync';
import {
  CaptureNotice,
  Chip,
  EmptyState,
  ErrorState,
  IconCheck,
  IconDream,
  IconInfo,
  IconMoon,
  IconPlay,
  IconRefresh,
  IconSearch,
  IconShield,
  IconWarn,
  LoadingState,
  Modal,
  Notice,
  Provenance,
  Stat,
  plural,
  relTime,
} from '../components/ui';

type Tab = 'lineages' | 'runs' | 'hollow';

export default function DreamsView({ param }: { param: string }) {
  const [tab, setTab] = useState<Tab>('lineages');
  const [kind, setKind] = useState('');
  const [query, setQuery] = useState('');
  const [onlyUnpromoted, setOnlyUnpromoted] = useState(false);
  const [openId, setOpenId] = useState<string | null>(param || null);
  const [showNew, setShowNew] = useState(false);

  const dreams = useAsync(() => loadDreams({ kind, onlyUnpromoted }), [kind, onlyUnpromoted]);
  const envelope = dreams.data;
  const list = envelope?.list.data ?? null;

  if (dreams.loading) return <LoadingState rows={4} label="Reading dream lineages" />;
  if (dreams.error) return <ErrorState error={dreams.error} onRetry={dreams.reload} />;

  const filtered = (list?.dreams ?? []).filter((d) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      d.dream_id.toLowerCase().includes(q) ||
      (d.kind ?? '').toLowerCase().includes(q) ||
      (d.hollow_why ?? '').toLowerCase().includes(q)
    );
  });

  return (
    <>
      <div className="spread" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div className="flex" style={{ flexWrap: 'wrap' }}>
          {envelope ? <Provenance loaded={envelope.list} what="Dreams" /> : null}
          {list ? (
            <>
              <Chip tone="dream">{plural(list.total, 'lineage')}</Chip>
              <Chip tone="green">{list.dreams.filter((d) => d.promoted).length} promoted</Chip>
              <Chip tone="red">{list.dreams.filter((d) => d.hollow).length} hollow</Chip>
            </>
          ) : null}
        </div>
        <div className="flex">
          <button type="button" className="btn btn-sm" onClick={dreams.reload}>
            <IconRefresh size={13} /> Refresh
          </button>
          <button type="button" className="btn btn-sm btn-primary" onClick={() => setShowNew(true)}>
            <IconMoon size={13} /> New dream
          </button>
        </div>
      </div>

      {envelope ? <CaptureNotice loaded={envelope.list} /> : null}

      <div className="tabs" role="tablist" aria-label="Dream surfaces">
        <button
          type="button"
          role="tab"
          className="tab"
          aria-selected={tab === 'lineages'}
          onClick={() => setTab('lineages')}
        >
          Lineages
        </button>
        <button
          type="button"
          role="tab"
          className="tab"
          aria-selected={tab === 'runs'}
          onClick={() => setTab('runs')}
        >
          Runs
        </button>
        <button
          type="button"
          role="tab"
          className="tab"
          aria-selected={tab === 'hollow'}
          onClick={() => setTab('hollow')}
        >
          Hollow census
        </button>
      </div>

      <div style={{ paddingTop: 16 }}>
        {tab === 'lineages' ? (
          envelope?.empty || !list ? (
            <EmptyStore />
          ) : (
            <>
              <div className="flex" style={{ marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                <div className="search" style={{ maxWidth: 340 }}>
                  <IconSearch className="search-icon" />
                  <input
                    className="input"
                    placeholder="Filter by id, kind or reason…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    aria-label="Filter dreams"
                  />
                </div>
                <select
                  className="select"
                  style={{ width: 'auto', minWidth: 150 }}
                  value={kind}
                  onChange={(e) => setKind(e.target.value)}
                  aria-label="Filter by kind"
                >
                  <option value="">All kinds</option>
                  {(list.kinds ?? []).map((k) => (
                    <option key={k} value={k}>
                      {k}
                    </option>
                  ))}
                </select>
                <label className="flex" style={{ fontSize: 12.5, color: 'var(--text-dim)', gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={onlyUnpromoted}
                    onChange={(e) => setOnlyUnpromoted(e.target.checked)}
                  />
                  Unpromoted only
                </label>
              </div>

              <div className="stat-row" style={{ marginBottom: 14 }}>
                <Stat
                  label="Total"
                  value={list.total}
                  hint={list.artifacts_included ? '' : 'bodies excluded'}
                />
                <Stat label="Returned" value={list.returned} hint={`read in ${list.read_s}s`} />
                <Stat label="Hidden hollow" value={list.hidden_hollow} hint="when excluded" />
                <Stat
                  label="Promotions root"
                  value={
                    <span className="mono" style={{ fontSize: 11 }}>
                      {list.promotions_root.split('/').slice(-1)[0]}
                    </span>
                  }
                  hint={list.promotions_root}
                />
              </div>

              {filtered.length === 0 ? (
                <EmptyState title="Nothing matches that filter" icon={<IconSearch size={20} />} />
              ) : (
                <div style={{ display: 'grid', gap: 8 }}>
                  {filtered.map((row) => (
                    <DreamCard
                      key={row.dream_id}
                      row={row}
                      onOpen={() => setOpenId(row.dream_id)}
                    />
                  ))}
                </div>
              )}

              {list.artifacts_note ? (
                <p className="muted" style={{ fontSize: 11.5, marginTop: 12 }}>
                  {list.artifacts_note}
                </p>
              ) : null}
            </>
          )
        ) : null}

        {tab === 'runs' ? <RunsPanel /> : null}
        {tab === 'hollow' ? <HollowPanel /> : null}
      </div>

      {openId ? (
        <DreamDetailPanel
          dreamId={openId}
          onClose={() => setOpenId(null)}
          onChanged={dreams.reload}
        />
      ) : null}
      {showNew ? (
        <NewDreamModal
          onClose={() => setShowNew(false)}
          onCreated={() => {
            setShowNew(false);
            dreams.reload();
          }}
        />
      ) : null}
    </>
  );
}

/* ------------------------------------------------------------ empty store */

function EmptyStore() {
  return (
    <div className="card card-pad" style={{ display: 'grid', gap: 14 }}>
      <EmptyState title="The dream store is empty" icon={<IconDream size={22} />}>
        The control plane answered, and the lineage store it reads holds nothing.
      </EmptyState>
      <div className="notice">
        <IconInfo className="notice-icon" size={16} />
        <div>
          It looks in <span className="mono">/opt/mem20/store/dreams</span> for lineages and{' '}
          <span className="mono">/opt/mem20/store/promotions</span> for packs. Neither directory
          existed on <span className="mono">sidney</span> at capture time, so there are zero lineages
          and zero promotions to show. Nothing here is a placeholder — an empty store is the true
          state.
        </div>
      </div>
      <div className="notice" data-tone="ok">
        <IconCheck className="notice-icon" size={16} />
        <div>
          Creating a dream is free: <span className="mono">POST /api/dreams</span> with a seed calls
          no model. Only <span className="mono">run</span> spends money, and it is bounded to{' '}
          <span className="mono">20</span> iterations.
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------ dream cards */

function DreamCard({ row, onOpen }: { row: DreamRow; onOpen: () => void }) {
  return (
    <article
      className="card"
      style={{
        padding: '12px 14px',
        display: 'grid',
        gap: 8,
        borderLeft: `3px solid ${
          row.hollow ? 'var(--red)' : row.promoted ? 'var(--state-promoted)' : 'var(--state-dream)'
        }`,
      }}
    >
      <div className="spread" style={{ gap: 10 }}>
        <div style={{ minWidth: 0 }}>
          <button
            type="button"
            onClick={onOpen}
            className="mono"
            style={{ fontSize: 13, fontWeight: 600, textAlign: 'left', wordBreak: 'break-all' }}
          >
            {row.dream_id}
          </button>
          <div className="flex" style={{ flexWrap: 'wrap', gap: 5, marginTop: 6 }}>
            <Chip tone="dream">{row.kind || 'unknown kind'}</Chip>
            {row.hollow ? (
              <Chip tone="red" title={row.hollow_why}>
                hollow
              </Chip>
            ) : null}
            {row.promoted ? <Chip tone="green">promoted</Chip> : null}
            {typeof row.iteration_count === 'number' ? (
              <Chip>{plural(row.iteration_count, 'iteration')}</Chip>
            ) : null}
            {typeof row.artifact_chars === 'number' ? (
              <Chip>{row.artifact_chars.toLocaleString()} chars</Chip>
            ) : null}
          </div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div className="muted" style={{ fontSize: 11 }}>
            {row.age_s !== undefined
              ? `${Math.round(row.age_s)}s old`
              : relTime(row.last_iteration_at)}
          </div>
          <button type="button" className="btn btn-sm" style={{ marginTop: 6 }} onClick={onOpen}>
            Open
          </button>
        </div>
      </div>

      {row.hollow && row.hollow_why ? (
        <div className="notice" data-tone="error" style={{ padding: '8px 11px', fontSize: 11.5 }}>
          <IconWarn className="notice-icon" size={14} />
          <div>{row.hollow_why}</div>
        </div>
      ) : null}
    </article>
  );
}

/* ---------------------------------------------------------- detail panel */

function DreamDetailPanel({
  dreamId,
  onClose,
  onChanged,
}: {
  dreamId: string;
  onClose: () => void;
  onChanged: () => void;
}) {
  const detail = useAsync(() => loadDreamDetail(dreamId), [dreamId]);
  const [verifyResult, setVerifyResult] = useState<string | null>(null);
  const [promoteResult, setPromoteResult] = useState<string | null>(null);
  const [promoteOk, setPromoteOk] = useState(false);
  const [busy, setBusy] = useState(false);

  const d: DreamDetail | null = detail.data;

  const doVerify = async () => {
    setBusy(true);
    setVerifyResult(null);
    try {
      const r = await verifyDream(dreamId);
      setVerifyResult(
        r.healthy
          ? `Chain verified: ${r.verified}/${r.checked} nodes proved.${r.note ? ` ${r.note}` : ''}`
          : `Chain did NOT verify: ${r.broken.length} broken of ${r.checked}. ${r.note ?? ''}`,
      );
    } catch (err) {
      setVerifyResult(err instanceof ControlError ? err.message : 'Verification failed.');
    } finally {
      setBusy(false);
    }
  };

  const doPromote = async (force: boolean) => {
    setBusy(true);
    setPromoteResult(null);
    try {
      const r = await promoteDream(dreamId, force);
      setPromoteOk(r.promoted);
      setPromoteResult(
        r.promoted
          ? `Promoted. Pack written to ${r.path ?? 'the promotions store'}${
              r.files?.length ? ` (${r.files.length} files).` : '.'
            }`
          : `Refused: ${r.reason ?? 'the engine declined without a stated reason.'}`,
      );
      if (r.promoted) onChanged();
    } catch (err) {
      setPromoteOk(false);
      setPromoteResult(err instanceof ControlError ? err.message : 'Promotion failed.');
    } finally {
      setBusy(false);
    }
  };

  const doRun = async () => {
    setBusy(true);
    setPromoteResult(null);
    try {
      const r = await startRun(dreamId, 1);
      setPromoteOk(true);
      setPromoteResult(`Run started as job ${r.job_id}. Open the Runs tab to watch it.`);
    } catch (err) {
      setPromoteOk(false);
      setPromoteResult(err instanceof ControlError ? err.message : 'Could not start the run.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={dreamId}
      subtitle="One lineage in full — the artifact, its critique panel, and the provenance chain."
    >
      {detail.loading ? <LoadingState rows={4} label="Reading dream" /> : null}
      {detail.error ? <ErrorState error={detail.error} onRetry={detail.reload} /> : null}

      {d ? (
        <div className="stack">
          <div className="flex" style={{ flexWrap: 'wrap', gap: 5 }}>
            <Chip tone="dream">{d.kind}</Chip>
            {d.hollow ? <Chip tone="red">hollow</Chip> : null}
            {d.promotion.promoted ? <Chip tone="green">promoted</Chip> : null}
            <Chip>{plural(d.critique_count ?? 0, 'critique')}</Chip>
            {d.best_iteration !== null ? <Chip>best iteration {d.best_iteration}</Chip> : null}
          </div>

          {d.hollow ? (
            <Notice tone="error">
              <strong>This lineage is hollow.</strong> It recorded provider errors, not work
              {d.hollow_why ? ` — ${d.hollow_why}` : ''}. Its signatures may still verify, because a
              signature proves the bytes are intact, not that a dream happened.
            </Notice>
          ) : null}

          <div className="grid-2">
            <div className="card card-pad">
              <div className="stat-label">Provenance</div>
              <div className="stack" style={{ gap: 6, marginTop: 6, fontSize: 12 }}>
                <div className="spread">
                  <span className="muted">Braid CIDs</span>
                  <span className="mono">{d.provenance.braid_cids}</span>
                </div>
                <div className="spread">
                  <span className="muted">Uncommitted</span>
                  <span className="mono">{d.provenance.uncommitted}</span>
                </div>
                <div className="spread">
                  <span className="muted">Verified</span>
                  <span className="mono">
                    {d.provenance.verified === null
                      ? 'not proven yet'
                      : String(d.provenance.verified)}
                  </span>
                </div>
              </div>
              <button
                type="button"
                className="btn btn-sm"
                style={{ marginTop: 10 }}
                onClick={doVerify}
                disabled={busy || d.hollow}
                title={d.hollow ? 'A hollow lineage cannot be usefully verified' : undefined}
              >
                <IconShield size={12} /> Re-prove chain
              </button>
            </div>

            <div className="card card-pad">
              <div className="stat-label">Promotion</div>
              <div className="stack" style={{ gap: 6, marginTop: 6, fontSize: 12 }}>
                <div className="spread">
                  <span className="muted">State</span>
                  <span className="mono">{d.promotion.promoted ? 'promoted' : 'unpromoted'}</span>
                </div>
                <div className="spread">
                  <span className="muted">Derived from</span>
                  <span className="mono" style={{ fontSize: 10.5, textAlign: 'right' }}>
                    {d.promotion.derived_from}
                  </span>
                </div>
                {d.promotion.promoted ? (
                  <div className="flex" style={{ flexWrap: 'wrap', gap: 4 }}>
                    {d.promotion.files.map((f) => (
                      <Chip key={f}>{f}</Chip>
                    ))}
                  </div>
                ) : null}
              </div>
              <p className="muted" style={{ fontSize: 10.5, margin: '8px 0 0', lineHeight: 1.5 }}>
                {d.promotion.not_derived_from}
              </p>
              <div className="flex" style={{ marginTop: 10, gap: 6 }}>
                <button
                  type="button"
                  className="btn btn-sm btn-primary"
                  onClick={() => doPromote(false)}
                  disabled={busy || d.hollow}
                >
                  <IconCheck size={12} /> Promote
                </button>
                {d.promotion.promoted ? (
                  <button
                    type="button"
                    className="btn btn-sm"
                    onClick={() => doPromote(true)}
                    disabled={busy || d.hollow}
                    title="Overwrites this dream's pack only"
                  >
                    Force
                  </button>
                ) : null}
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={doRun}
                  disabled={busy || d.hollow || Boolean(d.done)}
                >
                  <IconPlay size={12} /> Run 1 iteration
                </button>
              </div>
            </div>
          </div>

          {verifyResult ? (
            <Notice tone={verifyResult.includes('NOT') ? 'error' : 'ok'}>{verifyResult}</Notice>
          ) : null}
          {promoteResult ? <Notice tone={promoteOk ? 'ok' : 'warn'}>{promoteResult}</Notice> : null}

          <div>
            <div className="stat-label" style={{ marginBottom: 6 }}>
              Artifact
            </div>
            {d.artifact ? (
              <pre
                style={{
                  margin: 0,
                  padding: 12,
                  background: 'var(--bg-panel-2)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--r-md)',
                  fontSize: 11.5,
                  lineHeight: 1.6,
                  maxHeight: 300,
                  overflow: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {d.artifact}
              </pre>
            ) : (
              <div className="notice" style={{ fontSize: 11.5 }}>
                No artifact on this lineage.
              </div>
            )}
          </div>

          <div>
            <div className="stat-label" style={{ marginBottom: 6 }}>
              Chain
            </div>
            <ChainTable dreamId={dreamId} />
          </div>
        </div>
      ) : null}
    </Modal>
  );
}

/** Read one lineage in full; kept separate so the modal's deps stay tight. */
function loadDreamDetail(id: string) {
  return loadDream(id);
}

function ChainTable({ dreamId }: { dreamId: string }) {
  const chain = useAsync(() => loadChain(dreamId), [dreamId]);
  if (chain.loading) return <LoadingState rows={2} label="Reading chain" />;
  if (chain.error) return <ErrorState error={chain.error} />;
  const c = chain.data;
  if (!c) return null;

  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="flex" style={{ flexWrap: 'wrap', gap: 5 }}>
        <Chip>{plural(c.iterations, 'iteration')}</Chip>
        <Chip tone="green">{c.braid_committed} committed</Chip>
        {c.uncommitted.length ? (
          <Chip tone="amber">{c.uncommitted.length} uncommitted</Chip>
        ) : null}
      </div>
      {c.chain.length === 0 ? (
        <div className="notice" style={{ fontSize: 11.5 }}>
          No braid nodes recorded — nothing has been committed for this lineage.
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>#</th>
              <th>CID</th>
            </tr>
          </thead>
          <tbody>
            {c.chain.map((n) => (
              <tr key={n.iteration}>
                <td className="mono">{n.iteration}</td>
                <td className="mono" style={{ wordBreak: 'break-all' }}>
                  {n.cid}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- runs tab */

function RunsPanel() {
  const runs = useAsync(loadRuns, []);
  if (runs.loading) return <LoadingState rows={3} label="Reading runs" />;
  if (runs.error) return <ErrorState error={runs.error} onRetry={runs.reload} />;

  const data = runs.data;
  if (!data) return null;

  return (
    <div className="stack">
      <div className="notice">
        <IconInfo className="notice-icon" size={16} />
        <div>
          <strong>Run records are in-memory.</strong> {data.note} A restart forgets them, and a
          forgotten run is not a live one.
        </div>
      </div>
      <div className="stat-row">
        <Stat label="Jobs" value={data.total} />
        <Stat label="Running" value={data.running} hint="holds the lock" />
      </div>
      {data.jobs.length === 0 ? (
        <EmptyState title="No runs in this process" icon={<IconPlay size={20} />}>
          A run is minutes of panel work, spawned as the engine's own CLI so its lock discipline is
          what bounds it.
        </EmptyState>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Job</th>
              <th>Dream</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Exit</th>
            </tr>
          </thead>
          <tbody>
            {data.jobs.map((j) => (
              <tr key={j.job_id}>
                <td className="mono">{j.job_id}</td>
                <td className="mono" style={{ wordBreak: 'break-all' }}>
                  {j.dream_id}
                </td>
                <td>
                  <Chip
                    tone={
                      j.status === 'done'
                        ? 'green'
                        : j.status === 'running'
                          ? 'accent'
                          : j.status === 'paused'
                            ? 'amber'
                            : 'red'
                    }
                    title={j.note}
                  >
                    {j.status}
                  </Chip>
                </td>
                <td className="mono">{j.duration_note}</td>
                <td className="mono">{j.exit_code ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <RunCosts />
    </div>
  );
}

function RunCosts() {
  const manifest = useAsync(loadManifest, []);
  if (!manifest.data) return null;
  const m = manifest.data;

  return (
    <div className="card card-pad">
      <div className="stat-label" style={{ marginBottom: 8 }}>
        Run contract
      </div>
      <div className="grid-2">
        <div className="stack" style={{ gap: 5, fontSize: 12 }}>
          <div className="spread">
            <span className="muted">Max iterations</span>
            <span className="mono">{m.run.max_iterations}</span>
          </div>
          <div className="spread">
            <span className="muted">Ceiling</span>
            <span className="mono">{Math.round(m.run.timeout_s / 60)} min</span>
          </div>
          <div className="spread">
            <span className="muted">Default</span>
            <span className="mono">{m.run.default_iterations}</span>
          </div>
        </div>
        <div>
          <div className="stat-label" style={{ marginBottom: 4 }}>
            Exit codes
          </div>
          {Object.entries(m.run.exit_codes).map(([code, meaning]) => (
            <div key={code} className="flex" style={{ gap: 6, fontSize: 11.5, marginBottom: 3 }}>
              <span className="chip mono">{code}</span>
              <span className="muted">{meaning}</span>
            </div>
          ))}
        </div>
      </div>
      <p className="muted" style={{ fontSize: 11, marginTop: 10 }}>
        {m.run.cost_note}
      </p>
    </div>
  );
}

/* -------------------------------------------------------------- hollow tab */

function HollowPanel() {
  const hollow = useAsync(loadHollow, []);
  const idle = useAsync(loadIdleStats, []);

  if (hollow.loading) return <LoadingState rows={3} label="Reading hollow census" />;
  if (hollow.error) return <ErrorState error={hollow.error} onRetry={hollow.reload} />;

  const h = hollow.data;
  if (!h) return null;

  return (
    <div className="stack">
      <div className="notice" data-tone={h.hollow_lineages > 0 ? 'warn' : 'ok'}>
        <IconInfo className="notice-icon" size={16} />
        <div>
          <strong>Read-only census.</strong> {h.note}
        </div>
      </div>
      <div className="stat-row">
        <Stat label="Hollow lineages" value={h.hollow_lineages} />
        <Stat label="Already marked" value={h.already_marked} />
        <Stat label="Unmarked" value={h.unmarked} />
        <Stat label="Hollow iterations" value={h.hollow_iterations} />
      </div>

      {h.entries.length === 0 ? (
        <EmptyState title="No hollow lineages" icon={<IconCheck size={20} />}>
          Nothing in the store recorded provider errors instead of work.
        </EmptyState>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Dream</th>
              <th>Kind</th>
              <th>Iterations</th>
              <th>Marked</th>
            </tr>
          </thead>
          <tbody>
            {h.entries.map((e) => (
              <tr key={e.dream_id}>
                <td className="mono" style={{ wordBreak: 'break-all' }}>
                  {e.dream_id}
                </td>
                <td>{e.kind}</td>
                <td className="mono">{e.iterations.join(', ') || '—'}</td>
                <td>
                  {e.already_marked ? <Chip tone="green">yes</Chip> : <Chip tone="amber">no</Chip>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="card card-pad">
        <div className="stat-label" style={{ marginBottom: 6 }}>
          Idle service
        </div>
        {idle.loading ? (
          <LoadingState rows={1} label="Reading idle stats" />
        ) : idle.error ? (
          <p className="muted" style={{ fontSize: 12 }}>
            Idle stats unavailable: {idle.error.message}
          </p>
        ) : (
          <div className="stack" style={{ gap: 4, fontSize: 12 }}>
            <div className="spread">
              <span className="muted">Run lock</span>
              <span className="mono">
                {idle.data?.run_lock ? JSON.stringify(idle.data.run_lock) : 'free'}
              </span>
            </div>
            {Object.entries(idle.data ?? {})
              .filter(([k]) => k !== 'run_lock')
              .slice(0, 8)
              .map(([k, v]) => (
                <div className="spread" key={k}>
                  <span className="muted">{k}</span>
                  <span className="mono" style={{ fontSize: 11 }}>
                    {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------ new dream */

function NewDreamModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [seed, setSeed] = useState('');
  const [foundation, setFoundation] = useState('');
  const [kind, setKind] = useState('active');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const manifest = useAsync(loadManifest, []);
  const kinds = manifest.data?.kinds ?? ['active', 'idle_prototype', 'idle_proposal', 'idle_idea'];

  return (
    <Modal
      open
      onClose={onClose}
      title="New dream"
      subtitle="Creating a lineage costs nothing — no model is called until the dream is run."
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={saving || !seed.trim()}
            onClick={async () => {
              setSaving(true);
              setErr(null);
              try {
                await createDream({ seed: seed.trim(), foundation: foundation.trim(), kind });
                onCreated();
              } catch (error) {
                setErr(
                  error instanceof ControlError ? error.message : 'Could not create the dream.',
                );
                setSaving(false);
              }
            }}
          >
            {saving ? 'Creating…' : 'Create lineage'}
          </button>
        </>
      }
    >
      {err ? (
        <div style={{ marginBottom: 12 }}>
          <Notice tone="error">{err}</Notice>
        </div>
      ) : null}
      <div className="field">
        <label htmlFor="nd-seed">Seed</label>
        <textarea
          id="nd-seed"
          className="textarea"
          rows={6}
          value={seed}
          onChange={(e) => setSeed(e.target.value)}
          placeholder="The brief the dream starts from. Max 4000 characters."
          autoFocus
        />
        <span className="field-hint">{seed.length}/4000</span>
      </div>
      <div className="field">
        <label htmlFor="nd-foundation">Foundation</label>
        <input
          id="nd-foundation"
          className="input"
          value={foundation}
          onChange={(e) => setFoundation(e.target.value)}
          placeholder="Defaults to the seed"
        />
      </div>
      <div className="field" style={{ marginBottom: 0 }}>
        <label htmlFor="nd-kind">Kind</label>
        <select id="nd-kind" className="select" value={kind} onChange={(e) => setKind(e.target.value)}>
          {kinds.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
        <span className="field-hint">
          A kind outside this list is refused by the server, not stored.
        </span>
      </div>
    </Modal>
  );
}

/* Small health strip, used by the Status route. */
export function DreamsHealth() {
  const probe = useAsync(probeControl, []);
  const [manual, setManual] = useState<{ ok: boolean; detail: string; latencyMs: number } | null>(
    null,
  );

  return (
    <div className="card card-pad">
      <div className="spread" style={{ marginBottom: 8 }}>
        <div className="stat-label">Control plane</div>
        <button
          type="button"
          className="btn btn-sm btn-ghost"
          onClick={async () => setManual(await probeControl())}
        >
          <IconRefresh size={12} /> Probe
        </button>
      </div>
      {probe.loading && !manual ? (
        <span className="muted" style={{ fontSize: 12 }}>
          Probing /api/health…
        </span>
      ) : (
        <div className="flex" style={{ gap: 6, flexWrap: 'wrap' }}>
          <Chip tone={(manual ?? probe.data)?.ok ? 'green' : 'red'}>
            {(manual ?? probe.data)?.ok ? 'reachable' : 'unreachable'}
          </Chip>
          <span className="muted mono" style={{ fontSize: 11 }}>
            {(manual ?? probe.data)?.detail ?? probe.error?.message ?? 'no answer'}
          </span>
          {(manual ?? probe.data)?.latencyMs !== undefined ? (
            <Chip>{(manual ?? probe.data)?.latencyMs}ms</Chip>
          ) : null}
        </div>
      )}
    </div>
  );
}
