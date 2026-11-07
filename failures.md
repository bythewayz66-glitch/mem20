# failures.md — what did not work (mem20 estate)

- 2026-09-20: `mem20_imagination_dream` refused with "No LLM API key configured". Root cause: mem20 `llm.py` `_ENV_CANDIDATES` only read legacy `.env` paths (`/opt/mem20/Desktop/jayson-openwebui/.env`, `/opt/mem20/mem20/.env`), both empty/missing. Real keys live at `/opt/mem20/secrets/.env` (per 2026-09-07 key rule) — file was never read. NEXT ACTION: done — added `/opt/mem20/secrets/.env` as first candidate. Verified working via bridge. The running MCP bridge needed an opencode restart to pick up the module change.
- Legacy `.env` candidates now empty — confirmed 2026-09-20 by direct grep (NVIDIA/GROQ keys EMPTY/missing in both legacy files).- 2026-09-20: `mem20_a2a_*` MCP tools failed with `No such file or directory: '/root/.hermes/config.yaml'` — the MCP A2A tool reads `~/.hermes/config.yaml` (absent). NEXT ACTION: bypassed for the mem20 bus (mem20crewz `A2AClient` + `peers.yaml` are the live fleet path); flag MCP tool config gap separately from this build.
- 2026-09-20: mem20ucgz text query returned empty for "who provides episodic memory graph?" — cause: single-substring exact match + case-sensitive `re.sub` in register script (`rm/rm/` prefix) + `?` in token. NEXT ACTION: done — token-based query w/ stopwords+punctuation strip; register script flags=IGNORECASE; verified resolves.
- 2026-09-20: demo.sh initial run failed "fs-cv: command not found" — cause: venv bin not on PATH. NEXT ACTION: done — demo auto-falls back to `fs-cv`; CLI braid receipt moved to stderr so stdout stays pure JSON.
- 2026-09-23: `fs-sense /twin` and `/exec` failed on the 8784 server. Cause A: `braid_hook` inserted `/opt/mem20` on sys.path[0] to import braid_bridge and never removed it, so `from mem20langz import InMemorySaver` resolved to the namespace directory `/opt/mem20/mem20langz` (no `__init__.py`) instead of the venv editable install → "cannot import name 'InMemorySaver' from 'mem20langz' (unknown location)". Cause B: `SenseService.__init__` set `self.twin = WorkflowTwin()` which shadowed the `twin()` method → "'WorkflowTwin' object is not callable". NEXT ACTION: done — braid_hook now removes the repo-root sys.path entry in a `finally`; instance attribute renamed to `self.workflow_twin`; tests 8/8 + live HTTP re-verified.
- 2026-09-23: initial A2A fleet queries with natural wording ("who provides capability gap mapping", "phase replanning") returned no match — cause: UCG matching is exact-token; "mapping"/"replanning" tokens not in the registered haystack. NOT a defect (matches documented exact-token semantics). NEXT ACTION: verified intended behavior with token-aligned wording ("capability gap mapper" → cap.sense-gap.v1).
- 2026-09-23: `fs-sense accelerate/enroll` descriptors 400'd from UCG on registration ("capability signature verification failed") — cause: descriptors claimed `signed: True` but the estate's UCG runs with no `FREESTACK_UCG_SIGNING_KEY` configured (every registered cap is unsigned), so signing verification correctly failed. NEXT ACTION: done — requested honesty: caps are signed:False at the UCG manifest level (matching all 24 caps in the graph); the per-device/per-human attestation inside the capability itself is real Ed25519 and is what the trust bridge enforces. Re-registered, braid-journaled, proven.

- 2026-09-23: mem20mktz journal() did NOT return a braid cid. Root cause (proven):
   BRAID_AVAILABLE was True but `import braid_python` under the mktz venv resolved
   to the repo-root SOURCE DIR `/opt/mem20/braid_python/` (Rust Cargo tree, no
   __init__.py) as an empty namespace module → no PyBraidEngine → get_engine
   AttributeError. The estate organs (sensez/ucgz) never hit this because their
   venvs have the COMPILED braid_python abi3 wheel installed (a regular package,
   which wins over the namespace portion on sys.path).
   RESOLVED 2026-09-23: pip-installed the estate's own wheel
   `braid_python-0.1.0-cp311-abi3-manylinux_2_34_x86_64.whl`
   (from /opt/mem20/braid_python/target/wheels/) into
   /opt/mem20/mem20mktz/.venv — mirror verbatim, no workaround.
   Verified: journal('offer.published', 'test-offer-journal-verify', {...}) →
   BRAID_AVAILABLE True, cid br25166abf9a68c78abb8545dacb65dbcedbcb1f69ec0b02be4c1e4a4f48fec32c,
   proving via estate bridge = True, depth 449, precommit_verified True.
   NO further action.

- 2026-11-04: Session completed successfully following all mem20 AGENTS.md rules. No failures encountered.
- 2026-11-04: Godot headless test failed with `add_child()` during
  `_ready()` — the client tried to parent its `HTTPRequest` helper inside a
  node that was still entering the tree, so `health()`/`ready()` could never
  complete. NEXT ACTION: done — the helper is created unparented and
  `_http_get` waits for the scene tree root to be ready before parenting and
  issuing the request; all 11 headless checks pass.
- 2026-11-04: `surface_manifest.py --check` failed under system `python3`
  (`tools/list returned no response`) because the server's dependencies live in
  `.venv`, not the system interpreter. NEXT ACTION: done — added
  `_server_python()` to prefer `.venv/bin/python` for the server subprocess, so
  both interpreters now verify 311/39.
- 2026-11-04: launch-gate check flagged the served page because `VERSION`
  (3.1.2) was itself listed in `RETIRED_VERSIONS`. NEXT ACTION: done —
  `retired_versions_for(current)` filters the live version; regression test
  added.
- 2026-11-06: Conformance criterion 6 still failed after adding genuine
  cross-module calls because the calls sat inside a multi-line dict literal and
  coverage only marked the assignment line. NEXT ACTION: done — every mem20
  call in `estate_context()` is now its own statement; the gate logs list each
  call site and report 7/7.
- 2026-11-06: Crew-runtime subsystems (`mem20twinz`, `mem20studioz`) had no
  package-level `domain.py` and no package-level `tests/` directory, so the
  generated-package fixer could not apply. NEXT ACTION: done — added a real
  `domain.py`, put the integration test in the existing `tests/` directory, and
  registered the real `--members` CLI entry.
- 2026-11-06: Shared working tree race — staging only my files was not enough
  because another agent had already staged its `mem20assistz` files, so
  `git commit` swept them into 87f4d4e5. NEXT ACTION: done — use
  `git commit --only <paths>` for every commit in a shared tree. The swept files
  were byte-identical to the other agent's staged work, so no content was lost
  or reverted.

- 2026-11-07: Building #300 (`mem20edgefleetbrainz`) exposed a real defect in
  `mem20energyawarecomputemigrationz.greenest_node`: it built `(cost, node)`
  tuples and called `sort()`, so two identical machines with equal cost tried to
  compare the node dicts and raised `TypeError: '<' not supported between
  instances of 'dict' and 'dict'`. The fleet's rebalance path surfaced it as
  `{"ok": false, "error": "..."}` instead of a green plan. NEXT ACTION: done —
  `scored.sort(key=lambda item: (item[0], str(item[1].get("id", ""))))` breaks
  ties deterministically by node id; the peer's own suite still passes (5/5)
  and the fleet ecosystem/service suites now exercise the equal-cost case.

- 2026-11-07: Building #302 (`mem20edgetransportfabricz`) exposed two integration issues.
  (1) `mem20edgetransportfabricz.__init__` lazy `__getattr__` used
  `from . import ecosystem`, which recursed under root-conftest/pytest collection
  in this estate; fixed by `importlib.import_module(".ecosystem", __name__)`.
  (2) The `mem20meshz` peer import path resolves as
  `mem20meshz.mem20meshz.meshes.selfhealing.domain` in this layout; the ecosystem
  adapter now tries the nested path and falls back. Domain routing was also made
  bandwidth-aware so admission finds feasible paths when the shortest-latency path
  cannot carry required demand. Legacy `route_path`/`qos_class`/
  `allocate_bandwidth`/`transport_health` behavior preserved for existing callers
  (e.g. `mem20edgetocloudintelligencecontinuumz`).
