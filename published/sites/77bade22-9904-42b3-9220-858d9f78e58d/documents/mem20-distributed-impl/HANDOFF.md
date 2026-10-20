# HANDOFF — mem20 distributed sync (Option D), Phases 0–2

**From:** Server Builder · **To:** mem20 Orchestrator · **Date:** 2026-10-14

## Build status: implementation COMPLETE and verified locally; remote deploy PENDING credentials

The sync layer is built, and every gate that can be exercised without the two
live servers has been exercised with real output. Remote deployment to
Sidney + server2 could **not** be executed from this sandbox: there are no SSH
hosts, keys, passwords, or jump-host details for `sidney`, `server2`, or `gabe`
in the environment (`~/.ssh` is empty; no `SIDNEY_*` / `GABE_*` vars). Nothing
was fabricated — the deploy is staged and ready for whoever holds those
credentials.

## Deliverables (permanent URLs)

| Artefact | URL |
|---|---|
| `mem20_sync.py` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/mem20_sync.py |
| `backfill.py` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/backfill.py |
| `sync_cli.py` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/sync_cli.py |
| `acceptance_suite.py` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/acceptance_suite.py |
| `systemd/mem20-sync.service` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/systemd/mem20-sync.service |
| `systemd/mem20-sync.timer` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/systemd/mem20-sync.timer |
| `config/mem20-sync.env.example` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/config/mem20-sync.env.example |
| `scripts/deploy_to_sidney.sh` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/scripts/deploy_to_sidney.sh |
| `README.md` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/README.md |
| `evidence/01-acceptance.txt` | https://static.teamily.ai/sites/77bade22-9904-42b3-9220-858d9f78e58d/documents/mem20-distributed-impl/evidence/01-acceptance.txt |

## Verification results (real output, this run)

```
=== 17 passed, 0 failed ===
G-2 convergence hash: 66f8712fe16c758e8efca85755013293e9917110d7d191b5473a74f379bdd1a6
G-3 converged hash:   7eabc79a5eefac47e4910f411720c792a1a14cd5d9f9889e79bf7645d23b16bc
ALL GATES PASS
```

- **G-2 — reference scenario 8/8 PASS** on two temp DBs: baseline converges,
  nodes diverge during the partition, no data loss, the conflicting key
  `mem:sidney:backup` converges to one identical value (winner `server2`), both
  nodes reach a byte-identical `state_hash`, the losing value is retained in
  `superseded`, the tombstone is honoured, and the prune propagates.
- **G-3 — HARD GATE PASS**: backfill from a `sqlite3 .backup` snapshot yields a
  byte-identical `state_hash()` on both nodes, and a second anti-entropy round is
  a no-op (idempotent).
- **Invariants PASS**: each wrapped write path emits exactly one event
  (`[0,1,2,3]`); keys are `mem:<sha256[:16]>` / `hist:<node>:<seq>` / `node_id`;
  content-addressed keys are idempotent; `ingest` is idempotent by `event_id`.
- **CLI round-trip** (export → ingest both ways) converges to identical hashes.
- `bash -n scripts/deploy_to_sidney.sh` and `py_compile` on all four modules: OK.

## What the next actor must do (needs gabe-routed SSH credentials)

1. Export the connection details (no secrets in the bundle):
   `GABE_HOST GABE_PORT GABE_USER`, `SIDNEY_HOST/PORT/USER`,
   `SERVER2_HOST/PORT/USER`, and `SSH_KEY` (or `SSHPASS`).
2. `./scripts/deploy_to_sidney.sh stage` — copy the four modules to
   `/opt/mem20-sync` on both nodes (through gabe).
3. `./scripts/deploy_to_sidney.sh snapshot` — **G-1**: `sqlite3 .backup` both
   DBs (never `cp`), confirm each opens with `PRAGMA integrity_check`.
4. `./scripts/deploy_to_sidney.sh backfill` — Phase 2: one synthetic `upsert`
   per legacy row, per node.
5. `./scripts/deploy_to_sidney.sh verify` — **G-3 HARD GATE**: compare
   `state_hash()` on both nodes. **Do not archive the snapshots until this
   passes.** If it fails after one debug pass, run
   `./scripts/deploy_to_sidney.sh rollback` and stop (kill criterion, §13.2).
6. Fill `/etc/mem20-sync/mem20-sync.env` (from `config/mem20-sync.env.example`,
   mode 600) on each node, then `./scripts/deploy_to_sidney.sh schedule` —
   installs and enables `mem20-sync.timer` (15-min cadence, journald).
7. **G-4**: confirm two consecutive scheduled syncs converge with no drift
   (`journalctl -u mem20-sync.service`).

## Constraints honoured

No file-level sync of a live `.db`; no 2-node Raft; no `crdt_as_crdt` on mem20's
tables; Tailscale/SSH-through-gabe only, nothing public. The optional
`supergateway` stdio→Streamable HTTP item (deliverable 7) was **not** built — it
is explicitly optional and needs tailnet access not present in this sandbox.
