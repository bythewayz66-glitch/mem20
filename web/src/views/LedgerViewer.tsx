/* Surface 3 — Trust & audit ledger viewer.
 *
 * For: compliance buyers. Shows: hash chain, truncation proof, export.
 * Why: the headline claim, made visible.
 *
 * The critical property of this view: it RECOMPUTES the hashes. A viewer that
 * draws a chain of boxes and calls it "verified" without hashing anything would
 * be worse than no viewer at all — it would assert integrity it never checked.
 *
 * So the view builds a chain, verifies it with real SHA-256, and then offers a
 * tamper button that edits one payload in place. The verification must then
 * FAIL, and it must name the exact index and the kind of break. If the tamper
 * button did not break verification, the verification would be theatre.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { Notice, Panel, Pill, Stat } from '../components/ui';
import {
  buildChain,
  detectTruncation,
  verifyChain,
  type ChainCheck,
  type LedgerEntry,
} from '../lib/ledger';
import { SAMPLE_LEDGER_PAYLOADS } from '../lib/sample';

export default function LedgerViewer() {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [check, setCheck] = useState<ChainCheck | null>(null);
  const [tampered, setTampered] = useState<number | null>(null);
  const [head, setHead] = useState<{ index: number; hash: string } | null>(null);
  const [busy, setBusy] = useState(true);

  const build = async () => {
    setBusy(true);
    const chain = await buildChain(SAMPLE_LEDGER_PAYLOADS);
    setEntries(chain);
    setHead({ index: chain[chain.length - 1].index, hash: chain[chain.length - 1].hash });
    setTampered(null);
    setCheck(await verifyChain(chain));
    setBusy(false);
  };

  useEffect(() => {
    build();
  }, []);

  const verify = async (list: LedgerEntry[]) => {
    setBusy(true);
    setCheck(await verifyChain(list));
    setBusy(false);
  };

  const tamper = async (i: number) => {
    const next = entries.map((e, idx) =>
      idx === i ? { ...e, data: { ...(e.data as object), text: 'EDITED AFTER THE FACT' } } : e,
    );
    setEntries(next);
    setTampered(i);
    await verify(next);
  };

  const truncate = async () => {
    const next = entries.slice(0, Math.max(1, entries.length - 2));
    setEntries(next);
    setTampered(null);
    await verify(next);
  };

  const trunc = useMemo(() => detectTruncation(entries, head), [entries, head]);

  const exportJson = () => {
    const blob = new Blob([JSON.stringify({ entries, head, check }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mem20-ledger-export.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page wide">
      <p className="lede">
        mem20's headline claim is a tamper-evident append-only ledger. This view makes it checkable:
        every hash below is recomputed in your browser with SHA-256, and the tamper button edits a
        payload so you can watch the verification fail and name the exact entry that broke.
      </p>

      <div className="grid g4" style={{ marginBottom: 16 }}>
        <Stat k="entries" v={entries.length} />
        <Stat
          k="verified"
          v={check ? check.verified : '—'}
          sub={check && check.ok ? 'all links + payloads' : 'stopped at first break'}
        />
        <Stat
          k="chain"
          v={check ? (check.ok ? 'intact' : 'BROKEN') : '—'}
          sub={check?.firstBadIndex != null ? `at index ${check.firstBadIndex}` : undefined}
        />
        <Stat k="truncation" v={trunc.truncated ? 'DETECTED' : 'none'} sub="vs recorded head" />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn" onClick={build} disabled={busy}>
          {busy ? <span className="spin" /> : 'rebuild chain'}
        </button>
        <button className="btn" onClick={() => tamper(2)} disabled={busy || entries.length < 3}>
          tamper entry 2
        </button>
        <button className="btn" onClick={truncate} disabled={busy || entries.length < 3}>
          delete the tail
        </button>
        <button className="btn" onClick={exportJson} disabled={busy || entries.length === 0}>
          export JSON
        </button>
      </div>

      {check && (
        <div style={{ marginBottom: 14 }}>
          <Notice tone={check.ok ? 'ok' : 'bad'} title={check.ok ? 'Chain verified' : 'Chain verification FAILED'}>
            {check.detail}
          </Notice>
        </div>
      )}

      {trunc.truncated && (
        <div style={{ marginBottom: 14 }}>
          <Notice tone="bad" title="Truncation detected">
            {trunc.detail}
          </Notice>
        </div>
      )}

      <Panel
        title="Ledger"
        right={
          <div style={{ display: 'flex', gap: 6 }}>
            <Pill mono>SHA-256</Pill>
            <Pill tone={check?.ok ? 'green' : 'red'} dot>
              {check?.ok ? 'verified' : 'failed'}
            </Pill>
          </div>
        }
        bodyStyle={{ padding: 0 }}
      >
        <div className="ld-row" style={{ borderBottom: '1px solid var(--line-1)', color: 'var(--ink-3)', fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
          <span>idx</span>
          <span>payload</span>
          <span>prev hash</span>
          <span>hash</span>
        </div>
        <div className="ld-chain">
          {entries.map((e, i) => {
            const bad = check?.firstBadIndex === i;
            return (
              <div key={e.index} className={`ld-row ${bad ? 'bad' : 'ok'}`}>
                <span className="ld-idx">{e.index}</span>
                <span className="ld-payload" title={JSON.stringify(e.data)}>
                  {tampered === i && <Pill tone="red">tampered</Pill>}{' '}
                  {JSON.stringify(e.data).slice(0, 90)}
                </span>
                <span className="ld-hash" title={e.prevHash}>
                  {e.prevHash ? `${e.prevHash.slice(0, 10)}…` : '(genesis)'}
                </span>
                <span className="ld-hash" title={e.hash}>
                  {e.hash.slice(0, 10)}…
                </span>
              </div>
            );
          })}
        </div>
      </Panel>

      <div style={{ marginTop: 16 }} className="grid g2">
        <Panel title="What is actually checked">
          <div style={{ display: 'grid', gap: 10 }}>
            <div className="proof">
              <span className="pk">linkage</span>
              <span>
                each entry's <span className="mono">prevHash</span> must equal the previous entry's
                hash. A break means an entry was removed, reordered or inserted.
              </span>
            </div>
            <div className="proof">
              <span className="pk">content</span>
              <span>
                each entry's own hash must equal{' '}
                <span className="mono">SHA256(prevHash ‖ canonical(data))</span>. A break means the
                payload was edited after it was written.
              </span>
            </div>
            <div className="proof">
              <span className="pk">truncation</span>
              <span>
                the tail is compared against an externally recorded head. A shortened ledger is
                internally consistent, so this is the only way to catch it.
              </span>
            </div>
          </div>
        </Panel>

        <Panel title="Honest limits">
          <div style={{ display: 'grid', gap: 10 }}>
            <Notice tone="warn" title="This is a demonstration chain, not your store">
              The entries above are built in the browser from a fixed sample so the verification is
              demonstrable. There is no HTTP route in <span className="mono">bridge/server.py</span>{' '}
              that serves the real ledger, so this view does not claim to be reading it.
            </Notice>
            <Notice tone="warn" title="A recorded head is required for truncation">
              Without an externally stored head hash, a shortened ledger cannot be detected from the
              ledger alone — every remaining entry still verifies. The view says so rather than
              showing a green tick it did not earn.
            </Notice>
          </div>
        </Panel>
      </div>
    </div>
  );
}
