# mem20 — SDK docs pages publish leg (via gabe)

**Leg:** publish the mem20 SDK docs pages to the Sidney live surface, through **gabe**
(the sole publish authority).
**Producer:** `webpage-developer` · **Agent session:** see `publish-records.json` (`judged_sig`)
**Date:** 2026-10-14 · **Host:** `root@216.198.115.91:2222` (sidney, Kali) · live root `/opt/mem20/live`
**Canonical repo:** `github.com/bythewayz66-glitch/mem20` · branch `main` · MIT · `v2.1.0rc2` · 268 tools · protocol `2025-06-18`

## Outcome — BOTH PAGES PUBLISHED (verdict `pass`)

| Page | gabe seq | Live path | sha256 (manifest == disk == staged) |
|---|---|---|---|
| Perl SDK docs page | **104** | `/opt/mem20/live/mem20-perl-sdk-docs.html` | `f525acb697f4441bb4c0d931991889bf987f6640ba89f5220d3d73da4c4bfd34` |
| C++ SDK docs page | **143** | `/opt/mem20/live/mem20-cpp-sdk-docs.html` | `3dcfa11af351604e0e412ee4fb28ffe6f68dab0cdafcc36051cb5b61a731712a` |

Gate: `L1` deterministic floor clean (no isolated-prefix refs, no cheat-shape findings);
`L2` adversarial judge = real external LLM call (NVIDIA NIM, `nvidia/nemotron-3-*`);
`L3` separation of duties satisfied (judge id ≠ producer; distinct session).
Both entries carry a judge approval **signed by Gabe's Ed25519 key**.

Chain after publish: `chain ok (161 entries)`, `halted: false`, `published_artifacts: 28`.

## Gate findings worth recording

The Perl page had been **refused 13 times** by its own producer, for a real reason:
`B2` — the gate scans **every file in the artifact's source directory**, and the staged
directory carried a `README.md` whose install snippet used an isolated-prefix path
(`.venv/bin/pip`). Publishing the page from a clean directory cleared the hit while the
docs bundle itself stays untouched.

The C++ page was refused twice before passing, both times by the L2 judge on
unverifiable figures — exactly the "right shape, nothing behind it" class the gate exists
to catch:
- first: the commit chip `c274404` was asserted but not shown as verified → annotated as
  the current `main` HEAD, confirmed on the canonical clone with `git rev-parse HEAD`;
- second: a stat card claimed **12** stale refs "fixed" with no way to derive it → replaced
  with **7 files**, the figure the page's own §3 table actually enumerates (and the doc-file
  card likewise grounded on the §2 table).

Both refusals are preserved in the append-only manifest (seq 90 and 137), so the
corrections are auditable rather than silent.

## Stale-reference check on the published pages

- Perl page: `JaysonAIOnline` occurrences = **0** (canonical refs = 9).
- C++ page: 4 occurrences, **all inside the labelled `Was` column of the §3 migration
  table** (the required before/after row). `href` links to the stale org = **0**;
  clone-style `/JaysonAIOnline/mem20` = **0**. Canonical refs = 10.

Guardrails held on the C++ page: adversarial `0.000` benchmark row visible, C++ build/install
instructions present, promotion described as evidence-based with an append-only audit trail,
no LoCoMo/LongMemEval claim, no ledger-mutating API.

## Evidence files

- `publish-records.json` — the two signed manifest entries (seq 104, 143), verbatim.
- `mem20-perl-sdk-docs.html`, `mem20-cpp-sdk-docs.html` — byte-identical copies of the live pages.

## Still open (not this leg)

- The Perl/C++ **SDK docs bundles** (`documents/…`) still contain isolated-prefix install
  snippets; that is why they were refused when passed as publish artifacts. Correcting the
  snippets, or publishing the bundle from a clean directory, is a separate step.
- `live/index.html` and `live/README.md` were (re)published by other producers during this
  leg; each peer publish appends its own chained, signed entry.
