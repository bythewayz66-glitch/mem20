# mem20adapz — adaptive systems runtime

Unified organ for every former top-level package whose name contains **adaptive**.
Those packages are absorbed here; implementations are vendored under `members/`.

## Absorbed members (7)

| Short id | Former package |
|----------|----------------|
| achievement | mem20adaptiveachievementenginez |
| dispatch | mem20adaptivedispatchenginez |
| forgetting | mem20adaptiveforgettingenginez |
| inference | mem20adaptiveinferencemarketplacez |
| interface | mem20adaptiveinterfacecomposerz |
| personality | mem20adaptivepersonalityruntimez |
| pricing | mem20adaptivepricingbrainz |

```python
from mem20adapz import load_member
load_member("dispatch")
```

## Consolidate (local)

```bash
# 1) Copy full source trees into members/ (while old dirs still exist)
bash scripts/vendor_into_members.sh
git add mem20adapz/members mem20autoz/members
git commit -m "chore: vendor adaptive/auto organ sources into members/"

# 2) Remove former root directories
bash mem20adapz/DELETE_ORIGINALS.sh
bash mem20autoz/DELETE_ORIGINALS.sh
git commit -m "chore: remove absorbed adaptive/auto organ roots"
```

## CLI

```bash
mem20adapz --version
mem20adapz --members
```
