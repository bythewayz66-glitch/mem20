# mem20famz

The family registry for the `mem20*z` packages.

## Why this exists

A clone audit hashed all 293 `mem20*z` packages with each package's own name
normalised out. **Only 65 distinct implementations exist** — 228 packages are
byte-identical copies of three templates. Because every clone could do every
sibling's job, a package's name told you nothing about what it contained.
`mem20adaptivepricingbrainz` contained no pricing brain.

So the groupings were decided deliberately, one at a time, and stored here as
data rather than left in a markdown table. This package makes package identity
**queryable**, so "which family does this belong to" has one answer rather than
as many as there are readers.

## What it does

| call | returns |
|---|---|
| `families()` | every family id |
| `purpose(f)` | what that family is for |
| `members(f)` | packages in that family |
| `family_of(pkg)` | the family a package belongs to, or `None` |
| `spec(pkg)` | family, name, purpose, what it must refuse, what proves it |
| `orphans()` | families with no members |
| `unmapped()` | packages with no family |
| `stats()` | integrity counters |

```bash
cd /opt/mem20/mem20famz
python3 -m mem20famz stats
python3 -m mem20famz which mem20adaptivepricingbrainz
python3 -m mem20famz spec  mem20adaptivepricingbrainz
```

## Current state

**231 packages, 15 families, 0 unmapped, 0 orphans.** Largest family 24
packages, smallest 4.

| family | packages | family | packages |
|---|---|---|---|
| simulation | 24 | markets-economics | 22 |
| production | 23 | compilation | 20 |
| networking | 19 | coordination | 15 |
| scheduling | 18 | human-team | 15 |
| learning-adaptation | 15 | interfaces | 14 |
| resilience | 12 | inference-serving | 11 |
| memory-cognition | 10 | trust-governance | 9 |
| platform | 4 | | |

## Two things worth knowing about how it was built

**An earlier keyword pass was discarded.** Scraping family keywords out of the
names left 161 of 231 packages unclassified, and the few that did match were
wrong. The stragglers here are assigned explicitly in `EXTRA_ASSIGN` rather than
inferred, because inference is what produced the original problem.

**A test caught a real defect.** `test_two_clones_can_land_in_different_families`
failed on first run: `adaptivepricingbrainz` and `adaptiveforgettingenginez`
both landed in `learning-adaptation`, because the generic key `adaptive`
(8 characters) outscored `pricing` (7). That is precisely the failure this
registry exists to prevent — the whole point is that names discriminate. Fixed
by dropping the over-broad key and assigning the ambiguous cases deliberately.
