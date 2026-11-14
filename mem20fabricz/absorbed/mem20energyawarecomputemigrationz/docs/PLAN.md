# Energy-Aware Compute Migration (RM-047) — implementation plan

## Goal
Schedule compute around battery, thermal limits, electricity price, and
renewable availability. The fleet optimizes both performance and energy use.

## Delivered
- `domain.py`: legacy-compatible `energy_cost`, `migrate_decision`,
  `carbon_footprint`, `greenest_node` (tie-break by node id, preserved),
  `migration_plan`; plus `ComputeNode`/`Workload`, feasibility, scoring,
  `plan_migrations`, `fleet_energy_summary`.
- `store.py`: SQLite WAL versioned nodes/workloads, events, migration journal,
  idempotency, snapshots/restore.
- `ecosystem.py`: 6 unique peers (different from #300/#301/#302):
  `mem20batteryawareagentschedulerz`, `mem20energyawarefoundationz`,
  `mem20datalocalityoptimizerz`, `mem20causalroutingbrainz`,
  `mem20goaleconomyschedulerz`, `mem20planetarybatchfabricz`.
- `service.py`/`runtime.py`/`web/`: plan/migrate/status/doctor, CLI, JSON HTTP,
  cockpit, 400/404/409 mapping.

## Compatibility
Preserves domain API used by `mem20causalroutingbrainz` (`greenest_node` tie-break fix retained).

## Verification
`pytest mem20energyawarecomputemigrationz/tests -q`, `simulate` 9/9, `doctor` 6/6, conformance 7/7.
