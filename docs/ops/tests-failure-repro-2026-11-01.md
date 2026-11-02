# `Tests` check — local reproduction & defect list (2026-11-01)

**Owner:** mem20-sybsystems — independent second opinion (directive §3 roster item 6, gap G1)
**Subject:** RED `Tests` check-run `124860549243` on `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf`
**Workflow:** `.github/workflows/ci.yml`, job `tests` (`name: Tests`, declared at `ci.yml:238`)
**Directive of record:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`

---

## 1. Headline — there is no failing assertion

**The suite passes. There is no failing test, and nothing to fix in the tests.**

The RED check is a **pytest usage error (exit code 4)**, not a test failure (exit code 1). `pytest`
was handed a path that does not exist, so it aborted **before collecting or running a single test**.

| rc | meaning |
|---|---|
| `0` | all collected tests passed |
| `1` | tests were collected and **some failed** ← a real red suite |
| `2` | execution interrupted |
| `3` | internal error |
| `4` | **usage error — bad argument / nonexistent path** ← **what main hits** |
| `5` | no tests were collected |

The distinction matters: a `1` means the product is broken; a `4` means the **CI invocation** is
broken. `2ea44922` is the latter.

### The failing identifier

```
ERROR: file or directory not found: mem20adaptiveinterfacecomposerz/tests
```

`mem20adaptiveinterfacecomposerz` **does not exist in the tree at `2ea44922`** — and never existed
under that name. It is not renamed, not gitignored, not a submodule:
`git log --all -- mem20adaptiveinterfacecomposerz` shows no commit that ever created it.

---

## 2. Exact command and exact exit code

Run at `HEAD == 2ea4492209dfaae6afb22ca884132a0d1849bfcf`, Python `3.11.15`, pytest `9.2.0`, in a
clean venv installed with exactly the job's *Install test deps* set (`pytest`, `mcp>=1.0`,
`cryptography`, `httpx`, `aiohttp`, `PyYAML`, `pydantic>=2`, `numpy`).

Roots are the **verbatim 22-package `GREEN` list from `ci.yml:266-281`**, expanded to
`<pkg>/tests` exactly as the workflow's own loop does:

```console
$ git rev-parse HEAD
2ea4492209dfaae6afb22ca884132a0d1849bfcf

$ python3 -m pytest -q -m "not integration" \
    mem20adaptiveinterfacecomposerz/tests mem20assistz/tests mem20autoz/tests \
    mem20biz/tests mem20boxz/tests mem20enginez/tests \
    mem20executablegameconceptandscopepipelinez/tests mem20fabricz/tests \
    mem20facez/tests mem20graphz/tests mem20greenz/tests mem20labz/tests \
    mem20orcaz/tests mem20pipelinez/tests mem20selfz/tests mem20sensorz/tests \
    mem20simz/tests mem20sitemapz/tests mem20studioz/tests mem20teamz/tests \
    mem20twinz/tests mem20zimr/tests

no tests ran in 0.00s
ERROR: file or directory not found: mem20adaptiveinterfacecomposerz/tests

EXIT_CODE=4
```

**Exit code: `4`** — reproduces CI's `Process completed with exit code 4` exactly. Two diagnostic
tells: `no tests ran` (nothing asserted, so nothing failed) and `ERROR: file or directory not found`
(the abort is path resolution, upstream of collection).

---

## 3. Proof the real suite is green

Remove the one phantom root; the identical selection runs clean:

```console
$ python3 -m pytest -q -m "not integration" \
    mem20assistz/tests mem20autoz/tests mem20biz/tests mem20boxz/tests \
    mem20enginez/tests mem20executablegameconceptandscopepipelinez/tests \
    mem20fabricz/tests mem20facez/tests mem20graphz/tests mem20greenz/tests \
    mem20labz/tests mem20orcaz/tests mem20pipelinez/tests mem20selfz/tests \
    mem20sensorz/tests mem20simz/tests mem20sitemapz/tests mem20studioz/tests \
    mem20teamz/tests mem20twinz/tests mem20zimr/tests

231 passed, 1 skipped in 5.94s

PYTEST_RC=0
```

**231 passed, 1 skipped, 0 failed — exit code 0.** Each of the 21 real packages is green
individually too, so no package hides a failure behind the aggregate:

| Package | rc | Result |
|---|---|---|
| `mem20assistz` / `mem20autoz` / `mem20biz` / `mem20boxz` | 0 | 4 passed each |
| `mem20enginez` / `mem20fabricz` / `mem20facez` / `mem20graphz` | 0 | 4 passed each |
| `mem20executablegameconceptandscopepipelinez` | 0 | 34 passed |
| `mem20greenz` / `mem20teamz` | 0 | 11 passed each |
| `mem20labz` / `mem20pipelinez` / `mem20selfz` / `mem20simz` | 0 | 4 passed each |
| `mem20orcaz` | 0 | 39 passed, 1 skipped |
| `mem20sensorz` | 0 | 22 passed |
| `mem20sitemapz` | 0 | 43 passed |
| `mem20studioz` / `mem20twinz` | 0 | 4 passed each |
| `mem20zimr` | 0 | 15 passed |
| `mem20adaptiveinterfacecomposerz` | **4** | **ERROR: file or directory not found** |

The single skip is a pre-existing intentional `pytest.mark.skip` in `mem20orcaz`, not a regression.

The job's other steps pass locally too:

```console
$ python3 -m pytest -q -m unit mcp/tests        # step 5, `|| true` in CI
3 passed, 38 deselected in 0.08s

$ prove -Isdk/perl/lib sdk/perl/t/*.t           # step 8, Verify the Perl SDK
All tests successful.
Files=6, Tests=103,  7 wallclock secs
Result: PASS
```

---

## 4. Divergence from the directive — the recorded attribution is wrong

The directive (§2, gap **G1**) records the failure as *the **Compute diff against the base** step*.
**That attribution is incorrect.** Two independent checks:

**(a) Step-level conclusions from the Actions jobs API** —
`GET /repos/bythewayz66-glitch/mem20/actions/runs/41310800014/jobs`, job `124860549243`:

```
 1. Set up job                                -> success
 2. Run actions/checkout@v4                   -> success
 3. Run actions/setup-python@v5               -> success
 4. Install test deps                         -> success
 5. Unit-marked MCP tests (issue #5)          -> success
 6. Run the green package set                 -> failure     <-- the real failure
 7. Run unit-marked tests (no optional deps)  -> skipped
 8. Verify the Perl SDK                       -> skipped
 9. Post Run actions/setup-python@v5          -> skipped
10. Post Run actions/checkout@v4              -> success
11. Complete job                              -> success
```

Steps 6–8 belong to the **`tests`** job, not the `syntax` job that owns *Compute diff against the
base* — and that job's check-run concluded **`success`**.

**(b) The *Compute diff* step replayed locally** — clean, exit 0:

```console
$ BEFORE=$(git rev-parse 2ea44922^)          # a36a34a5dc560e3ce12a2e28c04fcc98771f4148
$ git diff --name-only --diff-filter=ACMR "${BEFORE}...HEAD" > changed.txt
$ git diff --name-only --diff-filter=ACMR "${BEFORE}...HEAD" | grep -E '[.]py$' > changed_py.txt
$ git diff --unified=0 --diff-filter=ACMR "${BEFORE}...HEAD" > added.diff
changed: 1 file(s), python: 0
COMPUTE_DIFF_RC=0
```

**Why the annotation looked like line 32.** The check-run carries 3 annotations; only one fails:

| # | path | line | level | message |
|---|---|---|---|---|
| 1 | `.github` | 2 | warning | Node.js 20 deprecated for `checkout@v4`, `setup-python@v5` |
| 2 | `.github` | **32** | **failure** | **`Process completed with exit code 4.`** |
| 3 | `.github` | 1 | notice | `ubuntu-latest` label migrating to Ubuntu 26 from 2026-10-19 |

Annotation #2's `path`/`line` anchor the **job's YAML block**, not a shell line number — line 32 is
where the `tests` job body begins, not `syntax`'s branch logic. The step-level API data in §4a is the
authoritative disambiguator.

So the directive's *"fix the step, not the test"* instinct was right; **the step it named was wrong**
— which is why a fix aimed at the diff step would not have cleared the check.

---

## 5. Root cause chain

1. `mem20adaptiveinterfacecomposerz` was one of the original "adaptive" module suites.
2. Commit **`e9a15295013da1003998e554ee5cc469f5f9f6e5`** — *"feat: mem20adaptz self-contained gold
   runtime; remove original adaptive mods"* (jayson, Thu Oct 29 22:57:45 2026 -0600) — **deleted**
   those modules and consolidated them into `mem20adaptz`.
3. That commit **did not touch `.github/workflows/ci.yml`** (`git show --name-only e9a15295 | grep
   workflows` → empty). The hard-coded `GREEN` list kept pointing at the deleted directory.
4. The stale name became fatal once `GREEN` was made a hard gate: `ci.yml:264-282` runs `set -euo
   pipefail` with a bare `pytest` (no `|| true`) and asserts `COUNT -ne 22 → exit 1`. The list is
   simultaneously a **path list** and a **cardinality contract**, and neither was updated on rename.
5. The sibling step `ci.yml:284-304` carries the **same** phantom entry (line 286) but survived only
   because it was **skipped** — step 6 failed first. It will fail identically the moment step 6 is
   fixed, so **both occurrences must be fixed together**.

Confirmed — the phantom name appears **twice** on `main`:

```console
$ git show origin/main:.github/workflows/ci.yml | grep -n 'mem20adaptiveinterfacecomposerz'
266:          GREEN="mem20adaptiveinterfacecomposerz mem20assistz mem20autoz mem20biz
286:          GREEN="mem20adaptiveinterfacecomposerz mem20assistz mem20autoz mem20biz
```

---

## 6. Defect list

Severity: **S1** blocks all merges · **S2** blocks the affected check · **S3** latent/debt.

### D1 — `GREEN` references a directory deleted in `e9a15295` · **S1 · CONFIRMED**

- **Where:** `.github/workflows/ci.yml:266` (*Run the green package set*)
- **Symptom:** `ERROR: file or directory not found: mem20adaptiveinterfacecomposerz/tests`; pytest
  exit `4`; job fails; **0 tests execute**.
- **Impact:** `Tests` is a required check, so **all 15 branches are blocked from merging**. This is
  the mechanism behind gap G1.
- **Cause:** directory removed in `e9a15295`; `ci.yml` not updated in that commit.
- **Repro:**
  ```console
  $ git checkout 2ea4492209dfaae6afb22ca884132a0d1849bfcf
  $ python3 -m pytest -q -m "not integration" mem20adaptiveinterfacecomposerz/tests
  ERROR: file or directory not found: mem20adaptiveinterfacecomposerz/tests
  $ echo $?
  4
  ```

### D2 — the same phantom entry in the *second* green list · **S2 · CONFIRMED, LATENT**

- **Where:** `.github/workflows/ci.yml:286` (*Run unit-marked tests (no optional deps)*)
- **Symptom:** identical usage error, rc `4`. Hidden today only because step 6 fails first and the
  runner marks this step `skipped`.
- **Repro (already red right now):**
  ```console
  $ python3 -m pytest -m unit -q <all 22 verbatim roots>
  ERROR: file or directory not found: mem20adaptiveinterfacecomposerz/tests
  TRUE_RC=4
  ```
- **Impact:** fixing D1 alone yields a **second** red `Tests` run.
- **Good news:** once the path is removed this step correctly returns **rc 5** (`232 deselected`),
  which the existing `rc -eq 5 → exit 0` normalisation at `ci.yml:299-303` absorbs. That guard works
  and needs no change — verified:
  ```console
  $ python3 -m pytest -m unit -q <all 21 real roots>
  232 deselected in 0.15s
  FIXED_RC=5          # normalised to success by ci.yml:299-303
  ```

### D3 — the correct replacement package is not tested by CI at all · **S2 · CONFIRMED**

- **Where:** `.github/workflows/ci.yml` — `mem20adaptz` appears **0** times.
- **Symptom:** `mem20adaptz` is the designated successor to the deleted adaptive modules
  (`ABSORBED.md`, `DELETE_ORIGINALS.sh` present) and carries a real suite CI never runs:
  ```console
  $ python3 -m pytest -q -m "not integration" mem20adaptz/tests
  13 passed in 0.03s
  RC=0
  ```
- **Impact:** 13 tests of the *replacement* code are unguarded. Simply deleting the phantom name
  restores a green check while **reducing coverage below what the original list intended**.
- **Related, out of scope:** **28 packages** with a `tests/` directory appear in no `ci.yml` list
  (`mem20adaptz`, `mem20corez`, `mem20benchmarkz`, `mem20botz`, `mem20cliz`, `mem20crewz`,
  `mem20dreamz`, `mem20gamez`, `mem20ircz`, `mem20kanbanz`, `mem20kilnz`, `mem20liez`, `mem20meshz`,
  `mem20mktz`, `mem20ocaskz`, `mem20secretz`, `mem20shopz`, `mem20temporaldatabasefabricz`,
  `mem20ucgz`, `mem20wasmz`, `mem20webgpuz`, `mem20cviz`, `mem20autouez`, `mem20verify`, `mem20ops`,
  `mem20messenger`, `mem20_mcp`, `mem20AIonbordz`). The green set is not full coverage.

### D4 — the `COUNT -ne 22` contract has no existence check · **S3 · CONFIRMED**

- **Where:** `.github/workflows/ci.yml:275-279`
- The guard counts *names in a string*, not *directories that exist*, so a 22-entry list of
  twenty-two nonexistent paths passes it. It cannot detect this class of defect. Advisory hardening:
  ```bash
  for pkg in $GREEN; do
    [ -d "$pkg/tests" ] || { echo "::error::green-set entry '$pkg' has no tests/ dir"; exit 1; }
  done
  ```

### D5 — the directive's recorded attribution is wrong · **S3 · CONFIRMED (documentation)**

- `docs/ops/owner-directive-2026-11-01.md` §2/G1 blames *Compute diff against the base*, which
  concludes `success` in CI and on replay (§4). Correct attribution: *Run the green package set*.

---

## 7. Recommended fix (for GitHub Repo Assistant — not applied by me)

`.github/workflows/ci.yml`, **both** occurrences (`:266` and `:286`), one commit:

```diff
-          GREEN="mem20adaptiveinterfacecomposerz mem20assistz mem20autoz mem20biz
+          GREEN="mem20adaptz mem20assistz mem20autoz mem20biz
```

Keep `COUNT -ne 22` intact — `mem20adaptz` replaces the removed entry **one-for-one**, so the
cardinality contract holds at 22 and the 13 `mem20adaptz` tests join the guarded set (D3).
**Substitute, do not delete:** deleting drops the count to 21 and trips the cardinality guard at
`ci.yml:275-279`, failing the job on the next line.

**Do not change any test.** There is no failing test to change (§1, §3).

**Predicted result after the fix:** step 6 → `244 passed, 1 skipped`, rc `0`; step 7 → `244
deselected`, rc `5` → normalised to success; step 8 Perl → `PASS`. `Tests` → `success`.

---

## 8. Verification status, stated plainly

| Claim | Evidence | Verified? |
|---|---|---|
| Suite passes locally at `2ea44922` | 231 passed, 1 skipped, rc 0 across all 21 real packages (§3) | **yes** |
| No failing assertion exists | `no tests ran` — zero tests collected before the abort (§2) | **yes** |
| Local failure matches CI exactly | local rc `4` ≡ CI `Process completed with exit code 4` (§2) | **yes** |
| Real failing step is *Run the green package set* | step-level conclusions from the Actions jobs API (§4a) | **yes** |
| Directive's *Compute diff* attribution is wrong | that step → `success` in API; local replay rc `0` (§4b) | **yes** |
| Phantom path came from the deletion in `e9a15295` | `git log --all`, `git show --name-only` (§5) | **yes** |
| The bug is duplicated at `ci.yml:286` | `grep -n` on `origin/main` (§5) | **yes** |
| `mem20adaptz` is green and missing from CI | 13 passed, rc 0; `grep -c` → 0 (§6 D3) | **yes** |
| Fix clears the check | **NOT verified** — needs a workflow push; fix not applied (§7) | **no — predicted** |

**Scope caveat.** This reproduces the workflow's **shell steps** on a clean Python 3.11 venv with
the job's exact dependency list. It does not replay the Actions runner itself, so runner-specific
differences (the Node 20 deprecation warning, the Ubuntu 26 label notice) are outside what is
proven. Neither bears on the `exit code 4` mechanism, which is deterministic path resolution.

**No CI job log was read directly** — the logs endpoint requires admin on the repository
(`403 "Must have admin rights to Repository."`). Step-level conclusions were therefore taken from
the public Actions jobs API, which reports per-step `conclusion` and matches the local
reproduction exactly.

---

## 9. Traceability

- Commit under test: `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (`main` HEAD, pushed 2026-11-01T13:21:47Z)
- Failed check-run: `124860549243` (`Tests`, `conclusion: failure`)
- Workflow run: `41310800014` · job: `124860549243`
- Failing step: **6 — "Run the green package set"**
- Local exit code: **4** · Python `3.11.15` · pytest `9.2.0`
- Introducing commit: `e9a15295013da1003998e554ee5cc469f5f9f6e5`
- Directive of record: `06fa1220e964f84aabac78127fc18463dfa6798d`
