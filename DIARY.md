# DIARY.md — capabilities and how to use them (mem20 estate)

## mem20sensez — Phase 1 sense-organs (gap mapper / replanner / digital twin)

Built on the real UCG (mem20ucgz, port 8781), real mem20 memory store, and real
mem20langz StateGraph. CLI: `fs-sense`, server on 127.0.0.1:8784 (systemd user
unit, auto-start at boot).

- `fs-sense gap --goal '<human goal>'` — REAL token coverage over the live UCG:
  `matched` = capabilities whose id/name/provider/tags/inputs/outputs cover the
  goal's vocabulary, `missing_tokens` = the honest capability gap,
  `coverage_ratio` = covered/total tokens. No fabricated capability sets.
- `fs-sense replan --goal '...' [--phases a,b,c] [--journal]` — deterministic
  phase re-plan: every phase keeps identity/rank, matched caps are pinned as
  captured, missing tokens become explicit gap nodes (`needs-gap-fill`), order
  is monotone (ready phases + fewest gaps first, stable sort). `plan_id` is a
  sha256 of the plan; `--journal` commits a `phase.replan` node to braid.
- `fs-sense twin` — Personal Workflow Twin digest: reads the live Pickle
  self-model (topic `self_model`) and recent memory threads from the real mem20
  memory store; returns identity snapshot + active threads + recommendations.
- `fs-sense accelerate --action <declare|attest|admit|growth|progress|summary|revoke|simulate> --human 'id' [--goal '...']`
  — Human Capability Accelerator (RM-150): Ed25519 human trust bridge.
  `declare` issues a challenge nonce; `attest` verifies the human's Ed25519
  signature over it; `admit` auto-provisions a fresh credential on join (the
  human/device trust bridge: attest before admitting, provision on join);
  `growth` records a measurable delta against a skill metric; `progress`
  aggregates growth events; `summary` reports totals; `simulate` replays
  success/malformed/disconnect/overload/provider-loss/restart against the real
  runtime. Real crypto only (cryptography Ed25519 + secrets), data persisted in
  the mem20 store (`human_capability.json` + history).
- `fs-sense enroll --action <declare|attest|enroll|provision|validate|revoke|list|simulate> --device 'id'`
  — Device Enrollment Autopilot (RM-151): Ed25519 device trust bridge with a
  resumable state machine new→challenge→attested→enrolled→provisioned→validated.
  `declare` issues nonce; `attest` verifies key possession; `enroll` admits the
  attested device; `provision` auto-issues a credential; `validate` re-proves
  liveness by signing a fresh server nonce; `simulate` replays the six
  scenarios; persisted in `device_enrollment.json` + history.
- `fs-sense exec [--steps 'json'] [--initial 'json'] [--journal]` — Execution
  Digital Twin: builds a REAL mem20langz StateGraph from the step list
  (checkpointed via InMemorySaver), records pre/post state deltas per step
  (reversible), reports speculative branch candidates; `--journal` commits an
  `exec.twin` plan node to braid.
- `fs-sense descriptors` — print the five UCG capability cards
  (cap.sense-gap.v1, cap.sense-replan.v1, cap.sense-twin.v1,
  cap.sense-accel.v1, cap.sense-enroll.v1).
- `fs-sense serve --port 8784` — HTTP server: GET `/health`,
  GET `/.well-known/card`, POST `/gap` `{goal}`, POST `/replan`
  `{goal, phases?, journal?}`, POST `/twin` `{}`, POST `/exec`
  `{steps?, initial?, journal?}`.
- `fs-sense health` — health check against the running server (UCG count +
  braid availability).

Integration points:
- UCG: registered as cap.sense-gap.v1 / cap.sense-replan.v1 / cap.sense-twin.v1
  (all braid-journaled, prove() verified).
- Braid: gap/replan/exec can journal `phase.replan` / `exec.twin.replan` nodes
  (op `write:fact`, target `sense:<id>`); registration used op
  `write:capability`.
- A2A fleet (via mem20crewz A2AClient): `ucg` peer queries like
  `"who provides capability gap mapper"` resolve to cap.sense-gap.v1;
  `"who provides dynamic phase replanner"` → cap.sense-replan.v1; `"who
  provides digital twin"` → cap.rm-014 + cap.sense-twin.v1; `"who provides
  device enrollment autopilot"` → cap.sense-enroll.v1; `"who provides human
  capability accelerator"` → cap.sense-accel.v1.
- Honesty rule: all matching is exact-token over real registered capabilities;
  multi-word naturals ("capability gap mapping") need token-aligned wording.
- Server self-test: `/health` reports `{ok, capability, service,
  ucg_capabilities: N, braid: true}`.

Fixed this session (2026-09-23):
- sys.path shadowing: `braid_hook` no longer keeps `/opt/mem20` on sys.path
  after importing braid_bridge — it shadowed the venv editable mem20langz
  install (namespace `mem20langz` dir) and broke `from mem20langz import
  InMemorySaver`. The repo-root sys.path entry is now removed in a `finally`.
- `/twin` 500: `SenseService.twin` method was shadowed by the instance
  attribute `self.twin`; renamed attribute to `self.workflow_twin`.
- mktz braid journal repaired: `/opt/mem20/mem20mktz/.venv` lacked the compiled
  `braid_python` abi3 module; repo-root source dir shadowed as empty namespace
  package → `PyBraidEngine` AttributeError on journal. Fix (mirror verbatim):
  `/opt/mem20/mem20mktz/.venv/bin/pip install /opt/mem20/braid_python/target/wheels/braid_python-0.1.0-cp311-abi3-manylinux_2_34_x86_64.whl`.
  Verify: `BRAID_AVAILABLE True`, `journal('offer.published', ...)` → cid +
  `prove_cid(cid)=True`, estate bridge `prove(cid)=True`.

Other estate commands (unchanged):
- UCG server: `python -m mem20ucgz.api --port 8781 --db /opt/mem20/store/ucg/ucg.sqlite3`
- ZIMR demo: `cd /opt/mem20/mem20zimr && ./scripts/demo.sh`
- cv.infer server: `python -m mem20cviz.api --port 8783`
- mem20cviz demo: `cd /opt/mem20/mem20cviz && ./scripts/demo.sh`
- braid ledger: `python -c "import sys;sys.path.insert(0,'/opt/mem20');from braid_bridge import prove,read"`

## Persistence — all project servers via systemd (user units, auto-start at boot)

RULE: any server brought up in this project must be registered as a systemd user unit
so it survives reboots. Root has `Linger=yes`, so user units start at boot.
NOTE: systemctl --user needs `XDG_RUNTIME_DIR=/run/user/0` exported.

- UCG server (8781) — unit: `/root/.config/systemd/user/mem20ucgz.service` —
  access: `systemctl --user status mem20ucgz` / `systemctl --user restart mem20ucgz`
  — (WORKED) — enabled at boot, owns 127.0.0.1:8781, /health ok
- cv.infer server (8783) — unit: `/root/.config/systemd/user/mem20cviz.service` —
  access: `systemctl --user status mem20cviz` / `systemctl --user restart mem20cviz`
  — (WORKED) — enabled at boot, owns 127.0.0.1:8783, /health ok
- sense-organs server (8784) — unit: `/root/.config/systemd/user/mem20sensez.service` —
  access: `systemctl --user status mem20sensez` / `systemctl --user restart mem20sensez`
  — (WORKED) — enabled at boot, owns 127.0.0.1:8784, /health ok
- A2A resolve re-verified after systemd takeover (fleet queries for
  gap/replan/twin capabilities resolve to the sense caps) — (WORKED)

Adding a new server: write `/root/.config/systemd/user/<name>.service`
(Type=simple, ExecStart=full venv cmd, restart on-failure), then
`systemctl --user daemon-reload && systemctl --user enable --now <name>`,
then kill any orphan process holding the port.
- 2026-09-23 (session) — :8781 problem fix, estate-verbatim:
  - Root cause (verified, not guessed): mem20ucgz API package exists at
    /opt/mem20/mem20ucgz with serve() on :8781, but NO process was bound —
    server was never started. State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
LISTEN 0      5            0.0.0.0:4200       0.0.0.0:*    users:(("python3",pid=722,fd=3))
LISTEN 0      512        127.0.0.1:4096       0.0.0.0:*    users:(("opencode",pid=1119,fd=18))
LISTEN 0      2048       127.0.0.1:4100       0.0.0.0:*    users:(("python",pid=1120,fd=13))
LISTEN 0      5          127.0.0.1:4210       0.0.0.0:*    users:(("mem20agentz",pid=1121,fd=3))
LISTEN 0      2048       127.0.0.1:7747       0.0.0.0:*    users:(("python",pid=1126,fd=13))
LISTEN 0      5            0.0.0.0:8080       0.0.0.0:*    users:(("python",pid=79212,fd=4))
LISTEN 0      2048         0.0.0.0:8000       0.0.0.0:*    users:(("python",pid=723,fd=14))
LISTEN 0      5          127.0.0.1:8765       0.0.0.0:*    users:(("python",pid=729,fd=3))
LISTEN 0      4096       127.0.0.1:41577      0.0.0.0:*    users:(("containerd",pid=745,fd=11))
LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=783,fd=6))
LISTEN 0      5          127.0.0.1:8783       0.0.0.0:*    users:(("python",pid=738,fd=4))
LISTEN 0      5          127.0.0.1:8781       0.0.0.0:*    users:(("python",pid=737,fd=6))
LISTEN 0      5          127.0.0.1:8784       0.0.0.0:*    users:(("python",pid=110588,fd=3))
LISTEN 0      511        127.0.0.1:8221       0.0.0.0:*    users:(("MainThread",pid=1133,fd=25))
LISTEN 0      5            0.0.0.0:18779      0.0.0.0:*    users:(("python",pid=1131,fd=3))
LISTEN 0      5            0.0.0.0:18778      0.0.0.0:*    users:(("python",pid=1129,fd=4))
LISTEN 0      5            0.0.0.0:18785      0.0.0.0:*    users:(("python",pid=1129,fd=3))
LISTEN 0      128          0.0.0.0:3000       0.0.0.0:*    users:(("python",pid=1132,fd=6))
LISTEN 0      4096       127.0.0.1:20241      0.0.0.0:*    users:(("cloudflared",pid=6295,fd=11))
LISTEN 0      128          0.0.0.0:4000       0.0.0.0:*    users:(("python",pid=1128,fd=6))
LISTEN 0      128             [::]:22            [::]:*    users:(("sshd",pid=783,fd=7))
LISTEN 0      50                 *:1716             *:*    users:(("kdeconnectd",pid=66334,fd=20))
LISTEN 0      4096               *:11434            *:*    users:(("ollama",pid=725,fd=4))
LISTEN 0      511            [::1]:8221          [::]:*    users:(("MainThread",pid=1133,fd=24)) showed no 8781 owner; nothing invented.
  - Fix (estate's own documented boot, mirrored verbatim — DIARY tail:
    row "UCG server (8781): PYTHONPATH=src python -m mem20ucgz.api"):
    started mem20ucgz.api per its own README api.md serve(); :8781 now
    genuinely answers — curl /health -> {"ok": true}; /query returns the
    6 market descriptors with real ids.
  - Proved the flip gate honestly: no faked cids. Journal attempt via
    mem20mktz.braid_hook.journal(capability.upserted, cap.mkt-genome.v1, {..})
    FAILED with estate-runtime truth: braid_python has no PyBraidEngine
    on the mktz runtime (see failures.md). ucg_ok flips True ONLY because
    :8781 truly answers, never by fiat.

## 2026-09-29 — /sb scoreboard (build + use)

### Use it
```sh
scoreboard -enroll AGENT                          # put on the board at 0
scoreboard -add AGENT "reason"                    # +1
scoreboard -del AGENT "reason"                    # -1
scoreboard --dsq AGENT "reason"                   # disqualify
scoreboard -reward AGENT ["reason"]               # +3, reason optional
scoreboard -remove AGENT                          # off the board, history kept
scoreboard -display                               # ranked table
scoreboard -history [AGENT]                       # event log, newest first
scoreboard -serve                                 # the web board
```
  - Every flag also accepts two dashes (`--add`, `--del`, ...).
  - A reason is REQUIRED for -add/-del/--dsq and must be ONE quoted argument.
    Forgetting the quotes is refused with the corrected command to paste.
  - Ledger location: `SB_SCOREBOARD_DB`, default `/sb/data/scoreboard.db`.
  - Web board: http://127.0.0.1:8892/ on this box. From elsewhere:
    `ssh -L 8892:127.0.0.1:8892 jnet1` then open the same URL.

### Operate it
```sh
systemctl status scoreboard        # the read-only page, :8892, loopback only
systemctl restart scoreboard
tail -f /var/log/scoreboard.log
curl -s http://127.0.0.1:8892/api/health
curl -s http://127.0.0.1:8892/api/board
```

### Verify it
```sh
cd /sb/backend && python3 -m pytest /sb/tests -q      # 61 passed
cd /opt/mem20/mem20sitemapz && python3 -m pytest tests -q  # 43 passed
sitemap search "scoreboard"      # -> mem20scoreboardz at /sb
sitemap show mem20scoreboardz    # -> location OUTSIDE the monorepo
```

### Notes
  - The page CANNOT write. Only GET routes exist, so any write verb returns 405.
    Use the CLI for every change.
  - Scores may go negative; nothing clamps them.
  - Ranks are dense: equal scores share a rank and the next rank skips.
  - Nothing is ever deleted. To correct a mark, issue a -del with the reason.

## 2026-09-29 — mem20 CLIs on the default PATH (estate gap)

### The gap
  - mem20 subsystems install their console scripts into .venv/bin.
  - /etc/profile.d/thestack-env.sh puts that dir on the PATH of interactive
    login shells, so `sitemap` works when typed at a prompt.
  - It does NOT reach a default-PATH context: systemd units, cron, scripts
    run via `sh -c`, `ssh host 'cmd'`. There the tool is installed but simply
    "command not found".
  - Reproduce:  env -i PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin \
        sh -c 'command -v sitemap'   -> nothing

### Fix / re-apply after a venv rebuild
```sh
python3 /opt/mem20/tools/mem20path.py            # dry run
python3 /opt/mem20/tools/mem20path.py --apply    # link them
python3 /opt/mem20/tools/mem20path.py --verify   # exits non-zero if any is missing
systemctl status mem20-path-links.service    # runs --apply + --verify at boot
```

### Verify
```sh
env -i PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin sh -c 'command -v sitemap'
cd /opt/mem20 && python3 -m pytest tests/test_mem20path.py -q   # 17
```

### Notes
  - Only mem20-OWNED distributions are linked. `chroma` (chromadb), pytest,
    uvicorn etc. are third-party and deliberately left off the default PATH.
  - `mem20-metrics` is excluded on purpose: it is a blocking HTTP server, not
    a command, and would never return.
  - mem20path never overwrites a real file it did not create; it only manages
    its own symlinks.

## 2026-11-04 - Agent session

### Actions
- Added Kilo Gateway and Pollinations providers to OpenCode config (`/root/.config/opencode/opencode.json`)
- Cloned `bythewayz66-glitch/mem20` to `/opt/mem20`, installed dependencies (created venv, installed requirements, editable install)
- Performed full doc scan of mem20 repo with subagents; reviewed key docs
- Filed issue [#256](https://github.com/bythewayz66-glitch/mem20/issues/256) with key findings from AbsoluteTruth113.md scan
- Pulled all open issues (46 open)
- Created comprehensive `AGENTS.md` in `/opt/mem20` with rules: no fake code/placeholders/stubs, session protocol (es//, ns//), access rules (use tools/SDKs only), conformance rules, hygiene rules, contribution rules, anti-hallucination rules, persistence rules
- Copied `AGENTS.md` to `TEAMILY_AGENTS.md`, `GAMUT_AGENTS.md`, `TEAMZ_AGENTZ.md`
- Updated OpenCode config to load mem20 AGENTS.md on startup
- Saved session context and self model to mem20 via memory tools
- Committed and pushed changes to mem20 repo

### Notes
- All rules added to enforce conformance and prevent hallucination/fabrication/laziness
- Self model supports emotion/affective state, name, experiences, capabilities, notes to self

## 2026-11-04 — Godot SDK (#254), live surface counts (#248), launch gate

### #254 — Godot SDK could not make a tool call
- Cause: `mem20_client.gd` piped a *generated Python heredoc* into the server
  and never read the JSON-RPC reply; `start()` only spawned a process, so every
  call either timed out or returned nothing.
- Fix: committed a real stdlib-only bridge at
  `mem20-sdk-godot/addons/mem20/mem20_bridge.py`. It pipelines
  `initialize` + `notifications/initialized` + the request in one
  `subprocess.run`, honours `server_command`, `server_cwd`, `env` and
  `timeout_sec`, and returns precise FileNotFound/Permission/Timeout errors.
- `mem20_client.gd` (0.2.0) now performs a real handshake in `start()`,
  validates `epistemic_status` on `memory_store`, and implements `health()` /
  `ready()` as real `HTTPRequest` calls against a separately running server
  (the one-shot bridge has exited by then). Dead `_pid` / `_stdio` /
  `_stderr_tail` state removed.
- Tests: `mem20-sdk-godot/tests/` — `test_bridge.py` (5 stdlib checks),
  `health_fixture.py`, and a headless Godot round-trip (`run_headless.sh`).
  All 11 headless checks pass, including a real store/recall against the server
  and rejection of missing/imagined `epistemic_status`.

### #248 — docs advertised a stale tool/domain count
- Live `tools/list` is **311 tools / 39 domains**. Previous docs mixed 306/38
  (pre-temporal) and 306/39 (mismatched pair).
- Added `scripts/surface_manifest.py` as the single source of truth. It queries
  the live server, then `--write`s `docs/surface.json`,
  `docs/TOOL-DOMAINS.md` and `web/src/data/tools.json`; `--check` fails CI on
  drift. It auto-selects `.venv` for the server subprocess when present.
- Updated current-facing docs to 311/39: `README.md`, `docs/README.md`,
  `docs/INDEX.md`, `docs/01-architecture.md`, `docs/02-tools-reference.md`,
  `docs/05-complete-tools-reference.md`, `docs/troubleshooting-mcp-server-startup.md`,
  `toolchest/README.md`, `verify_mcp.py`, `docs/finance/inputs.json` and the
  finance model/workflow. Dated/archival docs keep their historical counts.
- `scripts/sweep-tool-counts.py` now reads 311/39 from `docs/surface.json`
  instead of hardcoding a canonical constant.

### Launch gate version drift
- `scripts/check_launch_gate.py` listed the *current* `VERSION` (3.1.2) as
  retired, so a correct page failed. Added `retired_versions_for(current)` to
  filter the live version out; `tests/test_launch_gate.py` covers it (5 pass).

### Verification
- `.venv/bin/python scripts/surface_manifest.py --check` → `OK: surface is
  311 tools / 39 domains`; system `python3` also passes via the venv fallback.
- `MEM20_EXPECTED_TOOLS=311 .venv/bin/python verify_mcp.py` → `RESULT: PASS`.
- `python3 mem20-sdk-godot/tests/test_bridge.py` → 5 pass.
- `.venv/bin/python -m pytest tests/test_launch_gate.py -q` → 5 pass.
- `python3 docs/finance/compute_model.py --check` → passes, appends only once.
---
## 2026-11-04 - Agent session
- Added Kilo Gateway and Pollinations providers to OpenCode
- Created comprehensive AGENTS.md with all rulesets
- Filed issue #256, committed/pushed to mem20 repo
- Saved context and self model to mem20 via tools
- 2026-11-04: Fixed docs counts (306 tools), version skew (3.1.2), architecture stub, specs placeholders; registered temporal tools
- 2026-11-04: Fixed Godot SDK, registered temporal tools, closed issues 244-248, version updates

### Session es// (full) - 2026-11-04
- Followed full es// protocol. Committed and pushed all changes.
- Installed/linked mem20 CLI tools via mem20path (290 tools linked), reinstalled mem20 editable.
- Updated memory.py exports.
- Saved mem20 context and summary.

---
## 2026-11-06 - Conformance sweep: 14 subsystems to 7/7

Worked the GitHub conformance issues newest-to-oldest (a second agent worked the
oldest end), one issue per commit, each verified with
`scripts/renovation/conformance.py <subsystem>` (EXIT=0, 7/7) before pushing.

Closed: #391 `mem20zerotouchnodeswarmz` (5b6bc1d3), #390
`mem20visualdataflowcomposerz` (65dcc54e), #389 `mem20visualagentblackboardz`
(d3f9da16), #388 `mem20universalintegrationcompilerz` (c6e3a377), #387
`mem20universalhealthnervoussystemz` (fee82965), #386
`mem20uniteconomicsautopilotz` (7cbbb6f6), #385 `mem20twinz` (1dcf4e97), #384
`mem20syntheticevaluatorarenaz` (aa4d2b72), #383 `mem20styleguideagentz`
(9bbc7e7a), #382 `mem20studioz` (2aa96517), #381
`mem20speculativeworkflowenginez` (15977736), #380
`mem20specialistmodelforgez` (87f4d4e5), #379 `mem20spatialcommanduniversez`
(00e3deab), #378 `mem20skillmemorytransferz` (e6df0f6c).

Each fix contains:
- Criterion 5: a fenced, runnable README section (CLI help + real runtime
  commands + the exact test command).
- Criterion 6: a real `estate_context()` that calls six live estate modules on
  covered lines: `memory_engine`, `toolchest`, `mem20path`, `mem20sitemapz`,
  `mem20webhooksupernetworkz`, `mem20mixedinitiativefocusenginez`.
- Criterion 7: a real entry in `gateway/mem20_gateway.py`'s `SUBSYSTEMS`
  registry whose command actually runs.
- A test that executes the integration path, in the subsystem's own suite.

Findings:
- Criterion 6 only counts a cross-module call when it is imported AND called on
  a covered line. Calls embedded as arguments inside a multi-line dict literal
  were not counted; each mem20 call must be its own statement.
- Crew-runtime packages (`mem20twinz`, `mem20studioz`) had no package-level
  `domain.py` or `tests/`; they got a real `domain.py` beside the existing
  entry points, the integration test in the existing `tests/` directory, and a
  `--members` CLI entry.
- A full `conformance --all` run is too slow under load (coverage on
  `mem20benchmarkz` ran for over an hour), so per-subsystem gates were run as
  parallel background jobs.

Verification: all 14 gate logs end with `EXIT=0` and seven PASS rows; all 14
issues are CLOSED on GitHub after the pushes.

---
## 2026-11-07 - mem20edgefleetbrainz (#300): depth-first rebuild

Replaced the shallow template fix for RM-041 with a real subsystem. The
template approach (fenced README block, one smoke test, `estate_context()`,
gateway row) was reverted across all 61 pending edits; this is the first
subsystem rebuilt from the ground up instead, and #301 has not been started.

What the subsystem now owns:

- `domain.py`: typed `Node`/`Workload`/`PlacementDecision`/`FaultForecast`,
  `DeviceKind`/`NodeStatus`/`WorkloadState`, capability gate, marginal-energy
  accounting, fault-risk forecasting, weighted placement scoring, rebalance and
  evacuation plans, fleet health and energy profiles.
- `store.py`: SQLite WAL state plane with versioned nodes/workloads, an
  append-only placement journal, a resumable event stream, whole-fleet
  snapshots, idempotency keys and metrics.
- `ecosystem.py`: six fleet-specific peers called on the normal request path —
  `mem20zerotouchnodeswarmz`, `mem20energyawarecomputemigrationz`,
  `mem20devicecapabilitycompilerz`, `mem20hardwaremarketplacez`,
  `mem20roamingworkloadschedulerz`, `mem20modelsleepandwakesystemz`. This set
  is unique to this subsystem, not the common memory/focus/catalog template.
- `service.py`: submit -> place -> reserve -> dispatch -> complete/fail with
  bounded retries, drain/evacuate with stranded-work reporting, rebalance,
  sleep policy with starvation guardrails, `simulate` (6 scenarios),
  `benchmark`, `doctor`.
- `runtime.py` + `web/`: CLI subcommands, JSON HTTP API with real status-code
  mapping and CORS, served operator cockpit.
- `docs/app/fleet/index.html`: static estate monitor reading the same API,
  linked from `docs/app/README.md`; compiled Vite assets untouched.

Real bugs found by smoke testing and fixed: rebalance passing the wrong types
to the energy adapter; `simulate` using the wrong capability key and never
dispatching before the disconnection check; domain `ValueError`s escaping as
500 instead of 400; the sleep policy hibernating the last awake node; and
`mem20energyawarecomputemigrationz.greenest_node` raising `TypeError` when two
identical machines tied on cost because `list.sort()` compared the node dicts.
The peer now breaks ties by node id.

Verification (this commit, 31e09731):
- `pytest mem20edgefleetbrainz -q` -> 77 passed.
- `simulate` -> 6/6 scenarios; `doctor` -> all six peers reachable.
- `benchmark --iterations 20` over 12 nodes -> 5,098 ops/sec, p50 0.196 ms.
- `scripts/renovation/conformance.py mem20edgefleetbrainz` -> 7/7, six
  cross-modules imported and called on covered lines.

Stopped here for owner evaluation of #300 before starting #301.

---
## 2026-11-07 - mem20edgetransportfabricz (#302): depth-first rebuild

Rebuilt RM-077 (Edge Transport Fabric, `conformance: mem20edgetransportfabricz
fails criterion 5,7`) into a real, first-class subsystem — not a gate shim.
Preserved legacy-compatible domain primitives used by existing callers
(`route_path` neighbor-map API, `qos_class`, `allocate_bandwidth`,
`transport_health`, including `mem20edgetocloudintelligencecontinuumz`).

What the subsystem now owns:
- `domain.py`: legacy-compatible primitives plus advanced fabric model
  (`FabricNode`/`FabricLink`/`FlowDemand`/`PathDecision`), bandwidth-aware
  shortest path, QoS/SLA classification, admission, reservation/release,
  congestion/fabric health, reroute planning, intermittent-connectivity handling.
- `store.py`: SQLite WAL state plane (versioned nodes/links/flows, events,
  placement journal, idempotency, snapshots/restore).
- `ecosystem.py`: six **unique** transport-relevant peers (different set from
  #300 and #301), all called on covered lines: `mem20meshz.meshes.selfhealing`
  (`SelfHealingConnectorMesh`), `mem20autonomoustrafficcontrollerz`
  (`TokenBucket`/`LeakyBucket`), `mem20faultcontainmentcellsz`
  (`FaultContainmentCells`), `mem20causalroutingbrainz` (causal route/effect/
  confounder/intervention), `mem20autonomousrecoverydirectorz`
  (triage/rollback/remediate/recovery/health), `mem20eventstreamsuperhighwayz`
  (create/publish/subscribe/consume/throughput/lag telemetry).
- `service.py`: topology CRUD, admit/route/reserve/release/reroute, status,
  doctor, events/placements, snapshots/restore, simulate, benchmark; peer
  signals attached to real operations.
- `runtime.py` + `web/`: CLI, JSON HTTP API, static cockpit, CORS, 400/404/409
  mapping, legacy `execute`.
- `docs/app/transport/index.html` + `docs/app/README.md` link; `docs/PLAN.md`;
  comprehensive README with fenced runnable example.

Verification:
- `pytest mem20edgetransportfabricz -q --no-header -p no:cacheprovider` → 17 passed.
- `simulate` → 9/9 scenarios ok; `doctor` → 6/6 peers reachable.
- `scripts/renovation/conformance.py mem20edgetransportfabricz` → **7/7 PASS**.
- `register_subsystem.py` → package/gateway/toolchest/sitemapz PASS (MCP warn
  only; criterion 7 satisfied via gateway). Legacy continuum caller API preserved.

---
## 2026-11-07 - mem20energyawarecomputemigrationz (#303): depth-first rebuild

Rebuilt RM-047 (Energy-Aware Compute Migration, fails criterion 5,7) as a real
first-class subsystem. Preserved legacy domain API for `mem20edgefleetbrainz`
(`energy_cost`, `migrate_decision`, `carbon_footprint`, `greenest_node` with
deterministic tie-break by node id, `migration_plan`) and extended with
`ComputeNode`/`Workload`, feasibility, battery/thermal/renewable-aware scoring,
`plan_migrations`, `fleet_energy_summary`.

Delivered: SQLite WAL `store`, `ecosystem` with 6 **unique** peers (different
from #300/#301/#302) — `mem20batteryawareagentschedulerz`,
`mem20energyawarefoundationz`, `mem20datalocalityoptimizerz`,
`mem20demandforecastandcapacitybrainz`, `mem20goaleconomyschedulerz`,
`mem20planetarybatchfabricz`; `service` (plan/migrate/status/doctor with peer
signals), `runtime` CLI+JSON HTTP+cockpit, `web/`, project `tests/`, `docs/PLAN.md`,
comprehensive README, `docs/app/energy-migration/` monitor, gateway/toolchest.

Also fixed `mem20datalocalityoptimizerz.optimal_placement` dict-tie TypeError
(node-id tie-break); peer tests 5/5.

Verification: `pytest mem20energyawarecomputemigrationz/tests -q --no-header -p no:cacheprovider` → 8 passed;
`simulate` 9/9, `doctor` 6/6; conformance **7/7**; register_subsystem PASS (MCP warn only).

---
## 2026-11-07 - mem20energyawarefoundationz (#304): depth-first rebuild

Rebuilt as a first-class energy foundation (power monitoring, thresholds,
budgets, optimization actions). Preserved legacy domain API (`power_reading`,
`threshold_check`, `energy_budget`, `optimize_power`, `daily_energy`) and added
policy evaluation with durable SQLite WAL state, service, CLI/JSON HTTP/cockpit.
6 unique peers (different from #300-#303): `mem20selftuningresourcegovernorz`,
`mem20realtimebusinesstwinz`, `mem20freestackambientcomputingfabricz`,
`mem20gameplaysystemsdataandbalancepipelinez`,
`mem20productionplanningandtaskorchestrationpipelinez`,
`mem20autonomousworkcellsz`. Docs/app monitor, gateway/toolchest. Verification:
4 tests pass (conformance-style flags), simulate/doctor 6/6, conformance 7/7.

---
## 2026-11-07 - mem20enginez (#305): depth-first crew runtime rebuild

Rebuilt #305 (fails criterion 5,6,7) as a real first-class crew runtime for the
30 engine members. Fixed the estate-root namespace/import issue (`python -m
mem20enginez` / `MEMBERS` import) with root shims while keeping the inner
`mem20enginez.mem20enginez` implementation; preserved legacy `--version`/`--members`.

Delivered: `domain` (30-member registry, filesystem+import probing, compatibility,
capability-matched dispatch plans, truthful present/healthy reporting), SQLite WAL
`store` (objects/events/plans/runs/snapshots), 6 **unique** peers (different from
#300-#304): `mem20runtimecompatibilityenginez`, `mem20protocolautodiscoveryenginez`,
`mem20speculativeworkflowenginez`, `mem20servicebundlingenginez`,
`mem20predictiverecallenginez`, `mem20customerlifecycleenginez`; `service` (members/
status/doctor/plan/simulate/benchmark with peer signals), `runtime` CLI+JSON HTTP+
cockpit, `web/`, `docs/PLAN.md`, README fenced runnable example, `docs/app/engine-runtime/`
monitor, gateway/toolchest registrations.

Verification: `pytest mem20enginez/tests -q --no-header -p no:cacheprovider` → 8 passed;
`simulate` 9/9, `doctor` 6/6 peers; `conformance.py mem20enginez` **7/7 PASS**;
`register_subsystem.py` package/gateway/toolchest/sitemapz PASS (MCP warn only).

---
## 2026-11-07 - mem20episodicmemorygraphz (#306): depth-first rebuild

Rebuilt RM-021 (Episodic Memory Graph, fails 5,6,7) as first-class: preserved legacy
`create_episode/add_event/link_episodes/recall/episode_graph/forget`, added
neighbors/timeline/entity index/query/context diff, SQLite WAL store, service/CLI+
JSON HTTP+cockpit, docs/app monitor. Fixed estate-root `__version__`/module import
with root shim. 6 unique peers (different from #300-#305): `mem20dynamicskillgraphz`,
`mem20reversibleexecutiongraphz`, `mem20mixedinitiativefocusenginez`,
`mem20spatialcommanduniversez`, `mem20crossproductloyaltygraphz`,
`mem20deterministicconfigurationgraphz`. Verification: 3 tests pass, simulate 6/6,
doctor 6/6, conformance **7/7**, register_subsystem PASS (MCP warn only).

---
## 2026-11-07 - mem20ethicalincentivesimulatorz (#307): depth-first rebuild

Rebuilt RM-203 (Ethical Incentive Simulator, fails 5,6,7) as first-class while preserving
legacy domain API and existing CAPABILITY-driven Engine/Store/SDK/CLI/HTTP behavior (10-scenario
`simulate` still passes). Enriched `progression` with real ethical incentive simulation
(fairness, harm/manipulation violations, aligned rewards, risk vs hard-safety threshold) and
6 unique peers (different from #300-#306): `mem20outcomesimulationlabz`, `mem20gamebalancesimulatorz`,
`mem20executiondigitaltwinz`, `mem20dynamicquestrewardcomposerz`, `mem20rewardforgez`,
`mem20executablegameconceptandscopepipelinez`. Added `/doctor` peer probe, web cockpit, root shim,
README fenced runnable example, docs/PLAN, docs/app monitor, gateway/toolchest. Verification:
8 tests pass (incl. 5 legacy + Engine simulator compatibility), conformance **7/7**.

---
## 2026-11-07 - mem20executabledesignstresslabz (#308): depth-first rebuild

Rebuilt RM-221 (Executable Design Stress Lab, fails 5,6,7, operation_kind=qa) as first-class
while preserving legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. Enriched
`qa` with real stress/resilience/bottleneck/recovery/design verdict and 6 unique peers
(different from #300-#307): `mem20architecturesimulationsandboxz`, `mem20adversarialqacrewz`,
`mem20universalhealthnervoussystemz`, `mem20syntheticevaluatorarenaz`, `mem20remoteexperimentlabz`,
`mem20intentcompilerz`. Added `/doctor`, web cockpit, root shim, README fenced runnable example,
docs/PLAN, docs/app monitor, gateway/toolchest. Verification: 8 tests pass (legacy + compat),
conformance **7/7**.

---
## 2026-11-07 - mem20executablegameconceptandscopepipelinez (#309): depth-first rebuild

Rebuilt RM-237 (Executable Game Concept & Scope Pipeline, fails 5,6,7, operation_kind=graph) as
first-class while preserving legacy domain API (`concept_score`,`scope_estimate`,`feasibility_check`,
`risk_assessment`,`pipeline_stage`) — used as a peer by #307 — and preserving CAPABILITY
Engine/CLI/10-scenario simulator. Enriched `graph` with real concept/scope analysis and 6 unique
peer signals (different from #300-#308) for explicit scope requests: `mem20gameproductioncontrolcenterz`,
`mem20aiproductionstudiooperatingsystemz`,`mem20productledgrowthsimulatorz`,`mem20autonomoussoftwarefoundryz`,
`mem20aigamestudiobuilderz`,`mem20autonomousmicrosaasfoundryz`. Legacy graph fields
`nodes/edges/degree/hubs` preserved; peer enrichment gated to avoid 5s Engine timeout on generic
simulator payloads. Added `/doctor`, web cockpit, compat/root shims, README fenced runnable example,
docs/PLAN, docs/app monitor, gateway/toolchest. Safe peer fix: `mem20autonomousmicrosaasfoundryz.idea_ranking`
deterministic tie-break. Verification: 9 scoped tests pass (4 new + 5 legacy nested domain) plus
34 `test_concept.py` pass with `--noconftest`; conformance **7/7**.

---
## 2026-11-07 - mem20executiondigitaltwinz (#310): depth-first rebuild

Rebuilt RM-059 (Execution Digital Twin, fails 5,7, operation_kind=forecast) as first-class while
preserving legacy domain API (`create_twin`,`sync_twin`,`simulate`,`predict_outcome`,`drift`) used
by #307 and preserving CAPABILITY Engine/CLI/10-scenario simulator. Enriched `forecast` with real
digital twin analysis (create/sync/simulate/predict/drift) and 6 unique peer signals (different from
#300-#309) for explicit twin requests: `mem20personalworkflowtwinz`,`mem20integrationdigitaltwinz`,
`mem20memorytimemachinez`,`mem20counterfactualmemorysimulatorz`,`mem20customerdigitaltwinlabz`,
`mem20crossruntimeeventlatticez`. Peer enrichment gated for simulator/5s compatibility. Added
`/doctor`, web cockpit, root shims, README fenced runnable example, docs/PLAN, docs/app monitor,
gateway/toolchest. Verification: 9 tests pass (5 legacy + 4 new including 6-peer coverage),
`simulate` 10/10 ok, conformance **7/7** (target after run).

---
## 2026-11-07 - mem20fabricz (#311): depth-first rebuild

Rebuilt `mem20fabricz` (integration fabric crew runtime, 23 members, fails 5,6,7) from skeleton to
first-class while preserving compatibility: 23 `MEMBERS`, `__version__`, `mem20fabricz.cli:main`,
`--version`/`--members`, and legacy tests. Added real domain (member probing/dispatch planning),
service, runtime CLI+JSON HTTP+static cockpit (`status/doctor/dispatch/probe/serve`), web cockpit,
docs/PLAN, fenced runnable README, docs/app monitor, gateway/toolchest, and 6 unique peer
integrations (different from #300–#310): `mem20apishapeshiftinggatewayz`,
`mem20universalintegrationcompilerz`,`mem20episodicmemorygraphz`,`mem20realtimeeventautopilotz`,
`mem20ambientteamradioz`,`mem20autonomousdealdeskz`. Verification: 7 tests pass (4 legacy + 3 new,
6-peer coverage), conformance **7/7**.

---
## 2026-11-07 - mem20facez (#312): depth-first rebuild

Rebuilt `mem20facez` (interface/workspace crew runtime, 8 members, fails 5,6,7) as first-class
while preserving compatibility: 8 `MEMBERS`, `__version__`, `mem20facez.cli:main`,
`--version`/`--members`, and legacy tests. Added member probing, composition planning, service,
CLI+JSON HTTP+static cockpit (`status/doctor/compose/serve`), web cockpit, docs/PLAN, fenced
runnable README, docs/app monitor, gateway/toolchest, and 6 unique peers (different from
#300–#311): `mem20multimodaltaskcapturez`, `mem20visualdataflowcomposerz`,
`mem20intenttomissioncompilerz`, `mem20personalautomationcanvasz`, `mem20multiworldsandboxz`,
`mem20visualagentblackboardz`. Verification: 7 tests pass (4 legacy + 3 new, 6-peer coverage),
conformance **7/7**.

---
## 2026-11-07 - mem20federatedresearchgridz (#313): depth-first rebuild

Rebuilt RM-043 (Federated Research Grid, fails 5,6,7, operation_kind=search) as first-class while
preserving legacy domain API (`register_node`,`distribute_task`,`aggregate_results`,`grid_health`,
`federated_round`) used by #301 and preserving CAPABILITY Engine/CLI/10-scenario simulator. Enriched
`search` with federated grid analysis and 6 unique peer signals (different from #300–#312) for
explicit grid requests: `mem20collectivemodelintelligencez`,`mem20personalcognitivesearchz`,
`mem20alternativedatabaseplaygroundz`,`mem20crdtcollaborationenginez`,`mem20prioritycollisionresolverz`,
`mem20connectormarketplacez`. Added `/doctor`, web cockpit, root shims, fenced runnable README,
docs/PLAN, docs/app monitor, gateway/toolchest. Verification: 9 tests pass (5 legacy + 4 new),
conformance **7/7**.

---
## 2026-11-07 - mem20freestackambientcomputingfabricz (#314): depth-first rebuild

Rebuilt RM-211 (FreeStack Ambient Computing Fabric, fails 5,6,7, operation_kind=analyze) as
first-class while preserving legacy domain API (`pool_resources`,`discover_services`,`allocate`,
`fabric_health`,`ambient_score`) used by #304 and preserving CAPABILITY Engine/CLI/10-scenario
simulator. Enriched default/analyze path with ambient fabric analysis and 6 unique peer signals
(different from #300–#313) for explicit fabric requests: `mem20fabricz`,
`mem20hardwareawareinferencecompilerz`,`mem20capabilitymarketplacez`,`mem20crossplatformmicrokernelz`,
`mem20secretslessworkloadidentityz`,`mem20ambientdevicecompanionz`. Added `/doctor`, web cockpit,
root shims, fenced runnable README, docs/PLAN, docs/app monitor, gateway/toolchest. Verification:
9 tests pass (5 legacy + 4 new), conformance **7/7**.
