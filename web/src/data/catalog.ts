/* Normalised view of the AST-extracted tool catalog.
 *
 * `tools.json` is generated, and two generators have written it in two shapes:
 *
 *   short keys  n / t / d / x / p   — what is committed today (09ac980)
 *   long keys   name / title / description / domain / params
 *                                   — what .github/workflows/mem20-web.yml
 *                                     writes when it regenerates the catalog
 *
 * Commit 09ac980 regenerated the file at 270 tools / 27 domains but left the
 * three view components reading the long keys, so every row in the tool
 * reference rendered `undefined`. Teaching each view the short keys would just
 * move the breakage to the next regeneration, so normalise once here and
 * accept either shape.
 *
 * Counts come from the file's own header when present. `domain_count` is
 * derived from the records when the generator did not write it, because the
 * workflow's generator does not.
 */
import raw from './tools.json';

export type Tool = {
  name: string;
  title: string;
  description: string;
  domain: string;
  params: string[];
};

type RawTool = {
  n?: string;
  t?: string;
  d?: string;
  x?: string;
  p?: string[];
  name?: string;
  title?: string;
  description?: string;
  domain?: string;
  params?: string[];
};

type RawCatalog = {
  source?: string;
  files_scanned?: number;
  count?: number;
  domain_count?: number;
  domains?: string[];
  tools: RawTool[];
};

const rawCatalog = raw as unknown as RawCatalog;

const tools: Tool[] = rawCatalog.tools.map((t) => ({
  name: t.n ?? t.name ?? '',
  title: t.t ?? t.title ?? '',
  description: t.d ?? t.description ?? '',
  domain: t.x ?? t.domain ?? '',
  params: t.p ?? t.params ?? [],
}));

const domains = rawCatalog.domains ?? [...new Set(tools.map((t) => t.domain))].sort();

/* The header counts are advisory; the records are the evidence.
 *
 * `count` and `domain_count` are written by the generator, but they are only
 * ever *displayed* next to the rows they claim to summarise. If a regeneration
 * truncates the `tools` array while still writing the old header, or writes a
 * header from a different scan than the one that emitted the rows, the UI would
 * print a total that no row on screen can be checked against — exactly the
 * class of drift this surface exists to stop. So the records win, and the
 * header is consulted only when there are no records at all to count.
 */
const recordCount = tools.length;
const recordDomainCount = domains.length;

export const CATALOG: {
  source: string;
  files_scanned: number;
  count: number;
  domain_count: number;
  domains: string[];
  tools: Tool[];
} = {
  source: rawCatalog.source ?? 'mcp/tools/*.py',
  files_scanned: rawCatalog.files_scanned ?? 0,
  count: recordCount || (rawCatalog.count ?? 0),
  domain_count: recordDomainCount || (rawCatalog.domain_count ?? 0),
  domains,
  tools,
};

/* The repository release version, mirroring `VERSION` at the repo root
 * (3.1.2 as of 2026-11-01).
 *
 * A constant rather than a runtime read: the shell ships as a static bundle and
 * cannot open a file. `web/package.json` is deliberately NOT the source — it
 * carries the app's own `0.1.0` manifest, not the mem20 release. When the
 * release moves, this is the single line to change, and any surface that wants
 * to print a version imports this instead of typing the string again.
 */
export const MEM20_VERSION = '3.1.2';

export default CATALOG;
