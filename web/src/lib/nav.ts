/* The ONE navigation model for the whole shell.
 *
 * Before this file existed the route union, the nav list and the page titles
 * lived inline in App.tsx, and five finished views (MemoryGraphExplorer,
 * Playground, RuntimeConsole, LedgerViewer, EvalDashboard) were imported by
 * nobody: they compiled, they were never reachable. A nav that is a literal
 * inside a component cannot be checked, so nothing caught it.
 *
 * So the nav is data here, and App.tsx renders it. `ROUTES` is derived from
 * `NAV`, which means a view that is not in `NAV` is not a route, and a route
 * that has no view is a type error at the switch in App.tsx. The two cannot
 * drift apart silently again.
 */

export type NavGroup = 'Operate' | 'Explore' | 'Understand' | 'Sell' | 'Trust';

export type Route =
  | 'kanban'
  | 'dreams'
  | 'agents'
  | 'teamily'
  | 'catalog'
  | 'domains'
  | 'graph'
  | 'playground'
  | 'runtime'
  | 'docs'
  | 'eval'
  | 'sales'
  | 'memory'
  | 'ledger'
  | 'door'
  | 'connection';

export interface NavItem {
  id: Route;
  label: string;
  group: NavGroup;
  /** 24x24 stroke path, drawn with currentColor. */
  icon: string;
  /** Page heading. */
  title: string;
  /** One-line subtitle under the heading. */
  sub: string;
  /** Extra terms the command palette matches on. */
  keywords?: string[];
}

/** Group order in the rail. */
export const NAV_GROUPS: NavGroup[] = ['Operate', 'Explore', 'Understand', 'Sell', 'Trust'];

export const NAV: NavItem[] = [
  {
    id: 'kanban',
    label: 'Kanban',
    group: 'Operate',
    icon: 'M3 4h5v16H3zM10 4h5v10h-5zM17 4h4v7h-4z',
    title: 'Kanban',
    sub: 'the one board \u2014 mem20-kanban door, REST :8221',
    keywords: ['board', 'cards', 'wip', 'sarge', 'swimlane'],
  },
  {
    id: 'dreams',
    label: 'Dreams',
    group: 'Operate',
    icon: 'M12 3a9 9 0 100 18 9 9 0 000-18zM8 12a4 4 0 018 0',
    title: 'Dreams',
    sub: 'promotion and provenance, evidence-gated',
    keywords: ['promote', 'provenance', 'audit', 'simulated'],
  },
  {
    id: 'agents',
    label: 'Agent Builder',
    group: 'Operate',
    icon: 'M12 3v3M12 18v3M4.2 7.5l2.6 1.5M17.2 15l2.6 1.5M4.2 16.5l2.6-1.5M17.2 9l2.6-1.5M12 8a4 4 0 100 8 4 4 0 000-8z',
    title: 'Agent Builder',
    sub: 'identity \u00b7 prompt \u00b7 tools \u00b7 memory scope \u00b7 lifecycle',
    keywords: ['agent', 'identity', 'prompt', 'lifecycle', 'scope'],
  },
  {
    id: 'teamily',
    label: 'Teamily',
    group: 'Operate',
    icon: 'M9 11a3.5 3.5 0 100-7 3.5 3.5 0 000 7zM2.5 20a6.5 6.5 0 0113 0M16 11.5a3 3 0 100-6M17.5 20a5.5 5.5 0 00-2-4.3',
    title: 'Teamily',
    sub: 'members \u00b7 roles \u00b7 groups \u00b7 activity',
    keywords: ['team', 'members', 'roles', 'groups', 'gamut', 'lime'],
  },
  {
    id: 'catalog',
    label: 'Tool Catalog',
    group: 'Explore',
    icon: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
    title: 'Tool Catalog',
    sub: 'every registered tool, counted from source',
    keywords: ['tools', 'mcp', 'catalog', 'reference', 'schema'],
  },
  {
    id: 'domains',
    label: 'Domain Explorer',
    group: 'Explore',
    icon: 'M12 3l9 5-9 5-9-5zM3 12l9 5 9-5M3 16l9 5 9-5',
    title: 'Domain Explorer',
    sub: 'the 129 domains, their modules and prefixes',
    keywords: ['domains', 'modules', 'prefixes', 'surface'],
  },
  {
    id: 'graph',
    label: 'Memory Graph',
    group: 'Explore',
    icon: 'M6 6a2 2 0 100-4 2 2 0 000 4zM18 6a2 2 0 100-4 2 2 0 000 4zM12 22a2 2 0 100-4 2 2 0 000 4zM7.5 5.5l3 12M16.5 5.5l-3 12M8 4h8',
    title: 'Memory Graph',
    sub: 'records, edges and provenance \u2014 inferred edges labelled',
    keywords: ['graph', 'edges', 'records', 'provenance'],
  },
  {
    id: 'playground',
    label: 'Playground',
    group: 'Explore',
    icon: 'M6 4l14 8-14 8z',
    title: 'Playground',
    sub: 'write a memory, recall it, see the trace',
    keywords: ['sandbox', 'try', 'recall', 'trace', 'demo'],
  },
  {
    id: 'runtime',
    label: 'Runtime Console',
    group: 'Explore',
    icon: 'M4 5h16v14H4zM8 9l3 3-3 3M13 15h4',
    title: 'Runtime Console',
    sub: 'live runs, steps, budgets, traces',
    keywords: ['runtime', 'runs', 'budget', 'trace', 'observability'],
  },
  {
    id: 'docs',
    label: 'Docs / FAQ',
    group: 'Understand',
    icon: 'M5 3h9l5 5v13H5zM14 3v5h5M8 13h8M8 17h6',
    title: 'Docs / FAQ',
    sub: 'searchable, tool reference from source',
    keywords: ['docs', 'faq', 'help', 'questions'],
  },
  {
    id: 'eval',
    label: 'Eval Dashboard',
    group: 'Understand',
    icon: 'M12 13l4-4M4 18a8 8 0 1116 0z',
    title: 'Eval Dashboard',
    sub: 'recall@k, MRR, nDCG \u2014 diffed, regressions named',
    keywords: ['eval', 'recall', 'mrr', 'ndcg', 'metrics', 'ci'],
  },
  {
    id: 'sales',
    label: 'Sales',
    group: 'Sell',
    icon: 'M4 20V9M10 20V4M16 20v-7M22 20H2',
    title: 'Sales',
    sub: 'positioning \u00b7 proof \u00b7 pricing',
    keywords: ['pricing', 'positioning', 'value', 'cta'],
  },
  {
    id: 'memory',
    label: 'Memory model',
    group: 'Trust',
    icon: 'M12 3l8 4.5v9L12 21l-8-4.5v-9zM12 12l8-4.5M12 12v9M12 12L4 7.5',
    title: 'Memory model',
    sub: 'the five hard invariants, enforced at the store layer',
    keywords: ['invariants', 'grounded', 'simulated', 'partition'],
  },
  {
    id: 'ledger',
    label: 'Ledger',
    group: 'Trust',
    icon: 'M4 4h16v16H4zM8 8h8M8 12h8M8 16h5',
    title: 'Ledger',
    sub: 'hash chain, recomputed \u2014 not asserted',
    keywords: ['ledger', 'hash', 'chain', 'tamper', 'audit'],
  },
  {
    id: 'door',
    label: 'Door Sync',
    group: 'Trust',
    icon: 'M5 3h14v18H5zM12 12h.01M9 21v-2h6v2',
    title: 'Door Sync',
    sub: 'the real door contract, reported honestly',
    keywords: ['door', 'contract', 'wire', 'probe'],
  },
  {
    id: 'connection',
    label: 'Connection',
    group: 'Trust',
    icon: 'M9 15l6-6M7.5 10.5l-1.9 1.9a3.5 3.5 0 004.9 4.9l1.9-1.9M16.5 13.5l1.9-1.9a3.5 3.5 0 00-4.9-4.9L11.6 8.6',
    title: 'Connection',
    sub: 'where this shell reads from',
    keywords: ['endpoint', 'bridge', 'base', 'config'],
  },
];

/** Every route, derived from NAV so the two can never disagree. */
export const ROUTES: Route[] = NAV.map((n) => n.id);

const BY_ID = new Map<Route, NavItem>(NAV.map((n) => [n.id, n]));

export function isRoute(value: string): value is Route {
  return BY_ID.has(value as Route);
}

export function navItem(route: Route): NavItem {
  const item = BY_ID.get(route);
  if (!item) throw new Error(`no nav item for route "${route}"`);
  return item;
}

/** The default route when the hash is absent or unknown. */
export const DEFAULT_ROUTE: Route = 'kanban';

/** Resolve a location hash (with or without the leading '#') to a route. */
export function routeFromHash(hash: string): Route {
  const h = hash.replace(/^#/, '').split('?')[0];
  return isRoute(h) ? h : DEFAULT_ROUTE;
}
