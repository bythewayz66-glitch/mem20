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
  count: rawCatalog.count ?? tools.length,
  domain_count: rawCatalog.domain_count ?? domains.length,
  domains,
  tools,
};

export default CATALOG;
