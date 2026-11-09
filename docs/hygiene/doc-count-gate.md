# Doc-count drift gate — `scripts/ops/check-doc-counts.py`

**Owner:** mem20-docuguard · **Gate:** `scripts/ops/check-doc-counts.py` · **CI:** `.github/workflows/doc-counts.yml`

The tool surface has moved several times — **257 → 258-260 → 265 → 268 → 270 →
306 → 487 tools** and **26 → 27 → 38 → 129 domains**. Every move left prose
behind that still presents the old number as *current*. This gate is the
mechanical backstop: it scans the live-doc surface for a retired band and fails
the run.

## What it does

- Reads the live pin (`tools`, `domains`) from **`docs/surface.json`** — the file
  generated from the live JSON-RPC `tools/list` response by
  `scripts/surface_manifest.py`. The pin is **never hardcoded in the gate**, so
  the gate cannot drift when the surface moves.
- Scans every **live doc** (scope below) for a retired band attached to the word
  *tools* / *domains*, or written as a `tools/domains` pair.
- Exits **1** on any violation, **0** when clean, **2** when it cannot run
  (`docs/surface.json` missing, or `git ls-files` fails).

## Retired bands

| kind | retired values |
|---|---|
| tools | `257`, `258`, `259`, `260`, `265`, `268`, `270`, `306` |
| domains | `26`, `27`, `38` |

The live pin is whatever `docs/surface.json` says (currently **487 tools / 39
domains**). A retired band is a violation **only** when it is attached to
*tools* / *domains* (or a `tools/domains` pair), so a bare number in geometry,
a version string or a line number is never a false positive.

## Scope — what counts as a "live" doc

Only docs that describe the surface *as it is today* are in scope:

- `docs/*.md` (top level) and `docs/hygiene/*.md`
- `docs/index.html` and `docs/dashboard.html`
- every `mem20*z/README.md` subsystem entry doc
- `README.md`, `SDKS.md`, `toolchest/README.md`

**Out of scope** (excluded by prefix or exact path): `published/` (the immutable
delivery archive, `MANIFEST`-pinned), `docs/audit/`, `docs/recon/`, `docs/ops/`,
`docs/app/narrative/`, `docs/app/deck/`, `docs/renovation/`, `ops/`,
`.sitemap/`, `CHANGELOG.md`, `DIARY.md`, `failures.md`, `AbsoluteTruth113.md`,
`toolchest/inventory.json`, and any file whose name carries a `YYYY-MM` date
stamp.

Dated records, audits and the archive are **history**: rewriting their numbers
would falsify the record rather than correct it. The gate leaves them alone.

## Retirement markers — the exemption rule

A retired band is legal on a line that *names* it as history. The gate asks "is
this presented as current?" and the only machine-checkable proxy for that is the
absence of a retirement marker on the same line. Markers are **line-local**, so
every exemption is auditable by eye:

`retired`, `predates`, `superseded`, `previous`, `prior`, `earlier`, `historic`,
`before the`, `no longer`, `old value`, `stale`, `was `, `were `, `used to`,
`formerly`, `legacy`, `deprecated`, `withdrawn`, `banned`.

Example — both lines pass:

```text
The server exposes 487 tools across 129 domains.      # live pin
The retired 270 / 27 pair is history.                # marker on the line
```

## Usage

```bash
python3 scripts/ops/check-doc-counts.py            # gate (exit 1 on drift)
python3 scripts/ops/check-doc-counts.py --list     # print the scope, then exit
python3 scripts/ops/check-doc-counts.py --root DIR # scan a different checkout
python3 scripts/ops/check-doc-counts.py --self-test
```

## CI

`.github/workflows/doc-counts.yml` runs the self-test and then the gate on every
push to `main`, every PR to `main`, and on `workflow_dispatch`. It needs no
dependencies beyond the standard library and a checkout.

## Relationship to `scripts/surface_manifest.py`

`surface_manifest.py --check` already validates a hand-listed set of
current-facing docs (`CURRENT_DOCS`) and the generated files. This gate is the
**whole-surface backstop**: it covers the subsystem READMEs and the rest of the
`docs/` tree that the manifest's short list does not, and it is the one that
fails on a retired band anywhere in a live doc. The two are complementary — run
both.

## Fixing a failure

Replace the retired band with the live pin, or mark the line as history if it is
genuinely describing a past state. Do **not** edit `docs/surface.json` to match a
stale doc — regenerate it from the live server with
`python3 scripts/surface_manifest.py --write`.
