# mem20adapz — adaptive systems runtime

Unified organ for every former top-level package whose name contains **adaptive**.
Those packages are **absorbed here** and removed from the monorepo root.

## Absorbed members (7)

| Former package | Short id |
|----------------|----------|
| `mem20adaptiveachievementenginez` | `achievement` |
| `mem20adaptivedispatchenginez` | `dispatch` |
| `mem20adaptiveforgettingenginez` | `forgetting` |
| `mem20adaptiveinferencemarketplacez` | `inference` |
| `mem20adaptiveinterfacecomposerz` | `interface` |
| `mem20adaptivepersonalityruntimez` | `personality` |
| `mem20adaptivepricingbrainz` | `pricing` |

Source and capability manifests for each member live under `mem20adapz/members/<short>/`
(and historically under the long name). Import via:

```python
from mem20adapz import MEMBERS, load_member
load_member("dispatch")
```

## CLI

```bash
mem20adapz --version
mem20adapz --members
```

## Status

Consolidation package: single product surface for adaptive engines. Member
implementations are retained under `members/`; root `mem20adaptive*` directories
are deleted after this merge.
