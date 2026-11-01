# mem20 4.0 — Substrate

The stable public surface of the five wave-1 gate modules. Waves 2–3 wire
against these names, so **anything listed here is a compatibility commitment**:
it may gain optional arguments, but it will not be renamed or removed without a
major version bump.

Every entry below was read from the code on the wave-1 branches, not from the
plan. Where a module's surface is a CLI rather than a Python API, that is
stated — a CLI contract is a real contract and downstream code may shell out to
it.

Gate status at the time of writing. Four of the five gate modules pass
`python3 scripts/renovation/conformance.py <subsystem>` with exit 0. **`gateway`
does not** — it is 3/7 and is the one remaining blocker on the wave-1 exit gate.

| module | branch | gate |
|---|---|---|
| `mcp` | `feat/4.0-server-builder-mcp` | 7/7 |
| `memory_engine` | `feat/4.0-super-agent-memory-engine` | 7/7 |
| `toolchest` | `feat/4.0-super-agent-toolchest` | 7/7 |
| `mem20corez` | `feat/4.0-super-agent-mem20corez` | 7/7 |
| `gateway` | (pre-existing, unassigned) | **3/7 — FAIL** |

`gateway` fails criteria 3 (no test files), 4 (no CLI surface) and 6 (0
cross-module imports). Its public API is documented below because waves 2–3
call it, but it is not yet a stable substrate module and needs an owner.

---

## `memory_engine` — the grounded-fact store

The substrate's memory. Grounded facts and simulated hypotheses are stored
separately and never mix; every retrieval result carries its epistemic label.

### `memory_engine.memory`

| name | signature | contract |
|---|---|---|
| `remember` | `(topic, content, tags=None, epistemic_status=..., ...) -> dict` | Writes a grounded fact. `epistemic_status` is **required** — an unlabeled write is refused, because a defaulted label is indistinguishable from an asserted one at every later read. |
| `remember_simulated` | `(topic, content, tags=None, ...) -> dict` | Writes a hypothesis. Never returned by a grounded-only read. |
| `recall` | `(topic=None, tags=None, ...) -> list[dict]` | Exact/topic read. Each row carries `epistemic_status`. |
| `recall_at` | `(as_of=None, topic=None, ...) -> list[dict]` | Point-in-time read. |
| `recall_semantic` | `(query, k=5, topic=None, ...) -> list[dict]` | Vector read. Returns `[{"error": ...}]` — **not** an exception — when the vector backend is absent; callers must check for `"id"`. |
| `recall_hybrid` | `(query, k=5, topic=None, ...) -> list[dict]` | BM25 + vector fused by reciprocal rank. Degrades to whichever half is available. |
| `recall_graph` | `(entity, hops=2, max_results=20, ...) -> list[dict]` | Graph traversal. |
| `pin_block` | `(block_id, content, reason="", actor="agent", ...) -> dict` | Pins a block so it survives compaction. |
| `get_pinned_block` | `(block_id, actor="agent") -> dict` | Reads a pinned block back. |
| `list_pinned_blocks` | `(actor="agent") -> dict` | All pinned blocks. |
| `unpin_block` | `(block_id, actor="agent") -> dict` | Removes a pin. |
| `detect_secrets` | `(content, min_confidence="low") -> list[SecretFinding]` | Secret scan. |
| `redact_secrets` | `(content, min_confidence="low") -> tuple[str, list[SecretFinding]]` | Redacts and reports. |

### `memory_engine.retrieval_v2`

`calibrated_search`, `rerank`, `mmr` — hybrid retrieval primitives used by
`recall_hybrid`.

### `memory_engine.cli` — CLI contract

`python3 -m memory_engine.cli <command> [--json]`

| command | purpose |
|---|---|
| `stats` | store counts |
| `recall` | read by topic |
| `remember` | write a grounded fact (`--epistemic-status` required) |
| `wiring` | prove every cross-subsystem edge; `--record` also writes a snapshot |

With `--json` every command emits the shared `mem20.cli/1` envelope
(`schema`, `ok`, `command`, `argv`, `stdout`, `exit_code`). Exit code is
non-zero on failure, so `wiring` is usable as a health check.

### `memory_engine.integrations`

`available()`, `wiring_report(record=False)`, `ledger_digest()`,
`classify_topic_key()`, `model_parameter_count()`, `cli_envelope()`,
`test_bearing_packages()`, `tool_inventory_counts()`,
`record_estate_snapshot()`.

---

## `mcp` — the tool surface

### `mcp.server.Mem20MCPServer`

The single MCP server. Subsystem tools are contributed as mixins in
`mcp/tools/` and added to this class's bases; `_execute_tool` dispatches by
tool name. **Adding a subsystem's tools means adding its mixin to the bases
here** — that is the registration point criterion 7 checks.

### `mcp.surface`

Tool-surface admission control. `admit_tool()` delegates to estate modules
(`mem20ops`, `mem20verify`, `mem20liez`, `mem20temporaldatabasefabricz`,
`mem20ircz`) rather than reimplementing their rules.

### `mcp.cognitive_tools`, `mcp.memory_tools`, `mcp.roadmap_tools`

Tool mixins over `memory_engine` and the roadmap store.

---

## `toolchest` — the on-box tool inventory

### `toolchest.catalog`

| name | signature | contract |
|---|---|---|
| `build_inventory` | `(help_sampling=True) -> dict` | The full inventory: MCP tools, CLI binaries, subsystem packages. |
| `discover_mcp_tools` | `() -> dict` | MCP tools found by AST-walking the server modules. |
| `discover_cli_bins` | `(help_sampling=True) -> dict` | Installed CLI binaries, classified. |
| `cli_subcategory` | `(name) -> str` | Category for a CLI name. |

### `toolchest.cli` — CLI contract

`python3 -m toolchest <command>`; `main(argv=None) -> int`.

---

## `gateway` — agent registration and messaging

> **Not yet a stable substrate module.** 3/7 on the gate (no tests, no CLI,
> no cross-module wiring). Documented because waves 2–3 call it; treat these
> names as provisional until the module is brought to 7/7.

### `gateway.mem20_gateway`

| name | signature | contract |
|---|---|---|
| `register_agent` | `(name=None, location=None) -> dict` | Registers an agent with the gateway. |
| `list_agents` | `() -> dict` | Registered agents. |
| `load_names` | `() -> dict` | Name registry. |
| `broadcast` | `(message, agent_name=None, target="telegram_channel")` | Fan-out a message. |
| `read_messages` | `(since=None, agent=None, limit=50)` | Read the message log. |
| `ensure_dirs` | `()` | Create the gateway's state dirs. |

---

## `mem20corez` — the character model

### `mem20corez.mlp`

| name | signature | contract |
|---|---|---|
| `CharMLP` | `(vocab_size, hidden, ...)` | Character-level MLP. Parameter count scales with `hidden` in both layers. |
| `train_default_model` | `(...)` | Trains the default model. |
| `make_corpus` | `() -> str` | The training corpus. |
| `softmax` | `(z: np.ndarray) -> np.ndarray` | Numerically-stable softmax. |

### `mem20corez` modules

`batcher`, `distiller`, `evaluator`, `quantizer`, `config`, `server`, `cli`.

---

## Rules for waves 2–3

1. **Import from the module, not through a re-export.** `from memory_engine.memory import recall_hybrid`, not `from memory_engine import recall_hybrid`.
2. **Check `recall_semantic` for `"id"`.** It reports a missing backend as a result dict, not an exception.
3. **Never default `epistemic_status`.** A write without a label is refused by design.
4. **Register MCP tools by adding a mixin to `Mem20MCPServer`'s bases.** A tool that is not in the bases is not registered.
5. **Do not add the repo root to `sys.path`.** Bare `<root>/mem20foo` directories shadow the real packages; probe nested `src/` layouts first.
