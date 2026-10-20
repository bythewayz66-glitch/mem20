# mem20 distributed sync — implementation (Option D)

Origin-tagged append-only event log + deterministic projection, layered **under**
mem20's own tables. Implements the build handoff in §13.3 of
`mem20-distributed-design.md` (v2.0).

| | |
|---|---|
| **Target** | mem20 v1.0.1 — `github.com/JaysonAIOnline/mcp-cognitive-substrate`, `src/mcp_cognitive_substrate/memory.py` |
| **Nodes** | `sidney` (primary) + `server2` (already running mem20 with live data) |
| **Status** | Phases 0–2 implemented and verified locally; remote deploy pending gabe-routed SSH credentials |
| **Deps** | Python 3.11+ stdlib only |

## Files

| File | Purpose |
|---|---|
| `mem20_sync.py` | The sync layer: `replication_state` / `events` / `proj_*` DDL, `hlc_now`, `_emit`, `project`, `vector_clock`, `ingest`, `sync_with`, `state_hash`; wraps `persist_memory` / `persist_node` / `prune_failed_approach` |
| `backfill.py` | Phase 2 — one synthetic `upsert` per legacy row, per node, from a `sqlite3 .backup` snapshot |
| `sync_cli.py` | On-demand / scheduled entry point: `status`, `state-hash`, `export`, `ingest`, `sync`, `project`; SSH transport always jumps through gabe |
| `acceptance_suite.py` | Gates G-2 (reference scenario 8/8) + G-3 (byte-identical `state_hash`) + write-path/key invariants |
| `systemd/mem20-sync.service` | oneshot unit, journald logging, fail-closed on divergence |
| `systemd/mem20-sync.timer` | 15-minute cadence, `Persistent=true` (catches up after Sidney sleeps) |
| `config/mem20-sync.env.example` | environment template (install to `/etc/mem20-sync/mem20-sync.env`, mode 600) |
| `scripts/deploy_to_sidney.sh` | gabe-routed deploy: `stage` / `snapshot` / `backfill` / `verify` / `schedule` / `all` / `rollback` |

## Design invariants honoured

- **Never a file-level sync of a live `.db`.** The only database movement is a
  `sqlite3 .backup` snapshot taken on the target host (rollback artefact for G-3).
- **Never a 2-node Raft cluster.** No consensus; anti-entropy only.
- **Never `crdt_as_crdt` on mem20's tables.** The ledger keeps the losing value in
  `superseded` — the conflict history is preserved, not dropped.
- **Tailscale only.** The sync rides SSH through gabe; nothing is exposed publicly.
- **One event per write.** `persist_memory`, `persist_node`, and
  `prune_failed_approach` each append exactly one event (verified).

## Stable logical keys

| Table | Key |
|---|---|
| `memories` | `mem:` + `sha256(session_id\|topic\|content)[:16]` (content-addressed) |
| `cognitive_substrate_history` | `hist:` + `node_id` + `:` + `seq` |
| `tot_nodes` | `node_id` unchanged (already `TEXT PRIMARY KEY`) |

## Run the gates locally

```bash
python3 acceptance_suite.py     # exit 0 = all gates pass
```

Expected: `=== 17 passed, 0 failed ===`, `ALL GATES PASS`.

## Deploy (through gabe)

```bash
export GABE_HOST=... GABE_USER=gabe
export SIDNEY_HOST=... SIDNEY_USER=root
export SERVER2_HOST=... SERVER2_USER=root
export SSH_KEY=~/.ssh/id_ed25519        # or SSHPASS=...
./scripts/deploy_to_sidney.sh all
```

`all` = stage → snapshot (G-1) → backfill (Phase 2) → verify (G-3) → schedule
(Phase 4). If G-3 fails after one debug pass, run `./scripts/deploy_to_sidney.sh
rollback` and stop (kill criterion, §13.2).
