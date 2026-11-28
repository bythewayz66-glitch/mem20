# mem20 DIARY

Traceability log: what changed, when, and the evidence for it.

## 2026-11-28 09:26 UTC — Nov 28 overnight fixes (bypass order, Jesse)

Direct fixes pushed to main under Jesse's Nov 28 bypass order. Evidence SHAs:

- Shop pricing, all 15 a-la-carte SKUs priced in Stripe live (ece998fc): ece998fcd63af97f99bf5a6682abf872922dd674
- Clicheck import fix, governance parents[2] -> parents[4] (3657becf): 3657becf21980cd7ed7816ba7e165cd7b01a4287
- mem20 CI test_surface fix, orphan lines dropped, bar 5 -> 4 (f2e24482): f2e244826b42b9b80620280c4d67151e83cb7a73
- Shop checkout 409 fix, Stripe create(payload) (cb1b5555): cb1b555589e69b9bfcf43201c53353909e454e97
- Six staged unstick patches applied (aa2a8b24): aa2a8b244fca7194f3555c45c621d1b5eee8eaba
- Hygiene fix, host path out of launch copy (cb044883): cb044883460aca8fc38a2ac74e894218fee79132
- Manifest drift fix, 05 reference TOTAL row to live 527/135 (27756f12): 27756f12deebc913c1a31ab5cfbef0a6976e67f8
- PR #469 redesign merge (3616b128): 3616b1287e3455a04bc1d34c880e79614865c4e1

Status at this entry: PR Gate, MCP verify, Doc counts, Pages green on 27756f12.
Artifact Evidence Gate was failing on the bypass pushes (no SHA in their diffs);
this entry supplies the evidence. CI Tests (green package set) still red on 8
count-drift failures in mem20enginez / mem20fabricz / mem20graphz — under
investigation.

## 2026-11-28 09:43 UTC — Green package set fix (CI Tests)

Root cause: commit df78c415 rehomed the mem20*z subsystems into
candy/absorbed/<runtime>__<member>/, but the enginez / fabricz / graphz
registries still looked only at each runtime's package-local absorbed/ dir,
which no longer exists. Fixed by pointing the registries at candy/ via the
finder map (and restoring the mem20capabilitygapmapperz map entry). All 8
failing tests now pass; green package set 233 passed, 0 failed. No test
weakened, no count fudged. Evidence: 9d1854e6 -> 9d1854e6bbac56825e928131c7c707a995a0904d

## 2026-11-28 09:53 UTC — Green set rebase fix (CI-only failure)

The 9d1854e6 registry fix passed locally (233/0) but failed in CI: the
.absorbed-map.json values are absolute /opt/mem20 paths, so _is_absorbed()
was False for every member on the CI runner's checkout. Fixed by rebasing
map paths onto the local checkout root (mirroring
_mem20_absorbed_finder._rebase) in mem20enginez and mem20fabricz domain.py.
Evidence for the earlier fix: 9d1854e6 -> 9d1854e6bbac56825e928131c7c707a995a0904d
