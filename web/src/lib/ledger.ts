/* Ledger hash-chain verification - real SHA-256, in the browser.
 *
 * The deck's surface 3 exists because "tamper-evident append-only ledger" is
 * mem20's headline claim and nothing made it visible. A viewer that draws a
 * pretty chain without actually recomputing the hashes would be worse than no
 * viewer: it would assert integrity it never checked.
 *
 * So this file recomputes. It uses WebCrypto's SHA-256 (available in every
 * browser this shell targets and in Node 20 for the tests), and it reports the
 * FIRST index where the chain breaks rather than a boolean - "the chain is
 * broken" is not actionable, "entry 47 does not hash to the value entry 48
 * commits to" is.
 *
 * The chain rule implemented here is the standard one:
 *
 *   h[i] = SHA256( h[i-1] || canonical(entry[i]) )
 *
 * with h[-1] = the genesis value the ledger declares. `canonical` is a stable
 * JSON serialisation with sorted keys, because two implementations that
 * disagree about key order would disagree about the hash and both would be
 * "right".
 */

export interface LedgerEntry {
  /** Monotonic index, 0-based. */
  index: number;
  /** The entry payload. */
  data: unknown;
  /** The hash this entry claims for itself. */
  hash: string;
  /** The hash of the previous entry (or the genesis value for index 0). */
  prevHash: string;
  /** ISO timestamp, when the ledger carries one. */
  at?: string;
}

export interface ChainCheck {
  ok: boolean;
  /** Number of entries whose hash was recomputed and matched. */
  verified: number;
  /** Total entries examined. */
  total: number;
  /** The first index that failed, or null when the chain is intact. */
  firstBadIndex: number | null;
  /** A sentence naming what went wrong, for the UI. */
  detail: string;
}

/** Stable JSON: object keys sorted, so two implementations agree on the bytes. */
export function canonical(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null';
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${canonical(obj[k])}`).join(',')}}`;
}

/** SHA-256 of a UTF-8 string, lowercase hex. */
export async function sha256Hex(input: string): Promise<string> {
  const bytes = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** The hash an entry SHOULD have, given the previous hash. */
export async function expectedHash(entry: LedgerEntry, prevHash: string): Promise<string> {
  return sha256Hex(`${prevHash}${canonical(entry.data)}`);
}

/**
 * Verify a whole chain.
 *
 * Two independent things are checked per entry, and they are different bugs:
 *
 *   1. LINKAGE - entry.prevHash must equal the previous entry's hash. A break
 *      here means an entry was removed, reordered, or inserted.
 *   2. CONTENT - the entry's own hash must equal SHA256(prevHash || data). A
 *      break here means the payload was edited after the fact.
 *
 * Reporting which one failed is the difference between "someone deleted a row"
 * and "someone changed a row".
 */
export async function verifyChain(
  entries: LedgerEntry[],
  genesis = '',
): Promise<ChainCheck> {
  if (entries.length === 0) {
    return {
      ok: true,
      verified: 0,
      total: 0,
      firstBadIndex: null,
      detail: 'No entries to verify.',
    };
  }

  let prev = genesis;
  for (let i = 0; i < entries.length; i += 1) {
    const e = entries[i];

    if (e.prevHash !== prev) {
      return {
        ok: false,
        verified: i,
        total: entries.length,
        firstBadIndex: i,
        detail: `Linkage break at entry ${i}: it commits to prevHash ${short(e.prevHash)} but the previous entry hashes to ${short(prev)}. An entry was removed, reordered or inserted.`,
      };
    }

    const want = await expectedHash(e, prev);
    if (want !== e.hash) {
      return {
        ok: false,
        verified: i,
        total: entries.length,
        firstBadIndex: i,
        detail: `Content break at entry ${i}: its payload hashes to ${short(want)} but it claims ${short(e.hash)}. The payload was edited after it was written.`,
      };
    }

    prev = e.hash;
  }

  return {
    ok: true,
    verified: entries.length,
    total: entries.length,
    firstBadIndex: null,
    detail: `All ${entries.length} entries verified: every link matches and every payload hashes to its committed value.`,
  };
}

function short(h: string): string {
  if (!h) return '(empty)';
  return h.length > 16 ? `${h.slice(0, 8)}...${h.slice(-6)}` : h;
}

/**
 * Detect truncation against a known head.
 *
 * An append-only ledger can be silently shortened by deleting the tail, and
 * every remaining entry still verifies - the chain is internally consistent,
 * it is just shorter than it was. The only defence is an externally recorded
 * head hash. This compares the two.
 */
export function detectTruncation(
  entries: LedgerEntry[],
  knownHead: { index: number; hash: string } | null,
): { truncated: boolean; detail: string } {
  if (!knownHead) {
    return {
      truncated: false,
      detail: 'No externally recorded head to compare against - truncation cannot be detected from the ledger alone.',
    };
  }
  if (entries.length === 0) {
    return { truncated: true, detail: `The ledger is empty but a head was recorded at index ${knownHead.index}.` };
  }
  const last = entries[entries.length - 1];
  if (last.index < knownHead.index) {
    return {
      truncated: true,
      detail: `Truncated: the ledger ends at index ${last.index} but index ${knownHead.index} was recorded. ${knownHead.index - last.index} entries are missing from the tail.`,
    };
  }
  if (last.index === knownHead.index && last.hash !== knownHead.hash) {
    return {
      truncated: true,
      detail: `The head at index ${knownHead.index} hashes to ${short(last.hash)} but ${short(knownHead.hash)} was recorded. The tail was rewritten.`,
    };
  }
  return { truncated: false, detail: `Head matches the recorded value at index ${knownHead.index}.` };
}

/** Build a valid chain from raw payloads - used by the demo and by tests. */
export async function buildChain(
  payloads: unknown[],
  genesis = '',
  at = (i: number) => new Date(Date.UTC(2026, 0, 1, 0, 0, i)).toISOString(),
): Promise<LedgerEntry[]> {
  const out: LedgerEntry[] = [];
  let prev = genesis;
  for (let i = 0; i < payloads.length; i += 1) {
    const entry: LedgerEntry = { index: i, data: payloads[i], hash: '', prevHash: prev, at: at(i) };
    entry.hash = await expectedHash(entry, prev);
    out.push(entry);
    prev = entry.hash;
  }
  return out;
}
