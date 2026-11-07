# mem20audiovoiceandmusicpipelinez — Audio, Voice & Music Pipeline

Mix tracks, normalize audio, sync to beats, export formats, and apply mastering chains, with **subsystem-specific** estate integration (6 peers chosen for this pipeline’s job — not a generic memory/focus/catalog/webhook template).

## Pipeline-specific peers (real calls, reported-not-fatal)

| peer | why it matters to this pipeline |
|---|---|
| `mem20assetintakecatalogingandvalidationpipelinez` | validate/catalog ingested audio assets |
| `mem20aiproductionstudiooperatingsystemz` | schedule stages and allocate studio capacity/resources |
| `mem20loreragcontentgeneratorz` | bind/generate subtitle/narrative context with quality/ranking |
| `mem20livemodelfusionz` | fuse voice/model outputs by confidence/health |
| `mem202dand3dartproductionoptimizationpipelinez` | production pipeline optimization and frame/batch budgeting |
| `mem20eventstreamsuperhighwayz` | publish pipeline events and measure throughput |

## Python API

```python
from mem20audiovoiceandmusicpipelinez.domain import (
    mix_tracks, normalize, sync_to_beat, export_format, mastering_chain,
    pipeline_report, probe, estate_context,
)

print(mix_tracks([{"id": "vox", "samples": [0.1, 0.2]}], volumes=[0.8]))
print(normalize([0.5, 1.0, -0.8], target_db=-3.0))
print(sync_to_beat(audio_len_s=10.0, bpm=120))
print(export_format([0] * 44100, fmt="wav", sample_rate=44100))
print(mastering_chain(["limit"], [1.5, -1.2, 0.2]))

report = pipeline_report(tracks=[{"id": "vox", "samples": [0.1, 0.2]}], samples=[0.5, 1.0], prompt="bind subtitle")
print(report["ok"], len(report["peers"]))
print(probe()["ok"])
print(estate_context()["peer_count"])
```

## MCP

Registered as real tools via `mcp.tools.mem20audiovoiceandmusicpipelinez_tools.AudioVoiceMusicPipelineToolsMixin` in `mcp/server.py` (`audiovoiceandmusicpipelinez_status`, `_doctor`, `_mix`, `_master`).

## CLI

```bash
python -m mem20audiovoiceandmusicpipelinez --help
```

## Tests

```bash
cd /opt/mem20 && PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20audiovoiceandmusicpipelinez/mem20audiovoiceandmusicpipelinez/tests -q --noconftest -p no:cacheprovider
```
