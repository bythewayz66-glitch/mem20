# Documentation drift audit — 2026-11-07

**Status:** in progress  
**Tracking issue:** [#392](https://github.com/bythewayz66-glitch/mem20/issues/392)  
**Working branch:** `chatgpt/392-documentation-drift-remediation`  
**Repository:** `bythewayz66-glitch/mem20`

## 1. Verified current baseline

| Source | Current value | Evidence |
|---|---:|---|
| Release version | **3.1.2** | `VERSION` |
| MCP tools | **311** | `verify_mcp.py` default expectation and `docs/surface.json` |
| MCP domains | **39** | `docs/surface.json` `cross_check.ast_domains` |
| Tool/domain manifest | **311 / 39** | `docs/surface.json` |
| Finance model surface input | **311 / 39** | `docs/finance/inputs.json`; `compute_model.py` asserts 311 / 39 |

The root `README.md`, `docs/README.md`, `docs/02-tools-reference.md`,
`docs/05-complete-tools-reference.md`, `docs/surface.json`, and
`docs/INDEX.md` already agree on the 311 / 39 repository surface. These are not
the source of the current drift.

## 2. Search scope and counting caveat

Repository code searches returned the following *candidate-hit counts*:

| Search phrase | Results returned |
|---|---:|
| `270 tools` | 100 (search result cap reached) |
| `257 tools` | 100 (search result cap reached) |
| `26 domains` | 100 (search result cap reached) |
| `272 tools` | 44 |
| `3.1.0` | 50 |
| `v3.0.0` | 36 |

These counts overlap and include source code, tests, scripts, generated files,
release snapshots, daily reports, and historical evidence. They are **not** a
claim that every hit is stale or that there are exactly this many affected
documents. Every path needs a disposition before it is edited.

## 3. Confirmed dispositions

### Current-facing documentation that is already aligned

- `README.md`: 3.1.2 and 311 / 39.
- `docs/README.md`: 3.1.2 and 311 / 39.
- `docs/02-tools-reference.md`: 311 / 39.
- `docs/05-complete-tools-reference.md`: 311 / 39.
- `docs/INDEX.md`: finance surface statement says 311 / 39.
- `docs/surface.json`: generated 311 / 39 manifest.
- `verify_mcp.py`: expected live count defaults to 311.

### Confirmed stale current-facing documentation — defer README edits until the active run ends

| Path | Finding | Disposition |
|---|---|---|
| `docs/finance/README.md` | Still describes 270 / 27 as the live surface, while its own `inputs.json` and `compute_model.py` now assert 311 / 39. | Update after the owner-authorized README drift window closes. |
| `docs/gtm/README.md` | Still calls 270 / 27 current and says `docs/02-tools-reference.md` is stale at 268 / 26, although that reference now says 311 / 39. | Refresh current status after the README drift window closes; retain dated drift history as history. |
| `roadmaps/README.md` | Last updated 2026-09-06; contains old `/opt` paths and a 268-tool statement. | Defer because it is a README and because the roadmap registry must be reconciled against current roadmap sources first. |

### Non-README SDK documentation corrected in this pass

- `mem20-sdk-ruby/docs/INSTALL.md`
- `mem20-sdk-ruby/docs/USAGE.md`

The Ruby client obtains `client.tool_names` from the server's live `tools/list`
response, so the current main server returns 311 names. However,
`mem20-sdk-ruby/lib/mem20/surface.rb` and its spec still pin the SDK-local
`Mem20::Surface` constants to 272 tools / 27 domains (270 domain tools plus
two infrastructure tools). The guides now distinguish the live server count
from that stale SDK-local baseline rather than presenting both as the same
measurement. The Ruby SDK's surface constants/spec and `rake surface:check`
need a separate code-and-test refresh; a documentation-only change cannot make
that check current.

### Living status documentation needing evidence before editing

- `docs/handoff/STATE.md` says it was last updated 2026-10-30 and shows no
  in-progress work. The owner has reported three active agents, but this pass
  has not yet validated the exact issue/branch/claim mapping for those agents.
  Do not invent names or overwrite an active claim. Reconcile it against live
  claims, issues, branches, and open handoffs before updating the board.

### Historical evidence — preserve, do not rewrite

Examples include:

- `docs/ops/owner-directive-2026-11-01.md`
- `docs/ops/branch-disposition-2026-10-31.md`
- `docs/ops/branch-inventory-2026-10-31.md`
- `docs/ops/tool-count-270-27.md` and its associated patch/apply record
- `docs/gtm/claim-ledger.md` and its dated v7 supporting ledgers, pinned to
  their 2026-11-01 baseline
- `docs/app/deck/PERMANENT_URL.md` and dated deck evidence
- `published/daily-reports/*`, `published/history/*`, and captured verification
  logs

Those documents may contain old numbers accurately describing the commit or run
they measured. If a current decision needs newer evidence, add a new dated
record and point to it; do not rewrite the old measurement.

### Requires further validation — do not bulk-replace

- C++ SDK documents describe SDK release baselines and have their own pinned
  source ledger. Refresh only after comparing their constants, tests, and
  release target to the current server.
- Perl SDK constants/tests still pin an older surface. Treat this as an SDK
  implementation-and-test alignment task, not a prose-only number replacement.
- `docs/benchmarks/README.md` says v2 is the measured scale corpus. The root
  README notes that a v3 corpus exists, but existence alone does not prove that
  v3 has replaced the measured v2 results. Keep the measured/unmeasured
  distinction until benchmark artifacts establish otherwise.
- `docs/renovation/4.0/*` and current agent work products require claim/branch
  checks before any edits.

## 4. Rules for the remaining sweep

1. **Do not edit subsystem `README.md` files until the owner-authorized run is
   complete.** The current run is allowed to produce temporary README drift.
2. Read the implementation, tests, generated manifests, and current issue
   evidence before changing a claim.
3. Distinguish live repository facts from release-specific SDK baselines and
   historical snapshots.
4. Regenerate generated documentation from its generator; do not hand-edit
   generated regions.
5. Preserve append-only logs and dated audit records.
6. Check `docs/handoff/claims/` and current branches before every file edit.
7. Keep planned, implemented, tested, evidenced, deferred, and retired states
   distinct. Never turn a planned capability into a shipped claim.

## 5. Next work

1. Finish the non-README documentation inventory and safe corrections.
2. Reconcile the living handoff board only after validating current agent claims
   and branch ownership.
3. Refresh current-facing finance/GTM/roadmap README files when the active run
   closes.
4. Process subsystem README drift in small claimed batches, using the actual
   subsystem source and tests as the authority.
5. Run the repository's documentation, surface, and subsystem conformance
   checks; attach their outputs to the PR.
