/* Sales — positioning, value props, proof points, pricing, CTA.
 *
 * The only numbers on this page that are claimed as measurements are the ones
 * this estate can point at: the tool count from source, one store, five
 * invariants, and the board the door actually holds. Everything else is a
 * statement of position, not a metric.
 */
import React from 'react';
import { Pill } from '../components/ui';

import { CATALOG } from '../data/catalog';
const DOMAINS = new Set(CATALOG.tools.map((t) => t.domain)).size;

export default function Sales({ onOpenApp }: { onOpenApp: () => void }) {
  return (
    <div className="page">
      <div className="hero">
        <Pill tone="cyan" mono dot>
          auditable agent memory
        </Pill>
        <h2 style={{ marginTop: 14 }}>
          Your agent remembers.
          <br />
          <span className="grad">And you can prove what it remembers.</span>
        </h2>
        <p>
          Every agent memory product says it remembers. mem20 is built around a different question: when your agent acts on a
          memory, can you show where it came from? Facts and hypotheses live in separate partitions, indexes only accept grounded
          records, and promotion out of simulation requires evidence. That is enforced in the store, not promised in a prompt.
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="btn primary" style={{ height: 38, padding: '0 18px' }} onClick={onOpenApp}>
            open the board →
          </button>
          <a className="btn" style={{ height: 38, padding: '0 18px' }} href="#docs">
            read the FAQ
          </a>
        </div>
      </div>

      <hr className="sep" />

      <div className="grid g3" style={{ marginBottom: 26 }}>
        <div className="proof" style={{ flexDirection: 'column', gap: 8, padding: 16 }}>
          <span style={{ color: 'var(--ink-0)', fontWeight: 600, fontSize: 13.5 }}>Grounded vs simulated, by construction</span>
          <span>
            Hypotheticals never reach the vector or BM25 index. There is no flag to skip it — the guard runs inside the index
            write path itself.
          </span>
        </div>
        <div className="proof" style={{ flexDirection: 'column', gap: 8, padding: 16 }}>
          <span style={{ color: 'var(--ink-0)', fontWeight: 600, fontSize: 13.5 }}>Evidence-gated promotion</span>
          <span>
            A dream becomes a fact only with <span className="mono">prediction_error_evidence</span>: a prior prediction resolved
            in its favour, or a registered verifier's voucher.
          </span>
        </div>
        <div className="proof" style={{ flexDirection: 'column', gap: 8, padding: 16 }}>
          <span style={{ color: 'var(--ink-0)', fontWeight: 600, fontSize: 13.5 }}>One board, one store</span>
          <span>
            The estate had four kanban implementations and two databases — and a real board nobody could see. Now there is one
            door on <span className="mono">:8221</span> and one SQLite file.
          </span>
        </div>
      </div>

      <h3 style={{ color: 'var(--ink-0)', fontSize: 16, margin: '0 0 4px' }}>Proof, not adjectives</h3>
      <p className="lede" style={{ marginBottom: 14 }}>
        Each of these can be checked against the repository — the surface that shows it is named next to it.
      </p>
      <div className="panel" style={{ marginBottom: 26 }}>
        <table className="tbl">
          <thead>
            <tr>
              <th style={{ width: 150 }}>claim</th>
              <th>where it is verifiable</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono" style={{ color: 'var(--cyan-0)' }}>{CATALOG.count} tools</td>
              <td>
                every <span className="mono">mt.Tool(…)</span> registration in <span className="mono">mcp/tools/*.py</span>, across{' '}
                {DOMAINS} domains — browsable in Docs → Tool reference
              </td>
            </tr>
            <tr>
              <td className="mono" style={{ color: 'var(--cyan-0)' }}>5 invariants</td>
              <td>numbered and paired with the symbol that enforces each — Memory model surface</td>
            </tr>
            <tr>
              <td className="mono" style={{ color: 'var(--cyan-0)' }}>1 door, 1 store</td>
              <td>
                <span className="mono">mem20-kanban.service</span> on <span className="mono">127.0.0.1:8221</span>, sole writer of{' '}
                <span className="mono">kanban_3.db</span> — Door Sync surface
              </td>
            </tr>
            <tr>
              <td className="mono" style={{ color: 'var(--cyan-0)' }}>11 wire routes</td>
              <td>
                transcribed from <span className="mono">mem20kanbanz/door.py</span>, including the 422 WIP refusal — Door Sync
                surface
              </td>
            </tr>
            <tr>
              <td className="mono" style={{ color: 'var(--cyan-0)' }}>audit trail</td>
              <td>
                append-only <span className="mono">ledger.jsonl</span> with origin/store on every line, plus per-record provenance
                — Dreams surface
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3 style={{ color: 'var(--ink-0)', fontSize: 16, margin: '0 0 4px' }}>Who it is for</h3>
      <p className="lede" style={{ marginBottom: 14 }}>
        Teams running agents that take consequential actions — where “the model said so” is not an acceptable audit answer.
      </p>
      <div className="grid g3" style={{ marginBottom: 26 }}>
        {[
          ['Agent platform teams', 'Ship memory that survives a compliance review, without bolting on a second logging system.'],
          ['Automation and ops', 'One board every bot, CLI and human reads and writes through the same door.'],
          ['Research and evaluation', 'Keep counterfactuals out of the retrieval path while still being able to work with them.'],
        ].map(([t, d]) => (
          <div key={t} className="proof" style={{ flexDirection: 'column', gap: 6, padding: 16 }}>
            <span style={{ color: 'var(--ink-0)', fontWeight: 600 }}>{t}</span>
            <span>{d}</span>
          </div>
        ))}
      </div>

      <h3 style={{ color: 'var(--ink-0)', fontSize: 16, margin: '0 0 4px' }}>Pricing</h3>
      <p className="lede" style={{ marginBottom: 14 }}>
        Self-hosted by default — the store is your files. These are the tiers we quote; nothing here is metered by token.
      </p>
      <div className="grid g3" style={{ marginBottom: 26 }}>
        <div className="price">
          <div style={{ color: 'var(--ink-0)', fontWeight: 600 }}>Solo</div>
          <div className="amt">
            $0 <small>/ self-hosted</small>
          </div>
          <ul>
            <li>full memory engine, grounded/simulated split</li>
            <li>kanban door + CLI clients</li>
            <li>community support</li>
          </ul>
          <button className="btn" onClick={onOpenApp}>start</button>
        </div>
        <div className="price featured">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: 'var(--ink-0)', fontWeight: 600 }}>Team</span>
            <Pill tone="violet" mono>recommended</Pill>
          </div>
          <div className="amt">
            $— <small>/ seat · quoted</small>
          </div>
          <ul>
            <li>everything in Solo</li>
            <li>audit exports and provenance chains</li>
            <li>deployment review of your store layout</li>
            <li>priority fixes on the door and store</li>
          </ul>
          <button className="btn primary" onClick={onOpenApp}>talk to us</button>
        </div>
        <div className="price">
          <div style={{ color: 'var(--ink-0)', fontWeight: 600 }}>Platform</div>
          <div className="amt">
            $— <small>/ annual</small>
          </div>
          <ul>
            <li>everything in Team</li>
            <li>multi-board and multi-tenant planning</li>
            <li>architecture review and migration support</li>
            <li>named engineering contact</li>
          </ul>
          <button className="btn" onClick={onOpenApp}>scope it</button>
        </div>
      </div>

      <div
        className="panel"
        style={{
          padding: 24,
          background: 'linear-gradient(120deg, rgba(109,92,240,0.14), rgba(34,211,238,0.06) 60%, transparent)',
          borderColor: 'rgba(139,124,248,0.3)',
        }}
      >
        <div style={{ display: 'flex', gap: 18, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 340px' }}>
            <div style={{ fontSize: 19, color: 'var(--ink-0)', fontWeight: 650, letterSpacing: '-0.01em' }}>
              Bring your own store. Keep the audit trail.
            </div>
            <div style={{ color: 'var(--ink-2)', fontSize: 13.5, marginTop: 6, maxWidth: '58ch' }}>
              Start with the board you already run. If the memory model holds up against your own data, the rest of the stack
              follows.
            </div>
          </div>
          <button className="btn primary" style={{ height: 40, padding: '0 20px' }} onClick={onOpenApp}>
            open the board →
          </button>
        </div>
      </div>

      <div style={{ marginTop: 22, fontSize: 11.5, color: 'var(--ink-3)' }}>
        figures on this page are read from the repository at build time; the pricing rows marked “quoted” are intentionally not
        invented.
      </div>
    </div>
  );
}
