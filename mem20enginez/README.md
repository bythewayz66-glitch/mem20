# mem20enginez

Assimilated crew runtime for engine subsystems in the mem20 estate.

- **Members:** all absorbed engine subsystems rehomed under `mem20enginez/absorbed/` (auto-discovered). Current registry includes 31 absorbed members (code/READMEs/tests preserved in-place).
- **Peers:** core runtime peers (compatibility, protocol discovery, speculative workflow, service bundling, predictive recall, lifecycle) plus aggregated peer probes from absorbed member ecosystems, yielding a peer surface well above 6 (typically 50+ checks depending on environment).
- **Surfaces:** Python API (`domain`/`service`/`ecosystem`), CLI (`python -m mem20enginez ...`), JSON HTTP API/cockpit (`serve`).

## CLI

```bash
python -m mem20enginez --version
python -m mem20enginez --members
python -m mem20enginez status
python -m mem20enginez doctor
python -m mem20enginez members
python -m mem20enginez plan --intent "speculative protocol dispatch"
python -m mem20enginez simulate
python -m mem20enginez serve --port 8785
```

## Python API

```python
from mem20enginez.mem20enginez import MEMBERS, domain, ecosystem
from mem20enginez.mem20enginez.service import EngineRuntimeService

print(len(MEMBERS), MEMBERS[:3])
print(domain.summarize([domain.check_member(m) for m in MEMBERS]).members_present)
print(ecosystem.probe()["peer_surface_total"])  # core + absorbed member ecosystem peers
svc = EngineRuntimeService("state/enginez.db")
print(svc.status()["peer_surface_total"])
print(svc.plan("runtime compatibility and swarm dispatch")["ok"])
```

## Assimilation notes

Absorbed member source trees live in `absorbed/<member>/` with their tests under `tests/absorbed/<member>/` where present. Member probing locates absorbed directories and resolves imports via the repo absorbed-package finder when needed. Individual absorbed member probes may report environment/dependency limitations; aggregation and core runtime behavior remain real and reported truthfully.

## Tests

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20enginez/tests -q
```
