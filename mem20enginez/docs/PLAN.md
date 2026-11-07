# mem20enginez crew runtime — implementation plan (#305)

## Goal
First-class runtime for the 30-member engine crew: truthful member registry and
probing, compatibility/dispatch planning, durable state, operator surfaces, and
real integration with the mem20 ecosystem.

## Delivered
- `domain.py`: canonical 30 `MEMBERS` registry, `EngineMember`/`MemberStatus`/
  `RuntimePlan`/`RuntimeReport`, filesystem+import member checks, compatibility,
  deterministic dispatch planning by capability/intent.
- `store.py`: SQLite WAL objects/events/plans/runs/idempotency/snapshots.
- `ecosystem.py`: 6 unique peers (different from #300-#304), real calls:
  `mem20runtimecompatibilityenginez`, `mem20protocolautodiscoveryenginez`,
  `mem20speculativeworkflowenginez`, `mem20servicebundlingenginez`,
  `mem20predictiverecallenginez`, `mem20customerlifecycleenginez`.
- `service.py`: members/status/doctor/plan/execute/events/runs/simulate/benchmark.
- `runtime.py` + `web/`: CLI (`--version/--members`, status/doctor/members/simulate/
  benchmark/plan/events/serve/execute), JSON HTTP API, static cockpit.
- Root shims for estate-root import/`python -m mem20enginez` compatibility.
- `tests/`, README with fenced runnable example, docs/app monitor, gateway/toolchest.

## Verification
`pytest mem20enginez/tests -q` passes; `simulate`/`doctor` return 6/6 peers;
`conformance.py mem20enginez` target 7/7.
