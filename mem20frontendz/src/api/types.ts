/**
 * Domain types.
 *
 * These mirror the real stores, not a wishlist:
 *
 *   kanban  ← `kanban_3.db` (boards / columns / tasks) and `mem20kanbanz/door.py`
 *   dreams  ← `mem20controlz/dreams.py` return payloads
 *   tools   ← a live `tools/list` response from mem20-mcp
 *
 * Where the database and the door disagree, the door wins and the adapter
 * normalises (see `api/kanban.ts`): the door is the single writer, and a second
 * shape would be a second source of truth.
 */

/* ------------------------------------------------------------------ kanban */

/** Raw row from the `tasks` table. `metadata` is a JSON *string* in SQLite. */
export interface RawTaskRow {
  id: string;
  column_id: string;
  title: string;
  /** Omitted from board listings by the door; only `/api/tasks/{id}` carries it. */
  content?: string;
  position: number;
  created_at?: string;
  updated_at: string;
  update_reason?: string | null;
  metadata: string | null;
}

/** Raw row from the `columns` table. */
export interface RawColumnRow {
  id: string;
  board_id: string;
  name: string;
  position: number;
  wip_limit: number;
  is_done_column: number;
}

/** Raw row from the `boards` table. */
export interface RawBoardRow {
  id: string;
  name: string;
  goal: string;
  landing_column_id: string | null;
  created_at: string;
}

/** A read-only capture of `kanban_3.db`, as pulled from the host. */
export interface KanbanSnapshot {
  boards: RawBoardRow[];
  columns: RawColumnRow[];
  tasks: RawTaskRow[];
  counts: { boards: number; columns: number; tasks: number };
}

export interface Card {
  id: string;
  title: string;
  content: string;
  /** Column *name*, matching what the door reports. */
  status: string;
  assignee: string;
  tags: string[];
  metadata: Record<string, unknown>;
  position: number;
  createdAt: string | null;
  updatedAt: string | null;
  updateReason: string | null;
  /** True when the card sits in a column flagged isDoneColumn. */
  done: boolean;
}

export interface Column {
  id: string;
  name: string;
  position: number;
  wipLimit: number;
  isDone: boolean;
  isLanding: boolean;
  cards: Card[];
}

export interface Board {
  id: string;
  name: string;
  goal: string;
  landingColumnId: string | null;
  columns: Column[];
  createdAt: string | null;
}

/** One column definition as the door's create-board payload expects it. */
export interface ColumnSpec {
  name: string;
  wipLimit?: number;
  isDoneColumn?: boolean;
  isLanding?: boolean;
}

/* ------------------------------------------------------------------ dreams */

export type DreamKind = 'active' | 'idle_prototype' | 'idle_proposal' | 'idle_idea';

export interface DreamRow {
  dream_id: string;
  kind: string;
  /** Present in the engine's status payload; may be absent on older lineages. */
  state?: string;
  iteration_count?: number;
  iterations?: number;
  done?: boolean;
  hollow: boolean;
  hollow_why?: string;
  hollow_iterations?: number[];
  artifact_chars?: number | null;
  fidelity?: number | null;
  omission?: number | null;
  last_iteration_at?: number | string | null;
  age_s?: number;
  promoted: boolean;
  promotion_path?: string | null;
  promotion_files?: string[];
  derived_from?: string;
  not_derived_from?: string;
  created_at?: number;
}

export interface DreamListResponse {
  dreams: DreamRow[];
  total: number;
  returned: number;
  hidden_hollow: number;
  kinds: DreamKind[];
  promotions_root: string;
  read_s: number;
  artifacts_included: boolean;
  artifacts_note: string;
}

export interface DreamPromotion {
  promoted: boolean;
  path: string | null;
  files: string[];
  derived_from: string;
  not_derived_from: string;
}

export interface DreamDetail extends DreamRow {
  artifact: string;
  seed: string;
  foundation?: string;
  promotion: DreamPromotion;
  provenance: {
    braid_cids: number;
    uncommitted: string[];
    uncommitted_detail: string[];
    verified: boolean | null;
    verify_with: string;
  };
  kind_known: boolean;
  critique_count: number;
  best_iteration: number | null;
  iterations_detail?: DreamIteration[];
}

export interface DreamIteration {
  n: number;
  artifact?: string;
  critiques?: { model?: string; verdict?: string; text?: string }[];
  scores?: Record<string, unknown>;
  at?: number | string;
  provider_error?: string;
}

export interface DreamChain {
  dream_id: string;
  iterations: number;
  braid_committed: number;
  uncommitted: string[];
  chain: { iteration: number; cid: string }[];
}

export interface DreamVerify {
  dream_id: string;
  healthy: boolean;
  checked: number;
  verified: number;
  broken: string[];
  note?: string;
}

export interface DreamRun {
  job_id: string;
  dream_id: string;
  iterations: number;
  status: 'running' | 'done' | 'paused' | 'refused' | 'failed' | 'unknown';
  note: string;
  exit_code: number | null;
  started_at: number;
  finished_at: number | null;
  duration_s: number;
  duration_note: string;
  timed_out: boolean;
  log_path: string;
  log: string[];
  log_lines: number;
}

export interface DreamRunsResponse {
  jobs: DreamRun[];
  total: number;
  running: number;
  in_memory_only: boolean;
  note: string;
}

export interface DreamHollowReport {
  hollow_lineages: number;
  already_marked: number;
  unmarked: number;
  hollow_iterations: number;
  read_only: boolean;
  note: string;
  entries: {
    dream_id: string;
    kind: string;
    iterations: number[];
    already_marked: boolean;
  }[];
}

export interface DreamIdleStats {
  run_lock: unknown;
  [key: string]: unknown;
}

export interface DreamManifest {
  capabilities: string[];
  kinds: DreamKind[];
  default_kind: DreamKind;
  promotions_root: string;
  run: {
    max_iterations: number;
    default_iterations: number;
    timeout_s: number;
    cost_note: string;
    exit_codes: Record<string, string>;
  };
  promotion: { writes: string; refuses_on: string[]; force: string };
  honesty: Record<string, string>;
}

/* ------------------------------------------------------------------- tools */

export interface ToolSchema {
  type?: string;
  properties?: Record<string, unknown>;
  required?: string[];
  [key: string]: unknown;
}

export interface McpTool {
  name: string;
  title?: string;
  description: string;
  inputSchema: ToolSchema;
}

/** A tool plus the derived fields the browser groups and ranks on. */
export interface ToolEntry extends McpTool {
  /** Namespace prefix, e.g. `memory` for `memory_store`. */
  domain: string;
  /** Count of declared parameters. */
  paramCount: number;
  /** Names of required parameters. */
  required: string[];
}

export interface ToolDomain {
  id: string;
  count: number;
  /** The tool a newcomer should read first, chosen by the naming convention. */
  startHere: string;
  tools: ToolEntry[];
}

/* ---------------------------------------------------------------- roadmap */

/** One phase of a roadmap JSON file — Sarge's input. */
export interface RoadmapPhase {
  i: number;
  title: string;
  status: string;
  jobid: string;
  depends_on?: (number | string)[];
}

export interface RoadmapFile {
  file: string;
  goal?: string;
  phases: number;
  rows?: RoadmapPhase[];
  error?: string;
  no_phases?: boolean;
}

/* --------------------------------------------------------------- envelope */

/**
 * Every data read in this app returns this envelope.
 *
 * `source` is not decoration: the UI renders a badge from it, so a captured
 * snapshot can never be mistaken for a live read. `note` carries the specific
 * reason a fallback happened (e.g. "door unreachable at /api/door").
 */
export interface Loaded<T> {
  data: T;
  source: 'live' | 'snapshot';
  /** ISO timestamp of the read, or of the capture when source === 'snapshot'. */
  at: string;
  /** Human-readable reason when source === 'snapshot'. */
  note?: string;
  /** Milliseconds the live attempt took, when there was one. */
  latencyMs?: number;
}
