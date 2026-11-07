# mem20skillbasedprogressionbrainz — Skill-Based Progression Brain

First-class mem20 subsystem for skill-based progression (gain_xp/unlock_skill/level/progression_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20dynamicskillgraphz`, `mem20playermotivationtwinz`, `mem20rewardforgez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`.

## Python API (runnable)
```python
from mem20skillbasedprogressionbrainz.domain import gain_xp, unlock_skill, progression_report, probe
p=gain_xp({"xp":0},120); print(unlock_skill(p,"s1",20)["ok"])  # True
r=progression_report(); print(r["ok"], len(r["peers"]))  # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20skillbasedprogressionbrainz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20skillbasedprogressionbrainz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20skillbasedprogressionbrainz serve --port 8832
```

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20skillbasedprogressionbrainz/mem20skillbasedprogressionbrainz/tests -q --noconftest -p no:cacheprovider
```
